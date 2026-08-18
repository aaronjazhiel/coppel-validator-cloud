# Diagrama de Arquitectura — Coppel Cloud Validator

```mermaid
graph TB
    %% ── Cliente ──────────────────────────────────────────
    subgraph Cliente["🌐 Cliente"]
        PORTAL["Portal Web<br/>(S3 Static Website)"]
        SWAGGER["Swagger UI<br/>/docs"]
    end

    %% ── API Layer ────────────────────────────────────────
    subgraph API["☁️ API Gateway (REST)"]
        APIGW["API Gateway<br/>x-api-key auth<br/>CORS habilitado"]
    end

    %% ── Compute ──────────────────────────────────────────
    subgraph Lambdas["⚡ Lambda Functions (Python 3.12)"]
        L_CREAR["crear_iniciativa<br/>256MB / 30s"]
        L_LISTAR["listar_iniciativas<br/>256MB / 30s"]
        L_FICHA["ficha<br/>256MB / 30s"]
        L_PROCESAR["procesar_iniciativa<br/>1024MB / 900s"]
        L_GENERAR["generar_salidas<br/>1024MB / 900s"]
        L_REGISTRAR["registrar_insumo<br/>256MB / 30s"]
    end

    %% ── Storage ──────────────────────────────────────────
    subgraph Storage["🗄️ Almacenamiento"]
        S3_INI["S3: coppel-cloud-iniciativas<br/>KMS Encrypted / Versionado"]
        DYNAMO["DynamoDB: Iniciativas<br/>Single-Table / PAY_PER_REQUEST<br/>GSI1 (por estado)"]
    end

    %% ── AI ───────────────────────────────────────────────
    subgraph AI["🤖 Inteligencia Artificial"]
        CLAUDE["Anthropic Claude<br/>claude-sonnet-4-20250514"]
        SECRETS["Secrets Manager<br/>anthropic-api-key"]
    end

    %% ── IAM ──────────────────────────────────────────────
    subgraph IAM["🔐 Seguridad"]
        ROLE_CRUD["Role: lambda-crud<br/>DynamoDB + S3"]
        ROLE_AI["Role: lambda-ai<br/>DynamoDB + S3 + Secrets + Lambda:Invoke"]
        ROLE_REG["Role: lambda-registrar<br/>DynamoDB"]
    end

    %% ── Flujo Principal ──────────────────────────────────
    PORTAL -->|HTTPS + x-api-key| APIGW
    SWAGGER -->|HTTPS + x-api-key| APIGW

    APIGW -->|"POST /iniciativas"| L_CREAR
    APIGW -->|"GET /iniciativas<br/>GET /iniciativas/{id}"| L_LISTAR
    APIGW -->|"GET/PUT /iniciativas/{id}/ficha"| L_FICHA
    APIGW -->|"POST /iniciativas/{id}/procesar"| L_PROCESAR
    APIGW -->|"POST /iniciativas/{id}/generar/{tipo}"| L_GENERAR

    %% ── S3 Trigger ──────────────────────────────────────
    S3_INI -->|"S3:ObjectCreated<br/>(trigger automático)"| L_REGISTRAR

    %% ── Lambda → Storage ─────────────────────────────────
    L_CREAR --> S3_INI
    L_CREAR --> DYNAMO
    L_LISTAR --> DYNAMO
    L_LISTAR --> S3_INI
    L_FICHA --> S3_INI
    L_FICHA --> DYNAMO
    L_PROCESAR --> S3_INI
    L_PROCESAR --> DYNAMO
    L_PROCESAR --> CLAUDE
    L_GENERAR --> S3_INI
    L_GENERAR --> DYNAMO
    L_GENERAR --> CLAUDE
    L_REGISTRAR --> DYNAMO

    %% ── AI Auth ──────────────────────────────────────────
    L_PROCESAR --> SECRETS
    L_GENERAR --> SECRETS

    %% ── Async Self-Invoke ────────────────────────────────
    L_PROCESAR -.->|"async self-invoke<br/>InvocationType=Event"| L_PROCESAR
    L_GENERAR -.->|"async self-invoke<br/>InvocationType=Event"| L_GENERAR

    %% ── Upload directo ───────────────────────────────────
    PORTAL -->|"PUT presigned URL<br/>(upload directo)"| S3_INI
```

