from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import CARRERAS, RISK_COLORS
from src.modeling import predecir_estudiante
from src.repositories import agregar_estudiante_desconocido, obtener_estudiante
from src.services import validar_nuevo_estudiante
from src.ui.components import badge_riesgo, encabezado


def _mostrar_resultado(estudiante_id: int, bundle: dict) -> None:
    est = obtener_estudiante(estudiante_id)
    if not est:
        return
    prob = float(est.get("probabilidad_riesgo") or 0)
    nivel = str(est.get("nivel_riesgo") or "Bajo")

    st.markdown("### Resultado de la evaluación")
    left, right = st.columns([1, 1.3])
    with left:
        st.markdown(
            f"""
            <div class="result-hero">
                <div class="caption">RIESGO ESTIMADO DE DESERCIÓN</div>
                <div class="score">{prob * 100:.1f} %</div>
                <div style="margin:.35rem 0">{badge_riesgo(nivel)}</div>
                <div class="caption">{est['nombre_completo']} · {est['codigo']}<br>Evaluación registrada</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=prob * 100,
                number={"suffix": " %", "font": {"size": 34, "color": "#102A43"}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": RISK_COLORS[nivel]},
                    "steps": [
                        {"range": [0, 35], "color": "#E5F6EE"},
                        {"range": [35, 65], "color": "#FFF3D6"},
                        {"range": [65, 100], "color": "#FDEBEC"},
                    ],
                    "threshold": {"line": {"color": "#102A43", "width": 3}, "value": 65},
                },
            )
        )
        fig.update_layout(height=250, margin=dict(l=25, r=25, t=25, b=15), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    factores = est.get("factores_json")
    if factores:
        import json

        datos = json.loads(factores)
        fig = px.bar(
            x=list(datos.values()),
            y=list(datos.keys()),
            orientation="h",
            labels={"x": "Señal de impacto", "y": ""},
            color=list(datos.values()),
            color_continuous_scale=["#9EE3D5", "#F5A524", "#E5484D"],
        )
        fig.update_layout(height=260, coloraxis_showscale=False, margin=dict(l=5, r=5, t=10, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.markdown("#### Señales que requieren revisión")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    from src.services import factores_y_recomendaciones

    _, recomendaciones = factores_y_recomendaciones(est)
    st.markdown("#### Acciones sugeridas")
    for recomendacion in recomendaciones:
        st.markdown(f"- {recomendacion}")

    st.info(
        "El resultado es una señal preventiva para orientar el acompañamiento. "
        "Debe complementarse con la revisión del responsable de permanencia."
    )
    if st.button("Evaluar otro estudiante", width="content"):
        st.session_state.pop("ultimo_estudiante_nuevo", None)
        st.rerun()


def render(bundle: dict) -> None:
    encabezado(
        "Registrar y evaluar estudiante",
        "Incorpora un estudiante al padrón y obtén una evaluación inicial para orientar su seguimiento.",
        "Nuevo registro",
    )

    if st.session_state.get("ultimo_estudiante_nuevo"):
        _mostrar_resultado(int(st.session_state.ultimo_estudiante_nuevo), bundle)
        return

    st.markdown(
        """
        <div class="info-strip"><b>Antes de continuar:</b> verifica que los indicadores correspondan al periodo actual. Al guardar, el sistema calculará el nivel de riesgo y propondrá acciones de acompañamiento.</div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    with st.form("nuevo_estudiante", clear_on_submit=False):
        st.markdown("#### 1. Identificación")
        a, b, c, d = st.columns([1, 1.2, 1, 1])
        codigo = a.text_input("Código institucional *", max_chars=15)
        nombres = b.text_input("Nombres *", max_chars=60)
        apellido_paterno = c.text_input("Apellido paterno *", max_chars=60)
        apellido_materno = d.text_input("Apellido materno *", max_chars=60)
        e, f, g, h = st.columns([1.2, 1, 1.4, .7])
        email = e.text_input("Correo")
        telefono = f.text_input("Teléfono", max_chars=15)
        carrera = g.selectbox("Carrera *", list(CARRERAS))
        ciclo = h.number_input("Ciclo *", min_value=1, max_value=12, value=1, step=1)

        st.markdown("#### 2. Indicadores de seguimiento")
        st.caption("Registra la información académica y administrativa disponible para el periodo actual.")
        i, j, k = st.columns(3)
        asistencia = i.slider("Asistencia acumulada (%) *", 0.0, 100.0, 82.0, .5)
        promedio = j.slider("Promedio de notas (0–20) *", 0.0, 20.0, 14.0, .1)
        desaprobados = k.number_input("Cursos desaprobados *", 0, 20, 0, 1)
        l, m, n = st.columns(3)
        dias_sin_ingreso = l.number_input("Días sin ingresar al aula virtual *", 0, 365, 3, 1)
        meses_adeudados = m.number_input("Meses adeudados *", 0, 24, 0, 1)
        deuda_total = n.number_input("Deuda total (S/) *", 0.0, 100000.0, 0.0, 50.0)
        historico = st.checkbox("El estudiante tiene antecedente de interrupción o abandono")

        confirmacion = st.checkbox("Confirmo que los datos fueron revisados antes de registrar al estudiante.")
        enviar = st.form_submit_button("Guardar y evaluar estudiante", type="primary", width="stretch")

    if enviar:
        if not confirmacion:
            st.warning("Confirma la revisión de los datos antes de continuar.")
            return
        try:
            datos = validar_nuevo_estudiante(
                {
                    "codigo": codigo,
                    "nombres": nombres,
                    "apellido_paterno": apellido_paterno,
                    "apellido_materno": apellido_materno,
                    "email": email,
                    "telefono": telefono,
                    "carrera": carrera,
                    "ciclo": int(ciclo),
                    "asistencia_pct": asistencia,
                    "promedio_notas": promedio,
                    "cursos_desaprobados": int(desaprobados),
                    "dias_sin_ingreso": int(dias_sin_ingreso),
                    "meses_adeudados": int(meses_adeudados),
                    "deuda_total": deuda_total,
                    "historico_abandono": historico,
                }
            )
            estudiante_id = agregar_estudiante_desconocido(datos)
            predecir_estudiante(estudiante_id, bundle, guardar=True)
            st.session_state.ultimo_estudiante_nuevo = estudiante_id
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
