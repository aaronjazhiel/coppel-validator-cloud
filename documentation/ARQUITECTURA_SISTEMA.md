# Documento de Arquitectura — CloudArch AI
## Área de Arquitectura Cloud · Coppel
**Versión:** 1.0 | **Región AWS:** us-east-1 | **Ambiente:** Producción

---

## 1. Introducción

CloudArch AI es un portal serverless interno desarrollado para el Área de Arquitectura Cloud de Coppel. Su propósito es automatizar el ciclo completo de análisis, validación y generación de propuestas de arquitectura cloud, reduciendo el tiempo de entrega de 2–3 semanas a minutos mediante el uso de inteligencia artificial generativa.

El sistema recibe documentos de entrada (Quick Discovery, transcripciones, diagramas, inventarios), los analiza con IA, valida su completitud, extrae los servicios AWS requeridos y genera una propuesta de arquitectura en formato Word con estimación de costos reales.

---

## 2. Contexto y Problema

### Situación sin la herramienta

| Problema | Impacto |
|---|---|
| Quick Discovery incompleto | El arquitecto pierde días solicitando información faltante |
| Sin estándar de entregables | Cada arquitecto genera documentos con formato diferente |
| Estimación de costos manual | Consulta servicio por servicio en la calculadora AWS |
| Sin trazabilidad | No se conoce el estado de cada solicitud |
| Reprocesos constantes | Se regresa al solicitante 2–3 veces por datos faltantes |

### Solución

| Capacidad | Beneficio |
|---|---|
| Validación automática con IA | Detecta huecos en segundos y genera preguntas específicas |
| Plantilla corporativa estandarizada | Todas las propuestas siguen el mismo formato |
| AWS Pricing API | Estimación automática con precios reales |
| Dashboard de seguimiento | Visibilidad en tiempo real del estado de cada iniciativa |
| Generación en minutos | De solicitud a propuesta Word en ~2 minutos |

---

## 3. Stack Tecnológico

| Capa | Tecnología | Versión / Tier |
|---|---|---|
| Frontend | HTML5 + CSS3 + JavaScript vanilla | — |
| Hosting estático | Amazon S3 Static Website | — |
| API | Amazon API Gateway REST | Regional |
| Cómputo | AWS Lambda | Python 3.12 |
| Base de datos NoSQL | Amazon DynamoDB | On-demand (PAY_PER_REQUEST) |
| Base de datos relacional | Amazon RDS PostgreSQL | 16 / db.t3.micro |
| Almacenamiento de objetos | Amazon S3 | KMS + Versionado |
| IA generativa | Anthropic Claude (claude-sonnet-5) | API externa |
| Precios AWS | AWS Pricing API | — |
| Secretos | AWS Secrets Manager | — |
| Red privada | Amazon VPC (default) + VPC Endpoints | Gateway + Interface |
| IaC | Terraform | >= 1.5 / AWS Provider ~5.0 |
| Runtime dependencias | Lambda Layer (Python) | python3.12 |

---

## 4. Arquitectura General

```
┌──────────────────────────────────────────────────────────────────────┐
│                          USUARIO / NAVEGADOR                         │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│              S3 Static Website  (Portal Web)                         │
│   index.html · ingesta.html · detalle.html · listado.html            │
│   paso1-validacion · paso2-servicios · paso3-costos · paso4-propuesta│
└────────────────────────────┬─────────────────────────────────────────┘
                             │ REST + x-api-key
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    API Gateway (Regional)                             │
│   /iniciativas  /iniciativas/{id}  /validar  /procesar               │
│   /ficha  /generar/{tipo}  /propuesta  /resultados/{tipo}            │
└──────┬──────────┬──────────┬──────────┬──────────┬───────────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
  crear_ini  listar_ini  validar_ini  ficha   generar_propuesta
  (256MB)    (256MB)     (512MB)     (256MB)    (256MB)
       │                    │                      │
       │              (async invoke)         (async invoke)
       ▼                    ▼                      ▼
  DynamoDB           validar_worker          propuesta_worker
  S3 (PUT)           (1024MB/900s)           (1024MB/900s)
                          │                      │
                          ▼                      ▼
                     Claude AI            Claude AI + Pricing API
                          │                      │
                          ▼                      ▼
                     DynamoDB              S3 (.docx salida)
                     (resultado)

  S3 trigger (s3:ObjectCreated) → registrar_insumo → DynamoDB
```