## Flujo de Datos

```mermaid
sequenceDiagram
    participant U as Usuario
    participant P as Portal Web
    participant AG as API Gateway
    participant LC as Lambda: crear
    participant S3 as S3 Bucket
    participant LR as Lambda: registrar
    participant DB as DynamoDB
    participant LP as Lambda: procesar
    participant CL as Claude AI
    participant LG as Lambda: generar

    Note over U,LG: 1️⃣ INGESTA
    U->>P: Crea iniciativa + selecciona archivos
    P->>AG: POST /iniciativas
    AG->>LC: Invoke
    LC->>DB: Crear registro (estado=INGESTA)
    LC->>S3: Generar presigned URLs
    LC-->>P: 201 + upload_urls
    P->>S3: PUT archivos (presigned URL directo)
    S3->>LR: Trigger ObjectCreated
    LR->>DB: Registrar insumo

    Note over U,LG: 2️⃣ PROCESAMIENTO
    U->>P: Click "Procesar"
    P->>AG: POST /iniciativas/{id}/procesar
    AG->>LP: Invoke (sync → responde 202)
    LP->>LP: Auto-invoke async
    LP->>S3: Leer insumos (.docx, .xml, .xlsx, .txt)
    LP->>CL: Enviar texto + schema (tool_use forzado)
    CL-->>LP: Ficha Técnica estructurada
    LP->>S3: Guardar ficha.json
    LP->>DB: Actualizar estado=EXTRAIDO

    Note over U,LG: 3️⃣ REVISIÓN
    U->>P: Ver/editar Ficha Técnica
    P->>AG: GET /iniciativas/{id}/ficha
    P->>AG: PUT /iniciativas/{id}/ficha (edición manual)

    Note over U,LG: 4️⃣ GENERACIÓN
    U->>P: Click "Generar diagrama/documento/costos"
    P->>AG: POST /iniciativas/{id}/generar/{tipo}
    AG->>LG: Invoke (sync → responde 202)
    LG->>LG: Auto-invoke async
    LG->>S3: Leer ficha.json
    LG->>CL: Generar artefacto
    CL-->>LG: Contenido generado
    LG->>S3: Guardar salida (.drawio/.md/.csv)
    LG->>DB: Actualizar estado=GENERADO
```

## Estructura de S3

```
coppel-cloud-iniciativas/
└── iniciativas/
    └── {id_iniciativa}/
        ├── insumos/
        │   ├── discovery/       ← .docx (Quick Discovery)
        │   ├── diagrama/        ← .xml (draw.io)
        │   ├── transcripciones/ ← .txt
        │   └── componentes/     ← .xlsx
        ├── ficha/
        │   ├── ficha.json       ← Ficha Técnica actual
        │   ├── ficha-v1.json    ← Versión anterior
        │   └── ficha-v2.json
        └── salidas/
            ├── diagrama.drawio  ← Generado por Claude
            ├── documento.md
            └── costos.csv
```

## Modelo DynamoDB (Single-Table)

| PK | SK | Descripción |
|----|-----|-------------|
| `INIT#<id>` | `META` | Metadata de la iniciativa |
| `INIT#<id>` | `EVENT#<timestamp>` | Eventos de auditoría |

**GSI1:** `GSI1PK = ESTADO#<estado>`, `GSI1SK = timestamp` → consulta por estado

## Recursos AWS Desplegados

| Servicio | Recurso | Región |
|----------|---------|--------|
| API Gateway | `coppel-cloud-prod-api` | us-east-1 |
| Lambda x6 | crear, listar, ficha, procesar, generar, registrar | us-east-1 |
| Lambda Layer | `coppel-cloud-prod-deps:5` (anthropic, pydantic, docx, openpyxl) | us-east-1 |
| DynamoDB | `Iniciativas` (PAY_PER_REQUEST) | us-east-1 |
| S3 | `coppel-cloud-iniciativas` (KMS, versionado) | us-east-1 |
| S3 | `coppel-cloud-portal` (static website) | us-east-1 |
| Secrets Manager | `coppel-cloud/anthropic-api-key` | us-east-1 |
| IAM | 3 roles (crud, ai, registrar) | global |
