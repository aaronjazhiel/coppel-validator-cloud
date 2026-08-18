"""S3 trigger (ObjectCreated) — Registra insumo subido en DynamoDB."""
from common.helpers import DynamoHelper, log_event


def handler(event, context):
    for record in event.get("Records", []):
        key = record["s3"]["object"]["key"]
        parts = key.split("/")
        if len(parts) < 5 or parts[2] != "insumos":
            continue

        id_iniciativa = parts[1]
        tipo = parts[3]
        filename = "/".join(parts[4:])

        meta = DynamoHelper.get_meta(id_iniciativa)
        if not meta:
            continue

        # UPDATE atómico: agrega el insumo solo si el key no existe ya
        DynamoHelper.append_insumo(id_iniciativa, {
            "tipo": tipo,
            "key": key,
            "subido_en": DynamoHelper.now_iso()
        })
        DynamoHelper.put_event(id_iniciativa, "INSUMO_SUBIDO", {"tipo": tipo, "key": key})
        log_event("registrar_insumo", {"id_iniciativa": id_iniciativa, "tipo": tipo, "filename": filename})