---

## 5. Componentes del Sistema

### 5.1 Frontend

Aplicación web estática sin framework, alojada en S3 con acceso público.

| Página | Función |
|---|---|
| `index.html` | Dashboard principal / análisis |
| `ingesta.html` | Carga de documentos de entrada |
| `listado.html` | Listado de iniciativas |
| `detalle.html` | Seguimiento de una iniciativa |
| `paso1-validacion.html` | Resultado de validación IA |
| `paso2-servicios.html` | Servicios AWS identificados |
| `paso3-costos.html` | Estimación de costos |
| `paso4-propuesta.html` | Descarga de propuesta Word |

Los archivos se suben directamente a S3 mediante **presigned URLs** generadas por `crear_iniciativa`, sin pasar por el backend.

### 5.2 API Gateway

REST API regional con autenticación por `x-api-key`. CORS habilitado en todos los recursos mediante un módulo Terraform reutilizable (`modules/cors`). Gateway Responses configuradas para propagar headers CORS en errores 4xx y 5xx.

| Método | Endpoint | Lambda |
|---|---|---|
| POST | `/iniciativas` | `crear_iniciativa` |
| GET | `/iniciativas` | `listar_iniciativas` |
| GET | `/iniciativas/{id}` | `listar_iniciativas` |
| POST | `/iniciativas/{id}/validar` | `validar_iniciativa` |
| POST | `/iniciativas/{id}/procesar` | `procesar_iniciativa` |
| GET/PUT | `/iniciativas/{id}/ficha` | `ficha` |
| POST | `/iniciativas/{id}/generar/{tipo}` | `generar_salidas` |
| POST | `/iniciativas/{id}/propuesta` | `generar_propuesta` |
| GET | `/iniciativas/{id}/resultados/{tipo}` | `listar_iniciativas` |

### 5.3 Lambda Functions

Todas las funciones usan Python 3.12 con un Lambda Layer compartido de dependencias.

| Función | Timeout | Memoria | Rol IAM | Descripción |
|---|---|---|---|---|
| `crear_iniciativa` | 30s | 256MB | `lambda_crud` | Crea la iniciativa y genera presigned URLs para subir insumos |
| `registrar_insumo` | 30s | 256MB | `lambda_registrar` | Trigger S3 — registra cada archivo subido en DynamoDB |
| `listar_iniciativas` | 30s | 256MB | `lambda_crud` | Listado y detalle de iniciativas |
| `validar_iniciativa` | 300s | 512MB | `lambda_ai` | Dispatcher — invoca `validar_worker` de forma asíncrona |
| `validar_worker` | 900s | 1024MB | `lambda_ai` | Valida completitud de documentos con Claude (8 secciones) |
| `procesar_iniciativa` | 900s | 1024MB | `lambda_ai` | Extrae Ficha Técnica estructurada con Claude (tool_use forzado) |
| `ficha` | 30s | 256MB | `lambda_crud` | CRUD de la Ficha Técnica en DynamoDB |
| `generar_propuesta` | 30s | 256MB | `lambda_ai` | Dispatcher — invoca `propuesta_worker` de forma asíncrona |
| `propuesta_worker` | 900s | 1024MB | `lambda_ai` | Genera documento Word con costos reales (Claude + Pricing API) |
| `generar_salidas` | 900s | 1024MB | `lambda_ai` | Genera diagrama, CSV y otros artefactos de salida |

### 5.4 DynamoDB — Single-Table Design

Tabla: `Iniciativas` | Modo: PAY_PER_REQUEST

| Atributo | Tipo | Rol |
|---|---|---|
| `PK` | String | Partition key (ej. `INICIATIVA#<id>`) |
| `SK` | String | Sort key (ej. `METADATA`, `INSUMO#<nombre>`, `VALIDACION`) |
| `GSI1PK` | String | GSI para consultas por estado |
| `GSI1SK` | String | GSI sort key (fecha) |

El GSI1 permite listar iniciativas filtradas por estado (`INGESTA`, `VALIDANDO`, `VALIDADO`, `GENERANDO`, `COMPLETADO`).

### 5.5 S3 — Almacenamiento de Objetos

