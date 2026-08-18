"""AWS Pricing MCP — Usa Claude como agente inteligente de costos AWS.

Implementa el patrón Model Context Protocol (MCP) donde Claude actúa como
orquestador que decide qué consultas hacer a la AWS Pricing API basándose
en el contexto de los servicios identificados y sus especificaciones.

Flujo:
  1. Recibe lista de servicios con contexto (sizing, uso esperado, ambiente)
  2. Claude decide los filtros óptimos para cada servicio
  3. Ejecuta las consultas a AWS Pricing API
  4. Claude interpreta los resultados y calcula estimaciones mensuales realistas
"""
import json
import boto3
import logging
from typing import Any

logger = logging.getLogger()

pricing_client = boto3.client("pricing", region_name="us-east-1")
REGION_FILTER = "US East (N. Virginia)"

# ── Herramientas MCP disponibles para Claude ─────────────────────────────────

MCP_TOOLS = [
    {
        "name": "get_aws_price",
        "description": "Consulta el precio de un servicio AWS usando la Pricing API con filtros específicos. Retorna precio por unidad y detalles del producto.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_code": {
                    "type": "string",
                    "description": "Código del servicio AWS (ej: AmazonEC2, AmazonRDS, AmazonEKS, AWSLambda, AmazonS3)"
                },
                "filters": {
                    "type": "array",
                    "description": "Filtros para la consulta de precios",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string", "description": "Campo a filtrar (ej: instanceType, databaseEngine, storageClass)"},
                            "value": {"type": "string", "description": "Valor del filtro"}
                        },
                        "required": ["field", "value"]
                    }
                },
                "max_results": {
                    "type": "integer",
                    "description": "Máximo de resultados a retornar (default 3)",
                    "default": 3
                }
            },
            "required": ["service_code"]
        }
    },
    {
        "name": "calculate_monthly_cost",
        "description": "Calcula el costo mensual estimado dado un precio por hora/unidad y parámetros de uso.",
        "input_schema": {
            "type": "object",
            "properties": {
                "price_per_unit": {"type": "number", "description": "Precio por unidad (hora, GB, request, etc.)"},
                "unit_type": {"type": "string", "enum": ["hour", "gb_month", "request", "gb_transfer", "unit"], "description": "Tipo de unidad del precio"},
                "quantity": {"type": "number", "description": "Cantidad de uso mensual estimado"},
                "hours_per_month": {"type": "number", "description": "Horas de uso al mes (default 730 para 24/7)", "default": 730},
                "instances": {"type": "integer", "description": "Número de instancias/réplicas", "default": 1}
            },
            "required": ["price_per_unit", "unit_type", "quantity"]
        }
    },
    {
        "name": "list_service_offerings",
        "description": "Lista las opciones disponibles para un servicio AWS (tipos de instancia, engines, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_code": {"type": "string", "description": "Código del servicio AWS"},
                "attribute_name": {"type": "string", "description": "Atributo a listar (ej: instanceType, databaseEngine)"}
            },
            "required": ["service_code", "attribute_name"]
        }
    }
]

# ── Ejecutor de herramientas MCP ─────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Ejecuta una herramienta MCP y retorna el resultado."""
    if tool_name == "get_aws_price":
        return _tool_get_price(tool_input)
    elif tool_name == "calculate_monthly_cost":
        return _tool_calculate_monthly(tool_input)
    elif tool_name == "list_service_offerings":
        return _tool_list_offerings(tool_input)
    return {"error": f"Herramienta desconocida: {tool_name}"}


def _tool_get_price(params: dict) -> dict:
    """Consulta AWS Pricing API con filtros."""
    service_code = params["service_code"]
    filters = [{"Type": "TERM_MATCH", "Field": "location", "Value": REGION_FILTER}]

    for f in params.get("filters", []):
        filters.append({"Type": "TERM_MATCH", "Field": f["field"], "Value": f["value"]})

    try:
        resp = pricing_client.get_products(
            ServiceCode=service_code,
            Filters=filters,
            MaxResults=params.get("max_results", 3)
        )
        results = []
        for item_str in resp.get("PriceList", []):
            item = json.loads(item_str)
            product = item.get("product", {})
            attrs = product.get("attributes", {})
            on_demand = item.get("terms", {}).get("OnDemand", {})

            prices = []
            for term in on_demand.values():
                for dim in term.get("priceDimensions", {}).values():
                    usd = dim.get("pricePerUnit", {}).get("USD", "0")
                    if float(usd) > 0:
                        prices.append({
                            "description": dim.get("description", ""),
                            "unit": dim.get("unit", ""),
                            "price_usd": float(usd)
                        })

            results.append({
                "service": attrs.get("servicename", service_code),
                "instance_type": attrs.get("instanceType", ""),
                "vcpu": attrs.get("vcpu", ""),
                "memory": attrs.get("memory", ""),
                "storage": attrs.get("storage", ""),
                "engine": attrs.get("databaseEngine", ""),
                "usage_type": attrs.get("usagetype", ""),
                "operation": attrs.get("operation", ""),
                "prices": prices
            })

        return {"results": results, "count": len(results)}

    except Exception as e:
        return {"error": str(e)[:200], "results": [], "count": 0}


