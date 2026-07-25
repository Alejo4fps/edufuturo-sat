"""Consultas y operaciones de persistencia de la aplicación."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import DB_PATH
from src.database import conexion, insertar_estudiante


STUDENT_SELECT = """
SELECT
    e.id AS estudiante_id,
    e.codigo,
    e.nombres,
    e.apellido_paterno,
    e.apellido_materno,
    TRIM(e.nombres || ' ' || e.apellido_paterno || ' ' || e.apellido_materno) AS nombre_completo,
    e.email,
    e.telefono,
    e.carrera,
    e.ciclo,
    e.tipo_dato,
    e.abandono_observado,
    e.fecha_registro,
    ga.asistencia_pct,
    ga.promedio_notas,
    ga.cursos_desaprobados,
    ga.dias_sin_ingreso,
    c.meses_adeudados,
    c.deuda_total,
    a.historico_abandono,
    p.probabilidad_riesgo,
    p.clase_predicha,
    p.nivel_riesgo,
    p.version_modelo,
    p.fecha_prediccion,
    p.factores_json,
    p.evaluacion_lote_id,
    (SELECT COUNT(*) FROM intervenciones i WHERE i.estudiante_id = e.id) AS total_intervenciones
FROM estudiantes e
JOIN gestion_academica ga ON ga.estudiante_id = e.id
JOIN cobranzas c ON c.estudiante_id = e.id
JOIN antecedentes a ON a.estudiante_id = e.id
LEFT JOIN predicciones p ON p.id = (
    SELECT p2.id FROM predicciones p2
    WHERE p2.estudiante_id = e.id
    ORDER BY p2.fecha_prediccion DESC, p2.id DESC LIMIT 1
)
WHERE e.activo = 1
"""


def obtener_estudiantes(db_path: Path | str = DB_PATH, tipo: str | None = None) -> pd.DataFrame:
    query = STUDENT_SELECT
    params: tuple[Any, ...] = ()
    if tipo:
        query += " AND e.tipo_dato = ?"
        params = (tipo,)
    query += " ORDER BY e.apellido_paterno, e.apellido_materno, e.nombres"
    with conexion(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def obtener_estudiante(estudiante_id: int, db_path: Path | str = DB_PATH) -> dict[str, Any] | None:
    with conexion(db_path) as conn:
        fila = conn.execute(STUDENT_SELECT + " AND e.id = ?", (estudiante_id,)).fetchone()
        return dict(fila) if fila else None


def obtener_dataset_entrenamiento(db_path: Path | str = DB_PATH) -> pd.DataFrame:
    with conexion(db_path) as conn:
        return pd.read_sql_query(
            """
            SELECT
                e.id AS estudiante_id,
                e.codigo,
                TRIM(e.nombres || ' ' || e.apellido_paterno || ' ' || e.apellido_materno)
                    AS nombre_completo,
                ga.asistencia_pct,
                ga.promedio_notas,
                ga.cursos_desaprobados,
                ga.dias_sin_ingreso,
                c.meses_adeudados,
                a.historico_abandono,
                e.abandono_observado
            FROM estudiantes e
            JOIN gestion_academica ga ON ga.estudiante_id = e.id
            JOIN cobranzas c ON c.estudiante_id = e.id
            JOIN antecedentes a ON a.estudiante_id = e.id
            WHERE e.tipo_dato = 'CONOCIDO'
              AND e.abandono_observado IS NOT NULL
              AND e.activo = 1
            """,
            conn,
        )


def contar_casos_conocidos(db_path: Path | str = DB_PATH) -> int:
    with conexion(db_path) as conn:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM estudiantes WHERE tipo_dato = 'CONOCIDO' AND abandono_observado IS NOT NULL"
            ).fetchone()[0]
        )


def codigo_disponible(codigo: str, db_path: Path | str = DB_PATH) -> bool:
    with conexion(db_path) as conn:
        return conn.execute("SELECT 1 FROM estudiantes WHERE codigo = ?", (codigo,)).fetchone() is None


def agregar_estudiante_desconocido(registro: dict, db_path: Path | str = DB_PATH) -> int:
    datos = dict(registro)
    datos["tipo_dato"] = "DESCONOCIDO"
    datos["abandono_observado"] = None
    try:
        with conexion(db_path) as conn:
            return insertar_estudiante(conn, datos)
    except sqlite3.IntegrityError as exc:
        if "UNIQUE" in str(exc).upper():
            raise ValueError("El código del estudiante ya existe.") from exc
        raise ValueError("Los datos no cumplen las reglas de integridad de la base.") from exc


def guardar_prediccion(
    estudiante_id: int,
    version_modelo: str,
    probabilidad: float,
    clase: int,
    nivel: str,
    factores: dict[str, Any],
    db_path: Path | str = DB_PATH,
) -> int:
    with conexion(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO predicciones
            (estudiante_id, version_modelo, probabilidad_riesgo, clase_predicha, nivel_riesgo, factores_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (estudiante_id, version_modelo, probabilidad, clase, nivel, json.dumps(factores, ensure_ascii=False)),
        )
        return int(cursor.lastrowid)


def guardar_predicciones_lote(
    predicciones: list[dict[str, Any]],
    db_path: Path | str = DB_PATH,
    evaluacion_lote_id: int | None = None,
) -> int:
    if not predicciones:
        return 0
    with conexion(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO predicciones
            (
                estudiante_id, evaluacion_lote_id, version_modelo,
                probabilidad_riesgo, clase_predicha, nivel_riesgo, factores_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item["estudiante_id"], evaluacion_lote_id,
                    item["version_modelo"], item["probabilidad"], item["clase"], item["nivel"],
                    json.dumps(item["factores"], ensure_ascii=False),
                )
                for item in predicciones
            ],
        )
    return len(predicciones)


def crear_evaluacion_lote(
    codigo_ejecucion: str,
    version_modelo: str,
    tipo_dato: str,
    total_solicitados: int,
    fecha_inicio: str,
    db_path: Path | str = DB_PATH,
) -> int:
    with conexion(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO evaluaciones_lote (
                codigo_ejecucion, version_modelo, tipo_dato,
                total_solicitados, fecha_inicio
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                codigo_ejecucion,
                version_modelo,
                tipo_dato,
                total_solicitados,
                fecha_inicio,
            ),
        )
        return int(cursor.lastrowid)


def finalizar_evaluacion_lote(
    evaluacion_lote_id: int,
    procesados: int,
    errores: int,
    confianza_promedio: float | None,
    estado: str,
    fecha_fin: str,
    db_path: Path | str = DB_PATH,
) -> None:
    with conexion(db_path) as conn:
        conn.execute(
            """
            UPDATE evaluaciones_lote
            SET procesados = ?,
                errores = ?,
                confianza_promedio = ?,
                estado = ?,
                fecha_fin = ?
            WHERE id = ?
            """,
            (
                procesados,
                errores,
                confianza_promedio,
                estado,
                fecha_fin,
                evaluacion_lote_id,
            ),
        )


def obtener_evaluacion_lote(
    evaluacion_lote_id: int, db_path: Path | str = DB_PATH
) -> dict[str, Any] | None:
    with conexion(db_path) as conn:
        fila = conn.execute(
            "SELECT * FROM evaluaciones_lote WHERE id = ?",
            (evaluacion_lote_id,),
        ).fetchone()
        return dict(fila) if fila else None


def obtener_ultima_evaluacion_lote(
    db_path: Path | str = DB_PATH,
) -> dict[str, Any] | None:
    with conexion(db_path) as conn:
        fila = conn.execute(
            """
            SELECT * FROM evaluaciones_lote
            ORDER BY fecha_inicio DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        return dict(fila) if fila else None


