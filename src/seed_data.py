"""Generación reproducible del padrón simulado conocido y no evaluado."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from src.config import CARRERAS


NOMBRES = [
    "Adriana", "Alejandra", "Alessandra", "Alonso", "Andrea", "Ángel", "Ariana",
    "Brenda", "Bruno", "Camila", "Carlos", "Carolina", "César", "Claudia",
    "Cristian", "Daniel", "Daniela", "Diana", "Diego", "Eduardo", "Elena",
    "Emilio", "Esteban", "Fabiola", "Fernando", "Fiorella", "Gabriel", "Gianella",
    "Gonzalo", "Guadalupe", "Héctor", "Isabella", "Javier", "Jimena", "Joaquín",
    "Jorge", "José", "Karen", "Katherine", "Kiara", "Leonardo", "Luciana",
    "Luis", "Mariana", "María", "Martín", "Mateo", "Mía", "Milagros", "Natalia",
    "Nicolás", "Noelia", "Paola", "Patricia", "Rafael", "Renato", "Rodrigo",
    "Rosa", "Samantha", "Sebastián", "Sofía", "Thiago", "Valentina", "Valeria",
    "Víctor", "Ximena", "Yessenia",
]

APELLIDOS = [
    "Aguilar", "Alarcón", "Álvarez", "Arias", "Bautista", "Benavides", "Cabrera",
    "Campos", "Cárdenas", "Castillo", "Castro", "Chávez", "Condori", "Contreras",
    "Córdova", "Cruz", "Delgado", "Díaz", "Espinoza", "Fernández", "Flores",
    "García", "Gómez", "Gonzales", "Gutiérrez", "Herrera", "Huamán", "Jiménez",
    "López", "Lozano", "Mamani", "Medina", "Mendoza", "Morales", "Navarro",
    "Núñez", "Ortiz", "Palomino", "Paredes", "Peña", "Pérez", "Quispe", "Ramírez",
    "Ramos", "Reyes", "Ríos", "Rivera", "Rojas", "Romero", "Salazar", "Sánchez",
    "Silva", "Soto", "Suárez", "Torres", "Valdivia", "Vargas", "Vásquez", "Vega",
    "Velásquez", "Zambrano",
]


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def generar_estudiantes_conocidos(cantidad: int = 420, semilla: int = 2026) -> list[dict[str, Any]]:
    """Crea casos históricos variados con una variable objetivo observada.

    Los valores son simulados, reproducibles y correlacionados de forma no perfecta
    para evitar que el modelo memorice una regla determinista irreal.
    """
    rng = np.random.default_rng(semilla)
    carreras = list(CARRERAS)
    registros: list[dict[str, Any]] = []

    combinaciones = [(nombre, a1, a2) for nombre in NOMBRES for a1 in APELLIDOS for a2 in APELLIDOS if a1 != a2]
    indices = rng.choice(len(combinaciones), size=cantidad, replace=False)

    for posicion, indice in enumerate(indices, start=1):
        nombres, apellido_paterno, apellido_materno = combinaciones[int(indice)]
        carrera = str(rng.choice(carreras))
        ciclo = int(rng.integers(1, CARRERAS[carrera] + 1))

        perfil_vulnerable = rng.random() < 0.30
        if perfil_vulnerable:
            asistencia = float(np.clip(rng.normal(68, 13), 35, 96))
            promedio = float(np.clip(rng.normal(11.6, 2.7), 4, 18.5))
            cursos_desaprobados = int(np.clip(rng.poisson(2.4), 0, 8))
            dias_sin_ingreso = int(np.clip(rng.gamma(3.0, 8.0), 1, 90))
            meses_adeudados = int(np.clip(rng.poisson(1.7), 0, 6))
            historico = int(rng.random() < 0.28)
        else:
            asistencia = float(np.clip(rng.normal(88, 7), 55, 100))
            promedio = float(np.clip(rng.normal(15.1, 2.0), 8, 20))
            cursos_desaprobados = int(np.clip(rng.poisson(0.7), 0, 5))
            dias_sin_ingreso = int(np.clip(rng.gamma(1.5, 4.0), 0, 40))
            meses_adeudados = int(np.clip(rng.poisson(0.35), 0, 3))
            historico = int(rng.random() < 0.06)

        logit = (
            -3.20
            + (75 - asistencia) * 0.055
            + (12.5 - promedio) * 0.22
            + cursos_desaprobados * 0.28
            + dias_sin_ingreso * 0.018
            + meses_adeudados * 0.36
            + historico * 0.95
            + float(rng.normal(0, 0.50))
        )
        probabilidad_real = _sigmoid(logit)
        abandono_observado = int(rng.random() < probabilidad_real)
        deuda_total = round(meses_adeudados * float(rng.uniform(320, 590)), 2)

        # Un pequeño porcentaje de notas ausentes permite demostrar la imputación.
        promedio_guardado = None if rng.random() < 0.035 else round(promedio, 2)
        codigo = f"EF{2023 + (posicion % 3)}{posicion:05d}"
        correo_nombre = nombres.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        correo_apellido = apellido_paterno.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

        registros.append(
            {
                "codigo": codigo,
                "nombres": nombres,
                "apellido_paterno": apellido_paterno,
                "apellido_materno": apellido_materno,
                "email": f"{correo_nombre}.{correo_apellido}{posicion}@edufuturo.edu.pe",
                "telefono": f"9{int(rng.integers(10000000, 99999999))}",
                "carrera": carrera,
                "ciclo": ciclo,
                "tipo_dato": "CONOCIDO",
                "abandono_observado": abandono_observado,
                "asistencia_pct": round(asistencia, 2),
                "promedio_notas": promedio_guardado,
                "cursos_desaprobados": cursos_desaprobados,
                "dias_sin_ingreso": dias_sin_ingreso,
                "meses_adeudados": meses_adeudados,
                "deuda_total": deuda_total,
                "historico_abandono": historico,
            }
        )

    return registros


def generar_dataset_inicial(
    cantidad_total: int = 420,
    proporcion_conocidos: float = 0.80,
    semilla: int = 2026,
) -> list[dict[str, Any]]:
    """Genera el padrón inicial con 80 % de resultados conocidos y 20 % pendientes.

    Los casos pendientes conservan sus variables de entrada, pero la variable objetivo
    queda en NULL. Por eso pueden evaluarse después sin participar en el entrenamiento.
    """
    if cantidad_total < 100:
        raise ValueError("El padrón inicial debe contener al menos 100 estudiantes.")
    if not 0.50 <= proporcion_conocidos < 1:
        raise ValueError("La proporción de casos conocidos debe estar entre 0.50 y 0.99.")

    registros = generar_estudiantes_conocidos(cantidad_total, semilla)
    cantidad_conocidos = int(round(cantidad_total * proporcion_conocidos))
    rng = np.random.default_rng(semilla + 17)
    indices_pendientes = set(
        int(i)
        for i in rng.choice(
            cantidad_total,
            size=cantidad_total - cantidad_conocidos,
            replace=False,
        )
    )
    for indice, registro in enumerate(registros):
        if indice in indices_pendientes:
            registro["tipo_dato"] = "DESCONOCIDO"
            registro["abandono_observado"] = None
    return registros