def _tool_calculate_monthly(params: dict) -> dict:
    """Calcula costo mensual basado en uso."""
    price = params["price_per_unit"]
    unit_type = params["unit_type"]
    quantity = params["quantity"]
    hours = params.get("hours_per_month", 730)
    instances = params.get("instances", 1)

    if unit_type == "hour":
        monthly = price * hours * instances
    elif unit_type == "gb_month":
        monthly = price * quantity * instances
    elif unit_type == "request":
        monthly = price * quantity  # quantity = millones de requests
    elif unit_type == "gb_transfer":
        monthly = price * quantity
    else:  # unit
        monthly = price * quantity * instances

    return {
        "monthly_usd": round(monthly, 2),
        "annual_usd": round(monthly * 12, 2),
        "calculation": f"{price} x {quantity} {unit_type} x {instances} instancias = ${monthly:.2f}/mes"
    }


def _tool_list_offerings(params: dict) -> dict:
    """Lista atributos disponibles para un servicio."""
    try:
        resp = pricing_client.get_attribute_values(
            ServiceCode=params["service_code"],
            AttributeName=params["attribute_name"],
            MaxResults=20
        )
        values = [v["Value"] for v in resp.get("AttributeValues", [])]
        return {"attribute": params["attribute_name"], "values": values[:20]}
    except Exception as e:
        return {"error": str(e)[:200], "values": []}


# ── Orquestador MCP Principal ────────────────────────────────────────────────

def estimar_costos_mcp(servicios: list, contexto: str = "") -> dict:
    """Usa Claude como agente MCP para estimar costos AWS de forma inteligente.

    Args:
        servicios: Lista de servicios identificados con justificación y prioridad
        contexto: Contexto adicional del proyecto (sizing, usuarios, etc.)

    Returns:
        Dict con servicios_cotizados, total_mensual_usd, total_anual_usd, detalle_calculo
    """
    from common.claude_client import ClaudeClient
    client = ClaudeClient()

    system_prompt = """Eres un arquitecto de costos AWS experto. Tu tarea es estimar los costos mensuales 
de cada servicio AWS usando las herramientas disponibles.

REGLAS:
1. Para cada servicio, usa get_aws_price con filtros apropiados para obtener precios reales
2. Usa calculate_monthly_cost para calcular el costo mensual basado en uso típico
3. Si no encuentras precio exacto, estima basándote en tu conocimiento de precios AWS
4. Considera: instancias Multi-AZ para producción, storage adicional, transferencia de datos
5. Sé conservador en las estimaciones (mejor estimar de más que de menos)

SIZING POR DEFECTO (si no se especifica):
- EC2/EKS: t3.medium para dev, m5.large para prod
- RDS: db.t3.medium para dev, db.r5.large para prod con Multi-AZ
- ElastiCache: cache.t3.medium
- S3: 100GB standard
- Lambda: 1M invocaciones/mes
- CloudFront: 100GB transfer
- NAT Gateway: 100GB procesados
- ALB: 1 LCU promedio

Responde ÚNICAMENTE con JSON válido con esta estructura:
{
  "servicios_cotizados": [
    {
      "servicio": "nombre del servicio",
      "categoria": "COMPUTO|BD|RED|SEGURIDAD|etc",
      "especificacion": "t3.medium, db.r5.large, etc",
      "prioridad": "REQUERIDO|RECOMENDADO|OPCIONAL",
      "precio_unitario_usd": 0.0,
      "unidad": "hora|GB|request",
      "cantidad_mensual": 730,
      "instancias": 1,
      "precio_mensual_usd": 0.0,
      "nota": "detalle del cálculo"
    }
  ],
  "total_mensual_usd": 0.0,
  "total_anual_usd": 0.0,
  "supuestos": ["lista de supuestos usados para la estimación"],
  "recomendaciones_ahorro": ["Savings Plans", "Reserved Instances", etc]
}"""

    user_prompt = f"""Estima los costos mensuales AWS para los siguientes servicios identificados en un proyecto:

## Servicios a cotizar:
{json.dumps(servicios, ensure_ascii=False, indent=2)}

## Contexto del proyecto:
{contexto or "Proyecto empresarial en producción, región us-east-1, alta disponibilidad requerida."}

Usa las herramientas para consultar precios reales de AWS y calcula los costos mensuales.
Para cada servicio, busca el precio con los filtros más apropiados según las especificaciones.
"""

    # Llamada con tool_use iterativo (MCP loop)
    messages = [{"role": "user", "content": user_prompt}]
    max_iterations = 8  # Máximo de ciclos tool_use
    iteration = 0

    import anthropic
    import os

    secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
    secret = secrets_client.get_secret_value(SecretId="coppel-cloud/anthropic-api-key")
    api_key = json.loads(secret["SecretString"])["api_key"]
    anthropic_client = anthropic.Anthropic(api_key=api_key)

    while iteration < max_iterations:
        iteration += 1

        response = anthropic_client.messages.create(
            model="claude-sonnet-5",
            max_tokens=4096,
            system=system_prompt,
            tools=MCP_TOOLS,
            messages=messages
        )

        # Procesar respuesta
        if response.stop_reason == "end_turn":
            # Claude terminó — extraer JSON final
            for block in response.content:
                if hasattr(block, "text"):
                    return _parse_cost_response(block.text)
            break

        elif response.stop_reason == "tool_use":
            # Claude quiere usar herramientas
            tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"MCP Tool Call: {block.name}({json.dumps(block.input)[:100]})")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str)
                    })

            # Agregar respuesta del asistente y resultados de herramientas
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

        else:
            break

    # Fallback si no se obtuvo respuesta válida
    logger.warning("MCP: No se obtuvo respuesta válida de Claude, usando fallback")
    return _fallback_pricing(servicios)


