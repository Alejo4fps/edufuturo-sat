"""Fuerza un nuevo entrenamiento y actualiza las predicciones."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DB_PATH, MODEL_PATH
from src.database import inicializar_base_datos
from src.modeling import entrenar_modelo, sincronizar_predicciones


if __name__ == "__main__":
    inicializar_base_datos(DB_PATH)
    modelo = entrenar_modelo(DB_PATH, MODEL_PATH)
    generadas = sincronizar_predicciones(modelo, DB_PATH)
    metricas = modelo["metricas"]
    print(f"[OK] Versión: {modelo['version_modelo']}")
    print(f"[OK] Accuracy: {metricas['accuracy']:.3f}")
    print(f"[OK] Precision: {metricas['precision']:.3f}")
    print(f"[OK] Recall: {metricas['recall']:.3f}")
    print(f"[OK] F1: {metricas['f1']:.3f}")
    print(f"[OK] Predicciones sincronizadas: {generadas}")
