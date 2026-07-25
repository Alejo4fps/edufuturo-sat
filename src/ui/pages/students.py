from __future__ import annotations

import streamlit as st

from src.repositories import obtener_estudiante, obtener_estudiantes, obtener_intervenciones
from src.ui.components import badge_evaluacion, badge_riesgo, encabezado


def _detalle_estudiante(estudiante_id: int) -> None:
    est = obtener_estudiante(estudiante_id)
    if not est:
        st.warning("No se encontró el estudiante seleccionado.")
        return

    st.markdown(f"### {est['nombre_completo']}")
    evaluado = est["probabilidad_riesgo"] is not None
    distintivos = badge_evaluacion(evaluado)
    if evaluado:
        distintivos += f" &nbsp; {badge_riesgo(est['nivel_riesgo'])}"
    st.markdown(distintivos, unsafe_allow_html=True)
    st.caption(f"{est['codigo']} · {est['carrera']} · ciclo {est['ciclo']}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Probabilidad", f"{float(est['probabilidad_riesgo']) * 100:.1f} %" if evaluado else "Pendiente")
    c2.metric("Asistencia", f"{float(est['asistencia_pct']):.1f} %")
    promedio = est["promedio_notas"]
    c3.metric("Promedio", "Dato faltante" if promedio is None else f"{float(promedio):.1f}")
    c4.metric("Meses adeudados", str(est["meses_adeudados"]))

    st.markdown("**Indicadores complementarios**")
    st.write(
        f"Cursos desaprobados: **{est['cursos_desaprobados']}** · "
        f"Días sin ingresar: **{est['dias_sin_ingreso']}** · "
        f"Antecedente de abandono: **{'Sí' if est['historico_abandono'] else 'No'}**"
    )
    if not evaluado:
        st.warning(
            "Este estudiante aún no ha sido evaluado. Puedes procesarlo desde la bandeja "
            "**Estudiantes no evaluados**."
        )

    historial = obtener_intervenciones(estudiante_id)
    if not historial.empty:
        st.markdown("**Historial de intervención**")
        vista = historial[["fecha_intervencion", "tipo", "responsable", "estado"]].copy()
        vista.columns = ["Fecha", "Tipo", "Responsable", "Estado"]
        st.dataframe(vista, hide_index=True, width="stretch")


def render(bundle: dict) -> None:
    del bundle
    encabezado(
        "Padrón de estudiantes",
        "Consulta indicadores, resultados de riesgo y el historial de acompañamiento de cada estudiante.",
        "Gestión de estudiantes",
    )
    df = obtener_estudiantes()

    f1, f2, f3, f4 = st.columns([2, 1.3, 1.1, 1.1])
    buscar = f1.text_input("Buscar por código o nombre")
    carrera = f2.selectbox("Carrera", ["Todas"] + sorted(df["carrera"].dropna().unique().tolist()))
    riesgo = f3.selectbox("Riesgo", ["Todos", "Alto", "Medio", "Bajo", "No evaluado"])
    estado = f4.selectbox("Evaluación", ["Todos", "Evaluados", "Pendientes"])

    filtrado = df.copy()
    if buscar:
        patron = buscar.strip()
        filtrado = filtrado[
            filtrado["codigo"].str.contains(patron, case=False, na=False)
            | filtrado["nombre_completo"].str.contains(patron, case=False, na=False)
        ]
    if carrera != "Todas":
        filtrado = filtrado[filtrado["carrera"] == carrera]
    if riesgo == "No evaluado":
        filtrado = filtrado[filtrado["nivel_riesgo"].isna()]
    elif riesgo != "Todos":
        filtrado = filtrado[filtrado["nivel_riesgo"] == riesgo]
    if estado == "Evaluados":
        filtrado = filtrado[filtrado["probabilidad_riesgo"].notna()]
    elif estado == "Pendientes":
        filtrado = filtrado[filtrado["probabilidad_riesgo"].isna()]

    filtrado = filtrado.sort_values("probabilidad_riesgo", ascending=False)
    st.caption(f"Mostrando {len(filtrado)} de {len(df)} registros · fuente: SQLite")

    tabla = filtrado[
        [
            "codigo", "nombre_completo", "carrera", "ciclo",
            "nivel_riesgo", "probabilidad_riesgo", "asistencia_pct", "promedio_notas",
        ]
    ].copy()
    tabla.insert(4, "estado_evaluacion", tabla["probabilidad_riesgo"].notna().map({True: "Evaluado", False: "Pendiente"}))
    tabla["probabilidad_riesgo"] = tabla["probabilidad_riesgo"] * 100
    tabla["nivel_riesgo"] = tabla["nivel_riesgo"].fillna("No evaluado")
    tabla.columns = [
        "Código", "Estudiante", "Carrera", "Ciclo", "Evaluación", "Riesgo",
        "Probabilidad %", "Asistencia %", "Promedio",
    ]
    evento = st.dataframe(
        tabla,
        hide_index=True,
        width="stretch",
        height=460,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Probabilidad %": st.column_config.ProgressColumn("Probabilidad %", min_value=0, max_value=100, format="%.1f %%"),
            "Asistencia %": st.column_config.NumberColumn("Asistencia %", format="%.1f %%"),
            "Promedio": st.column_config.NumberColumn("Promedio", format="%.1f"),
        },
    )

    c1, c2 = st.columns([1, 2])
    with c1:
        st.download_button(
            "Descargar vista en CSV",
            data=tabla.to_csv(index=False).encode("utf-8-sig"),
            file_name="estudiantes_edufuturo.csv",
            mime="text/csv",
            width="stretch",
        )
    filas = evento.selection.rows if evento and evento.selection else []
    if filas:
        est_id = int(filtrado.iloc[filas[0]]["estudiante_id"])
        with st.expander("Perfil completo del estudiante", expanded=True):
            _detalle_estudiante(est_id)
