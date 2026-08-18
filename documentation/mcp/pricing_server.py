"""MCP Server: AWS Pricing — Estimación inteligente de costos AWS.

Herramientas disponibles:
  - get_service_price: Consulta precio de un servicio con filtros
  - estimate_monthly_cost: Calcula costo mensual con parámetros de uso
  - get_instance_types: Lista tipos de instancia disponibles
  - compare_pricing_options: Compara On-Demand vs Reserved vs Savings Plans
  - estimate_full_stack: Estima costo total de un stack completo
"""
import json
import sys
import boto3
import logging
from typing import Any

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mcp-pricing")

pricing_client = boto3.client("pricing", region_name="us-east-1")
REGION = "US East (N. Virginia)"

# ── Precios de referencia (fallback) ─────────────────────────────────────────
PRECIOS_REF = {
    "AmazonEC2": {
        "t3.micro": 0.0104, "t3.small": 0.0208, "t3.medium": 0.0416,
        "t3.large": 0.0832, "m5.large": 0.096, "m5.xlarge": 0.192,
        "m5.2xlarge": 0.384, "c5.large": 0.085, "c5.xlarge": 0.17,
        "r5.large": 0.126, "r5.xlarge": 0.252,
    },
    "AmazonRDS": {
        "db.t3.micro": 0.017, "db.t3.small": 0.034, "db.t3.medium": 0.068,
        "db.r5.large": 0.24, "db.r5.xlarge": 0.48, "db.r6g.large": 0.218,
    },
    "AmazonEKS": {"cluster": 0.10},
    "AmazonElastiCache": {
        "cache.t3.micro": 0.017, "cache.t3.medium": 0.068, "cache.r5.large": 0.166,
    },
    "AWSLambda": {"per_request": 0.0000002, "per_gb_second": 0.0000166667},
    "AmazonS3": {"standard_gb": 0.023, "ia_gb": 0.0125, "glacier_gb": 0.004},
    "AmazonCloudFront": {"per_gb": 0.085, "per_10k_requests": 0.01},
    "AWSWAF": {"web_acl": 5.0, "per_rule": 1.0, "per_million_requests": 0.60},
    "AmazonDynamoDB": {"wcu": 0.00065, "rcu": 0.00013, "storage_gb": 0.25},
    "NATGateway": {"per_hour": 0.045, "per_gb": 0.045},
    "ALB": {"per_hour": 0.0225, "per_lcu": 0.008},
}


# ── MCP Protocol Implementation ─────────────────────────────────────────────

def handle_request(request: dict) -> dict:
    """Procesa una solicitud MCP."""
    method = request.get("method", "")

    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "aws-pricing", "version": "1.0.0"}
        }

    elif method == "tools/list":
        return {"tools": TOOLS}

    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        arguments = request.get("params", {}).get("arguments", {})
        result = call_tool(tool_name, arguments)
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

    return {"error": {"code": -32601, "message": f"Method not found: {method}"}}


