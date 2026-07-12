-- Tabla de partidos (referencia para FOREIGN KEY)
CREATE TABLE IF NOT EXISTS partidos (
    codpar INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL
);

-- Tabla principal de resultados
CREATE TABLE IF NOT EXISTS resultados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    municipio TEXT NOT NULL,
    puesto TEXT NOT NULL,
    corporacion TEXT NOT NULL CHECK(corporacion IN ('CA','SE')),
    codpar INTEGER NOT NULL,
    candidato TEXT,
    votos INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (codpar) REFERENCES partidos(codpar),
    UNIQUE(municipio, puesto, corporacion, codpar, candidato)
);

-- Tabla de trazabilidad de cargas (ETL)
CREATE TABLE IF NOT EXISTS carga_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    municipio TEXT NOT NULL,
    filas_insertadas INTEGER NOT NULL DEFAULT 0,
    filas_omitidas INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Índices con justificación (bonus +2 pts)
CREATE INDEX IF NOT EXISTS idx_resultados_municipio ON resultados(municipio);
-- Justificación: acelera GROUP BY municipio, usado en casi todas las queries del Reto 3

CREATE INDEX IF NOT EXISTS idx_resultados_codpar ON resultados(codpar);
-- Justificación: acelera JOIN con partidos y filtros por partido (ej. arrastre Alianza Verde)

CREATE INDEX IF NOT EXISTS idx_resultados_puesto ON resultados(puesto);
-- Justificación: acelera GROUP BY puesto, usado en dominancia extrema y arrastre por mesa