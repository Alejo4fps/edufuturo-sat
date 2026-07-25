"""Esquema, conexión e inicialización reproducible de SQLite."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from src.config import DB_PATH
from src.seed_data import generar_dataset_inicial


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS estudiantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombres TEXT NOT NULL,
    apellido_paterno TEXT NOT NULL,
    apellido_materno TEXT NOT NULL,
    email TEXT,
    telefono TEXT,
    carrera TEXT NOT NULL,
    ciclo INTEGER NOT NULL CHECK (ciclo BETWEEN 1 AND 12),
    tipo_dato TEXT NOT NULL CHECK (tipo_dato IN ('CONOCIDO', 'DESCONOCIDO')),
    abandono_observado INTEGER CHECK (abandono_observado IN (0, 1) OR abandono_observado IS NULL),
    fecha_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS gestion_academica (
    estudiante_id INTEGER PRIMARY KEY,
    asistencia_pct REAL NOT NULL CHECK (asistencia_pct BETWEEN 0 AND 100),
    promedio_notas REAL CHECK (promedio_notas BETWEEN 0 AND 20 OR promedio_notas IS NULL),
    cursos_desaprobados INTEGER NOT NULL CHECK (cursos_desaprobados BETWEEN 0 AND 20),
    dias_sin_ingreso INTEGER NOT NULL CHECK (dias_sin_ingreso BETWEEN 0 AND 365),
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cobranzas (
    estudiante_id INTEGER PRIMARY KEY,
    meses_adeudados INTEGER NOT NULL CHECK (meses_adeudados BETWEEN 0 AND 24),
    deuda_total REAL NOT NULL DEFAULT 0 CHECK (deuda_total >= 0),
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS antecedentes (
    estudiante_id INTEGER PRIMARY KEY,
    historico_abandono INTEGER NOT NULL DEFAULT 0 CHECK (historico_abandono IN (0, 1)),
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evaluaciones_lote (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_ejecucion TEXT NOT NULL UNIQUE,
    version_modelo TEXT NOT NULL,
    tipo_dato TEXT NOT NULL CHECK (tipo_dato IN ('CONOCIDO', 'DESCONOCIDO')),
    total_solicitados INTEGER NOT NULL CHECK (total_solicitados >= 0),
    procesados INTEGER NOT NULL DEFAULT 0 CHECK (procesados >= 0),
    errores INTEGER NOT NULL DEFAULT 0 CHECK (errores >= 0),
    confianza_promedio REAL CHECK (
        confianza_promedio BETWEEN 0 AND 1 OR confianza_promedio IS NULL
    ),
    estado TEXT NOT NULL DEFAULT 'EN_PROCESO'
        CHECK (estado IN ('EN_PROCESO', 'COMPLETADO', 'COMPLETADO_CON_ERRORES', 'ERROR')),
    fecha_inicio TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TEXT
);

CREATE TABLE IF NOT EXISTS predicciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id INTEGER NOT NULL,
    evaluacion_lote_id INTEGER,
    version_modelo TEXT NOT NULL,
    probabilidad_riesgo REAL NOT NULL CHECK (probabilidad_riesgo BETWEEN 0 AND 1),
    clase_predicha INTEGER NOT NULL CHECK (clase_predicha IN (0, 1)),
    nivel_riesgo TEXT NOT NULL CHECK (nivel_riesgo IN ('Bajo', 'Medio', 'Alto')),
    factores_json TEXT,
    fecha_prediccion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE,
    FOREIGN KEY (evaluacion_lote_id) REFERENCES evaluaciones_lote(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS intervenciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    detalle TEXT NOT NULL,
    compromisos TEXT,
    responsable TEXT NOT NULL,
    estado TEXT NOT NULL,
    fecha_intervencion TEXT NOT NULL,
    proximo_seguimiento TEXT,
    fecha_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ejecuciones_modelo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_modelo TEXT NOT NULL UNIQUE,
    algoritmo TEXT NOT NULL,
    registros_entrenamiento INTEGER NOT NULL,
    registros_prueba INTEGER NOT NULL,
    accuracy REAL NOT NULL,
    precision_score REAL NOT NULL,
    recall_score REAL NOT NULL,
    f1_score REAL NOT NULL,
    matriz_confusion_json TEXT NOT NULL,
    importancia_json TEXT NOT NULL,
    fecha_entrenamiento TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_estudiantes_tipo ON estudiantes(tipo_dato);
CREATE INDEX IF NOT EXISTS idx_predicciones_estudiante ON predicciones(estudiante_id, fecha_prediccion DESC);
CREATE INDEX IF NOT EXISTS idx_predicciones_nivel ON predicciones(nivel_riesgo);
CREATE INDEX IF NOT EXISTS idx_intervenciones_estudiante ON intervenciones(estudiante_id, fecha_intervencion DESC);
CREATE INDEX IF NOT EXISTS idx_evaluaciones_lote_fecha ON evaluaciones_lote(fecha_inicio DESC);
"""