TOOLS = [
    {
        "name": "get_service_price",
        "description": "Consulta el precio de un servicio AWS específico con filtros opcionales. Retorna precio por hora/unidad, especificaciones del producto y términos de pago.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "service_code": {
                    "type": "string",
                    "description": "Código del servicio AWS: AmazonEC2, AmazonRDS, AmazonEKS, AWSLambda, AmazonS3, AmazonCloudFront, AmazonDynamoDB, AmazonElastiCache, AWSWAF, AmazonVPC, AmazonECS, AmazonSQS, AmazonSNS"
                },
                "instance_type": {
                    "type": "string",
                    "description": "Tipo de instancia (ej: m5.large, db.r5.large, cache.t3.medium)"
                },
                "database_engine": {
                    "type": "string",
                    "description": "Motor de base de datos para RDS (PostgreSQL, MySQL, Aurora PostgreSQL)"
                },
                "additional_filters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "value": {"type": "string"}
                        }
                    },
                    "description": "Filtros adicionales como tenancy, operatingSystem, etc."
                }
            },
            "required": ["service_code"]
        }
    },
    {
        "name": "estimate_monthly_cost",
        "description": "Calcula el costo mensual estimado de un servicio AWS basado en uso esperado. Considera horas de operación, número de instancias, storage y transferencia.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "service_code": {"type": "string", "description": "Código del servicio AWS"},
                "instance_type": {"type": "string", "description": "Tipo de instancia"},
                "hours_per_month": {"type": "number", "description": "Horas de uso al mes (730 = 24/7)", "default": 730},
                "instances": {"type": "integer", "description": "Número de instancias/réplicas", "default": 1},
                "storage_gb": {"type": "number", "description": "GB de almacenamiento", "default": 0},
                "data_transfer_gb": {"type": "number", "description": "GB de transferencia de datos mensual", "default": 0},
                "multi_az": {"type": "boolean", "description": "Si es Multi-AZ (duplica costo de instancia)", "default": False},
                "requests_per_month": {"type": "number", "description": "Número de requests/invocaciones al mes", "default": 0}
            },
            "required": ["service_code"]
        }
    },
    {
        "name": "get_instance_types",
        "description": "Lista los tipos de instancia disponibles para un servicio AWS con sus especificaciones (vCPU, memoria, precio/hora).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "service_code": {"type": "string", "description": "AmazonEC2, AmazonRDS, AmazonElastiCache"},
                "family": {"type": "string", "description": "Familia de instancias (t3, m5, r5, c5, db.r5, cache.t3)"}
            },
            "required": ["service_code"]
        }
    },
    {
        "name": "compare_pricing_options",
        "description": "Compara opciones de pricing: On-Demand vs 1yr Reserved vs 3yr Reserved vs Savings Plans para un servicio.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "service_code": {"type": "string"},
                "instance_type": {"type": "string"},
                "hours_per_month": {"type": "number", "default": 730},
                "instances": {"type": "integer", "default": 1}
            },
            "required": ["service_code", "instance_type"]
        }
    },
    {
        "name": "estimate_full_stack",
        "description": "Estima el costo mensual total de un stack completo de servicios AWS. Recibe una lista de servicios con sus especificaciones y retorna desglose + total.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "services": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "service": {"type": "string", "description": "Nombre del servicio (Amazon EKS, Amazon RDS, etc.)"},
                            "instance_type": {"type": "string"},
                            "instances": {"type": "integer", "default": 1},
                            "multi_az": {"type": "boolean", "default": False},
                            "storage_gb": {"type": "number", "default": 0},
                            "environment": {"type": "string", "enum": ["prod", "qa", "dev"], "default": "prod"}
                        },
                        "required": ["service"]
                    },
                    "description": "Lista de servicios a cotizar"
                },
                "include_base_services": {
                    "type": "boolean",
                    "description": "Incluir servicios base (CloudWatch, KMS, NAT Gateway, etc.)",
                    "default": True
                }
            },
            "required": ["services"]
        }
    }
]


def call_tool(name: str, args: dict) -> dict:
    """Ejecuta una herramienta MCP."""
    if name == "get_service_price":
        return _get_service_price(args)
    elif name == "estimate_monthly_cost":
        return _estimate_monthly_cost(args)
    elif name == "get_instance_types":
        return _get_instance_types(args)
    elif name == "compare_pricing_options":
        return _compare_pricing(args)
    elif name == "estimate_full_stack":
        return _estimate_full_stack(args)
    return {"error": f"Tool not found: {name}"}


def _get_service_price(args: dict) -> dict:
    service_code = args["service_code"]
    filters = [{"Type": "TERM_MATCH", "Field": "location", "Value": REGION}]

    if args.get("instance_type"):
        filters.append({"Type": "TERM_MATCH", "Field": "instanceType", "Value": args["instance_type"]})
    if args.get("database_engine"):
        filters.append({"Type": "TERM_MATCH", "Field": "databaseEngine", "Value": args["database_engine"]})
    for f in args.get("additional_filters", []):
        filters.append({"Type": "TERM_MATCH", "Field": f["field"], "Value": f["value"]})

    try:
        resp = pricing_client.get_products(ServiceCode=service_code, Filters=filters, MaxResults=5)
        results = []
        for item_str in resp.get("PriceList", []):
            item = json.loads(item_str)
            attrs = item.get("product", {}).get("attributes", {})
            on_demand = item.get("terms", {}).get("OnDemand", {})
            prices = []
            for term in on_demand.values():
                for dim in term.get("priceDimensions", {}).values():
                    usd = float(dim.get("pricePerUnit", {}).get("USD", "0"))
                    if usd > 0:
                        prices.append({"price_usd": usd, "unit": dim.get("unit", ""), "description": dim.get("description", "")})

            results.append({
                "instance_type": attrs.get("instanceType", ""),
                "vcpu": attrs.get("vcpu", ""),
                "memory": attrs.get("memory", ""),
                "storage": attrs.get("storage", ""),
                "engine": attrs.get("databaseEngine", ""),
                "os": attrs.get("operatingSystem", ""),
                "prices": prices
            })
        return {"service": service_code, "region": REGION, "results": results}
    except Exception as e:
        # Fallback a precios de referencia
        ref = PRECIOS_REF.get(service_code, {})
        instance = args.get("instance_type", "")
        price = ref.get(instance, list(ref.values())[0] if ref else None)
        return {"service": service_code, "region": REGION, "results": [{"instance_type": instance, "prices": [{"price_usd": price, "unit": "Hrs"}]}], "source": "reference_prices", "note": str(e)[:100]}


def _estimate_monthly_cost(args: dict) -> dict:
    service_code = args["service_code"]
    instance_type = args.get("instance_type", "")
    hours = args.get("hours_per_month", 730)
    instances = args.get("instances", 1)
    storage_gb = args.get("storage_gb", 0)
    transfer_gb = args.get("data_transfer_gb", 0)
    multi_az = args.get("multi_az", False)
    requests = args.get("requests_per_month", 0)

    # Obtener precio unitario
    ref = PRECIOS_REF.get(service_code, {})
    price_per_hour = ref.get(instance_type, 0)

    if not price_per_hour and ref:
        price_per_hour = list(ref.values())[0]

    # Calcular
    compute_cost = price_per_hour * hours * instances
    if multi_az:
        compute_cost *= 2

    storage_cost = storage_gb * 0.115  # EBS gp3 default
    transfer_cost = transfer_gb * 0.09  # Data transfer out

    # Lambda pricing
    if service_code == "AWSLambda" and requests:
        compute_cost = (requests * 0.0000002) + (requests * 0.5 * 0.0000166667)  # 500ms avg

    total = compute_cost + storage_cost + transfer_cost

    return {
        "service": service_code,
        "instance_type": instance_type,
        "breakdown": {
            "compute_usd": round(compute_cost, 2),
            "storage_usd": round(storage_cost, 2),
            "transfer_usd": round(transfer_cost, 2),
        },
        "monthly_usd": round(total, 2),
        "annual_usd": round(total * 12, 2),
        "config": {"hours": hours, "instances": instances, "multi_az": multi_az, "storage_gb": storage_gb}
    }


def _get_instance_types(args: dict) -> dict:
    service_code = args["service_code"]
    family = args.get("family", "")
    ref = PRECIOS_REF.get(service_code, {})

    results = []
    for itype, price in ref.items():
        if family and not itype.startswith(family):
            continue
        results.append({"instance_type": itype, "price_per_hour_usd": price, "monthly_730h_usd": round(price * 730, 2)})

    return {"service": service_code, "family": family, "instances": results}


def _compare_pricing(args: dict) -> dict:
    service_code = args["service_code"]
    instance_type = args["instance_type"]
    hours = args.get("hours_per_month", 730)
    instances = args.get("instances", 1)

    ref = PRECIOS_REF.get(service_code, {})
    on_demand = ref.get(instance_type, 0.10)
    monthly_od = on_demand * hours * instances

    return {
        "service": service_code,
        "instance_type": instance_type,
        "options": {
            "on_demand": {"monthly_usd": round(monthly_od, 2), "annual_usd": round(monthly_od * 12, 2), "savings": "0%"},
            "1yr_reserved_no_upfront": {"monthly_usd": round(monthly_od * 0.60, 2), "annual_usd": round(monthly_od * 0.60 * 12, 2), "savings": "~40%"},
            "3yr_reserved_all_upfront": {"monthly_usd": round(monthly_od * 0.40, 2), "annual_usd": round(monthly_od * 0.40 * 12, 2), "savings": "~60%"},
            "savings_plan_1yr": {"monthly_usd": round(monthly_od * 0.65, 2), "annual_usd": round(monthly_od * 0.65 * 12, 2), "savings": "~35%"},
        },
        "recommendation": "Para cargas estables en producción, Savings Plans 1yr ofrece buen balance entre ahorro y flexibilidad."
    }


