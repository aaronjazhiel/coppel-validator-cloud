"""Worker asíncrono de validación — invocado por validar_iniciativa con InvocationType=Event."""
import json
import re
from urllib.parse import unquote_plus
from docx import Document
from io import BytesIO
from common.helpers import build_response, DynamoHelper, S3Helper, log_event

UMBRAL_DISCOVERY = 75
UMBRAL_TRANSCRIPCIONES = 60


def handler(event, context):
    id_iniciativa = event.get("id_iniciativa")
    etapa = event.get("etapa", "validar_discovery")
    log_event("worker_invocado", {"id_iniciativa": id_iniciativa, "etapa": etapa})

    meta = DynamoHelper.get_meta(id_iniciativa)
    if not meta:
        log_event("worker_sin_meta", {"id_iniciativa": id_iniciativa})
        return

    if etapa == "validar_discovery":
        _validar_discovery(id_iniciativa, meta)
    elif etapa == "validar_transcripciones":
        _validar_transcripciones(id_iniciativa, meta)
    elif etapa == "extraer_servicios":
        _extraer_servicios(id_iniciativa, meta)
    elif etapa == "validar_n2":
        _validar_n2(id_iniciativa, meta)
    elif etapa == "validar_todo":
        _validar_todo(id_iniciativa, meta)


def _validar_discovery(id_iniciativa: str, meta: dict):
    insumos = meta.get("insumos") or []
    discovery_keys = [unquote_plus(i["key"]) for i in insumos if i.get("tipo") == "discovery"]

    if not discovery_keys:
        DynamoHelper.update_meta(id_iniciativa, {"estado": "INCOMPLETO", "huecos": ["No se subió ningún archivo de Quick Discovery"]})
        return

    # Leer prompt combinado
    prompt_template = S3Helper.read_text("prompts/validar_combinado.md")

    # Leer Discovery
    texto_discovery = ""
    for key in discovery_keys:
        try:
            raw = S3Helper.read_bytes(key)
            doc = Document(BytesIO(raw))
            texto_discovery += f"\n\n--- Archivo: {key.split('/')[-1]} ---\n"
            texto_discovery += "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            texto_discovery += f"\n[Error leyendo {key}: {e}]"

    # Leer Transcripciones (si existen)
    trans_keys = [unquote_plus(i["key"]) for i in insumos if i.get("tipo") == "transcripciones"]
    texto_trans = "No se subieron transcripciones."
    if trans_keys:
        texto_trans = ""
        for key in trans_keys:
            try:
                texto_trans += f"\n\n--- Archivo: {key.split('/')[-1]} ---\n"
                texto_trans += S3Helper.read_text(key)
            except Exception as e:
                texto_trans += f"\n[Error leyendo {key}: {e}]"

    prompt = prompt_template.replace("{DISCOVERY}", texto_discovery).replace("{TRANSCRIPCIONES}", texto_trans)

    from common.claude_client import ClaudeClient
    respuesta = ClaudeClient().generate(
        system="Eres un arquitecto cloud senior de Coppel. Responde ÚNICAMENTE con JSON válido.",
        prompt=prompt
    )["text"]

    resultado = _parse_json(respuesta)
    S3Helper.put_json(f"iniciativas/{id_iniciativa}/resultados/validacion_discovery.json", resultado)

    puntaje = resultado.get("puntaje_total", 0)
    aprobado = puntaje >= UMBRAL_DISCOVERY
    nuevo_estado = "DISCOVERY_OK" if aprobado else "INCOMPLETO"

    # Huecos críticos como lista de preguntas
    huecos_raw = resultado.get("huecos_criticos", [])
    huecos = [h.get("pregunta", h) if isinstance(h, dict) else h for h in huecos_raw]

    DynamoHelper.update_meta(id_iniciativa, {
        "estado": nuevo_estado,
        "completitud": puntaje,
        "huecos": huecos,
    })
    DynamoHelper.put_event(id_iniciativa, nuevo_estado, {"puntaje": puntaje})
    log_event("validar_discovery", {"id_iniciativa": id_iniciativa, "puntaje": puntaje, "aprobado": aprobado})


def _validar_transcripciones(id_iniciativa: str, meta: dict):
    insumos = meta.get("insumos") or []
    trans_keys = [unquote_plus(i["key"]) for i in insumos if i.get("tipo") == "transcripciones"]

    if not trans_keys:
        DynamoHelper.update_meta(id_iniciativa, {"estado": "TRANSCRIPCIONES_OK"})
        DynamoHelper.put_event(id_iniciativa, "TRANSCRIPCIONES_OK", {"nota": "Sin transcripciones, etapa omitida"})
        return

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
    respuesta = ClaudeClient().generate(
        system="Eres un arquitecto cloud senior de Coppel. Responde ÚNICAMENTE con JSON válido.",
        prompt=prompt
    )["text"]

    resultado = _parse_json(respuesta)
    S3Helper.put_json(f"iniciativas/{id_iniciativa}/resultados/validacion_transcripciones.json", resultado)

    puntaje = resultado.get("puntaje_total", 0)
    aprobado = puntaje >= UMBRAL_TRANSCRIPCIONES
    nuevo_estado = "TRANSCRIPCIONES_OK" if aprobado else "TRANSCRIPCIONES_INSUFICIENTES"

    DynamoHelper.update_meta(id_iniciativa, {"estado": nuevo_estado})
    DynamoHelper.put_event(id_iniciativa, nuevo_estado, {"puntaje": puntaje})
    log_event("validar_transcripciones", {"id_iniciativa": id_iniciativa, "puntaje": puntaje})


