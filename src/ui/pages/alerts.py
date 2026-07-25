from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from src.repositories import obtener_estudiantes, obtener_intervenciones, registrar_intervencion
from src.ui.components import badge_riesgo, encabezado


TIPOS = [
    "Llamada de seguimiento",
    "Tutoría académica",
    "Orientación psicológica",
    "Derivación a Bienestar",
    "Acuerdo de pago",
    "Reincorporación académica",
]


def render(bundle: dict) -> None:
    del bundle
    encabezado(
        "Alertas e intervenciones",
        "Convierte cada alerta en una acción institucional trazable y medible.",
        "Acompañamiento estudiantil",
    )
    df = obtener_estudiantes()
    candidatos = df[df["nivel_riesgo"].isin(["Alto", "Medio"])].sort_values(
        ["nivel_riesgo", "probabilidad_riesgo"], ascending=[True, False]
    )
    if candidatos.empty:
        st.success("No existen alertas de riesgo alto o medio.")
        return

    total_altas = int((df["nivel_riesgo"] == "Alto").sum())
    atendidas_altas = int(df.loc[df["nivel_riesgo"] == "Alto", "total_intervenciones"].gt(0).sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Alertas altas", total_altas)
    c2.metric("Altas atendidas", atendidas_altas)
    c3.metric("Cobertura", f"{atendidas_altas / max(total_altas, 1) * 100:.1f} %")

    opciones = {
        int(row.estudiante_id): f"{row.codigo} · {row.nombre_completo} · {row.nivel_riesgo} ({row.probabilidad_riesgo * 100:.1f} %)"
        for row in candidatos.itertuples()
    }
    seleccionado = st.selectbox(
        "Selecciona una alerta",
        options=list(opciones),
        format_func=lambda value: opciones[value],
    )
    est = candidatos[candidatos["estudiante_id"] == seleccionado].iloc[0]

    st.write("")
    left, right = st.columns([1.1, 1.4])
    with left:
        with st.container(border=True):
            st.markdown(f"### {est['nombre_completo']}")
            st.markdown(badge_riesgo(est["nivel_riesgo"]), unsafe_allow_html=True)
            st.caption(f"{est['codigo']} · {est['carrera']} · ciclo {est['ciclo']}")
            st.metric("Probabilidad estimada", f"{est['probabilidad_riesgo'] * 100:.1f} %")
            st.write(f"**Asistencia:** {est['asistencia_pct']:.1f} %")
            promedio = "Sin dato" if est["promedio_notas"] is None else f"{est['promedio_notas']:.1f}"
            st.write(f"**Promedio:** {promedio}")
            st.write(f"**Días sin ingresar:** {est['dias_sin_ingreso']}")
            st.write(f"**Meses adeudados:** {est['meses_adeudados']}")
            st.caption(f"Intervenciones registradas: {int(est['total_intervenciones'])}")

    with right:
        with st.form("form_intervencion", clear_on_submit=True):
            st.markdown("### Registrar intervención")
            a, b = st.columns(2)
            tipo = a.selectbox("Tipo de acción *", TIPOS)
            responsable = b.text_input("Responsable *", value="Coordinación de Permanencia")
            detalle = st.text_area(
                "Detalle de la intervención *",
                max_chars=1200,
            )
            compromisos = st.text_area(
                "Compromisos acordados",
                max_chars=1000,
            )
            c, d, e = st.columns(3)
            fecha_intervencion = c.date_input("Fecha", value=date.today())
            proximo = d.date_input("Próximo seguimiento", value=date.today() + timedelta(days=7))
            estado = e.selectbox("Estado", ["En seguimiento", "Atendido", "Escalado", "Cerrado"])
            guardar = st.form_submit_button("Guardar intervención", type="primary", width="stretch")

        if guardar:
            if len(detalle.strip()) < 10 or len(responsable.strip()) < 3:
                st.warning("Completa un responsable y un detalle de al menos 10 caracteres.")
            elif proximo < fecha_intervencion:
                st.warning("El próximo seguimiento no puede ser anterior a la intervención.")
            else:
                registrar_intervencion(
                    {
                        "estudiante_id": int(seleccionado),
                        "tipo": tipo,
                        "detalle": detalle.strip(),
                        "compromisos": compromisos.strip(),
                        "responsable": responsable.strip(),
                        "estado": estado,
                        "fecha_intervencion": fecha_intervencion,
                        "proximo_seguimiento": proximo,
                    }
                )
                st.success("Intervención guardada de forma permanente en SQLite.")
                st.rerun()

    historial = obtener_intervenciones(int(seleccionado))
    st.write("")
    st.markdown("### Historial del caso")
    if historial.empty:
        st.info("Este caso aún no tiene acciones registradas.")
    else:
        for registro in historial.itertuples():
            with st.container(border=True):
                h1, h2 = st.columns([3, 1])
                h1.markdown(f"**{registro.tipo}** · {registro.fecha_intervencion}")
                h1.write(registro.detalle)
                if registro.compromisos:
                    h1.caption(f"Compromisos: {registro.compromisos}")
                h2.markdown(f"**{registro.estado}**")
                h2.caption(f"Responsable: {registro.responsable}")
                h2.caption(f"Seguimiento: {registro.proximo_seguimiento or 'No programado'}")