def obtener_historial_evaluaciones(
    db_path: Path | str = DB_PATH,
) -> pd.DataFrame:
    with conexion(db_path) as conn:
        return pd.read_sql_query(
            """
            SELECT
                id,
                codigo_ejecucion,
                version_modelo,
                total_solicitados,
                procesados,
                errores,
                confianza_promedio,
                estado,
                fecha_inicio,
                fecha_fin
            FROM evaluaciones_lote
            ORDER BY fecha_inicio DESC, id DESC
            """,
            conn,
        )


def obtener_resultados_evaluacion(
    evaluacion_lote_id: int, db_path: Path | str = DB_PATH
) -> pd.DataFrame:
    with conexion(db_path) as conn:
        return pd.read_sql_query(
            """
            SELECT
                p.id AS prediccion_id,
                p.evaluacion_lote_id,
                e.id AS estudiante_id,
                e.codigo,
                TRIM(e.nombres || ' ' || e.apellido_paterno || ' ' || e.apellido_materno)
                    AS nombre_completo,
                e.carrera,
                e.ciclo,
                ga.asistencia_pct,
                ga.promedio_notas,
                ga.cursos_desaprobados,
                ga.dias_sin_ingreso,
                c.meses_adeudados,
                c.deuda_total,
                a.historico_abandono,
                p.version_modelo,
                p.probabilidad_riesgo,
                p.clase_predicha,
                p.nivel_riesgo,
                p.factores_json,
                p.fecha_prediccion
            FROM predicciones p
            JOIN estudiantes e ON e.id = p.estudiante_id
            JOIN gestion_academica ga ON ga.estudiante_id = e.id
            JOIN cobranzas c ON c.estudiante_id = e.id
            JOIN antecedentes a ON a.estudiante_id = e.id
            WHERE p.evaluacion_lote_id = ?
            ORDER BY p.probabilidad_riesgo DESC, e.apellido_paterno, e.nombres
            """,
            conn,
            params=(evaluacion_lote_id,),
        )


