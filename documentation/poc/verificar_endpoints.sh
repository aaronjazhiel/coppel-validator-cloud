#!/bin/bash
# Verificación rápida de todos los endpoints del sistema
# Ejecutar: bash poc/verificar_endpoints.sh

API="https://1vo8syihoe.execute-api.us-east-1.amazonaws.com/prod"
KEY="58kfc3qsCWalMqjcrE89a5xOn6FLfFt821ohMh1E"

echo "🔍 Verificando endpoints CloudArch AI..."
echo ""

# 1. Listar iniciativas
echo -n "GET /iniciativas .............. "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "x-api-key:$KEY" "$API/iniciativas")
[ "$STATUS" = "200" ] && echo "✅ $STATUS" || echo "❌ $STATUS"

# 2. Detalle de iniciativa
echo -n "GET /iniciativas/{id} ......... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "x-api-key:$KEY" "$API/iniciativas/INI-2026-NBJJI")
[ "$STATUS" = "200" ] && echo "✅ $STATUS" || echo "❌ $STATUS"

# 3. Resultados discovery
echo -n "GET /resultados/discovery ..... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "x-api-key:$KEY" "$API/iniciativas/INI-2026-NBJJI/resultados/discovery")
[ "$STATUS" = "200" ] && echo "✅ $STATUS" || echo "❌ $STATUS"

# 4. Ficha técnica
echo -n "GET /ficha .................... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "x-api-key:$KEY" "$API/iniciativas/INI-2026-NBJJI/ficha")
[ "$STATUS" = "200" ] && echo "✅ $STATUS" || echo "❌ $STATUS"

# 5. Validar (sin ejecutar realmente)
echo -n "POST /validar ................. "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "x-api-key:$KEY" -H "Content-Type:application/json" \
  -d '{"etapa":"validar_discovery"}' "$API/iniciativas/INI-2026-NBJJI/validar")
echo "📝 $STATUS (dispatcher)"

# 6. Propuesta
echo -n "POST /propuesta ............... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "x-api-key:$KEY" -H "Content-Type:application/json" \
  "$API/iniciativas/INI-2026-NBJJI/propuesta")
echo "📝 $STATUS"

# 7. Portal web
echo -n "Portal S3 ..................... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://coppel-cloud-portal.s3-website-us-east-1.amazonaws.com")
[ "$STATUS" = "200" ] && echo "✅ $STATUS" || echo "❌ $STATUS"

echo ""
echo "━━━ Datos de la iniciativa de prueba ━━━"
curl -s -H "x-api-key:$KEY" "$API/iniciativas/INI-2026-NBJJI" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'  ID:           {d[\"id_iniciativa\"]}')
print(f'  Nombre:       {d[\"nombre\"]}')
print(f'  Estado:       {d[\"estado\"]}')
print(f'  Completitud:  {d[\"completitud\"]}%')
print(f'  Insumos:      {len(d.get(\"insumos\",[]))} archivos')
print(f'  Salidas:      {list(d.get(\"salidas\",{}).keys()) or \"Ninguna\"}')
"
