"""Helpers compartidos: S3, PostgreSQL, respuestas HTTP, logging."""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.config import Config
import psycopg2
import psycopg2.extras

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET      = os.environ.get("BUCKET_NAME", "coppel-cloud-iniciativas")
DB_HOST     = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT     = int(os.environ.get("DB_PORT", "5432"))
DB_NAME     = os.environ.get("DB_NAME", "coppel_cloud")
DB_USER     = os.environ.get("DB_USER", "coppel_admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

s3 = boto3.client("s3", region_name="us-east-1", config=boto3.session.Config(signature_version="s3v4"))


def _get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def log_event(action: str, detail: dict | None = None, **kwargs):
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "action": action, **(detail or {}), **kwargs}
    logger.info(json.dumps(entry, default=str))


def build_response(status: int, body: Any) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,x-api-key",
        },
        "body": json.dumps(body, default=str),
    }


class S3Helper:
    @staticmethod
    def presigned_put(key: str, content_type: str = "application/octet-stream", expires: int = 3600) -> str:
        return s3.generate_presigned_url("put_object",
            Params={"Bucket": BUCKET, "Key": key, "ContentType": content_type}, ExpiresIn=expires)

    @staticmethod
    def presigned_get(key: str, expires: int = 3600) -> str:
        return s3.generate_presigned_url("get_object",
            Params={"Bucket": BUCKET, "Key": key}, ExpiresIn=expires)

    @staticmethod
    def read_text(key: str) -> str:
        return s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode("utf-8")

    @staticmethod
    def read_bytes(key: str) -> bytes:
        return s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()

    @staticmethod
    def put_json(key: str, data: dict):
        s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(data, default=str, ensure_ascii=False), ContentType="application/json")

    @staticmethod
    def put_bytes(key: str, data: bytes, content_type: str = "application/octet-stream"):
        s3.put_object(Bucket=BUCKET, Key=key, Body=data, ContentType=content_type)

    @staticmethod
    def list_keys(prefix: str) -> list[str]:
        resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
        return [obj["Key"] for obj in resp.get("Contents", [])]


class DBHelper:
    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def get_meta(id_iniciativa: str) -> dict | None:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM iniciativas WHERE id_iniciativa = %s", (id_iniciativa,))
                return cur.fetchone()

    @staticmethod
    def put_meta(item: dict):
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO iniciativas
                        (id_iniciativa, nombre, descripcion, ambiente, solicitante, nube,
                         business_tags, estado, completitud, huecos, s3_prefix, insumos, salidas)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item["id_iniciativa"],
                    item.get("nombre", ""),
                    item.get("descripcion", ""),
                    item.get("ambiente", "Prod"),
                    item.get("solicitante", ""),
                    item.get("nube", "AWS"),
                    json.dumps(item.get("business_tags", {})),
                    item.get("estado", "INGESTA"),
                    item.get("completitud", 0),
                    json.dumps(item.get("huecos", [])),
                    item.get("s3_prefix", ""),
                    json.dumps(item.get("insumos", [])),
                    json.dumps(item.get("salidas", {})),
                ))
            conn.commit()

    @staticmethod
    def update_meta(id_iniciativa: str, updates: dict):
        allowed = {"nombre", "descripcion", "ambiente", "solicitante", "nube",
                   "business_tags", "estado", "completitud", "huecos",
                   "s3_prefix", "insumos", "salidas"}
        updates = {k: v for k, v in updates.items() if k in allowed}
        if not updates:
            return
        for field in ("business_tags", "huecos", "insumos", "salidas"):
            if field in updates and not isinstance(updates[field], str):
                updates[field] = json.dumps(updates[field])
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [id_iniciativa]
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE iniciativas SET {set_clause}, fecha_actualizacion = NOW() WHERE id_iniciativa = %s", values)
            conn.commit()

    @staticmethod
    def put_event(id_iniciativa: str, accion: str, detalle: dict | None = None):
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO eventos (id_iniciativa, accion, detalle) VALUES (%s, %s, %s)",
                    (id_iniciativa, accion, json.dumps(detalle or {}))
                )
            conn.commit()

    @staticmethod
    def append_insumo(id_iniciativa: str, insumo: dict):
        """Agrega un insumo atómicamente evitando condición de carrera."""
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE iniciativas
                    SET insumos = (
                        SELECT jsonb_agg(elem)
                        FROM (
                            SELECT DISTINCT ON (elem->>'key') elem
                            FROM jsonb_array_elements(
                                COALESCE(insumos, '[]'::jsonb) || %s::jsonb
                            ) AS elem
                            ORDER BY elem->>'key'
                        ) sub
                    ),
                    fecha_actualizacion = NOW()
                    WHERE id_iniciativa = %s
                """, (json.dumps([insumo]), id_iniciativa))
            conn.commit()

    @staticmethod
    def query_by_estado(estado: str, limit: int = 50) -> list[dict]:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM iniciativas WHERE estado = %s ORDER BY fecha_creacion DESC LIMIT %s", (estado, limit))
                return cur.fetchall() or []

    @staticmethod
    def scan_all_meta(limit: int = 100) -> list[dict]:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM iniciativas ORDER BY fecha_creacion DESC LIMIT %s", (limit,))
                return cur.fetchall() or []


DynamoHelper = DBHelper
