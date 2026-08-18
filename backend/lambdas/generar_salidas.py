"""POST /iniciativas/{id}/generar/{tipo} — Genera diagrama/documento/costos (async).

A partir de la Ficha Técnica extraída, genera artefactos de salida usando Claude:
- diagrama: archivo draw.io XML con la topología de arquitectura
- documento: documento de arquitectura en Markdown
- costos: estimación CSV compatible con AWS Pricing Calculator
"""
import json
import time

import boto3

from common.claude_client import ClaudeClient
from common.helpers import build_response, S3Helper, DynamoHelper, log_event

lambda_client = boto3.client("lambda")


def handler(event, context):
    """Punto de entrada: responde 202 al cliente e invoca generación async."""
    # Si es invocación directa async, ejecutar la generación
    if event.get("_async_generate"):
        return _generate(event["id_iniciativa"], event["tipo"])

    id_iniciativa = event.get("pathParameters", {}).get("id", "")
    tipo = event.get("pathParameters", {}).get("tipo", "")

    if not id_iniciativa or tipo not in ("diagrama", "documento", "costos"):
        return build_response(400, {"error": "id_iniciativa y tipo (diagrama|documento|costos) requeridos"})

    meta = DynamoHelper.get_meta(id_iniciativa)
    if not meta:
        return build_response(404, {"error": "Iniciativa no encontrada"})

    lambda_client.invoke(
        FunctionName=context.function_name,
        InvocationType="Event",
        Payload=json.dumps({"_async_generate": True, "id_iniciativa": id_iniciativa, "tipo": tipo}),
    )
    return build_response(202, {"id_iniciativa": id_iniciativa, "tipo": tipo, "status": "GENERANDO"})


def _generate(id_iniciativa: str, tipo: str):
    """Lee la ficha desde S3, genera el artefacto con Claude y guarda en S3."""
    start = time.time()
    meta = DynamoHelper.get_meta(id_iniciativa)
    prefix = meta.get("s3_prefix", f"iniciativas/{id_iniciativa}")

    try:
        ficha_text = S3Helper.read_text(f"{prefix}/ficha/ficha.json")
        ficha = json.loads(ficha_text)
    except Exception:
        DynamoHelper.put_event(id_iniciativa, "ERROR", {"detalle": "Ficha no encontrada para generación"})
        return

    client = ClaudeClient()

    if tipo == "diagrama":
        _gen_diagrama(client, ficha, prefix, id_iniciativa)
    elif tipo == "documento":
        _gen_documento(client, ficha, prefix, id_iniciativa)
    elif tipo == "costos":
        _gen_costos(client, ficha, prefix, id_iniciativa)

    duracion_ms = int((time.time() - start) * 1000)
    salidas = meta.get("salidas", {})
    salidas[tipo] = f"{prefix}/salidas/{_filename(tipo)}"
    DynamoHelper.update_meta(id_iniciativa, {
        "salidas": salidas,
        "estado": "GENERADO",
        "GSI1PK": "ESTADO#GENERADO",
        "GSI1SK": DynamoHelper.now_iso(),
        "fecha_actualizacion": DynamoHelper.now_iso(),
    })
    DynamoHelper.put_event(id_iniciativa, f"GENERADO_{tipo.upper()}", {"duracion_ms": duracion_ms})
    log_event(f"generar_{tipo}", {"id_iniciativa": id_iniciativa, "duracion_ms": duracion_ms})


def _gen_diagrama(client: ClaudeClient, ficha: dict, prefix: str, id_ini: str):
    """Genera un archivo draw.io XML con la topología de arquitectura usando iconos AWS."""
    componentes = ficha.get("componentes", {})
    topologia = ficha.get("topologia", {})
    if not componentes and not topologia:
        DynamoHelper.put_event(id_ini, "ERROR", {"detalle": "Diagrama requiere componentes y topología"})
        return

    system = "Genera un archivo draw.io XML válido con la topología de arquitectura cloud proporcionada. Usa iconos AWS estándar."
    prompt = f"Genera el XML draw.io para esta arquitectura:\nComponentes: {json.dumps(componentes)}\nTopología: {json.dumps(topologia)}"
    result = client.generate(system, prompt)
    S3Helper.put_bytes(f"{prefix}/salidas/diagrama.drawio", result["text"].encode(), "application/xml")


def _gen_documento(client: ClaudeClient, ficha: dict, prefix: str, id_ini: str):
    """Genera un documento de arquitectura en Markdown a partir de la ficha completa."""
    system = "Genera un documento de arquitectura cloud en formato Markdown estructurado. Marca como 'Pendiente' las secciones sin información."
    prompt = f"Genera el documento de arquitectura para esta Ficha Técnica:\n{json.dumps(ficha, ensure_ascii=False)}"
    result = client.generate(system, prompt, max_tokens=16384)
    S3Helper.put_bytes(f"{prefix}/salidas/documento.md", result["text"].encode(), "text/markdown")


def _gen_costos(client: ClaudeClient, ficha: dict, prefix: str, id_ini: str):
    """Genera estimación de costos en CSV compatible con AWS Pricing Calculator."""
    componentes = ficha.get("componentes", {})
    if not any(componentes.values()):
        DynamoHelper.put_event(id_ini, "ERROR", {"detalle": "Costos requiere specs de componentes"})
        return

    system = "Genera una estimación de costos AWS en formato CSV compatible con AWS Pricing Calculator bulk import. Columnas: Service, Description, Region, Monthly Cost (USD), Notes."
    prompt = f"Estima costos para estos componentes:\n{json.dumps(componentes, ensure_ascii=False)}\nProyecto nube: {ficha.get('proyecto', {}).get('nube', 'AWS')}"
    result = client.generate(system, prompt)
    S3Helper.put_bytes(f"{prefix}/salidas/costos.csv", result["text"].encode(), "text/csv")


def _filename(tipo: str) -> str:
    """Mapea el tipo de salida al nombre de archivo correspondiente."""
    return {"diagrama": "diagrama.drawio", "documento": "documento.md", "costos": "costos.csv"}[tipo]