def _parse_cost_response(text: str) -> dict:
    """Parsea la respuesta JSON de Claude con los costos."""
    import re
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return _empty_result()


def _fallback_pricing(servicios: list) -> dict:
    """Fallback con precios estimados si MCP falla."""
    PRECIOS_REFERENCIA = {
        "ec2": {"precio": 67.0, "nota": "m5.large 730h"},
        "eks": {"precio": 73.0, "nota": "cluster $0.10/h + nodos"},
        "ecs": {"precio": 40.0, "nota": "Fargate 2vCPU/4GB"},
        "rds": {"precio": 180.0, "nota": "db.r5.large Multi-AZ"},
        "aurora": {"precio": 220.0, "nota": "2 instancias db.r5.large"},
        "dynamodb": {"precio": 25.0, "nota": "On-demand 1M reads/writes"},
        "elasticache": {"precio": 50.0, "nota": "cache.t3.medium"},
        "s3": {"precio": 2.3, "nota": "100GB Standard"},
        "cloudfront": {"precio": 8.5, "nota": "100GB transfer"},
        "lambda": {"precio": 5.0, "nota": "1M invocaciones 256MB"},
        "alb": {"precio": 22.0, "nota": "1 ALB + 1 LCU"},
        "nlb": {"precio": 22.0, "nota": "1 NLB + 1 NLCU"},
        "waf": {"precio": 6.0, "nota": "1 Web ACL + 5 reglas"},
        "kms": {"precio": 1.0, "nota": "1 CMK + 10K requests"},
        "secrets_manager": {"precio": 0.4, "nota": "1 secreto"},
        "cloudwatch": {"precio": 10.0, "nota": "Dashboards + logs básicos"},
        "nat_gateway": {"precio": 45.0, "nota": "1 NAT + 100GB"},
        "vpc": {"precio": 0.0, "nota": "Sin costo base"},
        "route53": {"precio": 0.5, "nota": "1 hosted zone"},
        "sqs": {"precio": 0.4, "nota": "1M mensajes"},
        "sns": {"precio": 0.5, "nota": "1M notificaciones"},
        "backup": {"precio": 5.0, "nota": "50GB warm storage"},
        "guardduty": {"precio": 4.0, "nota": "Análisis básico"},
        "ecr": {"precio": 1.0, "nota": "10GB imágenes"},
    }

    resultado = {"servicios_cotizados": [], "total_mensual_usd": 0, "total_anual_usd": 0,
                 "supuestos": ["Precios de referencia us-east-1", "Sizing estándar producción"],
                 "recomendaciones_ahorro": ["Evaluar Savings Plans para cómputo (ahorro 30-40%)",
                                            "Reserved Instances para RDS (ahorro 40-60%)"]}

    for svc in servicios:
        nombre = svc.get("servicio", "").lower()
        matched = None
        for key, val in PRECIOS_REFERENCIA.items():
            if key in nombre.replace(" ", "").replace("amazon", "").replace("aws", ""):
                matched = val
                break

        precio = matched["precio"] if matched else None
        nota = matched["nota"] if matched else "Consultar calculadora AWS"

        resultado["servicios_cotizados"].append({
            "servicio": svc.get("servicio", ""),
            "categoria": svc.get("categoria", ""),
            "especificacion": nota.split(" ")[0] if matched else "",
            "prioridad": svc.get("prioridad", ""),
            "precio_mensual_usd": precio,
            "nota": nota
        })
        if precio:
            resultado["total_mensual_usd"] += precio

    resultado["total_mensual_usd"] = round(resultado["total_mensual_usd"], 2)
    resultado["total_anual_usd"] = round(resultado["total_mensual_usd"] * 12, 2)
    return resultado


def _empty_result() -> dict:
    return {"servicios_cotizados": [], "total_mensual_usd": 0, "total_anual_usd": 0,
            "supuestos": [], "recomendaciones_ahorro": []}
