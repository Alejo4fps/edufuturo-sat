import tempfile
import unittest
from pathlib import Path

from src.database import inicializar_base_datos
from src.modeling import (
    ejecutar_evaluacion_lote,
    entrenar_modelo,
    predecir_estudiante,
    sincronizar_predicciones,
)
from src.repositories import (
    agregar_estudiante_desconocido,
    obtener_evaluacion_lote,
    obtener_estudiante,
    obtener_estudiantes,
    obtener_intervenciones,
    obtener_resultados_evaluacion,
    registrar_intervencion,
)
from src.services import nivel_riesgo, validar_nuevo_estudiante
from src.ui.styles import APP_CSS


class EduFuturoCoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        raiz = Path(self.tempdir.name)
        self.db_path = raiz / "test.db"
        self.model_path = raiz / "modelo.joblib"
        inicializar_base_datos(self.db_path, cantidad=180)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_dataset_80_20_es_reproducible(self):
        estudiantes = obtener_estudiantes(self.db_path)
        conocidos = estudiantes[estudiantes["tipo_dato"] == "CONOCIDO"]
        pendientes = estudiantes[estudiantes["tipo_dato"] == "DESCONOCIDO"]
        self.assertEqual(len(estudiantes), 180)
        self.assertEqual(len(conocidos), 144)
        self.assertEqual(len(pendientes), 36)
        self.assertEqual(estudiantes["codigo"].nunique(), 180)
        self.assertGreater(estudiantes["nombre_completo"].nunique(), 170)
        self.assertTrue(conocidos["abandono_observado"].notna().all())
        self.assertTrue(pendientes["abandono_observado"].isna().all())

    def test_modelo_entrena_y_reporta_metricas_validas(self):
        bundle = entrenar_modelo(self.db_path, self.model_path)
        metricas = bundle["metricas"]
        for clave in ("accuracy", "precision", "recall", "f1"):
            self.assertGreaterEqual(metricas[clave], 0)
            self.assertLessEqual(metricas[clave], 1)
        self.assertEqual(len(metricas["matriz_confusion"]), 2)
        self.assertEqual(
            len(bundle["casos_validacion"]),
            metricas["registros_prueba"],
        )
        self.assertEqual(
            sum(sum(fila) for fila in metricas["matriz_confusion"]),
            metricas["registros_prueba"],
        )

    def test_caso_desconocido_se_registra_y_predice(self):
        bundle = entrenar_modelo(self.db_path, self.model_path)
        datos = validar_nuevo_estudiante(
            {
                "codigo": "NUEVO-001",
                "nombres": "Lucía",
                "apellido_paterno": "Valdivia",
                "apellido_materno": "Campos",
                "email": "lucia.valdivia@example.com",
                "telefono": "987654321",
                "carrera": "Ingeniería de Sistemas",
                "ciclo": 4,
                "asistencia_pct": 58,
                "promedio_notas": 9.5,
                "cursos_desaprobados": 3,
                "dias_sin_ingreso": 28,
                "meses_adeudados": 2,
                "deuda_total": 980,
                "historico_abandono": True,
            }
        )
        estudiante_id = agregar_estudiante_desconocido(datos, self.db_path)
        resultado = predecir_estudiante(estudiante_id, bundle, self.db_path)
        estudiante = obtener_estudiante(estudiante_id, self.db_path)
        self.assertEqual(estudiante["tipo_dato"], "DESCONOCIDO")
        self.assertIsNone(estudiante["abandono_observado"])
        self.assertGreaterEqual(resultado["probabilidad"], 0)
        self.assertLessEqual(resultado["probabilidad"], 1)

    def test_sincronizacion_no_duplica_misma_version(self):
        bundle = entrenar_modelo(self.db_path, self.model_path)
        primera = sincronizar_predicciones(bundle, self.db_path)
        segunda = sincronizar_predicciones(bundle, self.db_path)
        self.assertEqual(primera, 144)
        self.assertEqual(segunda, 0)
        estudiantes = obtener_estudiantes(self.db_path)
        self.assertEqual(int(estudiantes["probabilidad_riesgo"].notna().sum()), 144)
        self.assertEqual(int(estudiantes["probabilidad_riesgo"].isna().sum()), 36)

    def test_evaluacion_masiva_procesa_solo_pendientes(self):
        bundle = entrenar_modelo(self.db_path, self.model_path)
        sincronizar_predicciones(bundle, self.db_path)
        primera = sincronizar_predicciones(
            bundle,
            self.db_path,
            tipo_dato="DESCONOCIDO",
            solo_sin_historial=True,
        )
        segunda = sincronizar_predicciones(
            bundle,
            self.db_path,
            tipo_dato="DESCONOCIDO",
            solo_sin_historial=True,
        )
        self.assertEqual(primera, 36)
        self.assertEqual(segunda, 0)
        self.assertTrue(obtener_estudiantes(self.db_path)["probabilidad_riesgo"].notna().all())

    def test_evaluacion_verificable_persiste_comprobante_y_detalle(self):
        bundle = entrenar_modelo(self.db_path, self.model_path)
        sincronizar_predicciones(bundle, self.db_path)
        avances = []
        ejecucion = ejecutar_evaluacion_lote(
            bundle,
            self.db_path,
            progreso=lambda actual, total: avances.append((actual, total)),
        )

        self.assertEqual(ejecucion["procesados"], 36)
        self.assertEqual(ejecucion["errores"], 0)
        self.assertEqual(ejecucion["estado"], "COMPLETADO")
        self.assertTrue(str(ejecucion["codigo_ejecucion"]).startswith("EV-"))
        self.assertGreaterEqual(float(ejecucion["confianza_promedio"]), 0.5)
        self.assertEqual(avances[-1], (36, 36))

        comprobante = obtener_evaluacion_lote(int(ejecucion["id"]), self.db_path)
        resultados = obtener_resultados_evaluacion(int(ejecucion["id"]), self.db_path)
        self.assertIsNotNone(comprobante)
        self.assertEqual(len(resultados), 36)
        self.assertTrue(resultados["probabilidad_riesgo"].between(0, 1).all())
        self.assertTrue(resultados["factores_json"].notna().all())

    def test_reevaluacion_crea_historial_sin_borrar_resultados_previos(self):
        bundle = entrenar_modelo(self.db_path, self.model_path)
        sincronizar_predicciones(bundle, self.db_path)
        primera = ejecutar_evaluacion_lote(bundle, self.db_path)
        segunda = ejecutar_evaluacion_lote(
            bundle,
            self.db_path,
            solo_sin_historial=False,
        )
        self.assertNotEqual(primera["codigo_ejecucion"], segunda["codigo_ejecucion"])
        self.assertEqual(segunda["procesados"], 36)
        self.assertEqual(
            len(obtener_resultados_evaluacion(int(primera["id"]), self.db_path)),
            36,
        )
        self.assertEqual(
            len(obtener_resultados_evaluacion(int(segunda["id"]), self.db_path)),
            36,
        )

    def test_intervencion_permanece_en_sqlite(self):
        estudiante_id = int(obtener_estudiantes(self.db_path).iloc[0]["estudiante_id"])
        registrar_intervencion(
            {
                "estudiante_id": estudiante_id,
                "tipo": "Tutoría académica",
                "detalle": "Se acordó un plan semanal de recuperación académica.",
                "compromisos": "Asistir a dos tutorías.",
                "responsable": "Coordinación de Permanencia",
                "estado": "En seguimiento",
                "fecha_intervencion": "2026-07-20",
                "proximo_seguimiento": "2026-07-27",
            },
            self.db_path,
        )
        historial = obtener_intervenciones(estudiante_id, self.db_path)
        self.assertEqual(len(historial), 1)
        self.assertEqual(historial.iloc[0]["tipo"], "Tutoría académica")

    def test_umbrales_de_riesgo(self):
        self.assertEqual(nivel_riesgo(0.10), "Bajo")
        self.assertEqual(nivel_riesgo(0.35), "Medio")
        self.assertEqual(nivel_riesgo(0.65), "Alto")

    def test_control_para_reabrir_sidebar_permanece_visible(self):
        self.assertNotIn(
            '[data-testid="stToolbar"], [data-testid="stDecoration"]',
            APP_CSS,
        )
        self.assertIn('[data-testid="stExpandSidebarButton"]', APP_CSS)
        self.assertIn("display:inline-flex !important", APP_CSS)


if __name__ == "__main__":
    unittest.main()
