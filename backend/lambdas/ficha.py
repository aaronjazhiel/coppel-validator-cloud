"""GET/PUT /iniciativas/{id}/ficha — Lectura y actualización de la Ficha Técnica.

Permite consultar la ficha extraída por Claude (GET) o actualizarla manualmente
(PUT) con versionamiento automático de la ficha anterior en S3.
"""
import json

from common.schema import FichaTecnica
from common.helpers import build_response, S3Helper, DynamoHelper, log_event


def handler(event, context):
    """Dispatcher por método HTTP: GET para lectura, PUT para actualización."""
    method = event.get("httpMethod", "GET")
    id_iniciativa = event.get("pathParameters", {}).get("id", "")

    if not id_iniciativa:
        return build_response(400, {"error": "id_iniciativa requerido"})

    meta = DynamoHelper.get_meta(id_iniciativa)
    if not meta:
        return build_response(404, {"error": "Iniciativa no encontrada"})

    prefix = meta.get("s3_prefix", f"iniciativas/{id_iniciativa}")

    if method == "GET":
        return _get_ficha(prefix)
    elif method == "PUT":
        return _put_ficha(event, id_iniciativa, prefix)
    return build_response(405, {"error": "Método no permitido"})


def _get_ficha(prefix: str):
    """Lee la ficha actual desde S3 y la retorna como JSON."""
    try:
        text = S3Helper.read_text(f"{prefix}/ficha/ficha.json")
        return build_response(200, json.loads(text))
    except Exception:
        return build_response(404, {"error": "Ficha no encontrada. Ejecute procesar primero."})


def _put_ficha(event, id_iniciativa: str, prefix: str):
    """Valida con Pydantic, versiona la ficha anterior y guarda la nueva."""
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return build_response(400, {"error": "Body JSON inválido"})

    # Validar con Pydantic
    try:
        ficha = FichaTecnica.model_validate(body)
    except Exception as e:
        return build_response(422, {"error": f"Validación fallida: {str(e)}"})

    ficha_dict = ficha.model_dump()

    # Versionar ficha anterior antes de sobreescribir
    existing_keys = S3Helper.list_keys(f"{prefix}/ficha/ficha-v")
    version = len(existing_keys) + 1
    try:
        current = S3Helper.read_text(f"{prefix}/ficha/ficha.json")
        S3Helper.put_json(f"{prefix}/ficha/ficha-v{version}.json", json.loads(current))
    except Exception:
        pass

    # Guardar nueva versión
    S3Helper.put_json(f"{prefix}/ficha/ficha.json", ficha_dict)

    # Determinar nuevo estado según si hay huecos de información pendientes
    nuevo_estado = "EN_REVISION" if ficha.validacion.huecos else "VALIDADO"

    DynamoHelper.update_meta(id_iniciativa, {
        "estado": nuevo_estado,
        "GSI1PK": f"ESTADO#{nuevo_estado}",
        "GSI1SK": DynamoHelper.now_iso(),
        "completitud": ficha.validacion.completitud,
        "huecos": ficha.validacion.huecos,
        "fecha_actualizacion": DynamoHelper.now_iso(),
    })
    DynamoHelper.put_event(id_iniciativa, "FICHA_ACTUALIZADA", {"version": version, "estado": nuevo_estado})
    log_event("actualizar_ficha", {"id_iniciativa": id_iniciativa, "version": version})

    return build_response(200, {"message": "Ficha actualizada", "version": version, "estado": nuevo_estado})
