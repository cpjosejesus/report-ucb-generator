import pandas as pd
import os
import markdown
from reportlab.lib.units import inch

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


def add_header(canvas, doc):
    """Add UCB logo header to each page of the PDF report"""
    canvas.saveState()

    # Add UCB logo on the top left
    logo_path = "./logo/logo.png"

    if os.path.exists(logo_path):
        # Draw logo at top left, preserve aspect ratio
        canvas.drawImage(logo_path, 0.8*inch, doc.height + 0.5*inch,
                         width=1.5*inch, height=0.7*inch, preserveAspectRatio=True, mask='auto')

    # Add department text on the top right
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawRightString(doc.width + 0.5*inch, doc.height + 0.9*inch,
                           "Dirección Académica de Sede")

    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(doc.width + 0.5*inch, doc.height + 0.7*inch,
                           "Departamento de Desarrollo Curricular y Calidad Académica")

    canvas.restoreState()
