#!/bin/bash
# POC Demo — Flujo completo CloudArch AI
# Ejecuta todos los pasos del flujo desde validación hasta generación de Word

API="https://1vo8syihoe.execute-api.us-east-1.amazonaws.com/prod"
KEY="58kfc3qsCWalMqjcrE89a5xOn6FLfFt821ohMh1E"
H="-H x-api-key:$KEY -H Content-Type:application/json"

echo "═══════════════════════════════════════════════════"
echo "  CloudArch AI — Demo Flujo Completo"
echo "═══════════════════════════════════════════════════"

# Usar iniciativa existente o recibir como parámetro
ID=${1:-"INI-2026-NBJJI"}
echo ""
echo "📋 Iniciativa: $ID"
echo ""

# 1. Consultar estado actual
echo "━━━ PASO 1: Estado actual ━━━"
ESTADO=$(curl -s -H "x-api-key:$KEY" "$API/iniciativas/$ID" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['estado'])")
echo "   Estado: $ESTADO"

# 2. Validar si es necesario
if [ "$ESTADO" = "INGESTA" ] || [ "$ESTADO" = "INCOMPLETO" ]; then
  echo ""
  echo "━━━ PASO 2: Validando documentos con IA ━━━"
  curl -s -X POST -H "x-api-key:$KEY" -H "Content-Type:application/json" \
    "$API/iniciativas/$ID/validar" \
    -d '{"etapa":"validar_discovery"}' | python3 -m json.tool
  echo "   ⏳ Esperando validación (60s)..."
  sleep 60
  ESTADO=$(curl -s -H "x-api-key:$KEY" "$API/iniciativas/$ID" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['estado'])")
  echo "   Estado: $ESTADO"
fi

# 3. Extraer servicios si es necesario
if [ "$ESTADO" = "DISCOVERY_OK" ] || [ "$ESTADO" = "TRANSCRIPCIONES_OK" ]; then
  echo ""
  echo "━━━ PASO 3: Extrayendo servicios AWS ━━━"
  curl -s -X POST -H "x-api-key:$KEY" -H "Content-Type:application/json" \
    "$API/iniciativas/$ID/validar" \
    -d '{"etapa":"extraer_servicios"}' | python3 -m json.tool
  echo "   ⏳ Esperando extracción (60s)..."
  sleep 60
  ESTADO=$(curl -s -H "x-api-key:$KEY" "$API/iniciativas/$ID" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['estado'])")
  echo "   Estado: $ESTADO"
fi

# 4. Generar propuesta
if [ "$ESTADO" = "EXTRAIDO" ] || [ "$ESTADO" = "ERROR_PROPUESTA" ]; then
  echo ""
  echo "━━━ PASO 4: Generando Propuesta Word ━━━"
  curl -s -X POST -H "x-api-key:$KEY" -H "Content-Type:application/json" \
    "$API/iniciativas/$ID/propuesta" | python3 -m json.tool
  echo "   ⏳ Esperando generación (~120s)..."
  sleep 130
  ESTADO=$(curl -s -H "x-api-key:$KEY" "$API/iniciativas/$ID" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['estado'])")
  echo "   Estado: $ESTADO"
fi

# 5. Resultado final
echo ""
echo "━━━ RESULTADO FINAL ━━━"
curl -s -H "x-api-key:$KEY" "$API/iniciativas/$ID" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'   Estado: {d[\"estado\"]}')
print(f'   Completitud: {d[\"completitud\"]}%')
salidas = d.get('salidas',{})
if salidas:
    print(f'   Propuesta: {salidas.get(\"propuesta\",\"N/A\")}')
urls = d.get('salidas_urls',{})
if urls.get('propuesta'):
    print(f'   📥 URL descarga: {urls[\"propuesta\"][:100]}...')
"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Portal: http://coppel-cloud-portal.s3-website-us-east-1.amazonaws.com/detalle.html?id=$ID"
echo "═══════════════════════════════════════════════════"
