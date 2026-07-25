"""Reglas de negocio, validaciones e interpretación de predicciones."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from src.config import CARRERAS, FEATURE_LABELS


def nivel_riesgo(probabilidad: float) -> str:
    if probabilidad >= 0.65:
        return "Alto"
    if probabilidad >= 0.35:
        return "Medio"
    return "Bajo"


def normalizar_codigo(codigo: str) -> str:
    limpio = re.sub(r"\s+", "", codigo or "").upper()
    if not re.fullmatch(r"[A-Z0-9-]{5,15}", limpio):
        raise ValueError("El código debe tener entre 5 y 15 caracteres alfanuméricos.")
    return limpio


def limpiar_nombre(valor: str, campo: str) -> str:
    limpio = " ".join((valor or "").strip().split())
    if len(limpio) < 2 or len(limpio) > 60:
        raise ValueError(f"{campo} debe tener entre 2 y 60 caracteres.")
    if not all(ch.isalpha() or ch in " '-" for ch in limpio):
        raise ValueError(f"{campo} contiene caracteres no permitidos.")
    return limpio.title()


def validar_nuevo_estudiante(datos: dict[str, Any]) -> dict[str, Any]:
    resultado = dict(datos)
    resultado["codigo"] = normalizar_codigo(str(datos.get("codigo", "")))
    resultado["nombres"] = limpiar_nombre(str(datos.get("nombres", "")), "Nombres")
    resultado["apellido_paterno"] = limpiar_nombre(
        str(datos.get("apellido_paterno", "")), "Apellido paterno"
    )
    resultado["apellido_materno"] = limpiar_nombre(
        str(datos.get("apellido_materno", "")), "Apellido materno"
    )
    if datos.get("carrera") not in CARRERAS:
        raise ValueError("Selecciona una carrera válida.")
    max_ciclo = CARRERAS[str(datos["carrera"])]
    if not 1 <= int(datos.get("ciclo", 0)) <= max_ciclo:
        raise ValueError(f"El ciclo debe estar entre 1 y {max_ciclo} para la carrera seleccionada.")
    rangos = {
        "asistencia_pct": (0, 100),
        "promedio_notas": (0, 20),
        "cursos_desaprobados": (0, 20),
        "dias_sin_ingreso": (0, 365),
        "meses_adeudados": (0, 24),
        "deuda_total": (0, 100000),
    }
    for campo, (minimo, maximo) in rangos.items():
        valor = float(datos.get(campo, -1))
        if not minimo <= valor <= maximo:
            raise ValueError(f"{campo} debe estar entre {minimo} y {maximo}.")
    email = str(datos.get("email", "")).strip().lower()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("El correo electrónico no tiene un formato válido.")
    resultado["email"] = email or None
    telefono = re.sub(r"\D", "", str(datos.get("telefono", "")))
    if telefono and not 7 <= len(telefono) <= 15:
        raise ValueError("El teléfono debe tener entre 7 y 15 dígitos.")
    resultado["telefono"] = telefono or None
    resultado["historico_abandono"] = int(bool(datos.get("historico_abandono")))
    return resultado


def factores_y_recomendaciones(estudiante: dict[str, Any]) -> tuple[dict[str, float], list[str]]:
    factores: dict[str, float] = {}
    recomendaciones: list[str] = []

    asistencia = float(estudiante.get("asistencia_pct") or 0)
    promedio = float(estudiante.get("promedio_notas") or 0)
    desaprobados = int(estudiante.get("cursos_desaprobados") or 0)
    dias = int(estudiante.get("dias_sin_ingreso") or 0)
    deuda = int(estudiante.get("meses_adeudados") or 0)
    historico = int(estudiante.get("historico_abandono") or 0)

    if asistencia < 75:
        factores[FEATURE_LABELS["asistencia_pct"]] = round(100 - asistencia, 1)
        recomendaciones.append("Contactar por ausentismo y acordar un plan de recuperación de asistencia.")
    if promedio < 12.5:
        factores[FEATURE_LABELS["promedio_notas"]] = round((20 - promedio) * 4, 1)
        recomendaciones.append("Asignar tutoría académica y seguimiento de cursos críticos.")
    if desaprobados >= 2:
        factores[FEATURE_LABELS["cursos_desaprobados"]] = round(desaprobados * 10, 1)
    if dias >= 14:
        factores[FEATURE_LABELS["dias_sin_ingreso"]] = round(min(dias, 90), 1)
        recomendaciones.append("Verificar acceso al aula virtual y recuperar el contacto con el estudiante.")
    if deuda >= 1:
        factores[FEATURE_LABELS["meses_adeudados"]] = round(deuda * 15, 1)
        recomendaciones.append("Derivar a Bienestar o Finanzas para evaluar alternativas de pago.")
    if historico:
        factores[FEATURE_LABELS["historico_abandono"]] = 35.0
        recomendaciones.append("Priorizar acompañamiento personalizado por antecedente de interrupción de estudios.")
    if not factores:
        factores["Estabilidad general"] = 100.0
        recomendaciones.append("Mantener el monitoreo preventivo regular.")

    return factores, list(dict.fromkeys(recomendaciones))


def iniciales(nombre: str) -> str:
    palabras = [p for p in nombre.split() if p]
    return "".join(p[0] for p in palabras[:2]).upper() or "EF"


def texto_ascii(valor: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", valor) if not unicodedata.combining(ch)
    )

