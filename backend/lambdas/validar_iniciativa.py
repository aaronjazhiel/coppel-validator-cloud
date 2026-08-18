"""POST /iniciativas/{id}/validar — Valida insumos por etapas (async).

Dispara la validación de forma asíncrona invocando otra Lambda
y responde inmediatamente con estado 202.
"""
import json
import boto3
from common.helpers import build_response, DynamoHelper

lambda_client = boto3.client("lambda", region_name="us-east-1")
WORKER_NAME = "coppel-cloud-prod-validar-worker"


def handler(event, context):
    path_params = event.get("pathParameters") or {}
    id_iniciativa = path_params.get("id")
    if not id_iniciativa:
        return build_response(400, {"error": "id requerido"})

    body = {}
    try:
        body = json.loads(event.get("body") or "{}")
    except Exception:
        pass

    etapa = body.get("etapa", "validar_discovery")

    meta = DynamoHelper.get_meta(id_iniciativa)
    if not meta:
        return build_response(404, {"error": "Iniciativa no encontrada"})

    # Marcar estado inmediatamente
    DynamoHelper.update_meta(id_iniciativa, {"estado": "VALIDANDO"})

    # Invocar worker de forma asíncrona (Event)
    lambda_client.invoke(
        FunctionName=WORKER_NAME,
        InvocationType="Event",
        Payload=json.dumps({"id_iniciativa": id_iniciativa, "etapa": etapa})
    )

    return build_response(202, {
        "message": f"Validación iniciada para {id_iniciativa}",
        "etapa": etapa,
        "estado": "VALIDANDO"
    })


def _validar_discovery(id_iniciativa: str, meta: dict):
    insumos = meta.get("insumos") or []
    discovery_keys = [unquote_plus(i["key"]) for i in insumos if i.get("tipo") == "discovery"]

    if not discovery_keys:
        return build_response(400, {"error": "No hay archivos de discovery subidos"})

    DynamoHelper.update_meta(id_iniciativa, {"estado": "VALIDANDO"})
    DynamoHelper.put_event(id_iniciativa, "VALIDANDO_DISCOVERY")

    # Leer prompt de S3
    prompt_template = S3Helper.read_text("prompts/validar_discovery.md")

    # Leer y extraer texto del .docx
    texto_discovery = ""
    for key in discovery_keys:
        try:
            raw = S3Helper.read_bytes(key)
            doc = Document(BytesIO(raw))
            texto_discovery += f"\n\n--- Archivo: {key.split('/')[-1]} ---\n"
            texto_discovery += "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            texto_discovery += f"\n[Error leyendo {key}: {e}]"

    prompt = prompt_template.replace("{DOCUMENTO}", texto_discovery)

    # Llamar a Claude
    from common.claude_client import ClaudeClient
    respuesta = ClaudeClient().generate(system="Eres un arquitecto cloud senior de Coppel.", prompt=prompt)["text"]

    # Parsear JSON de respuesta
    resultado = _parse_json(respuesta)

    # Guardar resultado en S3
    result_key = f"iniciativas/{id_iniciativa}/resultados/validacion_discovery.json"
    S3Helper.put_json(result_key, resultado)

    # Actualizar estado según puntaje
    puntaje = resultado.get("puntaje_total", 0)
    aprobado = puntaje >= UMBRAL_DISCOVERY

    nuevo_estado = "DISCOVERY_OK" if aprobado else "INCOMPLETO"
    huecos = resultado.get("huecos_criticos", [])

    DynamoHelper.update_meta(id_iniciativa, {
        "estado": nuevo_estado,
        "completitud": puntaje,
        "huecos": huecos,
    })
    DynamoHelper.put_event(id_iniciativa, nuevo_estado, {"puntaje": puntaje, "huecos": huecos})
    log_event("validar_discovery", {"id_iniciativa": id_iniciativa, "puntaje": puntaje, "aprobado": aprobado})

    return build_response(200, {
        "etapa": "validar_discovery",
        "puntaje": puntaje,
        "aprobado": aprobado,
        "estado": nuevo_estado,
        "resultado": resultado,
    })


