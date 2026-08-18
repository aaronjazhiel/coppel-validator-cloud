-- ── Schema: coppel_cloud ─────────────────────────────────────

-- ── Tabla principal de iniciativas ───────────────────────────
CREATE TABLE IF NOT EXISTS iniciativas (
    id_iniciativa       VARCHAR(100)    NOT NULL PRIMARY KEY,
    nombre              VARCHAR(255)    NOT NULL,
    descripcion         TEXT,
    ambiente            VARCHAR(50)     DEFAULT 'Prod',
    solicitante         VARCHAR(255)    NOT NULL,
    nube                VARCHAR(50)     DEFAULT 'AWS',
    business_tags       JSONB,
    estado              VARCHAR(50)     DEFAULT 'INGESTA',
    completitud         INT             DEFAULT 0,
    huecos              JSONB,
    s3_prefix           VARCHAR(500),
    insumos             JSONB,
    salidas             JSONB,
    fecha_creacion      TIMESTAMPTZ     DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_estado       ON iniciativas (estado);
CREATE INDEX IF NOT EXISTS idx_solicitante  ON iniciativas (solicitante);
CREATE INDEX IF NOT EXISTS idx_fecha        ON iniciativas (fecha_creacion);

-- ── Tabla de eventos / auditoría ─────────────────────────────
CREATE TABLE IF NOT EXISTS eventos (
    id              BIGSERIAL       PRIMARY KEY,
    id_iniciativa   VARCHAR(100)    NOT NULL REFERENCES iniciativas(id_iniciativa) ON DELETE CASCADE,
    accion          VARCHAR(100)    NOT NULL,
    detalle         JSONB,
    timestamp       TIMESTAMPTZ     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ev_iniciativa ON eventos (id_iniciativa);
CREATE INDEX IF NOT EXISTS idx_ev_accion     ON eventos (accion);
