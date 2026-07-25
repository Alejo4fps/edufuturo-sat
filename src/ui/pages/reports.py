from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.repositories import obtener_estudiantes, obtener_intervenciones
from src.ui.components import encabezado


def render(bundle: dict) -> None:
    del bundle
    encabezado(
        "Reportes para la toma de decisiones",
        "Analiza programas, alertas e intervenciones y exporta evidencia para el seguimiento institucional.",
        "Analítica institucional",
    )
    df = obtener_estudiantes()
    intervenciones = obtener_intervenciones()

    resumen = (
        df.groupby("carrera")
        .agg(
            estudiantes=("estudiante_id", "count"),
            probabilidad_promedio=("probabilidad_riesgo", "mean"),
            asistencia_promedio=("asistencia_pct", "mean"),
            alertas_altas=("nivel_riesgo", lambda s: int((s == "Alto").sum())),
            casos_intervenidos=("total_intervenciones", lambda s: int((s > 0).sum())),
        )
        .reset_index()
    )
    resumen["riesgo_alto_pct"] = resumen["alertas_altas"] / resumen["estudiantes"] * 100
    resumen["cobertura_pct"] = resumen["casos_intervenidos"] / resumen["alertas_altas"].replace(0, 1) * 100

    a, b = st.columns(2)
    with a:
        st.markdown("#### Porcentaje de riesgo alto por carrera")
        fig = px.bar(
            resumen.sort_values("riesgo_alto_pct"),
            x="riesgo_alto_pct",
            y="carrera",
            orientation="h",
            color="riesgo_alto_pct",
            color_continuous_scale=["#9EE3D5", "#F5A524", "#E5484D"],
            labels={"riesgo_alto_pct": "% riesgo alto", "carrera": ""},
        )
        fig.update_layout(height=440, coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=5, r=5, t=15, b=20))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with b:
        st.markdown("#### Probabilidad y asistencia promedio")
        fig = px.scatter(
            resumen,
            x="asistencia_promedio",
            y="probabilidad_promedio",
            size="estudiantes",
            color="riesgo_alto_pct",
            hover_name="carrera",
            color_continuous_scale=["#22A06B", "#F5A524", "#E5484D"],
            labels={"asistencia_promedio": "Asistencia promedio (%)", "probabilidad_promedio": "Probabilidad promedio"},
        )
        fig.update_layout(height=440, coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=5, r=5, t=15, b=20))
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    vista = resumen.copy()
    vista["probabilidad_promedio"] *= 100
    vista = vista.rename(
        columns={
            "carrera": "Carrera",
            "estudiantes": "Estudiantes",
            "probabilidad_promedio": "Riesgo promedio %",
            "asistencia_promedio": "Asistencia promedio %",
            "alertas_altas": "Alertas altas",
            "casos_intervenidos": "Casos intervenidos",
            "riesgo_alto_pct": "Riesgo alto %",
            "cobertura_pct": "Cobertura %",
        }
    )
    st.markdown("#### Consolidado por programa")
    st.dataframe(vista.round(1), hide_index=True, width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Exportar consolidado por carrera",
            data=vista.round(2).to_csv(index=False).encode("utf-8-sig"),
            file_name="reporte_programas_edufuturo.csv",
            mime="text/csv",
            width="stretch",
        )
    with c2:
        exportar = df[
            ["codigo", "nombre_completo", "carrera", "tipo_dato", "nivel_riesgo", "probabilidad_riesgo", "total_intervenciones"]
        ].copy()
        exportar["probabilidad_riesgo"] *= 100
        st.download_button(
            "Exportar padrón de alertas",
            data=exportar.to_csv(index=False).encode("utf-8-sig"),
            file_name="padron_alertas_edufuturo.csv",
            mime="text/csv",
            width="stretch",
        )

    st.write("")
    st.markdown("#### Seguimientos programados")
    if intervenciones.empty:
        st.info("No existen seguimientos registrados.")
    else:
        seguimiento = intervenciones[
            ["proximo_seguimiento", "estudiante", "tipo", "responsable", "estado"]
        ].dropna(subset=["proximo_seguimiento"])
        seguimiento.columns = ["Próxima fecha", "Estudiante", "Acción", "Responsable", "Estado"]
        st.dataframe(seguimiento, hide_index=True, width="stretch")