| Bucket | Contenido | Configuración |
|---|---|---|
| `coppel-cloud-iniciativas` | Insumos (.docx, .txt, .xlsx, .drawio), resultados JSON, propuestas .docx, prompts, plantillas | KMS + Versionado + CORS (GET/PUT) |
| `coppel-cloud-portal` | Archivos estáticos del portal web | Public read + Static website |

Trigger S3 (`s3:ObjectCreated:*`) en el prefijo `iniciativas/` invoca automáticamente `registrar_insumo`.

### 5.6 RDS PostgreSQL

Instancia auxiliar para datos relacionales del sistema.

| Parámetro | Valor |
|---|---|
| Motor | PostgreSQL 16 |
| Instancia | db.t3.micro |
| Almacenamiento | 20 GB gp2 |
| Multi-AZ | No |
| Credenciales | Secrets Manager (`coppel-cloud/rds/password`) |
| VPC | Default VPC |

### 5.7 Inteligencia Artificial — Claude

| Aspecto | Detalle |
|---|---|
| Modelo | `claude-sonnet-5` (Anthropic API) |
| Autenticación | API key en Secrets Manager (`coppel-cloud/anthropic-api-key`) |
| Uso 1 — Validación | Analiza 8 secciones del Quick Discovery, genera puntaje y lista de huecos |
| Uso 2 — Extracción | `tool_use` forzado para extraer Ficha Técnica estructurada (Pydantic schema) |
| Uso 3 — Generación | Genera contenido narrativo para la propuesta Word |
| Prompts | Almacenados en S3, versionados, editables sin redeploy |

Las 8 secciones validadas: Metadata · Requisitos · Datos · Dependencias · Entorno/Red · Migración · Infraestructura · Disaster Recovery.

---

## 6. Modelo de Datos — Ficha Técnica

La Ficha Técnica es el modelo canónico del sistema, definido en Pydantic v2 (`backend/common/schema.py`):

```
FichaTecnica
├── proyecto          (id, nombre, descripcion, nube, ambiente, business_tags)
├── requisitos        (sla, latencia_ms, disponibilidad, seguridad, escalabilidad)
├── datos             (tipo, volumen, clasificacion, cifrado)
├── dependencias      (onprem[], aws[], gcp[], otros[])
├── red               (vpc, subnets, seguridad_red, conectividad)
├── componentes
│   ├── nodos[]       (nombre, tipo_instancia, vcpu, ram_gb, so, cantidad)
│   ├── bases_datos[] (nombre, motor, version, multi_az, replicas)
│   ├── lambdas[]     (nombre, runtime, memoria_mb, timeout_s)
│   ├── kubernetes[]  (cluster, nodos_min, nodos_max, tipo_instancia)
│   └── servicios_adicionales[]
├── topologia         (nodos[], aristas[])
├── migracion         (estrategia, fases[], contingencia)
├── dr                (rpo, rto, estrategia, sitio_dr)
├── restricciones     (presupuesto, compliance[], exclusiones[])
└── validacion        (completitud 0-100, estado, huecos[], conflictos[])
```

---

## 7. Seguridad

### 7.1 IAM — Principio de Mínimo Privilegio

Tres roles diferenciados:

| Rol | Funciones | Permisos |
|---|---|---|
| `lambda_crud` | crear, listar, ficha | DynamoDB CRUD + S3 read/write + CloudWatch Logs |
| `lambda_registrar` | registrar_insumo | DynamoDB PutItem/UpdateItem + CloudWatch Logs |
| `lambda_ai` | validar, procesar, generar, propuesta | DynamoDB + S3 + Secrets Manager + Lambda:Invoke + Pricing API + CloudWatch Logs |

### 7.2 Cifrado y Secretos

| Componente | Mecanismo |
|---|---|
| S3 datos | SSE-KMS (aws:kms) |
| DynamoDB | Cifrado en reposo por defecto |
| API key Anthropic | AWS Secrets Manager |
| Credenciales RDS | AWS Secrets Manager |
| API Gateway | x-api-key obligatorio en todos los endpoints |

### 7.3 Red

