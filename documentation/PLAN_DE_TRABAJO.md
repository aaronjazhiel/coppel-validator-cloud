# Plan de Trabajo — coppel-validator-cloud

**Fecha inicio:** Semana del 2 de junio 2025  
**Fecha fin:** Última semana de julio 2025  
**Duración:** 9 semanas

---

## Semana 1 (2–6 junio) — Estabilización de Infraestructura

| Actividad | Responsable | Entregable |
|-----------|-------------|------------|
| Validar y aplicar Terraform en ambiente dev | Infra | Stack desplegado (API GW, Lambdas, DynamoDB, S3) |
| Configurar secreto en Secrets Manager (API key Anthropic) | Infra | Secreto `coppel-cloud/anthropic-api-key` creado |
| Construir y subir Lambda Layer (dependencias Python) | Backend | layer.zip funcional en Lambda |
| Pruebas de conectividad Lambda → DynamoDB / S3 | Backend | Logs exitosos en CloudWatch |

---

## Semana 2 (9–13 junio) — Backend: Flujo de Ingesta

| Actividad | Responsable | Entregable |
|-----------|-------------|------------|
| Pruebas E2E de `crear_iniciativa` (POST /iniciativas) | Backend | URLs prefirmadas funcionales |
| Pruebas E2E de `registrar_insumo` (trigger S3) | Backend | Insumos registrados automáticamente en DynamoDB |
| Pruebas de `listar_iniciativas` (GET /iniciativas) | Backend | Listado y detalle con filtros por estado |
| Definir colección Postman/Bruno para testing manual | QA | Colección con todos los endpoints documentados |

---

## Semana 3 (16–20 junio) — Backend: Procesamiento con Claude

| Actividad | Responsable | Entregable |
|-----------|-------------|------------|
| Pruebas E2E de `procesar_iniciativa` (extracción de ficha) | Backend | ficha.json generada en S3 con datos reales |
| Ajustar prompt de extracción según resultados | Backend | Prompt optimizado para calidad >80% completitud |
| Pruebas de `ficha.py` (GET/PUT con versionamiento) | Backend | Versionamiento de fichas funcionando |
| Validar manejo de errores y estados (PROCESANDO, ERROR, EXTRAIDO) | Backend | Flujo de estados completo |

---

## Semana 4 (23–27 junio) — Backend: Generación de Salidas

| Actividad | Responsable | Entregable |
|-----------|-------------|------------|
| Pruebas E2E de `generar_salidas` — tipo diagrama (draw.io XML) | Backend | Archivo .drawio válido generado |
| Pruebas E2E de `generar_salidas` — tipo documento (Markdown) | Backend | Documento de arquitectura completo |
| Pruebas E2E de `generar_salidas` — tipo costos (CSV) | Backend | CSV con estimación de costos AWS |
| Optimizar prompts de generación según revisión de calidad | Backend | Salidas ajustadas a estándar Coppel |

---

## Semana 5 (30 junio–4 julio) — Frontend: Integración con API

| Actividad | Responsable | Entregable |
|-----------|-------------|------------|
| Migrar frontend de API directa (Anthropic) a API Gateway propia | Frontend | app.js apuntando a API Gateway |
| Implementar flujo de ingesta en `ingesta.html` (upload con presigned URLs) | Frontend | Subida de archivos funcional |
| Mostrar estado y progreso de procesamiento en tiempo real | Frontend | UI con polling de estado |
| Implementar descarga de salidas (diagrama, documento, costos) | Frontend | Botones de descarga funcionales |

---

## Semana 6 (7–11 julio) — Frontend: Pulido y UX

| Actividad | Responsable | Entregable |
|-----------|-------------|------------|
| Vista de detalle de iniciativa (ficha técnica completa) | Frontend | Pantalla de detalle con todas las secciones |
| Edición manual de ficha técnica (PUT /ficha) desde UI | Frontend | Formulario de edición con validación |
| Dashboard de iniciativas con filtros y búsqueda | Frontend | index.html con listado dinámico |
| Manejo de errores y mensajes de usuario | Frontend | UX robusta ante fallos |

---

## Semana 7 (14–18 julio) — Testing y Seguridad

| Actividad | Responsable | Entregable |
|-----------|-------------|------------|
| Pruebas de carga (concurrencia en Lambda async) | QA | Reporte de rendimiento |
| Validar permisos IAM (principio de mínimo privilegio) | Seguridad | Políticas IAM ajustadas |
| Pruebas con datos reales de iniciativas Coppel | QA/Negocio | Fichas técnicas validadas por arquitectos |
| Corregir bugs encontrados en testing | Backend/Frontend | Issues cerrados |

---

## Semana 8 (21–25 julio) — Ambiente Productivo

| Actividad | Responsable | Entregable |
|-----------|-------------|------------|
| Crear workspace Terraform para prod (variables, tags) | Infra | `terraform.tfvars` para prod |
| Deploy a producción (API GW + Lambdas + DynamoDB + S3) | Infra | Stack productivo levantado |
| Configurar dominio personalizado en API Gateway | Infra | Endpoint final con HTTPS |
| Smoke tests en producción | QA | Flujo completo validado en prod |

---

## Semana 9 (28–31 julio) — Go-Live y Documentación

| Actividad | Responsable | Entregable |
|-----------|-------------|------------|
| Capacitación a usuarios (arquitectos cloud Coppel) | Todos | Sesión grabada + guía rápida |
| Documentación técnica (README, diagrama de arquitectura, runbook) | Backend | Docs actualizados en repo |
| Monitoreo y alertas (CloudWatch Alarms, dashboard) | Infra | Alarmas configuradas |
| Retrospectiva y backlog de mejoras fase 2 | Todos | Documento de cierre + backlog |

---

## Resumen de Hitos

| Hito | Fecha |
|------|-------|
| ✅ Infraestructura desplegada en dev | 6 junio |
| ✅ Flujo de ingesta completo | 13 junio |
| ✅ Procesamiento con Claude funcional | 20 junio |
| ✅ Generación de salidas funcional | 27 junio |
| ✅ Frontend integrado con backend | 4 julio |
| ✅ UI completa y pulida | 11 julio |
| ✅ Testing y seguridad validados | 18 julio |
| ✅ Producción desplegada | 25 julio |
| 🚀 **Go-Live** | **31 julio** |

---

## Riesgos Identificados

| Riesgo | Mitigación |
|--------|------------|
| Calidad de extracción de Claude insuficiente | Iteración rápida de prompts en semana 3, fallback a edición manual |
| Timeout en Lambda (procesamiento largo) | Patrón async ya implementado (auto-invocación con InvocationType=Event) |
| Costos de API Anthropic altos | Monitorear tokens consumidos, limitar max_tokens, cachear fichas |
| Datos sensibles en documentos | S3 cifrado con KMS, IAM restringido, no loguear contenido |
