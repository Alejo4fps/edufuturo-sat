from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import FEATURE_LABELS, RISK_COLORS
from src.modeling import ejecutar_evaluacion_lote
from src.repositories import (
    obtener_estudiantes,
    obtener_evaluacion_lote,
    obtener_historial_evaluaciones,
    obtener_resultados_evaluacion,
    obtener_ultima_evaluacion_lote,
)
from src.services import factores_y_recomendaciones
from src.ui.components import encabezado, tarjeta_metrica


def _confianza(probabilidad: float) -> float:
    return max(float(probabilidad), 1 - float(probabilidad))


def _nivel_confianza(probabilidad: float) -> str:
    valor = _confianza(probabilidad)
    if valor >= 0.80:
        return "Alta"
    if valor >= 0.65:
        return "Media"
    return "Moderada"


def _fecha_legible(valor: str | None) -> str:
    if not valor:
        return "—"
    try:
        return datetime.fromisoformat(valor).strftime("%d/%m/%Y · %H:%M:%S")
    except ValueError:
        return valor


def _leer_factores(valor: object) -> dict[str, float]:
    if isinstance(valor, dict):
        return {str(k): float(v) for k, v in valor.items()}
    try:
        datos = json.loads(str(valor or "{}"))
        return {str(k): float(v) for k, v in datos.items()}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def _principales_factores(valor: object, limite: int = 3) -> str:
    factores = _leer_factores(valor)
    ordenados = sorted(factores.items(), key=lambda item: item[1], reverse=True)
    return ", ".join(nombre for nombre, _ in ordenados[:limite]) or "Estabilidad general"


def _ejecutar(
    bundle: dict,
    *,
    solo_sin_historial: bool,
) -> None:
    progreso = st.progress(0, text="Preparando registros para la evaluación...")
    estado = st.empty()

    def actualizar(actual: int, total: int) -> None:
        proporcion = actual / max(total, 1)
        progreso.progress(
            proporcion,
            text=f"Procesando estudiantes: {actual} de {total}",
        )
        estado.caption(
            "Cada avance corresponde a un registro analizado por el modelo; "
            "los resultados se guardarán juntos al terminar."
        )

    try:
        ejecucion = ejecutar_evaluacion_lote(
            bundle,
            tipo_dato="DESCONOCIDO",
            solo_sin_historial=solo_sin_historial,
            progreso=actualizar,
        )
    except Exception as exc:
        progreso.empty()
        estado.empty()
        st.error(f"No se pudo completar la evaluación: {exc}")
        return

    progreso.progress(1.0, text="Evaluación completada y guardada en SQLite")
    estado.success(
        f"Se procesaron {ejecucion['procesados']} estudiantes. "
        f"Comprobante: {ejecucion['codigo_ejecucion']}"
    )
    st.session_state["ultima_evaluacion_id"] = int(ejecucion["id"])
    st.rerun()


