import pandas as pd
import os
import markdown
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Add a variable to store the latest data
_latest_data = None


def process_columns(data):
    """Process the dataframe columns and return a clean version"""
    global _latest_data
    # Store the data for later use by get_data()
    _latest_data = data.copy()

    column_rename_mapping = {
        "1. EN LA PRIMERA SEMANA DE CLASES, ¿EL DOCENTE PRESENTÓ Y EXPLICÓ SU PLAN DE ASIGNATURA?": "plan_asignatura",
        '2. VALORA EL DESEMPEÑO DEL DOCENTE CON RELACIÓN A LOS SIGUIENTES CREITERIOS: [Es puntual y cumple con el horario de clase.]': 'puntualidad',
        '2. VALORA EL DESEMPEÑO DEL DOCENTE CON RELACIÓN A LOS SIGUIENTES CREITERIOS: [Promueve un ambiente cordial y de respeto mutuo.]': 'ambiente',
        '2. VALORA EL DESEMPEÑO DEL DOCENTE CON RELACIÓN A LOS SIGUIENTES CREITERIOS: [Demuestra disponibilidad y apertura para responder a dudas y/o consultas.]': 'disponibilidad',
        '2. VALORA EL DESEMPEÑO DEL DOCENTE CON RELACIÓN A LOS SIGUIENTES CREITERIOS: [Cumple con la planificación de la clase.]': 'planificación',
        '2. VALORA EL DESEMPEÑO DEL DOCENTE CON RELACIÓN A LOS SIGUIENTES CREITERIOS: [El desarrollo de la clase es ordenado, estructurado y se relaciona con lo avanzado.]': 'desarrollo',
        '2. VALORA EL DESEMPEÑO DEL DOCENTE CON RELACIÓN A LOS SIGUIENTES CREITERIOS: [Aplica estrategias y técnicas que ayudan a comprender mejor los contenidos.]': 'estrategias',
        '2. VALORA EL DESEMPEÑO DEL DOCENTE CON RELACIÓN A LOS SIGUIENTES CREITERIOS: [Sus explicaciones son claras y refuerzan lo aprendido.]': 'claridad',
        '2. VALORA EL DESEMPEÑO DEL DOCENTE CON RELACIÓN A LOS SIGUIENTES CREITERIOS: [Asigna tareas y/o actividades que me preparan para tener un rendimiento satisfactorio en la asignatura.]': 'tareas',
        '2. VALORA EL DESEMPEÑO DEL DOCENTE CON RELACIÓN A LOS SIGUIENTES CREITERIOS: [Constantemente brinda retroalimentación/información precisa, oportuna y constructiva de mis logros, fortalezas, debilidades y aspectos a mejorar, que me ayudan a progresar en mi desempeño académico.]': 'retroalimentación',
        "3. EN GENERAL, ¿CÓMO EVALUARÍAS EL DESEMPEÑO DEL DOCENTE?": "evaluacion_docente_general",
        "4. MENCIONA ASPECTOS POSITIVOS Y/O ASPECTOS EN LOS QUE EL DOCENTE NECESITA TRABAJAR PARA MEJORAR SU DESEMPEÑO.": "comentarios",
    }

    data.rename(columns=column_rename_mapping, inplace=True)

    return data


def get_data():
    """Return the original dataset."""
    global _latest_data
    if _latest_data is None:
        raise ValueError(
            "No data has been loaded yet. Please load data first.")
    return _latest_data


def analyze_data_q2(data):
    columns_to_analyze = [
        'puntualidad',  # puntualidad
        'ambiente',  # ambiente
        'disponibilidad',  # disponibilidad
        'planificación',  # planificación
        'desarrollo',  # desarrollo
        'estrategias',  # estrategias
        'claridad',  # claridad
        'tareas',  # tareas
        'retroalimentación',  # retroalimentación
    ]

    rating_summary = data.groupby(['DOCENTE', 'ASIGNATURA'])[columns_to_analyze].apply(
        lambda group: group.apply(lambda col: col.value_counts()).fillna(0)
    ).unstack(fill_value=0)
    return rating_summary


def save_figure_to_temp(fig, prefix="figure"):
    """
    Save a matplotlib figure to a temporary file and return the path.

    Parameters:
    -----------
    fig : matplotlib.figure.Figure
        The figure to save
    prefix : str
        Prefix for the filename
    dpi : int
        Resolution for the saved image

    Returns:
    --------
    str
        Path to the saved image file
    """
    # Create a unique filename
    temp_dir = "./images/"
    file_path = os.path.join(temp_dir, f"{prefix}.png")

    # Save the figure to the file
    fig.savefig(file_path)

    return file_path


def markdown_to_reportlab_html(markdown_text):
    """
    Convert markdown text to HTML that ReportLab can understand.

    Parameters:
    -----------
    markdown_text : str
        Markdown formatted text

    Returns:
    --------
    str
        HTML formatted text compatible with ReportLab's Paragraph
    """

    # Convert markdown to HTML
    html = markdown.markdown(markdown_text)

    # Clean up and adjust HTML for ReportLab compatibility

    # Replace <p> tags with line breaks
    html = html.replace('<p>', '').replace('</p>', '<br/><br/>')

    # Handle lists - ReportLab has limited list support
    html = html.replace('<ul>', '').replace('</ul>', '<br/>')
    html = html.replace('<ol>', '').replace('</ol>', '<br/>')
    html = html.replace('<li>', '• ').replace('</li>', '<br/>')

    # Handle headings
    html = html.replace('<h1>', '<b><font size="14">').replace(
        '</h1>', '</font></b><br/><br/>')
    html = html.replace('<h2>', '<b><font size="12">').replace(
        '</h2>', '</font></b><br/><br/>')
    html = html.replace('<h3>', '<b><font size="11">').replace(
        '</h3>', '</font></b><br/><br/>')
    html = html.replace('<h4>', '<b>').replace('</h4>', '</b><br/><br/>')

    # Handle emphasis
    # Bold and italic are already handled correctly by ReportLab

    # Handle code blocks - ReportLab doesn't have good support for these
    html = html.replace('<pre><code>', '<font face="Courier">').replace(
        '</code></pre>', '</font><br/>')

    # Handle blockquotes
    html = html.replace('<blockquote>', '<i>').replace(
        '</blockquote>', '</i><br/>')

    # Remove any double breaks at the end
    while html.endswith('<br/><br/>'):
        html = html[:-5]

    return html


def generate_ai_summary(docente, asignatura, comentarios_text):
    """
    Generate an AI summary of student comments using OpenAI's GPT-4o-mini model.

    Parameters:
    -----------
    docente : str
        Teacher name
    asignatura : str
        Subject name
    comentarios_text : str
        Text of comments to summarize

    Returns:
    --------
    tuple
        (success: bool, summary: str or error message: str)
    """

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = f"""
        Eres un asistente encargado de analizar comentarios de estudiantes sobre profesores y asignaturas.
        Tu tarea es leer los siguientes comentarios y generar un resumen conciso de los puntos clave mencionados.

        **Instrucción Importante: La respuesta DEBE estar escrita exclusivamente en español.**

        Comentarios de los estudiantes para el docente {docente} en la asignatura {asignatura}:
        {comentarios_text}

        Resumen de los comentarios de los estudiantes sobre el docente para la asignatura:
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente especializado en análisis de comentarios de evaluaciones docentes. Tus respuestas deben ser en español, concisas y enfocadas en extraer patrones relevantes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        # Get the response content
        summary = response.choices[0].message.content
        return True, summary

    except Exception as e:
        return False, f"Error calling OpenAI API: {str(e)}"
