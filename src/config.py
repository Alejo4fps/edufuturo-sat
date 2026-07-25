from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
MODEL_DIR = ROOT_DIR / "models"
DB_PATH = DATA_DIR / "edufuturo.db"
MODEL_PATH = MODEL_DIR / "modelo_riesgo.joblib"

APP_NAME = "EduFuturo SAT"
APP_SUBTITLE = "Sistema de Alerta Temprana de Deserción Estudiantil"
MODEL_NAME = "Random Forest Classifier"

FEATURE_COLUMNS = [
    "asistencia_pct",
    "promedio_notas",
    "cursos_desaprobados",
    "dias_sin_ingreso",
    "meses_adeudados",
    "historico_abandono",
]

FEATURE_LABELS = {
    "asistencia_pct": "Asistencia (%)",
    "promedio_notas": "Promedio de notas",
    "cursos_desaprobados": "Cursos desaprobados",
    "dias_sin_ingreso": "Días sin ingresar al aula virtual",
    "meses_adeudados": "Meses adeudados",
    "historico_abandono": "Antecedente de abandono",
}

CARRERAS = {
    "Ingeniería de Software": 10,
    "Ingeniería de Sistemas": 10,
    "Computación e Informática": 8,
    "Administración de Empresas": 10,
    "Contabilidad": 10,
    "Arquitectura": 10,
    "Ingeniería Civil": 10,
    "Ingeniería Industrial": 10,
    "Psicología": 10,
    "Enfermería": 10,
    "Derecho": 12,
    "Diseño Digital": 8,
}

RISK_COLORS = {
    "Alto": "#E5484D",
    "Medio": "#F5A524",
    "Bajo": "#22A06B",
}

OBJECTIVE_TEXT = (
    "Reducir en 20 % la tasa de deserción semestral mediante la identificación "
    "temprana y la intervención oportuna de estudiantes en riesgo."
)

