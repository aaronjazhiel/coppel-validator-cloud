# Guía de Despliegue — Coppel Validator Cloud

## Índice
1. [Prerrequisitos](#1-prerrequisitos)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Estructura del Proyecto](#3-estructura-del-proyecto)
4. [Preparar el Backend (Layer + Código)](#4-preparar-el-backend-layer--código)
5. [Levantar la Infraestructura con Terraform](#5-levantar-la-infraestructura-con-terraform)
6. [Inicializar la Base de Datos](#6-inicializar-la-base-de-datos)
7. [Desplegar el Frontend en S3](#7-desplegar-el-frontend-en-s3)
8. [Verificar el Sistema](#8-verificar-el-sistema)
9. [Outputs del Sistema](#9-outputs-del-sistema)
10. [Destruir la Infraestructura](#10-destruir-la-infraestructura)

---

## 1. Prerrequisitos

### Herramientas requeridas

| Herramienta | Versión mínima | Instalación |
|---|---|---|
| Terraform | >= 1.5 | https://developer.hashicorp.com/terraform/install |
| AWS CLI | >= 2.x | https://aws.amazon.com/cli/ |
| Python | >= 3.12 | https://www.python.org/downloads/ |
| pip3 | >= 23.x | Incluido con Python |

### Configurar credenciales AWS

```bash
aws configure
# AWS Access Key ID: <tu-access-key>
# AWS Secret Access Key: <tu-secret-key>
# Default region name: us-east-1
# Default output format: json
```

Verificar que las credenciales funcionan:

```bash
aws sts get-caller-identity
```

### Secret de Anthropic en AWS Secrets Manager

El sistema usa Claude (Anthropic) para el análisis de iniciativas. Antes de desplegar, crea el secret:

```bash
aws secretsmanager create-secret \
  --name "coppel-cloud/anthropic-api-key" \
  --secret-string '{"api_key":"<tu-anthropic-api-key>"}' \
  --region us-east-1
```

---

## 2. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        USUARIO                              │
│              S3 Static Website (frontend)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS + x-api-key
┌─────────────────────────▼───────────────────────────────────┐
│              API Gateway REST (prod stage)                  │
│                   x-api-key requerida                       │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬───────────────┘
   │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
Lambda Lambda Lambda Lambda Lambda Lambda Lambda
crear  listar validar proce  ficha  generar propuesta
inic.  inic.  inic.   sar           salidas worker
   │      │      │      │      │      │      │
   └──────┴──────┴──┬───┴──────┴──────┴──────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   PostgreSQL    S3 Bucket   DynamoDB
   RDS (16)     iniciativas  Iniciativas
   coppel_cloud
        │
        ▼
  Secrets Manager
  (RDS password +
   Anthropic key)
```

### Componentes principales

| Componente | Servicio AWS | Descripción |
|---|---|---|
| Frontend | S3 Website | Portal web estático |
| API | API Gateway REST | Endpoints con API Key |
| Lógica | Lambda (Python 3.12) | 10 funciones serverless |
| Base de datos | RDS PostgreSQL 16 | `db.t3.micro`, 20 GB |
| Almacenamiento | S3 `coppel-cloud-iniciativas` | Documentos e insumos |
| Caché/Estado | DynamoDB `Iniciativas` | Estado de iniciativas |
| Secretos | Secrets Manager | Credenciales RDS y Anthropic |
| Red | VPC Endpoints | S3, Lambda, Secrets Manager |

### Lambdas del sistema

| Función | Handler | Timeout | Memoria | Rol |
|---|---|---|---|---|
| `crear-iniciativa` | `lambdas.crear_iniciativa.handler` | 30s | 256 MB | crud |
| `listar` | `lambdas.listar_iniciativas.handler` | 30s | 256 MB | crud |
| `ficha` | `lambdas.ficha.handler` | 30s | 256 MB | crud |
| `registrar-insumo` | `lambdas.registrar_insumo.handler` | 30s | 256 MB | registrar |
| `validar` | `lambdas.validar_iniciativa.handler` | 300s | 512 MB | ai |
| `validar-worker` | `lambdas.validar_worker.handler` | 900s | 1024 MB | ai |
| `procesar` | `lambdas.procesar_iniciativa.handler` | 900s | 1024 MB | ai |
| `generar` | `lambdas.generar_salidas.handler` | 900s | 1024 MB | ai |
| `generar-propuesta` | `lambdas.generar_propuesta.handler` | 30s | 256 MB | ai |
| `propuesta-worker` | `lambdas.propuesta_worker.handler` | 900s | 1024 MB | ai |

### Endpoints de la API

| Método | Ruta | Lambda | Descripción |
|---|---|---|---|
| POST | `/iniciativas` | crear-iniciativa | Crear nueva iniciativa |
| GET | `/iniciativas` | listar | Listar todas las iniciativas |
| GET | `/iniciativas/{id}` | listar | Obtener iniciativa por ID |
| POST | `/iniciativas/{id}/validar` | validar | Validar iniciativa con IA |
| POST | `/iniciativas/{id}/procesar` | procesar | Procesar con Claude |
| GET | `/iniciativas/{id}/ficha` | ficha | Obtener ficha técnica |
| PUT | `/iniciativas/{id}/ficha` | ficha | Actualizar ficha técnica |
| POST | `/iniciativas/{id}/generar/{tipo}` | generar | Generar salidas (diagrama, costos, etc.) |
| POST | `/iniciativas/{id}/propuesta` | generar-propuesta | Generar propuesta Word |
| GET | `/iniciativas/{id}/resultados/{tipo}` | listar | Obtener resultados |

---

## 3. Estructura del Proyecto

```
coppel-validator-cloud/
├── frontend/               # Portal web estático
│   ├── index.html          # Dashboard principal
│   ├── login.html          # Pantalla de login
│   ├── listado.html        # Listado de iniciativas
│   ├── ingesta.html        # Carga de documentos
│   ├── paso1-validacion.html
│   ├── paso2-servicios.html
│   ├── paso3-costos.html
│   ├── paso4-propuesta.html
│   ├── detalle.html
│   ├── costos.html
│   ├── propuesta.html
│   ├── css/styles.css
│   └── js/
│       ├── app.js
│       └── sidebar.js
├── backend/                # Código Lambda Python
│   ├── lambdas/            # Handlers de cada función
│   ├── common/             # Utilidades compartidas
│   ├── requirements.txt    # Dependencias Python
│   ├── schema.sql          # DDL de la base de datos
│   └── build_layer.sh      # Script para construir el layer
├── infra/                  # Infraestructura Terraform
│   ├── main.tf             # Provider y variables
│   ├── s3.tf               # Buckets S3
│   ├── lambda.tf           # Funciones Lambda
│   ├── apigateway.tf       # API Gateway
│   ├── rds.tf              # PostgreSQL RDS
│   ├── dynamodb.tf         # Tabla DynamoDB
│   ├── iam.tf              # Roles y políticas
│   ├── apikey.tf           # API Key y Usage Plan
│   ├── vpc_endpoints.tf    # VPC Endpoints
│   ├── outputs.tf          # Outputs del stack
│   └── modules/cors/       # Módulo CORS para API GW
└── documentation/          # Documentación del proyecto
```

---

## 4. Preparar el Backend (Layer + Código)

El layer contiene todas las dependencias Python que usan las Lambdas.

```bash
cd coppel-validator-cloud/backend

# Dar permisos de ejecución al script
chmod +x build_layer.sh

# Construir el layer (genera layer.zip)
./build_layer.sh
```

El script instala las siguientes dependencias en el layer:

```
anthropic>=0.34.0     # Cliente Claude AI
pydantic>=2.0         # Validación de datos
boto3>=1.34           # SDK AWS
python-docx>=1.1      # Generación de documentos Word
openpyxl>=3.1         # Manejo de Excel
psycopg2-binary>=2.9  # Conexión PostgreSQL
```

Al finalizar verás:
```
✅ layer.zip generado (~XXX MB)
```

> El `lambda.zip` con el código fuente lo genera automáticamente Terraform en el siguiente paso.

---

## 5. Levantar la Infraestructura con Terraform

```bash
cd coppel-validator-cloud/infra
```

### 5.1 Inicializar Terraform

```bash
terraform init
```

Descarga los providers necesarios:
- `hashicorp/aws ~> 5.0`
- `hashicorp/random ~> 3.6`
- `hashicorp/archive`

### 5.2 Revisar el plan

```bash
terraform plan
```

Revisa que se van a crear los recursos esperados. Deberías ver aproximadamente **60+ recursos** a crear.

### 5.3 Aplicar la infraestructura

```bash
terraform apply
```

Escribe `yes` cuando lo solicite. El proceso tarda aproximadamente **8-12 minutos** principalmente por la creación del RDS.

Al finalizar verás los outputs:

```
Outputs:

api_url            = "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod"
iniciativas_bucket = "coppel-cloud-iniciativas"
portal_url         = "coppel-cloud-portal.s3-website-us-east-1.amazonaws.com"
rds_endpoint       = "coppel-cloud-prod-postgres.xxxxxxxxx.us-east-1.rds.amazonaws.com"
rds_secret_arn     = "arn:aws:secretsmanager:us-east-1:xxxxxxxxxxxx:secret:..."
```

### 5.4 Obtener la API Key

```bash
terraform output -raw api_key_value
```

Guarda este valor, lo necesitarás para configurar el frontend.

---

## 6. Inicializar la Base de Datos

Una vez que el RDS esté disponible, ejecuta el schema:

```bash
# Obtener el endpoint del RDS
RDS_HOST=$(terraform -chdir=infra output -raw rds_endpoint)

# Ejecutar el schema (requiere psql instalado)
psql -h $RDS_HOST -U coppel_admin -d coppel_cloud -f backend/schema.sql
```

Esto crea las tablas:
- `iniciativas` — tabla principal con índices por estado, solicitante y fecha
- `eventos` — auditoría de acciones sobre iniciativas

Si no tienes `psql`, puedes conectarte desde AWS Console → RDS → Query Editor.

---

## 7. Desplegar el Frontend en S3

### 7.1 Configurar la API URL en el frontend

Edita `frontend/js/app.js` y actualiza la URL de la API y la API Key:

```javascript
const API_URL = "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod";
const API_KEY = "<valor-obtenido-en-paso-5.4>";
```

### 7.2 Subir los archivos al bucket del portal

```bash
aws s3 sync frontend/ s3://coppel-cloud-portal/ --delete
```

### 7.3 Acceder al portal

```
http://coppel-cloud-portal.s3-website-us-east-1.amazonaws.com
```

---

## 8. Verificar el Sistema

### 8.1 Verificar la API

```bash
API_URL=$(terraform -chdir=infra output -raw api_url)
API_KEY=$(terraform -chdir=infra output -raw api_key_value)

# Listar iniciativas (debe retornar 200 con lista vacía)
curl -s -X GET "$API_URL/iniciativas" \
  -H "x-api-key: $API_KEY" | python3 -m json.tool
```

### 8.2 Crear una iniciativa de prueba

```bash
curl -s -X POST "$API_URL/iniciativas" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Iniciativa de prueba",
    "descripcion": "Test de despliegue",
    "solicitante": "admin",
    "ambiente": "Prod",
    "nube": "AWS"
  }' | python3 -m json.tool
```

### 8.3 Verificar Lambdas en AWS Console

```bash
# Ver logs de una Lambda
aws logs tail /aws/lambda/coppel-cloud-prod-crear-iniciativa --follow
```

### 8.4 Verificar conectividad RDS

```bash
psql -h $RDS_HOST -U coppel_admin -d coppel_cloud -c "SELECT COUNT(*) FROM iniciativas;"
```

---

## 9. Outputs del Sistema

| Output | Valor actual | Descripción |
|---|---|---|
| `api_url` | `https://1vo8syihoe.execute-api.us-east-1.amazonaws.com/prod` | URL base de la API |
| `portal_url` | `coppel-cloud-portal.s3-website-us-east-1.amazonaws.com` | URL del portal web |
| `iniciativas_bucket` | `coppel-cloud-iniciativas` | Bucket de documentos |
| `rds_endpoint` | `coppel-cloud-prod-postgres.cirege8e8twb.us-east-1.rds.amazonaws.com` | Host de PostgreSQL |

---

## 10. Destruir la Infraestructura

> ⚠️ Esto elimina **todos** los recursos incluyendo datos en RDS y S3.

```bash
cd infra

# Vaciar los buckets S3 primero (requerido antes de destruir)
aws s3 rm s3://coppel-cloud-iniciativas --recursive
aws s3 rm s3://coppel-cloud-portal --recursive

# Destruir toda la infraestructura
terraform destroy
```

Escribe `yes` para confirmar.

---

## Notas adicionales

- El RDS tiene `publicly_accessible = true` para facilitar el desarrollo. En producción se recomienda cambiar a `false` y acceder solo desde las Lambdas vía VPC.
- Los VPC Endpoints de S3, Lambda y Secrets Manager están configurados para reducir latencia y costos de transferencia.
- El Usage Plan de la API Key tiene un límite de **10,000 requests/día** con throttling de 100 req/s y burst de 50.
- Las Lambdas de IA (`validar`, `procesar`, `generar`, `propuesta-worker`) tienen timeout de **900 segundos** para soportar respuestas largas de Claude.