def _extraer_servicios(id_iniciativa: str, meta: dict):
    estado_actual = meta.get("estado", "")
    if estado_actual not in ("DISCOVERY_OK", "TRANSCRIPCIONES_OK", "TRANSCRIPCIONES_INSUFICIENTES"):
        DynamoHelper.put_event(id_iniciativa, "ERROR_EXTRACCION", {"motivo": f"Estado inválido: {estado_actual}"})
        return

    DynamoHelper.update_meta(id_iniciativa, {"estado": "EXTRAYENDO_SERVICIOS"})

    prompt_template = S3Helper.read_text("prompts/extraer_servicios.md")

    try:
        disc_result = S3Helper.read_text(f"iniciativas/{id_iniciativa}/resultados/validacion_discovery.json")
    except Exception:
        disc_result = ""

    try:
        trans_result = S3Helper.read_text(f"iniciativas/{id_iniciativa}/resultados/validacion_transcripciones.json")
    except Exception:
        trans_result = "No disponibles"

    prompt = prompt_template.replace("{DISCOVERY}", disc_result).replace("{TRANSCRIPCIONES}", trans_result)

    from common.claude_client import ClaudeClient
    respuesta = ClaudeClient().generate(
        system="Eres un arquitecto cloud senior de Coppel. Responde ÚNICAMENTE con JSON válido.",
        prompt=prompt
    )["text"]

    resultado = _parse_json(respuesta)
    S3Helper.put_json(f"iniciativas/{id_iniciativa}/resultados/servicios_aws.json", resultado)

    DynamoHelper.update_meta(id_iniciativa, {"estado": "EXTRAIDO"})
    DynamoHelper.put_event(id_iniciativa, "EXTRAIDO", {"servicios": len(resultado.get("servicios", []))})
    log_event("extraer_servicios", {"id_iniciativa": id_iniciativa})


def _validar_n2(id_iniciativa: str, meta: dict):
    """Valida el Excel N2 con reglas deterministas."""
    from lambdas.validar_n2 import validar_n2
    resultado = validar_n2(id_iniciativa, meta)
    puntaje = resultado.get("puntaje_total", 0) if resultado else 0
    nuevo_estado = "N2_OK" if puntaje >= 60 else "N2_INCOMPLETO"
    DynamoHelper.update_meta(id_iniciativa, {"estado": nuevo_estado})


def _validar_todo(id_iniciativa: str, meta: dict):
    """Ejecuta Discovery + N2 + Coherencia en secuencia."""
    # 1. Validar Discovery
    _validar_discovery(id_iniciativa, meta)

    # 2. Validar N2
    from lambdas.validar_n2 import validar_n2
    validar_n2(id_iniciativa, meta)

    # 3. Coherencia (IA) — solo si ambos tienen datos
    _validar_coherencia(id_iniciativa)

    # Estado final
    DynamoHelper.update_meta(id_iniciativa, {"estado": "VALIDADO"})
    DynamoHelper.put_event(id_iniciativa, "VALIDACION_COMPLETA")


def _validar_coherencia(id_iniciativa: str):
    """Usa IA para cruzar Discovery vs N2 y detectar inconsistencias."""
    try:
        discovery_json = S3Helper.read_text(f"iniciativas/{id_iniciativa}/resultados/validacion_discovery.json")
    except Exception:
        discovery_json = "{}"

    try:
        n2_json = S3Helper.read_text(f"iniciativas/{id_iniciativa}/resultados/validacion_n2.json")
    except Exception:
        # Sin N2 no hay coherencia que validar
        S3Helper.put_json(f"iniciativas/{id_iniciativa}/resultados/validacion_coherencia.json", {
            "puntaje_coherencia": 0, "alertas": [], "resumen": "No se pudo ejecutar: falta N2."
        })
        return

    prompt_template = S3Helper.read_text("prompts/validar_coherencia.md")
    prompt = prompt_template.replace("{DISCOVERY}", discovery_json).replace("{N2_DATA}", n2_json)

    from common.claude_client import ClaudeClient
    respuesta = ClaudeClient().generate(
        system="Eres un arquitecto cloud senior de Coppel. Responde ÚNICAMENTE con JSON válido.",
        prompt=prompt
    )["text"]

    resultado = _parse_json(respuesta)
    S3Helper.put_json(f"iniciativas/{id_iniciativa}/resultados/validacion_coherencia.json", resultado)
    DynamoHelper.put_event(id_iniciativa, "COHERENCIA_VALIDADA", {
        "puntaje": resultado.get("puntaje_coherencia", 0),
        "alertas": resultado.get("total_alertas", 0)
    })
    log_event("validar_coherencia", {"id_iniciativa": id_iniciativa})


def _parse_json(texto: str) -> dict:
    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", texto).strip().rstrip("`")
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {"error": "No se pudo parsear la respuesta", "raw": texto[:500]}