def _mostrar_resumen(
    ejecucion: dict,
    resultados: pd.DataFrame,
    historial: pd.DataFrame,
) -> None:
    confianza = float(ejecucion.get("confianza_promedio") or 0)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta_metrica(
            "Procesados",
            str(int(ejecucion["procesados"])),
            f"de {int(ejecucion['total_solicitados'])} solicitados",
            "#17A589",
        )
    with c2:
        tarjeta_metrica(
            "Errores",
            str(int(ejecucion["errores"])),
            "Registros que no pudieron evaluarse",
            "#E5484D" if int(ejecucion["errores"]) else "#22A06B",
        )
    with c3:
        tarjeta_metrica(
            "Confianza promedio",
            f"{confianza * 100:.1f} %",
            "Probabilidad de la clase asignada",
            "#176B87",
        )
    with c4:
        tarjeta_metrica(
            "Estado del lote",
            "Completado" if ejecucion["estado"] == "COMPLETADO" else "Con observaciones",
            _fecha_legible(ejecucion.get("fecha_fin")),
            "#17A589" if ejecucion["estado"] == "COMPLETADO" else "#F5A524",
        )

    if resultados.empty:
        st.warning("Esta ejecución no contiene predicciones disponibles.")
        return

    st.write("")
    grafico, confianza_col = st.columns([1.1, 1])
    with grafico:
        st.markdown("#### Distribución de resultados")
        conteo = (
            resultados["nivel_riesgo"]
            .value_counts()
            .reindex(["Bajo", "Medio", "Alto"])
            .fillna(0)
            .astype(int)
        )
        figura = go.Figure(
            data=[
                go.Pie(
                    labels=conteo.index,
                    values=conteo.values,
                    hole=0.68,
                    marker_colors=[RISK_COLORS[nivel] for nivel in conteo.index],
                    textinfo="label+value",
                )
            ]
        )
        figura.update_layout(
            height=330,
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            annotations=[
                dict(
                    text=(
                        f"<b>{len(resultados)}</b><br>"
                        "<span style='font-size:11px'>evaluados</span>"
                    ),
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
            ],
        )
        st.plotly_chart(figura, width="stretch", config={"displayModeBar": False})

    with confianza_col:
        st.markdown("#### Confianza de las predicciones")
        grafico_confianza = resultados.copy()
        grafico_confianza["confianza"] = grafico_confianza["probabilidad_riesgo"].map(
            _confianza
        )
        figura = px.histogram(
            grafico_confianza,
            x="confianza",
            nbins=8,
            color_discrete_sequence=["#176B87"],
            labels={"confianza": "Confianza", "count": "Estudiantes"},
        )
        figura.update_layout(
            height=330,
            bargap=0.12,
            margin=dict(l=10, r=10, t=10, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        figura.update_xaxes(tickformat=".0%", gridcolor="#EDF2F6")
        figura.update_yaxes(gridcolor="#EDF2F6")
        st.plotly_chart(figura, width="stretch", config={"displayModeBar": False})

    exportar = resultados[
        [
            "codigo",
            "nombre_completo",
            "carrera",
            "nivel_riesgo",
            "probabilidad_riesgo",
            "fecha_prediccion",
        ]
    ].copy()
    exportar["confianza"] = exportar["probabilidad_riesgo"].map(_confianza)
    exportar.columns = [
        "Código",
        "Estudiante",
        "Carrera",
        "Resultado predicho",
        "Probabilidad de riesgo",
        "Fecha de evaluación",
        "Confianza",
    ]
    st.download_button(
        "Descargar resultados de esta ejecución",
        data=exportar.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"resultados_{ejecucion['codigo_ejecucion']}.csv",
        mime="text/csv",
        width="stretch",
    )

    if len(historial) > 1:
        st.write("")
        st.markdown("#### Historial de ejecuciones")
        vista_historial = historial.copy()
        vista_historial["confianza_promedio"] *= 100
        vista_historial = vista_historial[
            [
                "codigo_ejecucion",
                "procesados",
                "errores",
                "confianza_promedio",
                "estado",
                "fecha_fin",
            ]
        ]
        vista_historial.columns = [
            "Código de ejecución",
            "Procesados",
            "Errores",
            "Confianza promedio %",
            "Estado",
            "Finalización",
        ]
        st.dataframe(
            vista_historial,
            hide_index=True,
            width="stretch",
            column_config={
                "Confianza promedio %": st.column_config.NumberColumn(format="%.1f %%")
            },
        )


def _mostrar_detalle(resultados: pd.DataFrame) -> None:
    if resultados.empty:
        st.info("No hay resultados individuales en esta ejecución.")
        return

    vista = resultados.copy()
    vista["resultado"] = vista["nivel_riesgo"].map(lambda nivel: f"Riesgo {nivel.lower()}")
    vista["confianza"] = vista["probabilidad_riesgo"].map(_confianza)
    vista["nivel_confianza"] = vista["probabilidad_riesgo"].map(_nivel_confianza)
    vista["factores"] = vista["factores_json"].map(_principales_factores)
    vista["estado"] = "Evaluado"
    tabla = vista[
        [
            "codigo",
            "nombre_completo",
            "resultado",
            "probabilidad_riesgo",
            "confianza",
            "nivel_confianza",
            "factores",
            "estado",
        ]
    ].copy()
    tabla.columns = [
        "Código",
        "Estudiante",
        "Resultado predicho",
        "Probabilidad de riesgo",
        "Confianza",
        "Nivel de confianza",
        "Indicadores principales",
        "Estado",
    ]
    st.dataframe(
        tabla,
        hide_index=True,
        width="stretch",
        height=min(560, 44 + 35 * len(tabla)),
        column_config={
            "Probabilidad de riesgo": st.column_config.ProgressColumn(
                format="percent",
                min_value=0,
                max_value=1,
            ),
            "Confianza": st.column_config.ProgressColumn(
                format="percent",
                min_value=0,
                max_value=1,
            ),
        },
    )

    st.write("")
    st.markdown("#### ¿Cómo se obtuvo esta predicción?")
    opciones = vista["estudiante_id"].astype(int).tolist()
    etiquetas = {
        int(fila["estudiante_id"]): f"{fila['codigo']} · {fila['nombre_completo']}"
        for _, fila in vista.iterrows()
    }
    seleccionado = st.selectbox(
        "Selecciona un estudiante para revisar la explicación",
        opciones,
        format_func=lambda estudiante_id: etiquetas[estudiante_id],
        key="detalle_evaluacion_estudiante",
    )
    fila = vista[vista["estudiante_id"] == seleccionado].iloc[0].to_dict()
    probabilidad = float(fila["probabilidad_riesgo"])
    factores = _leer_factores(fila.get("factores_json"))
    _, recomendaciones = factores_y_recomendaciones(fila)

    st.markdown(
        f"""
        <div class="prediction-explain">
            <div>
                <span class="explain-label">Resultado asignado</span>
                <strong>Riesgo {str(fila['nivel_riesgo']).lower()}</strong>
            </div>
            <div>
                <span class="explain-label">Probabilidad de riesgo</span>
                <strong>{probabilidad * 100:.1f} %</strong>
            </div>
            <div>
                <span class="explain-label">Probabilidad de permanencia</span>
                <strong>{(1 - probabilidad) * 100:.1f} %</strong>
            </div>
            <div>
                <span class="explain-label">Confianza de la decisión</span>
                <strong>{_confianza(probabilidad) * 100:.1f} % · {_nivel_confianza(probabilidad)}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    entrada, lectura = st.columns([1.05, 1])
    with entrada:
        st.markdown("##### Datos analizados por el modelo")
        datos_modelo = pd.DataFrame(
            [
                (FEATURE_LABELS["asistencia_pct"], fila["asistencia_pct"]),
                (FEATURE_LABELS["promedio_notas"], fila["promedio_notas"]),
                (FEATURE_LABELS["cursos_desaprobados"], fila["cursos_desaprobados"]),
                (FEATURE_LABELS["dias_sin_ingreso"], fila["dias_sin_ingreso"]),
                (FEATURE_LABELS["meses_adeudados"], fila["meses_adeudados"]),
                (
                    FEATURE_LABELS["historico_abandono"],
                    "Sí" if int(fila["historico_abandono"]) else "No",
                ),
            ],
            columns=["Indicador", "Valor recibido"],
        )
        st.dataframe(datos_modelo, hide_index=True, width="stretch")

    with lectura:
        st.markdown("##### Indicadores relevantes detectados")
        if factores:
            chips = "".join(
                f"<span class='factor-chip'>{nombre}</span>"
                for nombre, _ in sorted(
                    factores.items(), key=lambda item: item[1], reverse=True
                )[:5]
            )
            st.markdown(f"<div class='factor-list'>{chips}</div>", unsafe_allow_html=True)
        else:
            st.caption("No se registraron indicadores adicionales.")
        st.markdown("##### Acciones sugeridas")
        for recomendacion in recomendaciones[:4]:
            st.markdown(f"- {recomendacion}")


def _mostrar_evidencia(bundle: dict) -> None:
    metricas = bundle["metricas"]
    casos = pd.DataFrame(bundle.get("casos_validacion", []))

    st.markdown(
        f"""
        <div class="evidence-note">
            <div class="evidence-icon material-symbols-rounded">verified</div>
            <div>
                <strong>Validación realizada con casos de resultado conocido</strong>
                <p>El modelo aprendió con {metricas['registros_entrenamiento']} estudiantes y se comprobó con
                {metricas['registros_prueba']} estudiantes distintos que no participaron en el entrenamiento.
                Estas cifras se calculan al entrenar el Random Forest; no son texto fijo.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta_metrica(
            "Exactitud",
            f"{metricas['accuracy'] * 100:.1f} %",
            "Predicciones correctas en validación",
            "#176B87",
        )
    with c2:
        tarjeta_metrica(
            "Precisión",
            f"{metricas['precision'] * 100:.1f} %",
            "Acierto de las alertas de abandono",
            "#17A589",
        )
    with c3:
        tarjeta_metrica(
            "Sensibilidad",
            f"{metricas['recall'] * 100:.1f} %",
            "Abandonos reales que fueron detectados",
            "#F5A524",
        )
    with c4:
        tarjeta_metrica(
            "Puntaje F1",
            f"{metricas['f1'] * 100:.1f} %",
            "Equilibrio entre precisión y detección",
            "#7C5CFC",
        )

    st.write("")
    matriz_col, importancia_col = st.columns([1, 1.12])
    with matriz_col:
        st.markdown("#### Matriz de confusión")
        matriz = metricas["matriz_confusion"]
        figura = go.Figure(
            data=go.Heatmap(
                z=matriz,
                x=["Predice permanencia", "Predice abandono"],
                y=["Real: permanencia", "Real: abandono"],
                colorscale=[
                    [0, "#EFF5F8"],
                    [0.5, "#8FD6C8"],
                    [1, "#176B87"],
                ],
                showscale=False,
                text=matriz,
                texttemplate="%{text}",
                textfont={"size": 22},
                hovertemplate="%{y}<br>%{x}<br>Casos: %{z}<extra></extra>",
            )
        )
        figura.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(figura, width="stretch", config={"displayModeBar": False})
        st.caption(
            "La diagonal representa los aciertos; los otros dos cuadros muestran los errores."
        )

    with importancia_col:
        st.markdown("#### Variables utilizadas por el modelo")
        importancia = pd.DataFrame(
            list(metricas["importancia_variables"].items()),
            columns=["Variable", "Importancia"],
        ).sort_values("Importancia")
        figura = px.bar(
            importancia,
            x="Importancia",
            y="Variable",
            orientation="h",
            color="Importancia",
            color_continuous_scale=["#BFE7DF", "#176B87"],
        )
        figura.update_layout(
            height=350,
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        figura.update_xaxes(tickformat=".0%", gridcolor="#EDF2F6")
        st.plotly_chart(figura, width="stretch", config={"displayModeBar": False})

    st.write("")
    st.markdown("#### Comparación entre resultado real y predicción")
    if casos.empty:
        st.info("El detalle de validación se regenerará en el próximo entrenamiento.")
        return
    casos["Estado"] = casos["coincide"].map(
        {True: "Correcto", False: "No coincidió"}
    )
    casos["probabilidad_permanencia"] = 1 - casos["probabilidad_riesgo"]
    vista = casos[
        [
            "codigo",
            "estudiante",
            "resultado_real",
            "resultado_predicho",
            "probabilidad_riesgo",
            "Estado",
        ]
    ].copy()
    vista.columns = [
        "Código",
        "Estudiante",
        "Resultado real",
        "Predicción del modelo",
        "Probabilidad de abandono",
        "Verificación",
    ]
    st.dataframe(
        vista,
        hide_index=True,
        width="stretch",
        height=min(520, 44 + 35 * len(vista)),
        column_config={
            "Probabilidad de abandono": st.column_config.ProgressColumn(
                format="percent",
                min_value=0,
                max_value=1,
            )
        },
    )
    st.caption(
        f"Versión evaluada: {bundle['version_modelo']} · "
        f"Entrenamiento: {_fecha_legible(metricas.get('fecha_entrenamiento'))}"
    )


def _mostrar_resultados(bundle: dict, ejecucion: dict) -> None:
    historial = obtener_historial_evaluaciones()
    if not historial.empty and len(historial) > 1:
        ids = historial["id"].astype(int).tolist()
        etiquetas = {
            int(fila["id"]): (
                f"{fila['codigo_ejecucion']} · {int(fila['procesados'])} procesados · "
                f"{_fecha_legible(fila['fecha_fin'])}"
            )
            for _, fila in historial.iterrows()
        }
        actual = int(ejecucion["id"])
        seleccionado = st.selectbox(
            "Ejecución mostrada",
            ids,
            index=ids.index(actual) if actual in ids else 0,
            format_func=lambda evaluacion_id: etiquetas[evaluacion_id],
        )
        if seleccionado != actual:
            otra = obtener_evaluacion_lote(seleccionado)
            if otra:
                ejecucion = otra

    resultados = obtener_resultados_evaluacion(int(ejecucion["id"]))
    st.markdown(
        f"""
        <div class="run-proof">
            <div>
                <span>COMPROBANTE DE EJECUCIÓN</span>
                <strong>{ejecucion['codigo_ejecucion']}</strong>
            </div>
            <div>
                <span>MODELO UTILIZADO</span>
                <strong>{ejecucion['version_modelo']}</strong>
            </div>
            <div>
                <span>INICIO</span>
                <strong>{_fecha_legible(ejecucion.get('fecha_inicio'))}</strong>
            </div>
            <div>
                <span>FINALIZACIÓN</span>
                <strong>{_fecha_legible(ejecucion.get('fecha_fin'))}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    resumen_tab, detalle_tab, evidencia_tab = st.tabs(
        ["Resumen", "Detalle por estudiante", "Evidencia del modelo"]
    )
    with resumen_tab:
        _mostrar_resumen(ejecucion, resultados, historial)
    with detalle_tab:
        _mostrar_detalle(resultados)
    with evidencia_tab:
        _mostrar_evidencia(bundle)


def render(bundle: dict) -> None:
    encabezado(
        "Estudiantes no evaluados",
        "Procesa los registros pendientes y conserva evidencia verificable de cada resultado.",
        "Evaluación automática",
    )

    df = obtener_estudiantes()
    pendientes = df[df["probabilidad_riesgo"].isna()].copy()
    evaluados = len(df) - len(pendientes)
    avance = evaluados / max(len(df), 1)

    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta_metrica(
            "Pendientes",
            str(len(pendientes)),
            "Estudiantes aún sin nivel de riesgo",
            "#F5A524",
        )
    with c2:
        tarjeta_metrica(
            "Evaluados",
            str(evaluados),
            "Registros con resultado disponible",
            "#17A589",
        )
    with c3:
        tarjeta_metrica(
            "Cobertura",
            f"{avance * 100:.1f} %",
            "Avance de evaluación del padrón",
            "#176B87",
        )

    st.write("")
    st.progress(avance, text=f"{evaluados} de {len(df)} estudiantes evaluados")
    st.write("")

    ultima = None
    evaluacion_sesion = st.session_state.get("ultima_evaluacion_id")
    if evaluacion_sesion:
        ultima = obtener_evaluacion_lote(int(evaluacion_sesion))
    if not ultima:
        ultima = obtener_ultima_evaluacion_lote()

    if pendientes.empty:
        st.success(
            "Todos los estudiantes del padrón ya cuentan con una evaluación de riesgo."
        )
        if ultima:
            st.markdown(
                """
                <div class="info-strip">
                    La ejecución quedó registrada. Revisa el resumen, el detalle de los
                    estudiantes y la validación calculada del modelo en las pestañas inferiores.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.warning(
                "Estas predicciones fueron creadas con una versión anterior que no guardaba "
                "comprobantes por lote. Puedes procesarlas nuevamente para generar evidencia."
            )

        with st.expander("Volver a ejecutar la evaluación para una demostración"):
            st.caption(
                "Se analizarán nuevamente los estudiantes de resultado desconocido y se "
                "creará un comprobante nuevo. Los registros anteriores no se eliminan."
            )
            confirmar_repeticion = st.checkbox(
                "Confirmo que deseo crear una nueva ejecución verificable.",
                key="confirmar_repeticion_evaluacion",
            )
            if st.button(
                f"Evaluar nuevamente los {int((df['tipo_dato'] == 'DESCONOCIDO').sum())} estudiantes",
                type="primary",
                width="stretch",
                disabled=not confirmar_repeticion,
            ):
                _ejecutar(bundle, solo_sin_historial=False)
    else:
        izquierda, derecha = st.columns([1.55, 1])
        with izquierda:
            st.markdown("#### Registros pendientes")
            tabla = pendientes[
                [
                    "codigo",
                    "nombre_completo",
                    "carrera",
                    "ciclo",
                    "asistencia_pct",
                    "promedio_notas",
                    "dias_sin_ingreso",
                ]
            ].copy()
            tabla.columns = [
                "Código",
                "Estudiante",
                "Carrera",
                "Ciclo",
                "Asistencia %",
                "Promedio",
                "Días sin ingresar",
            ]
            st.dataframe(
                tabla,
                hide_index=True,
                width="stretch",
                height=min(560, 44 + 35 * len(tabla)),
                column_config={
                    "Asistencia %": st.column_config.NumberColumn(format="%.1f %%"),
                    "Promedio": st.column_config.NumberColumn(format="%.1f"),
                },
            )

        with derecha:
            st.markdown(
                f"""
                <div class="action-card">
                    <div class="page-kicker">Proceso verificable</div>
                    <h3>Evaluar {len(pendientes)} estudiantes</h3>
                    <p>Se mostrará el avance registro por registro. Al terminar podrás revisar
                    las probabilidades, la explicación individual, la matriz de confusión y
                    los casos usados para validar el algoritmo.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            confirmar = st.checkbox(
                "Confirmo que los indicadores académicos fueron revisados.",
                key="confirmar_evaluacion_lote",
            )
            if st.button(
                f"Evaluar {len(pendientes)} estudiantes ahora",
                type="primary",
                width="stretch",
                disabled=not confirmar,
            ):
                _ejecutar(bundle, solo_sin_historial=True)

            st.caption(
                "Las predicciones, probabilidades, fecha y código de ejecución se guardan en SQLite."
            )

    if ultima:
        st.write("")
        st.markdown("## Resultados de la evaluación automática")
        _mostrar_resultados(bundle, ultima)
