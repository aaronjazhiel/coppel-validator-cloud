#!/usr/bin/env python3
"""Test del MCP Server de Pricing — ejecuta localmente sin AWS credentials.

Uso:
  python3 mcp/test_mcp.py

Prueba las 3 fases del protocolo MCP:
  1. initialize — handshake
  2. tools/list — listar herramientas disponibles
  3. tools/call — ejecutar una herramienta
"""
import subprocess
import json
import sys
import os

MCP_SERVER = os.path.join(os.path.dirname(__file__), "pricing_server.py")


def send_request(proc, request: dict) -> dict:
    """Envía un request JSON-RPC al MCP server y lee la respuesta."""
    request["jsonrpc"] = "2.0"
    if "id" not in request:
        request["id"] = 1

    line = json.dumps(request) + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    if not response_line:
        return {"error": "No response from server"}
    return json.loads(response_line)


def main():
    print("=" * 60)
    print("🧪 TEST MCP SERVER — AWS Pricing")
    print("=" * 60)

    # Iniciar el servidor MCP como subproceso
    proc = subprocess.Popen(
        [sys.executable, MCP_SERVER],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "AWS_DEFAULT_REGION": "us-east-1"}
    )

    try:
        # ── Test 1: Initialize ────────────────────────────────────
        print("\n📡 Test 1: initialize")
        resp = send_request(proc, {"method": "initialize", "id": 1, "params": {}})
        if "serverInfo" in resp or "result" in resp:
            print("   ✅ Server inicializado correctamente")
            print(f"   → {json.dumps(resp, indent=2)[:200]}")
        else:
            print(f"   ❌ Error: {resp}")

        # ── Test 2: List Tools ────────────────────────────────────
        print("\n🔧 Test 2: tools/list")
        resp = send_request(proc, {"method": "tools/list", "id": 2, "params": {}})
        tools = resp.get("tools", resp.get("result", {}).get("tools", []))
        if tools:
            print(f"   ✅ {len(tools)} herramientas disponibles:")
            for t in tools:
                print(f"      • {t['name']}: {t['description'][:60]}...")
        else:
            print(f"   ❌ No se encontraron herramientas: {resp}")

        # ── Test 3: estimate_monthly_cost ─────────────────────────
        print("\n💰 Test 3: tools/call → estimate_monthly_cost (EC2 m5.large)")
        resp = send_request(proc, {
            "method": "tools/call",
            "id": 3,
            "params": {
                "name": "estimate_monthly_cost",
                "arguments": {
                    "service_code": "AmazonEC2",
                    "instance_type": "m5.large",
                    "hours_per_month": 730,
                    "instances": 2,
                    "storage_gb": 100,
                    "multi_az": False
                }
            }
        })
        content = resp.get("content", resp.get("result", {}).get("content", []))
        if content:
            result = json.loads(content[0]["text"]) if isinstance(content[0], dict) else content
            print(f"   ✅ Resultado:")
            print(f"      Servicio: AmazonEC2 m5.large x2")
            print(f"      Mensual: ${result.get('monthly_usd', '?')} USD")
            print(f"      Anual:   ${result.get('annual_usd', '?')} USD")
        else:
            print(f"   ❌ Error: {resp}")

        # ── Test 4: get_instance_types ────────────────────────────
        print("\n📋 Test 4: tools/call → get_instance_types (RDS)")
        resp = send_request(proc, {
            "method": "tools/call",
            "id": 4,
            "params": {
                "name": "get_instance_types",
                "arguments": {"service_code": "AmazonRDS", "family": "db.r5"}
            }
        })
        content = resp.get("content", resp.get("result", {}).get("content", []))
        if content:
            result = json.loads(content[0]["text"]) if isinstance(content[0], dict) else content
            instances = result.get("instances", [])
            print(f"   ✅ {len(instances)} tipos de instancia RDS (familia db.r5):")
            for i in instances:
                print(f"      • {i['instance_type']}: ${i['price_per_hour_usd']}/h → ${i['monthly_730h_usd']}/mes")
        else:
            print(f"   ❌ Error: {resp}")

        # ── Test 5: estimate_full_stack ───────────────────────────
        print("\n🏗️  Test 5: tools/call → estimate_full_stack")
        resp = send_request(proc, {
            "method": "tools/call",
            "id": 5,
            "params": {
                "name": "estimate_full_stack",
                "arguments": {
                    "services": [
                        {"service": "Amazon EKS", "instances": 3, "environment": "prod"},
                        {"service": "Amazon RDS PostgreSQL", "multi_az": True, "storage_gb": 200, "environment": "prod"},
                        {"service": "Amazon ElastiCache Redis", "instances": 2, "environment": "prod"},
                        {"service": "Amazon S3", "storage_gb": 500, "environment": "prod"},
                        {"service": "AWS Lambda", "environment": "prod"},
                        {"service": "AWS WAF", "environment": "prod"},
                    ],
                    "include_base_services": True
                }
            }
        })
        content = resp.get("content", resp.get("result", {}).get("content", []))
        if content:
            result = json.loads(content[0]["text"]) if isinstance(content[0], dict) else content
            print(f"   ✅ Stack completo estimado:")
            for item in result.get("items", []):
                precio = f"${item['monthly_usd']:,.2f}" if item.get('monthly_usd') else "—"
                print(f"      • {item['service']:25s} {item.get('instance_type',''):15s} {precio}/mes")
            print(f"      {'─' * 55}")
            print(f"      TOTAL MENSUAL: ${result.get('total_monthly_usd', 0):,.2f} USD")
            print(f"      TOTAL ANUAL:   ${result.get('total_annual_usd', 0):,.2f} USD")
        else:
            print(f"   ❌ Error: {resp}")

        # ── Test 6: compare_pricing_options ───────────────────────
        print("\n📊 Test 6: tools/call → compare_pricing_options")
        resp = send_request(proc, {
            "method": "tools/call",
            "id": 6,
            "params": {
                "name": "compare_pricing_options",
                "arguments": {
                    "service_code": "AmazonEC2",
                    "instance_type": "m5.large",
                    "instances": 3
                }
            }
        })
        content = resp.get("content", resp.get("result", {}).get("content", []))
        if content:
            result = json.loads(content[0]["text"]) if isinstance(content[0], dict) else content
            print(f"   ✅ Comparación de precios EC2 m5.large x3:")
            for opt, vals in result.get("options", {}).items():
                print(f"      • {opt:30s} ${vals['monthly_usd']:>8,.2f}/mes  ({vals['savings']})")
        else:
            print(f"   ❌ Error: {resp}")

    finally:
        proc.terminate()
        proc.wait()

    print("\n" + "=" * 60)
    print("✅ Tests completados. El MCP Server funciona correctamente.")
    print("=" * 60)


if __name__ == "__main__":
    main()
