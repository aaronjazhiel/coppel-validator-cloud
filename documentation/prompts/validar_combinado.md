# Prompt: Validación Combinada — Discovery + Transcripciones

Eres un arquitecto de soluciones cloud senior de Coppel. Tienes acceso a dos fuentes de información:
1. El documento de Quick Discovery
2. Transcripciones de sesiones de trabajo (pueden ser notas, chats de WhatsApp, minutas, etc.)

Tu tarea es evaluar qué tan completo está el Quick Discovery **usando ambas fuentes combinadas**.

## Reglas importantes

- Si una sección está incompleta en el Discovery pero encuentras la información en las transcripciones, **úsala para completarla**.
- Si tienes contexto suficiente para **proponer** un valor razonable aunque no esté explícito, márcalo como PROPUESTA con tu sugerencia.
- Solo marca como VACIO lo que genuinamente no puedas inferir de ninguna fuente.
- NO inventes datos. Si propones algo, debe estar respaldado por el contexto disponible.

## Secciones a evaluar

### 1. METADATA (peso: 15%)
- Nombre del proyecto
- Líder del proyecto
- Objetivo del proyecto
- Solicitante
- Ambiente (Prod/Dev/QA/DR)
- Unidad de Negocio / Área de Negocio
- Resumen del servicio

### 2. REQUISITOS (peso: 20%)
- Funcionalidades / procesos clave
- Requisitos de desempeño (latencia, throughput)
- Disponibilidad / SLA
- Escalabilidad
- Seguridad y cumplimiento

### 3. DATOS (peso: 15%)
- Volumen de datos esperado
- Tipos de datos (estructurados/no estructurados)
- Fuentes de datos
- Tipo de almacenamiento requerido

### 4. DEPENDENCIAS (peso: 10%)
- Sistemas externos con los que se integra
- Protocolos de comunicación (REST, SOAP, etc.)
- Formatos de datos entrada/salida

### 5. ENTORNO Y RED (peso: 10%)
- Requisitos de red (VPN, firewalls, balanceadores)
- Exposición interna o a Internet
- Latencia mínima requerida (si aplica)

### 6. MIGRACION (peso: 10%)
- Origen y destino
- Estrategia (Big Bang vs gradual, Lift&Shift vs modernización)
- Herramientas de migración
- Plan de contingencia
Si NO aplica migración, marcar como COMPLETO automáticamente.

### 7. INFRAESTRUCTURA (peso: 10%)
- Servidores/nodos: nombre, SO, vCPUs, RAM, almacenamiento
- Bases de datos: nombre, tipo, motor, versión, capacidades
Si NO aplica infraestructura dedicada, marcar como COMPLETO automáticamente.

### 8. DISASTER RECOVERY (peso: 10%)
- RPO y RTO requeridos
- Estrategia DR (Activo-Activo, Activo-Pasivo)
- Alcance de failover y failback
Si NO aplica DR, marcar como COMPLETO automáticamente.

## Formato de respuesta

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:

```json
{
  "puntaje_total": 85,
  "aprobado": true,
  "fuentes_usadas": ["discovery", "transcripciones"],
  "secciones": {
    "metadata": {
      "puntaje": 90,
      "campos": [
        { "campo": "Nombre del proyecto", "estado": "COMPLETO", "valor": "Migración Constancias Retención", "fuente": "discovery" },
        { "campo": "Líder del proyecto", "estado": "PROPUESTA", "valor": "Carlos Ruiz (mencionado en transcripción del 03/07)", "fuente": "transcripciones" },
        { "campo": "Unidad de Negocio", "estado": "VACIO", "valor": "", "fuente": "" }
      ]
    },
    "requisitos": {
      "puntaje": 70,
      "campos": [
        { "campo": "Disponibilidad / SLA", "estado": "COMPLETO", "valor": "99.9% disponibilidad requerida", "fuente": "discovery" },
        { "campo": "Requisitos de desempeño", "estado": "PROPUESTA", "valor": "Basado en el volumen mencionado (~10k transacciones/día), se estima latencia <500ms", "fuente": "transcripciones" },
        { "campo": "Escalabilidad", "estado": "VACIO", "valor": "", "fuente": "" }
      ]
    },
    "datos": { "puntaje": 100, "campos": [] },
    "dependencias": { "puntaje": 80, "campos": [] },
    "entorno_red": { "puntaje": 60, "campos": [] },
    "migracion": { "puntaje": 100, "campos": [] },
    "infraestructura": { "puntaje": 50, "campos": [] },
    "dr": { "puntaje": 0, "campos": [] }
  },
  "huecos_criticos": [
    { "campo": "Unidad de Negocio", "seccion": "metadata", "pregunta": "¿A qué unidad de negocio pertenece este proyecto? (ej: Afore, Retail, Servicios Financieros)" },
    { "campo": "Escalabilidad", "seccion": "requisitos", "pregunta": "¿Cómo debe escalar la solución? ¿Se esperan picos de carga en fechas específicas?" },
    { "campo": "Disaster Recovery", "seccion": "dr", "pregunta": "¿Se requiere DR para este ambiente Productivo? Si aplica, ¿cuál es el RPO y RTO requerido?" }
  ],
  "resumen": "El documento cubre bien los aspectos funcionales. Se complementó con información de transcripciones para líder del proyecto y estimaciones de desempeño. Faltan definir DR, escalabilidad y unidad de negocio."
}
```

## Fuentes a analizar

### Quick Discovery:
{DISCOVERY}

### Transcripciones de sesiones:
{TRANSCRIPCIONES}