| Componente | Configuración |
|---|---|
| VPC Endpoint S3 | Gateway (sin costo, tráfico privado) |
| VPC Endpoint Secrets Manager | Interface (DNS privado habilitado) |
| VPC Endpoint Lambda | Interface (invocaciones asíncronas privadas) |
| Security Group RDS | Ingress solo desde SG de Lambda en puerto 5432 |
| Security Group Lambda | Egress abierto, sin ingress |

---

## 8. Flujo de Datos Detallado

```
1. INGESTA
   Usuario → Portal (S3) → POST /iniciativas → crear_iniciativa
   → DynamoDB (estado: INGESTA) + presigned URLs
   → Usuario sube archivos directamente a S3
   → S3 trigger → registrar_insumo → DynamoDB (registro de insumos)

2. VALIDACIÓN
   Usuario → POST /iniciativas/{id}/validar → validar_iniciativa
   → (async) validar_worker
   → Lee insumos de S3
   → Claude analiza 8 secciones
   → DynamoDB (puntaje, huecos, estado: VALIDADO si ≥75%)

3. PROCESAMIENTO
   Usuario → POST /iniciativas/{id}/procesar → procesar_iniciativa
   → Claude con tool_use forzado
   → Extrae FichaTecnica estructurada
   → S3 (ficha.json) + DynamoDB

4. GENERACIÓN DE PROPUESTA
   Usuario → POST /iniciativas/{id}/propuesta → generar_propuesta
   → (async) propuesta_worker
   → Claude genera contenido narrativo
   → AWS Pricing API consulta precios reales
   → python-docx genera documento Word con plantilla corporativa
   → S3 (propuesta.docx)
   → DynamoDB (estado: COMPLETADO + URL de descarga)

5. DESCARGA
   Usuario → GET /iniciativas/{id}/resultados/propuesta
   → presigned URL de S3 → descarga .docx
```

---

## 9. Infraestructura como Código

Todo el sistema se provisiona con Terraform (>= 1.5).

| Archivo | Recursos |
|---|---|
| `main.tf` | Provider AWS, variables, locals |
| `s3.tf` | Buckets iniciativas y portal, notificación S3→Lambda |
| `dynamodb.tf` | Tabla Iniciativas con GSI1 |
| `lambda.tf` | 10 funciones Lambda + Layer + variables de entorno |
| `apigateway.tf` | REST API, recursos, métodos, integraciones, deployment, stage prod |
| `apikey.tf` | API Key y Usage Plan |
| `iam.tf` | 3 roles + políticas con mínimo privilegio |
| `rds.tf` | RDS PostgreSQL, Security Groups, Subnet Group, Secrets Manager |
| `vpc_endpoints.tf` | VPC Endpoints S3 (Gateway), Secrets Manager e Lambda (Interface) |
| `modules/cors/` | Módulo reutilizable para OPTIONS en cada recurso API |
| `outputs.tf` | api_url, portal_url, iniciativas_bucket, rds_endpoint |

---

## 10. Entregables del Sistema

| Artefacto | Formato | Descripción |
|---|---|---|
| Propuesta de Arquitectura | `.docx` | Documento Word con plantilla corporativa, 8 secciones + tabla de costos |
| Ficha Técnica | `.json` | Modelo estructurado extraído por IA (Pydantic FichaTecnica) |
| Servicios AWS identificados | `.json` | Lista con justificación, prioridad (REQUERIDO/RECOMENDADO/OPCIONAL) y ambiente |
| Validación de completitud | Dashboard | Puntaje por sección, huecos críticos, estado del análisis |
| Estimación de costos | Tabla en Word | Costos mensuales/anuales por servicio con totales (AWS Pricing API) |

---

## 11. Consideraciones Operativas

| Aspecto | Detalle |
|---|---|
| Modelo de costo | 100% serverless — pago por uso (Lambda, DynamoDB on-demand, API Gateway) |
| Escalabilidad | Automática — Lambda y DynamoDB escalan sin configuración |
| Disponibilidad | Heredada de los servicios AWS administrados (SLA ≥ 99.9%) |
| Observabilidad | CloudWatch Logs en todas las funciones Lambda |
| Actualizaciones de prompts | Sin redeploy — prompts versionados en S3 |
| Timeout máximo | 900s (propuesta_worker, procesar_iniciativa, generar_salidas) |
| Invocaciones asíncronas | validar_worker y propuesta_worker se invocan con `InvocationType=Event` para evitar timeout de API Gateway (29s) |