@contextmanager
def conexion(db_path: Path | str = DB_PATH) -> Iterator[sqlite3.Connection]:
    ruta = Path(db_path)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ruta, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def crear_esquema(db_path: Path | str = DB_PATH) -> None:
    with conexion(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        # Compatibilidad con bases creadas por versiones anteriores del sistema.
        columnas_predicciones = {
            str(fila["name"]) for fila in conn.execute("PRAGMA table_info(predicciones)")
        }
        if "evaluacion_lote_id" not in columnas_predicciones:
            conn.execute(
                """
                ALTER TABLE predicciones
                ADD COLUMN evaluacion_lote_id INTEGER
                REFERENCES evaluaciones_lote(id) ON DELETE SET NULL
                """
            )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_predicciones_evaluacion_lote
            ON predicciones(evaluacion_lote_id)
            """
        )


def insertar_estudiante(conn: sqlite3.Connection, registro: dict) -> int:
    cursor = conn.execute(
        """
        INSERT INTO estudiantes (
            codigo, nombres, apellido_paterno, apellido_materno, email, telefono,
            carrera, ciclo, tipo_dato, abandono_observado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            registro["codigo"], registro["nombres"], registro["apellido_paterno"],
            registro["apellido_materno"], registro.get("email"), registro.get("telefono"),
            registro["carrera"], registro["ciclo"], registro["tipo_dato"],
            registro.get("abandono_observado"),
        ),
    )
    estudiante_id = int(cursor.lastrowid)
    conn.execute(
        """INSERT INTO gestion_academica
        (estudiante_id, asistencia_pct, promedio_notas, cursos_desaprobados, dias_sin_ingreso)
        VALUES (?, ?, ?, ?, ?)""",
        (
            estudiante_id, registro["asistencia_pct"], registro.get("promedio_notas"),
            registro["cursos_desaprobados"], registro["dias_sin_ingreso"],
        ),
    )
    conn.execute(
        "INSERT INTO cobranzas (estudiante_id, meses_adeudados, deuda_total) VALUES (?, ?, ?)",
        (estudiante_id, registro["meses_adeudados"], registro.get("deuda_total", 0)),
    )
    conn.execute(
        "INSERT INTO antecedentes (estudiante_id, historico_abandono) VALUES (?, ?)",
        (estudiante_id, registro["historico_abandono"]),
    )
    return estudiante_id


def poblar_dataset_inicial(
    db_path: Path | str = DB_PATH,
    cantidad_total: int = 420,
    proporcion_conocidos: float = 0.80,
) -> int:
    with conexion(db_path) as conn:
        existentes = conn.execute("SELECT COUNT(*) FROM estudiantes").fetchone()[0]
        if existentes:
            return int(existentes)
        for registro in generar_dataset_inicial(
            cantidad_total=cantidad_total,
            proporcion_conocidos=proporcion_conocidos,
        ):
            insertar_estudiante(conn, registro)
    return cantidad_total


def inicializar_base_datos(
    db_path: Path | str = DB_PATH,
    cantidad: int = 420,
    proporcion_conocidos: float = 0.80,
) -> int:
    crear_esquema(db_path)
    return poblar_dataset_inicial(db_path, cantidad, proporcion_conocidos)
