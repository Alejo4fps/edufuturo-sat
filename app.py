from __future__ import annotations

import streamlit as st

from src.config import APP_NAME, APP_SUBTITLE
from src.database import inicializar_base_datos
from src.modeling import asegurar_modelo, sincronizar_predicciones
from src.ui.pages import alerts, dashboard, new_student, reports, students, unevaluated
from src.ui.styles import APP_CSS


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def iniciar_sistema() -> dict:
    inicializar_base_datos()
    modelo = asegurar_modelo()
    sincronizar_predicciones(modelo)
    return modelo


try:
    with st.spinner("Preparando el sistema de seguimiento..."):
        bundle = iniciar_sistema()
except Exception as exc:
    st.error("No fue posible iniciar EduFuturo SAT.")
    st.exception(exc)
    st.stop()


PAGINAS = {
    "Inicio": dashboard.render,
    "Estudiantes": students.render,
    "Estudiantes no evaluados": unevaluated.render,
    "Registrar estudiante": new_student.render,
    "Alertas y seguimiento": alerts.render,
    "Reportes": reports.render,
}

ICONOS_NAVEGACION = {
    "Inicio": ":material/dashboard:",
    "Estudiantes": ":material/groups:",
    "Estudiantes no evaluados": ":material/pending_actions:",
    "Registrar estudiante": ":material/person_add:",
    "Alertas y seguimiento": ":material/notifications_active:",
    "Reportes": ":material/monitoring:",
}

if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = "Inicio"
elif st.session_state.pagina_actual not in PAGINAS:
    st.session_state.pagina_actual = "Inicio"


def navegar(pagina: str) -> None:
    st.session_state.pagina_actual = pagina


with st.sidebar:
    st.markdown(
        f"""
        <div class="ef-brand">
            <div class="ef-brand-row">
                <div class="ef-logo">EF</div>
                <div>
                    <div class="ef-brand-name">{APP_NAME}</div>
                    <div class="ef-brand-sub">{APP_SUBTITLE}</div>
                </div>
            </div>
            <div class="ef-system-state">
                <span class="ef-state-dot"></span>
                Sistema operativo
                <span class="ef-state-period">2026-II</span>
            </div>
        </div>
        <div class="ef-sidebar-section">Navegación</div>
        """,
        unsafe_allow_html=True,
    )
    for pagina in PAGINAS:
        st.button(
            pagina,
            key=f"nav_{pagina}",
            type="primary" if pagina == st.session_state.pagina_actual else "secondary",
            icon=ICONOS_NAVEGACION[pagina],
            width="stretch",
            on_click=navegar,
            args=(pagina,),
        )

    st.markdown('<div class="ef-sidebar-section">Sesión actual</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ef-profile">
            <strong>Periodo académico 2026-II</strong>
            <span>Seguimiento de permanencia activo</span>
        </div>
        <div class="ef-profile">
            <strong>Coordinación de Permanencia</strong>
            <span>Perfil responsable</span>
        </div>
        <div class="ef-sidebar-help">
            <span>EF</span>
            <div>
                <strong>EduFuturo SAT</strong>
                <small>Seguimiento institucional seguro</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


PAGINAS[st.session_state.pagina_actual](bundle)
