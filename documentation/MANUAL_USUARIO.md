# Manual de Usuario — CloudArch AI
### Portal de Arquitectura Cloud · Coppel
**Versión 1.0 · 2025**

---

## Tabla de Contenidos

1. [¿Qué es CloudArch AI?](#1-qué-es-cloudarch-ai)
2. [Acceso al Portal](#2-acceso-al-portal)
3. [Dashboard Principal](#3-dashboard-principal)
4. [Crear una Nueva Iniciativa](#4-crear-una-nueva-iniciativa)
5. [Paso 1 — Validación de Documentos](#5-paso-1--validación-de-documentos)
6. [Paso 2 — Servicios AWS Identificados](#6-paso-2--servicios-aws-identificados)
7. [Paso 3 — Estimación de Costos](#7-paso-3--estimación-de-costos)
8. [Paso 4 — Generar Propuesta](#8-paso-4--generar-propuesta)
9. [Estados de una Iniciativa](#9-estados-de-una-iniciativa)
10. [Preguntas Frecuentes](#10-preguntas-frecuentes)

---

## 1. ¿Qué es CloudArch AI?

CloudArch AI es un portal interno del Área de Arquitectura Cloud de Coppel que automatiza el proceso de análisis y generación de propuestas de arquitectura en AWS.

**¿Qué hace el sistema por ti?**

| Tarea manual (antes) | Con CloudArch AI |
|---|---|
| Revisar el Quick Discovery a mano | La IA evalúa completitud en segundos |
| Pedir información faltante por correo | El sistema genera el correo automáticamente |
| Identificar servicios AWS uno por uno | Extracción automática con IA |
| Consultar precios en calculator.aws | Consulta automática vía AWS Pricing API |
| Redactar la propuesta Word desde cero | Documento generado en ~2 minutos |

**Flujo general:**

```
Ingesta de documentos → Validación con IA → Servicios AWS → Costos → Propuesta Word
```

---

## 2. Acceso al Portal

Abre tu navegador y accede a la URL del portal:

```
http://coppel-cloud-portal.s3-website-us-east-1.amazonaws.com
```

> No se requiere usuario ni contraseña. El acceso está controlado por red interna.

<!-- IMAGEN: Pantalla de inicio del portal -->
> 📷 _[Insertar captura de la pantalla de inicio]_

---

## 3. Dashboard Principal

Al ingresar verás el dashboard con un resumen de todas las iniciativas registradas.

<!-- IMAGEN: Dashboard principal con las 4 tarjetas de estadísticas y la tabla de iniciativas -->
> 📷 _[Insertar captura del dashboard]_

### Tarjetas de resumen

| Tarjeta | Descripción |
|---|---|
| **Total Iniciativas** | Número total de iniciativas registradas en el sistema |
| **En Proceso** | Iniciativas que están siendo validadas o procesadas |
| **Propuestas Generadas** | Iniciativas con propuesta Word lista para descargar |
| **Incompletas** | Iniciativas con documentación insuficiente |

### Tabla de iniciativas

Muestra las iniciativas más recientes con:
- **ID** — Identificador único (ej. `INI-2025-ABCDE`)
- **Nombre** — Nombre del proyecto
- **Solicitante** — Quien solicitó la arquitectura
- **Estado** — Estado actual del flujo (ver sección 9)
- **Completitud** — Porcentaje de completitud del Quick Discovery
- **Fecha** — Fecha de creación

Haz clic en cualquier fila para abrir el detalle de esa iniciativa.

---

## 4. Crear una Nueva Iniciativa

Haz clic en el botón **+ Nueva Iniciativa** desde el dashboard o accede directamente a `ingesta.html`.

<!-- IMAGEN: Pantalla de ingesta con el formulario de datos de la iniciativa -->
> 📷 _[Insertar captura de la pantalla de ingesta]_

### 4.1 Datos de la Iniciativa

Completa los campos obligatorios marcados con `*`:

| Campo | Obligatorio | Descripción |
|---|---|---|
| Nombre del Proyecto | ✅ Sí | Nombre descriptivo del proyecto |
| Solicitante | ✅ Sí | Nombre de quien solicita la arquitectura |
| Objetivo del Proyecto | No | Descripción breve del objetivo |
| Líder del Proyecto | No | Nombre del líder técnico |

### 4.2 Business Tags

Sección colapsada por defecto. Expándela haciendo clic en el encabezado **🏷️ Business Tags**.

Contiene información organizacional y de presupuesto como: unidad de negocio, centro de costos, ambiente, responsables, etc.

> Estos datos se incluyen en la propuesta Word final. Completa los que apliquen.

<!-- IMAGEN: Sección de Business Tags expandida -->
> 📷 _[Insertar captura de la sección Business Tags]_

### 4.3 Subir Insumos

El sistema acepta 4 tipos de documentos:

| Tipo | Formato | Descripción |
|---|---|---|
| **Quick Discovery** | `.docx` | Documento principal con los requerimientos del proyecto |
| **Diagrama** | `.drawio` / `.xml` | Diagrama de arquitectura existente (si lo hay) |
| **Transcripciones / Notas** | `.txt` / `.md` | Notas o minutas de reuniones con el cliente |
| **Componentes N2** | `.xlsx` | Excel de inventario de infraestructura actual |

**Para subir archivos:**
1. Arrastra el archivo sobre la zona correspondiente, o
2. Haz clic en la zona y selecciona el archivo desde tu equipo
3. Puedes subir múltiples archivos por tipo

<!-- IMAGEN: Zonas de carga de archivos con un archivo ya seleccionado -->
> 📷 _[Insertar captura de las zonas de carga]_

> ⚠️ Se requiere al menos un archivo para poder crear la iniciativa.

### 4.4 Crear y Procesar

Una vez completados los datos y seleccionados los archivos:

1. Haz clic en **Crear y Subir Insumos** — el sistema crea la iniciativa y sube los archivos directamente a S3
2. Verás una barra de progreso por cada archivo
3. Cuando todos los archivos estén subidos, el botón **Procesar con IA** se habilitará
4. Haz clic en **Procesar con IA** para iniciar el análisis

<!-- IMAGEN: Barra de progreso de subida de archivos -->
> 📷 _[Insertar captura del progreso de subida]_

> 💡 El botón **Cargar datos de prueba** rellena el formulario con datos de ejemplo para hacer una prueba rápida.

---

## 5. Paso 1 — Validación de Documentos

Una vez creada la iniciativa, el sistema te lleva al **Paso 1: Validación de Documentos**.

Aquí la IA analiza los documentos subidos y evalúa su completitud.

<!-- IMAGEN: Pantalla completa del Paso 1 con el score y las secciones -->
> 📷 _[Insertar captura del Paso 1]_

### 5.1 Documentos Cargados

En la parte superior verás la lista de archivos subidos para esta iniciativa. Si falta algún tipo de documento, el sistema mostrará un aviso en naranja.

Puedes agregar más documentos directamente desde esta pantalla sin regresar a la ingesta:
1. Haz clic o arrastra sobre la zona del tipo de documento que quieres agregar
2. Haz clic en **Subir archivos**

### 5.2 Validar Quick Discovery

Haz clic en el botón **Validar Discovery** para que la IA analice el documento.

<!-- IMAGEN: Overlay de procesamiento con el ícono girando -->
> 📷 _[Insertar captura del overlay de procesamiento]_

El análisis tarda entre 30 y 90 segundos. Al terminar verás:

**Puntaje general de completitud** (0–100%)

| Rango | Significado |
|---|---|
| 🟢 75% o más | Documento aprobado — puedes continuar |
| 🟡 50–74% | Incompleto — se recomienda completar antes de continuar |
| 🔴 Menos de 50% | Muy incompleto — es necesario completar el documento |

**Detalle por sección** — el documento se evalúa en 8 secciones:

| Sección | Qué evalúa |
|---|---|
| Metadata | Nombre del proyecto, ambiente, responsables |
| Requisitos | SLA, usuarios concurrentes, disponibilidad |
| Datos | Volumen, tipo de datos, retención |
| Dependencias | Sistemas externos, APIs, integraciones |
| Entorno / Red | Conectividad, VPN, puertos |
| Migración | Origen, estrategia, ventana de migración |
| Infraestructura | Cómputo, storage, bases de datos |
| Disaster Recovery | RPO, RTO, estrategia de DR |

<!-- IMAGEN: Tarjetas de detalle por sección con colores verde/naranja/rojo -->
> 📷 _[Insertar captura del detalle por sección]_

Cada tarjeta muestra:
- El puntaje de esa sección
- Cuántos campos están completos
- Los campos específicos que faltan

### 5.3 Validar Componentes N2

Si subiste un archivo `.xlsx` de Componentes N2, haz clic en **Validar N2**.

El sistema analiza 3 hojas del Excel:

| Hoja | Descripción |
|---|---|
| Req Infra-Ambiente | Requerimientos de infraestructura por ambiente |
| Recursos AWS | Instancias y servicios AWS configurados |
| Recursos GCP | Instancias y servicios GCP configurados |

<!-- IMAGEN: Resultado de validación N2 con las 3 secciones -->
> 📷 _[Insertar captura del resultado N2]_

### 5.4 Puntaje General Combinado

Si validaste ambos documentos (Discovery + N2), el sistema calcula un **puntaje general combinado**:

```
Puntaje General = 50% Discovery + 50% N2
```

<!-- IMAGEN: Tarjeta de puntaje general combinado -->
> 📷 _[Insertar captura del puntaje general]_

### 5.5 Correo de Seguimiento

Cuando el puntaje es menor al 80%, el sistema genera automáticamente un **correo de seguimiento** listo para copiar y enviar al solicitante, con la lista exacta de información faltante.

<!-- IMAGEN: Área del correo de seguimiento generado -->
> 📷 _[Insertar captura del correo generado]_

1. Revisa el texto del correo
2. Haz clic en **📋 Copiar**
3. Pégalo en tu cliente de correo y envíalo al solicitante

### 5.6 Avanzar al Paso 2

Haz clic en **Siguiente: Servicios →** para continuar.

> Puedes avanzar aunque el puntaje sea menor al 75%, pero el botón se mostrará con menor opacidad como advertencia visual.

---

## 6. Paso 2 — Servicios AWS Identificados

En este paso verás los servicios AWS que la IA identificó como necesarios para el proyecto.

<!-- IMAGEN: Tabla de servicios AWS con categorías y prioridades -->
> 📷 _[Insertar captura del Paso 2]_

### 6.1 Tabla de Servicios

Cada servicio muestra:

| Columna | Descripción |
|---|---|
| Servicio AWS | Nombre del servicio (ej. Amazon EKS) |
| Categoría | Tipo de servicio (Cómputo, BD, Red, Seguridad, etc.) |
| Prioridad | REQUERIDO / RECOMENDADO / OPCIONAL |
| Justificación | Por qué la IA identificó este servicio |

**Prioridades:**
- 🟢 **REQUERIDO** — Indispensable para la arquitectura
- 🟡 **RECOMENDADO** — Mejora la solución pero no es crítico
- ⚪ **OPCIONAL** — Puede incluirse según presupuesto

### 6.2 Editar la Lista

**Eliminar un servicio:** Haz clic en el botón ✕ al final de la fila.

**Agregar un servicio manualmente:**
1. Escribe el nombre del servicio en el campo **Servicio AWS**
2. Selecciona la categoría y prioridad
3. Haz clic en **+ Agregar**

<!-- IMAGEN: Formulario de agregar servicio -->
> 📷 _[Insertar captura del formulario de agregar servicio]_

### 6.3 Avanzar al Paso 3

Haz clic en **Siguiente: Costos →** cuando la lista de servicios esté lista.

---

## 7. Paso 3 — Estimación de Costos

El sistema muestra la estimación de costos mensuales y anuales basada en los servicios identificados, consultando precios reales de la **AWS Pricing API** en la región `us-east-1`.

<!-- IMAGEN: Pantalla del Paso 3 con las 3 tarjetas de resumen y la gráfica de barras -->
> 📷 _[Insertar captura del Paso 3]_

### 7.1 Resumen de Costos

En la parte superior verás 3 tarjetas:

| Tarjeta | Descripción |
|---|---|
| **Total Mensual** | Suma de todos los servicios por mes (USD) |
| **Total Anual** | Total mensual × 12 |
| **Servicios Cotizados** | Número de servicios con precio asignado |

### 7.2 Distribución por Categoría

Gráfica de barras horizontales que muestra cuánto representa cada categoría del total mensual.

<!-- IMAGEN: Gráfica de barras por categoría -->
> 📷 _[Insertar captura de la gráfica de categorías]_

### 7.3 Tabla de Costos Editable

Puedes ajustar los precios directamente en la tabla:
- Haz clic en el campo de precio de cualquier servicio y escribe el valor correcto
- El total se recalcula automáticamente

**Agregar un servicio con costo:**
1. Completa los campos: Servicio, Especificación, Categoría y USD/mes
2. Haz clic en **+ Agregar**

**Eliminar un servicio:** Haz clic en ✕ en la fila correspondiente.

### 7.4 Descargar CSV

Haz clic en **⬇ Descargar CSV** para exportar la tabla de costos en formato `.csv` con el total mensual y anual al final.

> ⚠️ Los costos son estimaciones. Pueden variar según uso real, reservas y Savings Plans. Para una estimación más precisa usa [calculator.aws](https://calculator.aws).

### 7.5 Avanzar al Paso 4

Haz clic en **Siguiente: Generar Propuesta →**.

---

## 8. Paso 4 — Generar Propuesta

El paso final genera el documento Word con la propuesta de arquitectura completa.

<!-- IMAGEN: Pantalla del Paso 4 con el panel de "listo para generar" -->
> 📷 _[Insertar captura del Paso 4 antes de generar]_

### 8.1 Generar el Documento

Haz clic en **Generar Propuesta Word**.

El sistema iniciará el proceso de generación, que tarda aproximadamente **2–5 minutos**. Verás una barra de progreso con el paso actual:

<!-- IMAGEN: Panel de progreso con la barra y el paso actual -->
> 📷 _[Insertar captura del panel de progreso]_

El proceso tiene 6 pasos internos:
1. Lectura de la ficha técnica
2. Consulta de precios AWS
3. Generación de introducción y requerimientos
4. Generación de arquitectura y premisas
5. Generación de propuesta económica
6. Ensamblado del documento Word

### 8.2 Descargar la Propuesta

Cuando el proceso termina, aparece el panel de resultado con los botones de descarga:

<!-- IMAGEN: Panel de resultado con los botones de descarga -->
> 📷 _[Insertar captura del panel de resultado]_

| Botón | Archivo | Descripción |
|---|---|---|
| **Descargar Word (.docx)** | `propuesta_[ID].docx` | Propuesta completa con plantilla corporativa |
| **Descargar Costos (.csv)** | `costos_[ID]_[fecha].csv` | Tabla de costos exportada |

### 8.3 Contenido del Documento Word

El documento generado contiene 8 secciones:

| # | Sección |
|---|---|
| 1 | Introducción |
| 2 | Requerimiento Técnico |
| 3 | Premisas y Restricciones |
| 4 | Arquitectura de Infraestructura AWS |
| 5 | Fuera de Alcance |
| 6 | Consideraciones Generales |
| 7 | Propuesta Económica AWS |
| 8 | Consideraciones Comerciales |

### 8.4 Si la Generación Falla

Si el sistema muestra un error, verifica que:
- La iniciativa tenga al menos un documento subido
- El Quick Discovery haya sido validado previamente
- El estado de la iniciativa sea `DISCOVERY_OK` o superior

Haz clic en **← Ir a Validación** para revisar el estado de los documentos.

---

## 9. Estados de una Iniciativa

Cada iniciativa pasa por los siguientes estados a lo largo del flujo:

```
INGESTA → VALIDANDO → DISCOVERY_OK → EXTRAYENDO_SERVICIOS → EXTRAIDO → GENERANDO_PROPUESTA → GENERADO
                ↓                                                                ↓
           INCOMPLETO                                                     ERROR_PROPUESTA
```

| Estado | Color | Significado |
|---|---|---|
| `INGESTA` | 🔵 Azul | Iniciativa creada, documentos subidos |
| `VALIDANDO` | 🟠 Naranja | La IA está analizando los documentos |
| `INCOMPLETO` | 🟡 Amarillo | El documento no alcanzó el puntaje mínimo |
| `DISCOVERY_OK` | 🟢 Verde | Validación aprobada, listo para extraer servicios |
| `EXTRAYENDO_SERVICIOS` | 🟠 Naranja | La IA está identificando los servicios AWS |
| `EXTRAIDO` | 🟢 Verde | Servicios identificados correctamente |
| `GENERANDO_PROPUESTA` | 🟠 Naranja | La IA está generando el documento Word |
| `GENERADO` | 🟢 Verde oscuro | Propuesta lista para descargar |
| `ERROR_PROPUESTA` | 🔴 Rojo | Error durante la generación — se puede reintentar |

---

## 10. Preguntas Frecuentes

**¿Qué pasa si subo el archivo equivocado?**
Puedes agregar nuevos archivos desde el Paso 1 usando las zonas de carga inline. Los archivos anteriores permanecen en el sistema.

**¿Puedo editar la ficha técnica antes de generar la propuesta?**
Sí. El sistema permite editar manualmente la ficha técnica desde el detalle de la iniciativa antes de lanzar la generación.

**¿Cuánto tiempo tarda el proceso completo?**
- Validación de Discovery: 30–90 segundos
- Validación N2: 20–60 segundos
- Generación de propuesta: 2–5 minutos

**¿Puedo regenerar la propuesta si no me gustó el resultado?**
Sí. Regresa al Paso 4 y vuelve a hacer clic en **Generar Propuesta Word**. Se generará una nueva versión.

**¿Los costos son exactos?**
Son estimaciones basadas en precios de lista de AWS Pricing API en `us-east-1`. No incluyen descuentos por volumen, Reserved Instances ni Savings Plans. Para una cotización formal usa [calculator.aws](https://calculator.aws).

**¿Qué hago si el estado se queda en `VALIDANDO` por más de 5 minutos?**
Recarga la página. Si el estado no cambia, contacta al administrador del sistema.

**¿Puedo agregar servicios que la IA no detectó?**
Sí. En el Paso 2 puedes agregar servicios manualmente con su categoría y prioridad.

**¿El documento Word usa la plantilla corporativa de Coppel?**
Sí. El documento generado sigue el formato estándar del Área de Arquitectura Cloud con los colores y estructura corporativa.

---

*Área de Arquitectura Cloud — Coppel · 2025*
*Para soporte técnico contacta al equipo de Arquitectura Cloud*
