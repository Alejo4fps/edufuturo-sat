from __future__ import annotations

from html import escape

import streamlit as st

from src.config import RISK_COLORS
from src.services import iniciales


def encabezado(titulo: str, subtitulo: str, kicker: str) -> None:
    st.markdown(
        f"""
        <div class="page-heading">
            <div class="page-heading-copy">
                <div class="page-kicker">{escape(kicker)}</div>
                <h1>{escape(titulo)}</h1>
                <p>{escape(subtitulo)}</p>
            </div>
            <div class="page-heading-status">
                <span class="page-status-dot"></span>
                Datos actualizados
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tarjeta_metrica(etiqueta: str, valor: str, ayuda: str, color: str = "#17A589") -> None:
    iconos = {
        "Padrón activo": "groups",
        "Evaluados": "task_alt",
        "No evaluados": "hourglass_top",
        "Prioridad alta": "priority_high",
        "Pendientes": "pending_actions",
        "Cobertura": "donut_large",
        "Procesados": "done_all",
        "Errores": "error",
        "Confianza promedio": "verified",
        "Estado del lote": "database",
        "Exactitud": "target",
        "Precisión": "center_focus_strong",
        "Sensibilidad": "radar",
        "Puntaje F1": "balance",
    }
    icono = iconos.get(etiqueta, "analytics")
    st.markdown(
        f"""
        <div class="metric-card" style="--accent:{escape(color)}">
            <div class="metric-card-top">
                <div class="metric-label">{escape(etiqueta)}</div>
                <div class="metric-icon material-symbols-rounded">{escape(icono)}</div>
            </div>
            <div class="metric-value">{escape(valor)}</div>
            <div class="metric-help">{escape(ayuda)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge_riesgo(nivel: str) -> str:
    clase = {"Alto": "risk-alto", "Medio": "risk-medio", "Bajo": "risk-bajo"}.get(nivel, "risk-bajo")
    color = RISK_COLORS.get(nivel, "#6B7C8F")
    return (
        f'<span class="risk-badge {clase}"><span class="risk-dot" '
        f'style="background:{color}"></span>{escape(nivel)}</span>'
    )


def badge_evaluacion(evaluado: bool) -> str:
    if evaluado:
        return '<span class="data-badge data-evaluated">EVALUADO</span>'
    return '<span class="data-badge data-pending">PENDIENTE</span>'


def fila_estudiante(estudiante: dict, mostrar_estado: bool = False) -> None:
    nombre = str(estudiante.get("nombre_completo", "Estudiante"))
    carrera = str(estudiante.get("carrera", ""))
    codigo = str(estudiante.get("codigo", ""))
    evaluado = estudiante.get("probabilidad_riesgo") is not None
    nivel = str(estudiante.get("nivel_riesgo") or "Pendiente")
    prob = float(estudiante.get("probabilidad_riesgo") or 0) * 100
    estado = badge_evaluacion(evaluado) if mostrar_estado else ""
    resultado = (
        f'{badge_riesgo(nivel)}<div class="student-meta">{prob:.1f} % estimado</div>'
        if evaluado
        else '<span class="data-badge data-pending">POR EVALUAR</span><div class="student-meta">Sin resultado</div>'
    )
    st.markdown(
        f"""
        <div class="student-row">
            <div class="student-main">
                <div class="avatar">{escape(iniciales(nombre))}</div>
                <div>
                    <div class="student-name">{escape(nombre)} &nbsp; {estado}</div>
                    <div class="student-meta">{escape(codigo)} · {escape(carrera)}</div>
                </div>
            </div>
            <div style="text-align:right">{resultado}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def bloque_objetivo(texto: str) -> None:
    st.markdown(
        f"""
        <div class="objective-card">
            <div class="eyebrow">Objetivo estratégico seleccionado</div>
            <h3>{escape(texto)}</h3>
            <p>Proceso asociado: retención y acompañamiento estudiantil · KPI principal: tasa de deserción semestral.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
