"""Cliente Claude con tool_use forzado y llave desde Secrets Manager.

Provee dos métodos:
- extract_ficha: usa tool_use forzado para extraer datos estructurados según un schema.
- generate: llamada genérica de texto libre para generar artefactos.

La API key se obtiene de AWS Secrets Manager y se cachea en memoria.
"""
import json
import boto3
import anthropic
from functools import lru_cache

# Nombre del secreto en AWS Secrets Manager que contiene la API key de Anthropic
SECRET_NAME = "coppel-cloud/anthropic-api-key"


@lru_cache(maxsize=1)
def _get_api_key() -> str:
    """Obtiene la API key de Secrets Manager (cacheada para reutilizar entre invocaciones)."""
    client = boto3.client("secretsmanager")
    resp = client.get_secret_value(SecretId=SECRET_NAME)
    secret = json.loads(resp["SecretString"])
    return secret["api_key"]


class ClaudeClient:
    def __init__(self, model: str = "claude-sonnet-5"):
        self.model = model
        self.client = anthropic.Anthropic(api_key=_get_api_key())

    def extract_ficha(self, content: str, schema_json: dict) -> dict:
        """Llama a Claude con tool_use forzado para extraer la Ficha Técnica."""
        tool = {
            "name": "ficha_tecnica",
            "description": "Extrae y estructura la Ficha Técnica del proyecto a partir de los insumos proporcionados. NO inventes datos; marca como vacío lo que no encuentres.",
            "input_schema": schema_json,
        }
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            tools=[tool],
            tool_choice={"type": "tool", "name": "ficha_tecnica"},
            messages=[{"role": "user", "content": content}],
        )
        for block in response.content:
            if block.type == "tool_use":
                return {
                    "ficha": block.input,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                }
        return {"ficha": {}, "usage": {}}

    def generate(self, system: str, prompt: str, max_tokens: int = 8192) -> dict:
        """Llamada genérica a Claude."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return {
            "text": next(b.text for b in response.content if hasattr(b, "text")),
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }
