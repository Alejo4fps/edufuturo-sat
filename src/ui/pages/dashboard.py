from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import OBJECTIVE_TEXT, RISK_COLORS
from src.repositories import obtener_estudiantes, obtener_intervenciones
from src.ui.components import bloque_objetivo, encabezado, fila_estudiante, tarjeta_metrica


COLORES_ESTADO = {**RISK_COLORS, "No evaluado": "#B7C3CF"}


def _ir_a_pendientes() -> None:
    st.session_state.pagina_actual = "Estudiantes no evaluados"


def render(bundle: dict) -> None:
    del bundle  # La vista operativa no expone información técnica del modelo.
    encabezado(
        "Centro de control de permanencia",
        "Prioriza estudiantes, revisa la cobertura del padrón y organiza el acompañamiento.",
        "Resumen del periodo 2026-II",
    )
    df = obtener_estudiantes()
    intervenciones = obtener_intervenciones()

    total = len(df)
    evaluados = int(df["probabilidad_riesgo"].notna().sum())
    pendientes = total - evaluados
    alto = int((df["nivel_riesgo"] == "Alto").sum())
    casos_intervenidos = int(df.loc[df["nivel_riesgo"] == "Alto", "total_intervenciones"].gt(0).sum())
    cobertura = (casos_intervenidos / alto * 100) if alto else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta_metrica("Padrón activo", f"{total}", "Estudiantes en seguimiento", "#176B87")
    with c2:
        tarjeta_metrica("Evaluados", f"{evaluados}", f"{evaluados / max(total, 1) * 100:.1f} % del padrón", "#17A589")
    with c3:
        tarjeta_metrica("No evaluados", f"{pendientes}", "Pendientes de clasificación", "#F5A524")
    with c4:
        tarjeta_metrica("Prioridad alta", f"{alto}", f"{casos_intervenidos} con atención registrada", RISK_COLORS["Alto"])

    st.write("")
    left, right = st.columns([1.2, 1])
    with left:
        bloque_objetivo(OBJECTIVE_TEXT)
    with right:
        st.markdown(
            f"""
            <div class="action-card">
                <div class="page-kicker">Siguiente acción</div>
                <h3>{pendientes} estudiantes esperan evaluación</h3>
                <p>Completa la cobertura del padrón para que el equipo pueda priorizar alertas y registrar intervenciones con información actualizada.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if pendientes:
            st.button(
                "Revisar estudiantes pendientes",
                type="primary",
                width="stretch",
                on_click=_ir_a_pendientes,
            )

    st.write("")
    chart_col, priority_col = st.columns([1.55, 1])
    with chart_col:
        st.markdown("#### Estado de riesgo por carrera")
        grafico = df.copy()
        grafico["estado_riesgo"] = grafico["nivel_riesgo"].fillna("No evaluado")
        resumen = (
            grafico.groupby(["carrera", "estado_riesgo"], dropna=False)
            .size()
            .reset_index(name="estudiantes")
        )
        fig = px.bar(
            resumen,
            x="estudiantes",
            y="carrera",
            color="estado_riesgo",
            color_discrete_map=COLORES_ESTADO,
            category_orders={"estado_riesgo": ["Bajo", "Medio", "Alto", "No evaluado"]},
            barmode="stack",
            orientation="h",
            labels={"estudiantes": "Estudiantes", "carrera": "", "estado_riesgo": "Estado"},
        )
        fig.update_layout(
            height=460,
            legend_title_text="Estado",
            margin=dict(l=5, r=10, t=15, b=25),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans", color="#334E68"),
        )
        fig.update_xaxes(gridcolor="#EDF2F6")
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with priority_col:
        st.markdown("#### Atención prioritaria")
        prioritarios = df[df["probabilidad_riesgo"].notna()].nlargest(5, "probabilidad_riesgo")
        if prioritarios.empty:
            st.info("Todavía no existen resultados de evaluación.")
        else:
            with st.container(border=True):
                for _, row in prioritarios.iterrows():
                    fila_estudiante(row.to_dict())

    st.write("")
    a, b = st.columns(2)
    with a:
        st.markdown("#### Cobertura del padrón")
        conteo = (
            df["nivel_riesgo"]
            .fillna("No evaluado")
            .value_counts()
            .reindex(["Bajo", "Medio", "Alto", "No evaluado"])
            .fillna(0)
        )
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=conteo.index,
                    values=conteo.values,
                    hole=.68,
                    marker_colors=[COLORES_ESTADO[x] for x in conteo.index],
                )
            ]
        )
        fig.update_layout(
            height=310,
            showlegend=True,
            margin=dict(l=10, r=10, t=5, b=5),
            paper_bgcolor="rgba(0,0,0,0)",
            annotations=[
                dict(
                    text=f"<b>{evaluados}</b><br><span style='font-size:11px'>evaluados</span>",
                    x=.5,
                    y=.5,
                    showarrow=False,
                )
            ],
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with b:
        st.markdown("#### Actividad de acompañamiento")
        st.caption(f"Cobertura actual de alertas altas: {cobertura:.1f} %")
        if intervenciones.empty:
            st.info("Aún no se han registrado intervenciones. Las acciones aparecerán aquí y permanecerán en SQLite.")
        else:
            ultimas = intervenciones.head(7)[["fecha_intervencion", "estudiante", "tipo", "estado"]].copy()
            ultimas.columns = ["Fecha", "Estudiante", "Intervención", "Estado"]
            st.dataframe(ultimas, hide_index=True, width="stretch")
