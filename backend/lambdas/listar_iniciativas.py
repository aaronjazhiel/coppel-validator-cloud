"""GET /iniciativas — Lista iniciativas. GET /iniciativas/{id} — Detalle.

Maneja dos endpoints:
- GET /iniciativas: Retorna lista de todas las iniciativas (filtrable por estado).
- GET /iniciativas/{id}: Retorna detalle completo con URLs de descarga para salidas.
"""
import json
from common.helpers import build_response, DynamoHelper, S3Helper


def handler(event, context):
    """Dispatcher: redirige a detalle o listado según la presencia de path parameter."""
    path_params = event.get("pathParameters") or {}
    id_iniciativa = path_params.get("id")
    path = event.get("path", "")

    if id_iniciativa and path.endswith("/resultados/discovery"):
        return _resultado_discovery(id_iniciativa)
    if id_iniciativa and path.endswith("/resultados/n2"):
        return _resultado_n2(id_iniciativa)
    if id_iniciativa and path.endswith("/resultados/costos"):
        return _resultado_costos(id_iniciativa)
    if id_iniciativa and path.endswith("/resultados/servicios"):
        return _resultado_servicios(id_iniciativa)
    if id_iniciativa and path.endswith("/progreso"):
        return _progreso(id_iniciativa)
    if id_iniciativa:
        # Admin: PATCH estado via query param
        qs = event.get("queryStringParameters") or {}
        if qs.get("set_estado"):
            DynamoHelper.update_meta(id_iniciativa, {"estado": qs["set_estado"]})
            return build_response(200, {"ok": True, "estado": qs["set_estado"]})
        return _obtener(id_iniciativa)
    return _listar(event)


def _listar(event):
    """Retorna lista resumida de iniciativas, filtrable por estado vía query string."""
    qs = event.get("queryStringParameters") or {}
    estado = qs.get("estado")

    # Consultar por GSI si se filtra por estado, scan general si no
    if estado:
        items = DynamoHelper.query_by_estado(estado)
    else:
        items = DynamoHelper.scan_all_meta()

    # Proyectar solo campos relevantes para el listado
    result = []
    for item in items:
        result.append({
            "id_iniciativa": item.get("id_iniciativa"),
            "nombre": item.get("nombre"),
            "ambiente": item.get("ambiente"),
            "estado": item.get("estado"),
            "completitud": item.get("completitud", 0),
            "solicitante": item.get("solicitante"),
            "fecha_creacion": item.get("fecha_creacion"),
            "fecha_actualizacion": item.get("fecha_actualizacion"),
        })
    return build_response(200, {"iniciativas": result})


def _resultado_discovery(id_iniciativa: str):
    """Retorna el JSON de validación del discovery desde S3."""
    try:
        data = S3Helper.read_text(f"iniciativas/{id_iniciativa}/resultados/validacion_discovery.json")
        import json as _json
        return build_response(200, _json.loads(data))
    except Exception:
        return build_response(404, {"error": "Resultado de validación no disponible aún"})

def _resultado_n2(id_iniciativa: str):
    """Retorna el JSON de validación N2 desde S3."""
    try:
        data = S3Helper.read_text(f"iniciativas/{id_iniciativa}/resultados/validacion_n2.json")
        import json as _json
        return build_response(200, _json.loads(data))
    except Exception:
        return build_response(404, {"error": "Resultado de validación N2 no disponible aún"})

def _resultado_costos(id_iniciativa: str):
    """Retorna el JSON de costos estimados desde S3."""
    try:
        data = S3Helper.read_text(f"iniciativas/{id_iniciativa}/resultados/costos_estimados.json")
        import json as _json
        return build_response(200, _json.loads(data))
    except Exception:
        return build_response(404, {"error": "Estimación de costos no disponible aún"})

def _resultado_servicios(id_iniciativa: str):
    """Retorna el JSON de servicios AWS identificados desde S3."""
    try:
        data = S3Helper.read_text(f"iniciativas/{id_iniciativa}/resultados/servicios_aws.json")
        import json as _json
        return build_response(200, _json.loads(data))
    except Exception:
        return build_response(404, {"error": "Servicios no disponibles aún"})


def _progreso(id_iniciativa: str):
    """Retorna progreso de generación desde S3."""
    try:
        data = S3Helper.read_text(f"iniciativas/{id_iniciativa}/progreso.json")
        import json as _json
        return build_response(200, _json.loads(data))
    except Exception:
        return build_response(404, {"error": "Sin progreso disponible"})


def _obtener(id_iniciativa: str):
    """Retorna detalle completo de una iniciativa."""
    meta = DynamoHelper.get_meta(id_iniciativa)
    if not meta:
        return build_response(404, {"error": "Iniciativa no encontrada"})

    salidas_urls = {}
    for tipo, key in (meta.get("salidas") or {}).items():
        if key:
            salidas_urls[tipo] = S3Helper.presigned_get(key)

    meta.pop("PK", None)
    meta.pop("SK", None)
    meta.pop("GSI1PK", None)
    meta.pop("GSI1SK", None)
    meta["salidas_urls"] = salidas_urls

    return build_response(200, meta)
