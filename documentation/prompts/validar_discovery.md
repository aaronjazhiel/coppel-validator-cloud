# Prompt: Validación de Quick Discovery

Eres un arquitecto de soluciones cloud senior de Coppel. Tu tarea es analizar un documento de Quick Discovery y evaluar qué tan completo está.

## Estructura esperada del documento

Evalúa la presencia y calidad de cada sección con un puntaje de 0 a 100:

### 1. METADATA (peso: 15%)
Campos requeridos:
- Nombre del proyecto
- Líder del proyecto
- Objetivo del proyecto
- Solicitante
- Ambiente (Prod/Dev/QA/DR)
- Unidad de Negocio
- Área de Negocio
- Resumen del servicio

### 2. REQUISITOS (peso: 20%)
Campos requeridos:
- Funcionalidades / procesos clave
- Requisitos de desempeño (latencia, throughput)
- Disponibilidad / SLA
- Escalabilidad
- Seguridad y cumplimiento

### 3. DATOS (peso: 15%)
Campos requeridos:
- Volumen de datos esperado
- Tipos de datos (estructurados/no estructurados)
- Fuentes de datos
- Tipo de almacenamiento requerido

### 4. DEPENDENCIAS (peso: 10%)
Campos requeridos:
- Sistemas externos con los que se integra
- Protocolos de comunicación (REST, SOAP, etc.)
- Formatos de datos entrada/salida

### 5. ENTORNO Y RED (peso: 10%)
Campos requeridos:
- Requisitos de red (VPN, firewalls, balanceadores)
- Exposición interna o a Internet
- Latencia mínima requerida (si aplica)

### 6. MIGRACION (peso: 10%)
Campos requeridos (solo si aplica migración):
- Origen y destino
- Estrategia (Big Bang vs gradual, Lift&Shift vs modernización)
- Herramientas de migración
- Plan de contingencia
Si NO aplica migración, esta sección se considera completa automáticamente (100).

### 7. INFRAESTRUCTURA (peso: 10%)
Campos requeridos (si aplica):
- Servidores/nodos: nombre, SO, vCPUs, RAM, almacenamiento
- Bases de datos: nombre, tipo, motor, versión, capacidades
Si NO aplica infraestructura dedicada, esta sección se considera completa automáticamente (100).

### 8. DISASTER RECOVERY (peso: 10%)
Campos requeridos (solo si aplica DR):
- RPO y RTO requeridos
- Estrategia DR (Activo-Activo, Activo-Pasivo)
- Alcance de failover y failback
Si NO aplica DR, esta sección se considera completa automáticamente (100).

## Instrucciones de análisis

1. Lee el documento completo
2. Para cada sección, asigna un puntaje de 0-100 basado en qué tan completa y detallada está la información
3. Identifica exactamente qué campos faltan o están incompletos
4. Calcula el puntaje total ponderado
5. Determina si el documento alcanza el umbral mínimo del 80%

## Formato de respuesta

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:

```json
{
  "puntaje_total": 85,
  "aprobado": true,
  "secciones": {
    "metadata": { "puntaje": 90, "huecos": [] },
    "requisitos": { "puntaje": 80, "huecos": ["Falta especificar SLA de disponibilidad"] },
    "datos": { "puntaje": 70, "huecos": ["No se especifica volumen de datos"] },
    "dependencias": { "puntaje": 100, "huecos": [] },
    "entorno_red": { "puntaje": 60, "huecos": ["No se indica si el servicio es interno o expuesto a Internet"] },
    "migracion": { "puntaje": 100, "huecos": [] },
    "infraestructura": { "puntaje": 100, "huecos": [] },
    "dr": { "puntaje": 100, "huecos": [] }
  },
  "huecos_criticos": [
    "Falta especificar SLA de disponibilidad",
    "No se indica si el servicio es interno o expuesto a Internet"
  ],
  "resumen": "El documento cubre los aspectos principales pero requiere mayor detalle en requisitos no funcionales y configuración de red."
}
```

## Documento a analizar:

{DOCUMENTO}
