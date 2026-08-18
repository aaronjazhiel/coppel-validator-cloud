"""Worker asíncrono — genera la propuesta de arquitectura Word."""
from common.helpers import DynamoHelper, log_event
from lambdas.generar_propuesta import generar_propuesta_worker


def handler(event, context):
    id_iniciativa = event.get("id_iniciativa")
    if not id_iniciativa:
        return

    meta = DynamoHelper.get_meta(id_iniciativa)
    if not meta:
        return

    try:
        url = generar_propuesta_worker(id_iniciativa, meta)
        log_event("propuesta_worker_ok", {"id_iniciativa": id_iniciativa, "url": url[:80]})
    except Exception as e:
        DynamoHelper.update_meta(id_iniciativa, {"estado": "ERROR_PROPUESTA"})
        DynamoHelper.put_event(id_iniciativa, "ERROR_PROPUESTA", {"error": str(e)[:200]})
        log_event("propuesta_worker_error", {"id_iniciativa": id_iniciativa, "error": str(e)[:200]})
