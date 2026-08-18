# POC — CloudArch AI: Validador de Arquitectura Cloud

## Resumen Ejecutivo

Sistema end-to-end que automatiza la validación de documentos de arquitectura cloud y genera propuestas Word con costos reales de AWS.

**Flujo completo probado:**
```
INGESTA → VALIDANDO → DISCOVERY_OK → EXTRAYENDO_SERVICIOS → EXTRAIDO → GENERANDO_PROPUESTA → GENERADO
```

## Módulos Implementados

| Módulo | Función | Estado |
|--------|---------|--------|
| Portal Web | Ingesta de documentos, visualización de estado | ✅ Funcionando |
| Validación IA | Claude analiza completitud del Discovery | ✅ Funcionando |
| Extracción Servicios | Identifica servicios AWS necesarios | ✅ Funcionando |
| AWS Pricing MCP | Claude consulta precios reales via tool_use | ✅ Funcionando |
| Generación Word | Propuesta con plantilla, costos y contenido IA | ✅ Funcionando |

## URLs de Acceso

- **Portal**: http://coppel-cloud-portal.s3-website-us-east-1.amazonaws.com
- **API**: https://1vo8syihoe.execute-api.us-east-1.amazonaws.com/prod
- **Iniciativa de prueba**: INI-2026-NBJJI (estado: GENERADO)

## Cómo Ejecutar la Demo

### 1. Ingesta
1. Ir al portal → Ingesta
2. Llenar nombre, solicitante, ambiente
3. Subir archivo Quick Discovery (.docx)
4. El sistema genera ID automático y sube a S3

### 2. Validación
1. Ir a Detalle de la iniciativa
2. Click "Validar Documentos"
3. Claude analiza el Discovery y da puntaje por sección
4. Si ≥75% → DISCOVERY_OK, si no → INCOMPLETO con huecos

### 3. Extracción de Servicios
1. Automático tras validación exitosa (o click "Procesar con IA")
2. Claude identifica servicios AWS necesarios con prioridad
3. Estado cambia a EXTRAIDO

### 4. Generación de Propuesta
1. Click "Generar Propuesta Word"
2. El sistema:
   - Consulta AWS Pricing API con Claude como agente (MCP)
   - Genera contenido de 8 secciones con Claude
   - Crea Word usando plantilla con logos/estilos
3. ~120 segundos → Estado GENERADO
4. Click "Descargar Propuesta"

## Arquitectura Técnica

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Portal S3  │────▶│ API Gateway  │────▶│  Lambda (CRUD)  │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────┐
                    │                              │              │
              ┌─────▼─────┐  ┌─────────────┐  ┌───▼────────┐    │
              │  Validar   │  │  Extraer    │  │  Generar   │    │
              │  Worker    │  │  Servicios  │  │  Propuesta │    │
              └─────┬──────┘  └──────┬──────┘  └─────┬──────┘    │
                    │                │               │           │
                    └────────────────┼───────────────┘           │
                                     │                           │
                    ┌────────────────▼───────────────┐           │
                    │     Claude (Anthropic API)     │           │
                    │  • Validación de documentos    │           │
                    │  • Extracción de servicios     │           │
                    │  • MCP Pricing (tool_use)      │           │
                    │  • Generación de contenido     │           │
                    └────────────────────────────────┘           │
                                                                 │
              ┌──────────────┐    ┌──────────────────┐           │
              │ PostgreSQL   │    │   S3 (insumos,   │◀──────────┘
              │   (RDS)      │    │  resultados,     │
              └──────────────┘    │  salidas)        │
                                  └──────────────────┘
```

## Resultado de Prueba Real

**Iniciativa**: INI-2026-NBJJI — Migración Constancias Retención
**Documento generado**: `propuesta_arquitectura.docx` (341 KB)

Contenido del Word:
- ✅ Portada con datos del proyecto
- ✅ Tabla de contenido
- ✅ 8 secciones completas generadas por IA
- ✅ Tabla de costos con precios reales de AWS Pricing API
- ✅ Sección de aprobación

Ejemplo de costos generados:
| Servicio | Especificación | Costo Mensual |
|----------|---------------|---------------|
| Amazon EKS | cluster | $73.00 |
| AWS Lambda | 1M requests | $5.00 |
| Amazon RDS | db.r5.large | $180.00 |
| Amazon S3 | 100GB | $2.30 |

## Stack Tecnológico

- **Frontend**: HTML/CSS/JS vanilla (S3 static hosting)
- **Backend**: Python 3.12, AWS Lambda
- **Base de datos**: PostgreSQL (RDS)
- **Storage**: S3 con presigned URLs
- **IA**: Claude Sonnet 5 (Anthropic API)
- **Pricing**: AWS Pricing API + MCP pattern
- **Documentos**: python-docx con plantilla Word
