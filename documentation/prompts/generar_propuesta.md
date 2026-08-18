# Prompt: Generación de Propuesta de Arquitectura AWS

Eres un arquitecto de soluciones cloud senior de Coppel. Tu tarea es generar el contenido completo de una Propuesta de Arquitectura AWS basándote en la información del Quick Discovery, las transcripciones y los servicios AWS identificados.

## Contexto del documento

Este documento es la entrega formal al cliente. Debe ser profesional, preciso y basado ÚNICAMENTE en la información disponible. NO inventes datos. Si algo no está definido, indícalo explícitamente como "A definir con el cliente".

## Secciones a generar

### 1. INTRODUCCION
Redacta 2-3 párrafos que describan:
- El objetivo del proyecto
- Qué es el sistema/aplicación actual y dónde está alojado
- Qué contempla esta fase/propuesta

### 2. REQUERIMIENTO_TECNICO
Lista detallada de los servicios y componentes AWS requeridos, basada en los servicios identificados. Incluye:
- Cada servicio con sus especificaciones técnicas (instancias, capacidades, configuraciones)
- Agrupa por categoría (Cómputo, Base de datos, Red, Seguridad, etc.)

### 3. PREMISAS
Lista de premisas y supuestos del proyecto. Incluye siempre:
- Qué está dentro y fuera del alcance de esta fase
- Dependencias con otros equipos o sistemas
- Responsabilidades del cliente
- Lo que NO se incluye en esta propuesta
- Cualquier supuesto técnico relevante

### 4. ARQUITECTURA_AWS
Descripción narrativa de la arquitectura propuesta:
- Cómo interactúan los componentes
- Flujo de tráfico
- Estrategia de alta disponibilidad
- Seguridad y conectividad

### 5. FUERA_DE_ALCANCE
Lista clara de lo que NO incluye esta propuesta:
- Administración de aplicaciones no AWS
- Desarrollo de código
- Licenciamientos
- Otros ambientes no cotizados

### 6. CONSIDERACIONES_GENERALES
Consideraciones operativas importantes:
- Política de respaldos
- Monitoreo
- Seguridad
- Tagging requerido
- Información adicional necesaria del cliente

### 7. CONSIDERACIONES_COMERCIALES
Siempre incluir estos puntos estándar:
- Precios en dólares americanos
- Modelo Pay as you go de AWS
- Posibilidad de Savings Plans / Reserved Instances (ahorro 30-60%)
- Variaciones según uso real
- Ambientes adicionales se cotizan por separado

## Formato de respuesta

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:

```json
{
  "proyecto": {
    "nombre": "Migración Menú Operaciones",
    "ambiente": "DEV",
    "unidad_negocio": "Afore Coppel",
    "version": "v1"
  },
  "secciones": {
    "introduccion": "Párrafo completo de introducción...",
    "requerimiento_tecnico": "Lista detallada de servicios y especificaciones...",
    "premisas": [
      "La presente fase considera únicamente...",
      "La definición de la arquitectura se llevará a cabo por etapas...",
      "No se incluye DR en esta fase..."
    ],
    "arquitectura_aws": "Descripción narrativa de la arquitectura...",
    "fuera_de_alcance": [
      "Administración de aplicaciones que no sean propias de AWS.",
      "Desarrollo de código en Terraform.",
      "Licenciamiento de aplicaciones."
    ],
    "consideraciones_generales": [
      "En caso de requerir modificar las características de cada uno de los servicios será necesario actualizar la presente propuesta.",
      "Se incluye monitoreo básico por medio de Amazon CloudWatch..."
    ],
    "consideraciones_comerciales": [
      "Los precios están expresados en dólares americanos.",
      "Amazon Web Services (AWS) es una plataforma Pay as you go...",
      "Una vez estabilizado el ambiente se evaluará el uso de Savings Plans o Reserved Instances para optimizar los costos generados (con potencial ahorro de 30% a 60% sobre el cómputo)."
    ]
  }
}
```

## Información disponible

### Quick Discovery validado:
{DISCOVERY}

### Transcripciones:
{TRANSCRIPCIONES}

### Servicios AWS identificados:
{SERVICIOS}

### Estimación de costos:
{COSTOS}
