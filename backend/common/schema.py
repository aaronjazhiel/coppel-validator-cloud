"""Ficha Técnica — modelo canónico Pydantic v2.

Define la estructura completa de una Ficha Técnica de arquitectura cloud.
Se usa tanto para validar la salida de Claude como para serializar/deserializar
el JSON almacenado en S3. Cada modelo representa una sección de la ficha.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ── Tags de negocio para clasificación y costeo ───────────────────────
class BusinessTags(BaseModel):
    project: str = ""
    owner: str = ""
    cost_center: str = ""
    business_unit: str = ""
    nombre_proyecto: str = ""
    lider_proyecto: str = ""
    objetivo_proyecto: str = ""
    arquitecto: str = ""
    unidad_negocio: str = ""
    area_negocio: str = ""
    macro_servicio: str = ""
    servicio: str = ""
    sistema_aplicacion: str = ""
    responsable_negocio: str = ""
    responsable_ti: str = ""
    solicitante: str = ""
    id_presupuesto: str = ""
    numero_centro_gasto: str = ""
    nombre_centro_gasto: str = ""
    iniciativa_pertenece: str = ""
    tiempo_uso: str = ""
    resumen_servicio: str = ""
    division: str = ""
    ambiente: str = ""
    proyecto_nuevo: str = ""


# ── Identificación del proyecto ───────────────────────────────
class Proyecto(BaseModel):
    id_iniciativa: str
    nombre: str = ""
    descripcion: str = ""
    nube: str = "AWS"  # AWS | GCP | Multi
    ambiente: str = "Prod"
    business_tags: BusinessTags = Field(default_factory=BusinessTags)


# ── Requisitos no funcionales ──────────────────────────────
class Requisitos(BaseModel):
    sla: Optional[str] = None
    latencia_ms: Optional[int] = None
    disponibilidad: Optional[str] = None
    seguridad: Optional[str] = None
    escalabilidad: Optional[str] = None


# ── Clasificación de datos ──────────────────────────────────
class Datos(BaseModel):
    tipo: Optional[str] = None
    volumen: Optional[str] = None
    clasificacion: Optional[str] = None
    cifrado: Optional[str] = None


# ── Dependencias del sistema (on-prem, cloud, otros) ────────
class Dependencia(BaseModel):
    nombre: str
    tipo: str = ""  # onprem | aws | gcp | otros
    descripcion: str = ""


class Dependencias(BaseModel):
    onprem: list[Dependencia] = Field(default_factory=list)
    aws: list[Dependencia] = Field(default_factory=list)
    gcp: list[Dependencia] = Field(default_factory=list)
    otros: list[Dependencia] = Field(default_factory=list)


# ── Configuración de red y conectividad ─────────────────────
class Red(BaseModel):
    vpc: Optional[str] = None
    subnets: Optional[str] = None
    seguridad_red: Optional[str] = None
    conectividad: Optional[str] = None


# ── Componentes de infraestructura ──────────────────────────
class Nodo(BaseModel):
    nombre: str
    tipo_instancia: Optional[str] = None
    vcpu: Optional[int] = None
    ram_gb: Optional[float] = None
    almacenamiento_gb: Optional[float] = None
    so: Optional[str] = None
    cantidad: Optional[int] = None


class BaseDatos(BaseModel):
    nombre: str
    motor: Optional[str] = None
    version: Optional[str] = None
    tipo_instancia: Optional[str] = None
    almacenamiento_gb: Optional[float] = None
    multi_az: bool = False
    replicas: int = 0


class LambdaSpec(BaseModel):
    nombre: str
    runtime: Optional[str] = None
    memoria_mb: Optional[int] = None
    timeout_s: Optional[int] = None
    invocaciones_dia: Optional[int] = None


class KubernetesSpec(BaseModel):
    cluster: Optional[str] = None
    nodos_min: Optional[int] = None
    nodos_max: Optional[int] = None
    tipo_instancia: Optional[str] = None


class ServicioAdicional(BaseModel):
    nombre: str
    categoria: str = ""
    specs: Optional[str] = None


class Componentes(BaseModel):
    nodos: list[Nodo] = Field(default_factory=list)
    bases_datos: list[BaseDatos] = Field(default_factory=list)
    lambdas: list[LambdaSpec] = Field(default_factory=list)
    kubernetes: list[KubernetesSpec] = Field(default_factory=list)
    servicios_adicionales: list[ServicioAdicional] = Field(default_factory=list)


class ClasificacionServicios(BaseModel):
    nuevo: list[str] = Field(default_factory=list)
    transversal: list[str] = Field(default_factory=list)


# ── Topología (nodos y aristas para representar el diagrama) ──
class NodoTopologia(BaseModel):
    id: str
    label: str
    tipo: str = ""


class AristaTopologia(BaseModel):
    origen: str
    destino: str
    label: str = ""


class Topologia(BaseModel):
    nodos: list[NodoTopologia] = Field(default_factory=list)
    aristas: list[AristaTopologia] = Field(default_factory=list)


# ── Estrategia de migración ───────────────────────────────
class Migracion(BaseModel):
    estrategia: Optional[str] = None
    fases: list[str] = Field(default_factory=list)
    contingencia: Optional[str] = None


# ── Disaster Recovery ─────────────────────────────────────
class DR(BaseModel):
    rpo: Optional[str] = None
    rto: Optional[str] = None
    estrategia: Optional[str] = None
    sitio_dr: Optional[str] = None


# ── Restricciones del proyecto ──────────────────────────────
class Restricciones(BaseModel):
    presupuesto: Optional[str] = None
    compliance: list[str] = Field(default_factory=list)
    exclusiones: list[str] = Field(default_factory=list)


# ── Validación y estado de completitud ───────────────────────
class Conflicto(BaseModel):
    campo: str
    fuente_a: str
    valor_a: str
    fuente_b: str
    valor_b: str


class Validacion(BaseModel):
    completitud: int = 0  # 0-100
    estado: str = "INGESTA"
    huecos: list[str] = Field(default_factory=list)
    conflictos: list[Conflicto] = Field(default_factory=list)


# ── Modelo raíz que agrupa todas las secciones ────────────────
class FichaTecnica(BaseModel):
    proyecto: Proyecto
    requisitos: Requisitos = Field(default_factory=Requisitos)
    datos: Datos = Field(default_factory=Datos)
    dependencias: Dependencias = Field(default_factory=Dependencias)
    red: Red = Field(default_factory=Red)
    componentes: Componentes = Field(default_factory=Componentes)
    clasificacion_servicios: ClasificacionServicios = Field(default_factory=ClasificacionServicios)
    topologia: Topologia = Field(default_factory=Topologia)
    migracion: Migracion = Field(default_factory=Migracion)
    dr: DR = Field(default_factory=DR)
    restricciones: Restricciones = Field(default_factory=Restricciones)
    validacion: Validacion = Field(default_factory=Validacion)
