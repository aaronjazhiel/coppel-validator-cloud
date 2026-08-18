"""POST /iniciativas — Crea iniciativa y devuelve URLs prefirmadas.

Este módulo maneja la creación de nuevas iniciativas de arquitectura cloud.
Recibe los datos básicos del proyecto y genera URLs prefirmadas de S3
para que el cliente suba los archivos de insumo directamente al bucket.
"""
import json
from common.helpers import build_response, S3Helper, DynamoHelper, log_event

# Tipos de insumo soportados por la plataforma
INSUMO_TIPOS = ["discovery", "diagrama", "transcripciones", "componentes"]

CONTENT_TYPE = "application/octet-stream"


def handler(event, context):
    """Handler principal invocado por API Gateway (POST /iniciativas)."""
    # Parsear el body del request
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return build_response(400, {"error": "Body JSON inválido"})

    id_iniciativa = body.get("id_iniciativa", "").strip()
    nombre = body.get("nombre", "").strip()
    ambiente = body.get("ambiente", "Prod").strip()
    solicitante = body.get("solicitante", "").strip()
    descripcion = body.get("descripcion", "").strip()
    nube = body.get("nube", "AWS").strip()
    business_tags = body.get("business_tags", {})

    # Validar campos obligatorios
    if not id_iniciativa or not nombre or not solicitante:
        return build_response(400, {"error": "id_iniciativa, nombre y solicitante son obligatorios"})

    # Idempotencia: si ya existe, solo regenera URLs sin duplicar el registro
    existing = DynamoHelper.get_meta(id_iniciativa)
    if existing:
        # Regenerar URLs prefirmadas solo para archivos solicitados
        archivos = body.get("archivos", {})
        urls = _generate_urls(id_iniciativa, archivos, only_requested=True)
        return build_response(200, {"id_iniciativa": id_iniciativa, "upload_urls": urls, "message": "Iniciativa ya existente, URLs regeneradas"})

    # Crear registro en DynamoDB con estado inicial INGESTA
    s3_prefix = f"iniciativas/{id_iniciativa}"
    now = DynamoHelper.now_iso()

    item = {
        "PK": f"INIT#{id_iniciativa}",
        "SK": "META",
        "GSI1PK": "ESTADO#INGESTA",
        "GSI1SK": now,
        "id_iniciativa": id_iniciativa,
        "nombre": nombre,
        "descripcion": descripcion,
        "ambiente": ambiente,
        "solicitante": solicitante,
        "nube": nube,
        "business_tags": business_tags,
        "estado": "INGESTA",
        "completitud": 0,
        "huecos": [],
        "s3_prefix": s3_prefix,
        "insumos": [],
        "salidas": {},
        "fecha_creacion": now,
        "fecha_actualizacion": now,
    }
    DynamoHelper.put_meta(item)

    # Generar URLs prefirmadas para subida directa a S3
    urls = _generate_urls(id_iniciativa, body.get("archivos", {}))

    # Registrar evento de auditoría y log estructurado
    DynamoHelper.put_event(id_iniciativa, "CREADA", {"solicitante": solicitante})
    log_event("crear_iniciativa", {"id_iniciativa": id_iniciativa})

    return build_response(201, {"id_iniciativa": id_iniciativa, "upload_urls": urls})


def _generate_urls(id_iniciativa: str, archivos: dict, only_requested: bool = False) -> dict:
    """Genera URLs prefirmadas PUT de S3 para cada archivo agrupado por tipo de insumo."""
    urls = {}
    tipos = archivos.keys() if only_requested else INSUMO_TIPOS
    for tipo in tipos:
        if tipo not in INSUMO_TIPOS:
            continue
        files = archivos.get(tipo, [])
        if not files and not only_requested:
            files = [f"{tipo}_file"]
        if not files:
            continue
        urls[tipo] = []
        for filename in files:
            key = f"iniciativas/{id_iniciativa}/insumos/{tipo}/{filename}"
            url = S3Helper.presigned_put(key, CONTENT_TYPE)
            urls[tipo].append({"filename": filename, "key": key, "upload_url": url})
    return urls
