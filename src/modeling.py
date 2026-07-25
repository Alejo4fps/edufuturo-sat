"""Entrenamiento, evaluación, persistencia y predicción del modelo supervisado."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.config import DB_PATH, FEATURE_COLUMNS, FEATURE_LABELS, MODEL_NAME, MODEL_PATH
from src.repositories import (
    contar_casos_conocidos,
    crear_evaluacion_lote,
    finalizar_evaluacion_lote,
    guardar_ejecucion_modelo,
    guardar_prediccion,
    guardar_predicciones_lote,
    ids_sin_prediccion,
    obtener_dataset_entrenamiento,
    obtener_evaluacion_lote,
    obtener_estudiante,
    obtener_estudiantes,
)
from src.services import factores_y_recomendaciones, nivel_riesgo


def _version_modelo(dataset: pd.DataFrame) -> str:
    resumen = pd.util.hash_pandas_object(dataset.fillna(-999), index=True).values.tobytes()
    return "RF-" + hashlib.sha256(resumen).hexdigest()[:10].upper()


def entrenar_modelo(
    db_path: Path | str = DB_PATH,
    model_path: Path | str = MODEL_PATH,
    random_state: int = 42,
) -> dict[str, Any]:
    dataset = obtener_dataset_entrenamiento(db_path)
    if len(dataset) < 50:
        raise ValueError("Se necesitan al menos 50 casos conocidos para entrenar el modelo.")

    X = dataset[FEATURE_COLUMNS]
    y = dataset["abandono_observado"].astype(int)
    if y.nunique() < 2:
        raise ValueError("El dataset debe contener casos de abandono y de permanencia.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=random_state,
        stratify=y,
    )

    pipeline = Pipeline(
        steps=[
            ("imputador", SimpleImputer(strategy="median")),
            (
                "clasificador",
                RandomForestClassifier(
                    n_estimators=350,
                    max_depth=8,
                    min_samples_leaf=3,
                    class_weight="balanced",
                    random_state=random_state,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)
    predicciones = pipeline.predict(X_test)
    probabilidades_validacion = pipeline.predict_proba(X_test)[:, 1]

    version = _version_modelo(dataset)
    fecha = datetime.now().isoformat(timespec="seconds")
    importancias = pipeline.named_steps["clasificador"].feature_importances_
    importancia_variables = {
        FEATURE_LABELS[columna]: round(float(importancia), 6)
        for columna, importancia in zip(FEATURE_COLUMNS, importancias)
    }
    matriz = confusion_matrix(y_test, predicciones, labels=[0, 1]).astype(int).tolist()

    metricas = {
        "version_modelo": version,
        "algoritmo": MODEL_NAME,
        "registros_totales": int(len(dataset)),
        "registros_entrenamiento": int(len(X_train)),
        "registros_prueba": int(len(X_test)),
        "accuracy": float(accuracy_score(y_test, predicciones)),
        "precision": float(precision_score(y_test, predicciones, zero_division=0)),
        "recall": float(recall_score(y_test, predicciones, zero_division=0)),
        "f1": float(f1_score(y_test, predicciones, zero_division=0)),
        "matriz_confusion": matriz,
        "importancia_variables": importancia_variables,
        "fecha_entrenamiento": fecha,
        "casos_positivos": int(y.sum()),
        "casos_negativos": int((y == 0).sum()),
    }

    casos_validacion: list[dict[str, Any]] = []
    for indice, prediccion, probabilidad in zip(
        X_test.index,
        predicciones,
        probabilidades_validacion,
    ):
        fila = dataset.loc[indice]
        valor_real = int(y_test.loc[indice])
        valor_predicho = int(prediccion)
        casos_validacion.append(
            {
                "estudiante_id": int(fila["estudiante_id"]),
                "codigo": str(fila["codigo"]),
                "estudiante": str(fila["nombre_completo"]),
                "resultado_real": "Abandono" if valor_real else "Permanece",
                "resultado_predicho": "Abandono" if valor_predicho else "Permanece",
                "probabilidad_riesgo": float(probabilidad),
                "coincide": bool(valor_real == valor_predicho),
            }
        )

    bundle = {
        "pipeline": pipeline,
        "feature_columns": FEATURE_COLUMNS,
        "version_modelo": version,
        "training_rows": int(len(dataset)),
        "metricas": metricas,
        "casos_validacion": casos_validacion,
        "schema_version": 2,
    }
    ruta_modelo = Path(model_path)
    ruta_modelo.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, ruta_modelo)
    guardar_ejecucion_modelo(metricas, db_path)
    return bundle


def cargar_modelo(model_path: Path | str = MODEL_PATH) -> dict[str, Any]:
    ruta = Path(model_path)
    if not ruta.exists():
        raise FileNotFoundError("El modelo todavía no ha sido entrenado.")
    return joblib.load(ruta)


def asegurar_modelo(
    db_path: Path | str = DB_PATH, model_path: Path | str = MODEL_PATH
) -> dict[str, Any]:
    casos_conocidos = contar_casos_conocidos(db_path)
    try:
        bundle = cargar_modelo(model_path)
        if (
            int(bundle.get("training_rows", -1)) == casos_conocidos
            and int(bundle.get("schema_version", 0)) >= 2
            and bundle.get("casos_validacion")
        ):
            return bundle
    except Exception:
        # Un artefacto corrupto o serializado con otra versión de scikit-learn
        # no debe impedir el inicio: se reconstruye desde los casos conocidos.
        pass
    return entrenar_modelo(db_path, model_path)


def predecir_registro(registro: dict[str, Any], bundle: dict[str, Any]) -> dict[str, Any]:
    fila = pd.DataFrame([{columna: registro.get(columna) for columna in FEATURE_COLUMNS}])
    probabilidad = float(bundle["pipeline"].predict_proba(fila)[0, 1])
    clase = int(probabilidad >= 0.50)
    nivel = nivel_riesgo(probabilidad)
    factores, recomendaciones = factores_y_recomendaciones(registro)
    return {
        "probabilidad": probabilidad,
        "clase": clase,
        "nivel": nivel,
        "factores": factores,
        "recomendaciones": recomendaciones,
        "version_modelo": bundle["version_modelo"],
    }


def predecir_estudiante(
    estudiante_id: int,
    bundle: dict[str, Any],
    db_path: Path | str = DB_PATH,
    guardar: bool = True,
) -> dict[str, Any]:
    estudiante = obtener_estudiante(estudiante_id, db_path)
    if not estudiante:
        raise ValueError("No se encontró el estudiante solicitado.")
    resultado = predecir_registro(estudiante, bundle)
    if guardar:
        guardar_prediccion(
            estudiante_id,
            resultado["version_modelo"],
            resultado["probabilidad"],
            resultado["clase"],
            resultado["nivel"],
            resultado["factores"],
            db_path,
        )
    return resultado


def sincronizar_predicciones(
    bundle: dict[str, Any],
    db_path: Path | str = DB_PATH,
    tipo_dato: str | None = "CONOCIDO",
    solo_sin_historial: bool = False,
) -> int:
    pendientes = ids_sin_prediccion(
        bundle["version_modelo"],
        db_path,
        tipo_dato,
        solo_sin_historial=solo_sin_historial,
    )
    if not pendientes:
        return 0
    df = obtener_estudiantes(db_path)
    lote = df[df["estudiante_id"].isin(pendientes)].copy()
    probabilidades = bundle["pipeline"].predict_proba(lote[FEATURE_COLUMNS])[:, 1]
    predicciones: list[dict[str, Any]] = []
    for (_, fila), probabilidad in zip(lote.iterrows(), probabilidades):
        registro = fila.to_dict()
        factores, _ = factores_y_recomendaciones(registro)
        prob = float(probabilidad)
        predicciones.append(
            {
                "estudiante_id": int(registro["estudiante_id"]),
                "version_modelo": bundle["version_modelo"],
                "probabilidad": prob,
                "clase": int(prob >= 0.50),
                "nivel": nivel_riesgo(prob),
                "factores": factores,
            }
        )
    return guardar_predicciones_lote(predicciones, db_path)


def ejecutar_evaluacion_lote(
    bundle: dict[str, Any],
    db_path: Path | str = DB_PATH,
    tipo_dato: str = "DESCONOCIDO",
    solo_sin_historial: bool = True,
    progreso: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """Procesa un lote real y conserva un comprobante auditable en SQLite."""
    estudiantes = obtener_estudiantes(db_path, tipo=tipo_dato)
    if solo_sin_historial:
        estudiantes = estudiantes[estudiantes["probabilidad_riesgo"].isna()].copy()
    else:
        estudiantes = estudiantes.copy()

    total = int(len(estudiantes))
    if total == 0:
        raise ValueError("No hay estudiantes disponibles para esta evaluación.")

    ahora = datetime.now()
    codigo = f"EV-{ahora:%Y%m%d-%H%M%S}-{uuid4().hex[:6].upper()}"
    evaluacion_lote_id = crear_evaluacion_lote(
        codigo,
        str(bundle["version_modelo"]),
        tipo_dato,
        total,
        ahora.isoformat(timespec="seconds"),
        db_path,
    )

    predicciones: list[dict[str, Any]] = []
    errores = 0
    try:
        for _, fila in estudiantes.iterrows():
            registro = fila.to_dict()
            try:
                resultado = predecir_registro(registro, bundle)
                predicciones.append(
                    {
                        "estudiante_id": int(registro["estudiante_id"]),
                        "version_modelo": str(resultado["version_modelo"]),
                        "probabilidad": float(resultado["probabilidad"]),
                        "clase": int(resultado["clase"]),
                        "nivel": str(resultado["nivel"]),
                        "factores": resultado["factores"],
                    }
                )
            except Exception:
                errores += 1
            if progreso:
                progreso(len(predicciones) + errores, total)

        procesados = guardar_predicciones_lote(
            predicciones,
            db_path,
            evaluacion_lote_id=evaluacion_lote_id,
        )
        confianza_promedio = (
            float(
                np.mean(
                    [
                        max(item["probabilidad"], 1 - item["probabilidad"])
                        for item in predicciones
                    ]
                )
            )
            if predicciones
            else None
        )
        estado = "COMPLETADO" if errores == 0 else "COMPLETADO_CON_ERRORES"
        finalizar_evaluacion_lote(
            evaluacion_lote_id,
            procesados,
            errores,
            confianza_promedio,
            estado,
            datetime.now().isoformat(timespec="seconds"),
            db_path,
        )
    except Exception:
        finalizar_evaluacion_lote(
            evaluacion_lote_id,
            0,
            total,
            None,
            "ERROR",
            datetime.now().isoformat(timespec="seconds"),
            db_path,
        )
        raise

    ejecucion = obtener_evaluacion_lote(evaluacion_lote_id, db_path)
    if not ejecucion:
        raise RuntimeError("La evaluación terminó, pero no se pudo recuperar su comprobante.")
    return ejecucion


def exportar_resumen_modelo(bundle: dict[str, Any]) -> str:
    resumen = {k: v for k, v in bundle["metricas"].items() if k != "pipeline"}
    return json.dumps(resumen, ensure_ascii=False, indent=2)
