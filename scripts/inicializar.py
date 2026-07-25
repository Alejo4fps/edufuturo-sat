"""Crea o completa la base de datos y entrena el modelo inicial."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DB_PATH, MODEL_PATH
from src.database import inicializar_base_datos
from src.modeling import asegurar_modelo, sincronizar_predicciones
from src.repositories import obtener_estudiantes


if __name__ == "__main__":
    inicializar_base_datos(DB_PATH)
    modelo = asegurar_modelo(DB_PATH, MODEL_PATH)
    generadas = sincronizar_predicciones(modelo, DB_PATH)
    estudiantes = obtener_estudiantes(DB_PATH)
    conocidos = int((estudiantes["tipo_dato"] == "CONOCIDO").sum())
    pendientes = int(estudiantes["probabilidad_riesgo"].isna().sum())
    print(f"[OK] Base SQLite: {DB_PATH}")
    print(f"[OK] Registros históricos conocidos: {conocidos}")
    print(f"[OK] Estudiantes pendientes de evaluación: {pendientes}")
    print(f"[OK] Modelo: {modelo['version_modelo']}")
    print(f"[OK] Evaluaciones históricas generadas: {generadas}")