def _validar_transcripciones(id_iniciativa: str, meta: dict):
    insumos = meta.get("insumos") or []
    trans_keys = [unquote_plus(i["key"]) for i in insumos if i.get("tipo") == "transcripciones"]

    if not trans_keys:
        # Sin transcripciones — se omite la etapa
        DynamoHelper.update_meta(id_iniciativa, {"estado": "TRANSCRIPCIONES_OK"})
        return build_response(200, {
            "etapa": "validar_transcripciones",
            "puntaje": 100,
            "aprobado": True,
            "estado": "TRANSCRIPCIONES_OK",
            "resultado": {"resumen": "No se subieron transcripciones, etapa omitida."},
        })

    prompt_template = S3Helper.read_text("prompts/validar_transcripciones.md")

    texto = ""
    for key in trans_keys:
        try:
            texto += f"\n\n--- Archivo: {key.split('/')[-1]} ---\n"
            texto += S3Helper.read_text(key)
        except Exception as e:
            texto += f"\n[Error leyendo {key}: {e}]"

    prompt = prompt_template.replace("{DOCUMENTO}", texto)

    from common.claude_client import ClaudeClient
    respuesta = ClaudeClient().generate(system="Eres un arquitecto cloud senior de Coppel.", prompt=prompt)["text"]
    resultado = _parse_json(respuesta)

    result_key = f"iniciativas/{id_iniciativa}/resultados/validacion_transcripciones.json"
    S3Helper.put_json(result_key, resultado)

    puntaje = resultado.get("puntaje_total", 0)
    aprobado = puntaje >= UMBRAL_TRANSCRIPCIONES
    nuevo_estado = "TRANSCRIPCIONES_OK" if aprobado else "TRANSCRIPCIONES_INSUFICIENTES"

    DynamoHelper.update_meta(id_iniciativa, {"estado": nuevo_estado})
    DynamoHelper.put_event(id_iniciativa, nuevo_estado, {"puntaje": puntaje})
    log_event("validar_transcripciones", {"id_iniciativa": id_iniciativa, "puntaje": puntaje})

    return build_response(200, {
        "etapa": "validar_transcripciones",
        "puntaje": puntaje,
        "aprobado": aprobado,
        "estado": nuevo_estado,
        "resultado": resultado,
    })


def _extraer_servicios(id_iniciativa: str, meta: dict):
    estado_actual = meta.get("estado", "")
    if estado_actual not in ("DISCOVERY_OK", "TRANSCRIPCIONES_OK", "TRANSCRIPCIONES_INSUFICIENTES"):
        return build_response(400, {
            "error": f"El discovery debe estar aprobado antes de extraer servicios. Estado actual: {estado_actual}"
        })

    DynamoHelper.update_meta(id_iniciativa, {"estado": "EXTRAYENDO_SERVICIOS"})
    DynamoHelper.put_event(id_iniciativa, "EXTRAYENDO_SERVICIOS")

    prompt_template = S3Helper.read_text("prompts/extraer_servicios.md")

    # Leer resultado de validación discovery
    try:
        disc_result = S3Helper.read_text(f"iniciativas/{id_iniciativa}/resultados/validacion_discovery.json")
    except Exception:
        disc_result = ""

    # Leer transcripciones si existen
    trans_texto = ""
    try:
        trans_result = S3Helper.read_text(f"iniciativas/{id_iniciativa}/resultados/validacion_transcripciones.json")
        trans_texto = trans_result
    except Exception:
        trans_texto = "No disponibles"

    prompt = prompt_template.replace("{DISCOVERY}", disc_result).replace("{TRANSCRIPCIONES}", trans_texto)

    from common.claude_client import ClaudeClient
    respuesta = ClaudeClient().generate(system="Eres un arquitecto cloud senior de Coppel.", prompt=prompt)["text"]
    resultado = _parse_json(respuesta)

    result_key = f"iniciativas/{id_iniciativa}/resultados/servicios_aws.json"
    S3Helper.put_json(result_key, resultado)

    DynamoHelper.update_meta(id_iniciativa, {"estado": "EXTRAIDO"})
    DynamoHelper.put_event(id_iniciativa, "EXTRAIDO", {"servicios": len(resultado.get("servicios", []))})
    log_event("extraer_servicios", {"id_iniciativa": id_iniciativa})

    return build_response(200, {
        "etapa": "extraer_servicios",
        "estado": "EXTRAIDO",
        "resultado": resultado,
    })


def _parse_json(texto: str) -> dict:
    """Extrae el primer bloque JSON válido de la respuesta de Claude."""
    try:
        return json.loads(texto)
    except Exception:
        match = re.search(r"\{.*\}", texto, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {"error": "No se pudo parsear la respuesta", "raw": texto[:500]}
