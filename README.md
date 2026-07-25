# EduFuturo SAT 

Sistema de alerta temprana desarrollado para identificar estudiantes con posible riesgo de deserción académica mediante un modelo de aprendizaje automático **Random Forest**.

Proyecto académico del curso **Innovación y Transformación Digital**.

## Funciones principales

* Panel general de estudiantes.
* Registro de nuevos estudiantes.
* Identificación de niveles de riesgo.
* Evaluación automática de estudiantes pendientes.
* Probabilidad y confianza de cada predicción.
* Validación del algoritmo con datos conocidos.
* Matriz de confusión y métricas calculadas.
* Alertas para el seguimiento estudiantil.
* Generación de reportes.
* Historial de evaluaciones almacenado en SQLite.

## Cómo ejecutar el proyecto en Windows

### 1. Descargar el proyecto

1. Pulsa el botón verde **Code**.
2. Selecciona **Download ZIP**.
3. Extrae el archivo descargado.
4. Se recomienda colocar la carpeta en una ruta corta:

```text
C:\EduFuturo
```

### 2. Instalar Python

El equipo debe tener Python instalado.

Puede descargarse desde:

https://www.python.org/downloads/

Durante la instalación, se debe marcar la opción:

```text
Add Python to PATH
```

### 3. Iniciar EduFuturo

1. Abre la carpeta del proyecto.
2. Haz doble clic en:

```text
ejecutar.bat
```

3. En la primera ejecución, el sistema creará automáticamente el entorno virtual e instalará los componentes necesarios.
4. Espera a que EduFuturo se abra en el navegador.

> La primera ejecución requiere conexión a internet y puede tardar algunos minutos. Las siguientes ejecuciones serán más rápidas.

## Evaluar a los estudiantes pendientes

Cuando el sistema se encuentre abierto:

1. Entra en **Estudiantes no evaluados**.
2. Marca la casilla de confirmación.
3. Pulsa **Evaluar 84 estudiantes ahora**.
4. Espera a que finalice el procesamiento.

Al finalizar aparecerán tres pestañas:

* **Resumen:** presenta la cantidad de estudiantes procesados y la distribución de los resultados.
* **Detalle:** muestra la predicción, probabilidad, confianza y factores de cada estudiante.
* **Evidencia:** presenta las métricas calculadas y la matriz de confusión utilizada para comprobar el funcionamiento del modelo.

Cada evaluación queda registrada con su fecha, código de ejecución, probabilidades y resultados.

## Validación del algoritmo

El sistema contiene 420 registros:

* 336 estudiantes con resultado conocido.
* 84 estudiantes pendientes de evaluación.

Los casos conocidos se dividen en:

* 268 registros para entrenar el modelo.
* 68 registros para validar su desempeño.

Después de la validación, el modelo utiliza los datos disponibles para evaluar a los 84 estudiantes restantes. Las métricas se calculan durante la ejecución y no corresponden a valores colocados manualmente.

## Detener el sistema

Para cerrar completamente EduFuturo:

1. Regresa a la ventana negra que se abrió junto con el sistema.
2. Presiona `Ctrl + C` o cierra esa ventana.

## Solución de problemas

### El comando Python no se reconoce

Instala Python nuevamente y asegúrate de marcar:

```text
Add Python to PATH
```

### El navegador no se abre automáticamente

Abre manualmente esta dirección:

```text
http://localhost:8501
```

### Aparece un error por una ruta demasiado larga

Extrae el proyecto directamente en:

```text
C:\EduFuturo
```

### El sistema tarda en iniciar

En la primera ejecución se descargan e instalan las dependencias. No cierres la ventana mientras aparezca el mensaje de instalación.

## Tecnologías utilizadas

* Python
* Streamlit
* Pandas
* NumPy
* Scikit-learn
* Plotly
* SQLite
* Random Forest

## Estructura principal

```text
EduFuturo/
├── app.py
├── ejecutar.bat
├── requirements.txt
├── data/
├── src/
├── tests/
└── .streamlit/
```

## Uso académico

EduFuturo SAT fue desarrollado con fines académicos y demostrativos. Las predicciones sirven como apoyo para identificar casos que requieren seguimiento y no deben considerarse como una decisión definitiva sobre el estudiante.