def _estimate_full_stack(args: dict) -> dict:
    services = args["services"]
    include_base = args.get("include_base_services", True)

    items = []
    total = 0

    for svc in services:
        name = svc["service"].lower()
        env = svc.get("environment", "prod")
        instances = svc.get("instances", 1)
        multi_az = svc.get("multi_az", env == "prod")
        storage = svc.get("storage_gb", 0)

        # Mapear servicio a código
        service_code = _map_service_name(name)
        instance_type = svc.get("instance_type", _default_instance(service_code, env))

        est = _estimate_monthly_cost({
            "service_code": service_code,
            "instance_type": instance_type,
            "hours_per_month": 730,
            "instances": instances,
            "storage_gb": storage,
            "multi_az": multi_az,
        })

        items.append({
            "service": svc["service"],
            "instance_type": instance_type,
            "instances": instances,
            "multi_az": multi_az,
            "monthly_usd": est["monthly_usd"],
            "environment": env
        })
        total += est["monthly_usd"]

    # Servicios base
    if include_base:
        base = [
            {"service": "NAT Gateway", "monthly_usd": 45.0},
            {"service": "CloudWatch", "monthly_usd": 15.0},
            {"service": "KMS", "monthly_usd": 1.0},
            {"service": "Secrets Manager", "monthly_usd": 0.80},
            {"service": "Route 53", "monthly_usd": 0.50},
        ]
        for b in base:
            items.append({**b, "instance_type": "-", "instances": 1, "multi_az": False, "environment": "shared"})
            total += b["monthly_usd"]

    return {
        "items": items,
        "total_monthly_usd": round(total, 2),
        "total_annual_usd": round(total * 12, 2),
        "currency": "USD",
        "region": "us-east-1",
        "notes": [
            "Precios On-Demand sin descuentos aplicados",
            "No incluye transferencia de datos entre AZs",
            "Storage EBS calculado como gp3",
            "Evaluar Savings Plans para reducir 30-40%"
        ]
    }


def _map_service_name(name: str) -> str:
    mapping = {
        "ec2": "AmazonEC2", "eks": "AmazonEKS", "ecs": "AmazonECS",
        "rds": "AmazonRDS", "aurora": "AmazonRDS", "dynamodb": "AmazonDynamoDB",
        "elasticache": "AmazonElastiCache", "redis": "AmazonElastiCache",
        "s3": "AmazonS3", "cloudfront": "AmazonCloudFront",
        "lambda": "AWSLambda", "waf": "AWSWAF", "alb": "ALB", "nlb": "ALB",
    }
    for key, val in mapping.items():
        if key in name:
            return val
    return "AmazonEC2"


def _default_instance(service_code: str, env: str) -> str:
    defaults = {
        "AmazonEC2": {"prod": "m5.large", "qa": "t3.medium", "dev": "t3.small"},
        "AmazonRDS": {"prod": "db.r5.large", "qa": "db.t3.medium", "dev": "db.t3.small"},
        "AmazonElastiCache": {"prod": "cache.r5.large", "qa": "cache.t3.medium", "dev": "cache.t3.micro"},
        "AmazonEKS": {"prod": "m5.large", "qa": "t3.medium", "dev": "t3.medium"},
    }
    return defaults.get(service_code, {}).get(env, "t3.medium")


# ── Main: stdio MCP transport ────────────────────────────────────────────────

def main():
    """MCP Server usando transporte stdio (JSON-RPC 2.0)."""
    logger.info("AWS Pricing MCP Server started")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            response["jsonrpc"] = "2.0"
            response["id"] = request.get("id")
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            error_resp = {"jsonrpc": "2.0", "id": request.get("id") if 'request' in dir() else None,
                         "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(error_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