def ids_sin_prediccion(
    version_modelo: str,
    db_path: Path | str = DB_PATH,
    tipo_dato: str | None = None,
    solo_sin_historial: bool = False,
) -> list[int]:
    with conexion(db_path) as conn:
        filtro_prediccion = "p.estudiante_id = e.id"
        params: list[Any] = []
        if not solo_sin_historial:
            filtro_prediccion += " AND p.version_modelo = ?"
            params.append(version_modelo)
        query = f"""
            SELECT e.id FROM estudiantes e
            WHERE e.activo = 1 AND NOT EXISTS (
                SELECT 1 FROM predicciones p
                WHERE {filtro_prediccion}
            )
        """
        if tipo_dato:
            query += " AND e.tipo_dato = ?"
            params.append(tipo_dato)
        query += " ORDER BY e.id"
        filas = conn.execute(query, tuple(params)).fetchall()
        return [int(f[0]) for f in filas]


def contar_no_evaluados(db_path: Path | str = DB_PATH) -> int:
    with conexion(db_path) as conn:
        return int(
            conn.execute(
                """
                SELECT COUNT(*) FROM estudiantes e
                WHERE e.activo = 1 AND NOT EXISTS (
                    SELECT 1 FROM predicciones p WHERE p.estudiante_id = e.id
                )
                """
            ).fetchone()[0]
        )


def guardar_ejecucion_modelo(metricas: dict[str, Any], db_path: Path | str = DB_PATH) -> None:
    with conexion(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO ejecuciones_modelo (
                version_modelo, algoritmo, registros_entrenamiento, registros_prueba,
                accuracy, precision_score, recall_score, f1_score,
                matriz_confusion_json, importancia_json, fecha_entrenamiento
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metricas["version_modelo"], metricas["algoritmo"],
                metricas["registros_entrenamiento"], metricas["registros_prueba"],
                metricas["accuracy"], metricas["precision"], metricas["recall"], metricas["f1"],
                json.dumps(metricas["matriz_confusion"]),
                json.dumps(metricas["importancia_variables"], ensure_ascii=False),
                metricas["fecha_entrenamiento"],
            ),
        )


def obtener_ultima_ejecucion(db_path: Path | str = DB_PATH) -> dict[str, Any] | None:
    with conexion(db_path) as conn:
        fila = conn.execute(
            "SELECT * FROM ejecuciones_modelo ORDER BY fecha_entrenamiento DESC, id DESC LIMIT 1"
        ).fetchone()
        if not fila:
            return None
        resultado = dict(fila)
        resultado["matriz_confusion"] = json.loads(resultado.pop("matriz_confusion_json"))
        resultado["importancia_variables"] = json.loads(resultado.pop("importancia_json"))
        return resultado


def registrar_intervencion(datos: dict[str, Any], db_path: Path | str = DB_PATH) -> int:
    with conexion(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO intervenciones (
                estudiante_id, tipo, detalle, compromisos, responsable, estado,
                fecha_intervencion, proximo_seguimiento
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datos["estudiante_id"], datos["tipo"], datos["detalle"],
                datos.get("compromisos"), datos["responsable"], datos["estado"],
                str(datos.get("fecha_intervencion", date.today())),
                str(datos["proximo_seguimiento"]) if datos.get("proximo_seguimiento") else None,
            ),
        )
        return int(cursor.lastrowid)


def obtener_intervenciones(estudiante_id: int | None = None, db_path: Path | str = DB_PATH) -> pd.DataFrame:
    query = """
        SELECT i.*, e.codigo,
               TRIM(e.nombres || ' ' || e.apellido_paterno || ' ' || e.apellido_materno) AS estudiante
        FROM intervenciones i
        JOIN estudiantes e ON e.id = i.estudiante_id
    """
    params: tuple[Any, ...] = ()
    if estudiante_id is not None:
        query += " WHERE i.estudiante_id = ?"
        params = (estudiante_id,)
    query += " ORDER BY i.fecha_intervencion DESC, i.id DESC"
    with conexion(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def actualizar_resultado_observado(
    estudiante_id: int, abandono_observado: int, db_path: Path | str = DB_PATH
) -> None:
    with conexion(db_path) as conn:
        conn.execute(
            """UPDATE estudiantes
               SET abandono_observado = ?, tipo_dato = 'CONOCIDO'
               WHERE id = ?""",
            (abandono_observado, estudiante_id),
        )
