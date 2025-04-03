import streamlit as st
import sys
from streamlit.web import cli as stcli
from streamlit import runtime
import plotly.express as px
import plotly.graph_objects as go
from openpyxl import load_workbook
import pandas as pd
import utils
import os
import base64
from datetime import datetime
import tempfile
import io
import subprocess
import matplotlib.pyplot as plt  # Add matplotlib import
import markdown
# Try to import pdfkit but prepare for fallback
try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

# Try to import reportlab (fallback PDF generator)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Try to find wkhtmltopdf path
comments = {}


def find_wkhtmltopdf():
    try:
        # Try to find it using which (Unix) or where (Windows)
        if os.name == 'nt':  # Windows
            process = subprocess.Popen(['where', 'wkhtmltopdf'],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:  # Unix/Linux/Mac
            process = subprocess.Popen(['which', 'wkhtmltopdf'],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        output, _ = process.communicate()
        path = output.decode().strip()

        if path and os.path.exists(path):
            return path

        # Common installation paths
        common_paths = [
            '/usr/local/bin/wkhtmltopdf',
            '/usr/bin/wkhtmltopdf',
            'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe',
            'C:\\Program Files (x86)\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
        ]

        for p in common_paths:
            if os.path.exists(p):
                return p

        return None
    except:
        return None


# Check for wkhtmltopdf and configure - but DO NOT use any Streamlit commands here
WKHTMLTOPDF_PATH = find_wkhtmltopdf()
if PDFKIT_AVAILABLE and WKHTMLTOPDF_PATH:
    PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    PDF_GENERATOR = "pdfkit"
elif REPORTLAB_AVAILABLE:
    PDF_GENERATOR = "reportlab"
else:
    PDF_GENERATOR = None


def create_pdf_download_link(pdf_bytes, filename="report.pdf"):
    """Generate a download link for a PDF file"""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF Report</a>'
    return href


def generate_pdf_report(data, docente, docente_data):
    """Generate a PDF report for a specific docente"""
    if PDF_GENERATOR == "reportlab":
        return generate_pdf_with_reportlab(data, docente, docente_data)
    else:
        st.error("No PDF generation method available")
        return None


def generate_pdf_with_reportlab(data, docente, docente_data):
    """Generate a PDF report using reportlab (simplified version)"""
    buffer = io.BytesIO()
    page_width, page_height = letter
    margin = 0.75 * inch
    content_width = page_width - (2 * margin)
    try:
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title style
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            alignment=1,  # Center
            textColor=colors.darkblue,
            spaceAfter=0.3*inch
        )

        intro_note_style = ParagraphStyle(
            'IntroNote',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',  # Italic font
            textColor=colors.darkslategray,
            alignment=4,  # Justified
            spaceBefore=0.1*inch,
            spaceAfter=0.3*inch,
            firstLineIndent=20,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=10,
            borderRadius=5,
        )

        # Section style
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            textColor=colors.darkblue,
            spaceBefore=0.2*inch,
            spaceAfter=0.1*inch
        )

        # Add title and header
        elements.append(
            Paragraph(f"Evaluación Docente: {docente}", title_style))

        elements.append(Spacer(1, 0.25*inch))
        for (teacher, asignatura), row in docente_data.iterrows():
            elements.append(Paragraph(
                f"<b>Asignatura:</b> {asignatura}", styles['Normal']))
            elements.append(Spacer(1, 0.15*inch))

        elements.append(Paragraph(
            f"Generado el: {datetime.now().strftime('%d de %B de %Y')}", styles['Italic']))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            "<b>Estimado/a Docente:</b>", styles['Normal']))
        elements.append(Paragraph(
            "La evaluación inicial del desempeño docente constituye una herramienta esencial para garantizar la calidad académica, "
            "permitiendo identificar tanto las fortalezas como las áreas de mejora en las prácticas pedagógicas al inicio del semestre. "
            "Este proceso contribuye al desarrollo profesional del docente y al fortalecimiento de la experiencia de aprendizaje de los "
            "estudiantes a lo largo del semestre, favoreciendo un entorno académico de excelencia y promoviendo la mejora continua en "
            "los métodos de enseñanza.",
            styles['Normal']
        ))

        elements.append(Spacer(1, 0.1*inch))
        # 1. Introduction section
        # elements.append(Paragraph("Introducción", section_style))
        # elements.append(Paragraph(
        #     f"Este informe presenta los resultados de la evaluación docente para {docente}. "
        #     "La evaluación fue realizada por los estudiantes a través de encuestas estandarizadas "
        #     "que evalúan diferentes aspectos del desempeño docente.",
        #     styles['Normal']
        # ))
        # elements.append(Spacer(1, 0.15*inch))

        # 2. Resultados de la evaluacion section
        elements.append(
            Paragraph("Resultados de la Evaluación", section_style))
        elements.append(Paragraph(
            "En base a las respuestas de los estudiantes, se presentan los hallazgos agrupados en los siguientes criterios:", styles['Normal']))

        # Add criteria list
        criteria_list = [
            "Presentación del Plan de Asignatura.",
            "Puntualidad y cumplimiento de horario.",
            "Ambiente de respeto y cordialidad.",
            "Disponibilidad para resolver dudas.",
            "Organización y estructura de la clase.",
            "Aplicación de estrategias didácticas.",
            "Claridad en la enseñanza.",
            "Asignación de tareas y actividades académicas.",
            "Calidad de la retroalimentación.",
            "Evaluación general del docente."
        ]

        for criterion in criteria_list:
            elements.append(Paragraph(f"• {criterion}",
                                      ParagraphStyle('BulletStyle', parent=styles['Normal'], leftIndent=20)))

        elements.append(Spacer(1, 0.2*inch))

        # Add Niveles de logro section
        # elements.append(Paragraph("Niveles de logro:", section_style))

        # achievement_levels = [
        #     ("Excelente", "green", "El docente demuestra un dominio excepcional en este criterio. Cumple y supera consistentemente las expectativas establecidas, garantizando una experiencia de aprendizaje óptima para los estudiantes. Se observa un impacto positivo y sostenido, promoviendo un entorno académico motivador y efectivo."),
        #     ("Bueno", "blue", "El docente cumple adecuadamente con este criterio, mostrando un desempeño sólido y constante. Aunque puede haber oportunidades de mejora, su impacto en el proceso de enseñanza-aprendizaje es favorable y responde a las expectativas de calidad académica."),
        #     ("Regular", "orange", "El docente muestra cumplimiento parcial en este criterio, con áreas de mejora evidentes. Su desempeño es funcional, pero presenta inconsistencias que pueden afectar la experiencia educativa de los estudiantes. Se recomienda un plan de acompañamiento o estrategias de fortalecimiento."),
        #     ("Algo Deficiente", "red", "Se identifican debilidades significativas en este criterio, impactando negativamente en la dinámica de enseñanza-aprendizaje. El docente requiere intervención y apoyo inmediato para optimizar su desempeño y garantizar una mejor experiencia académica para los estudiantes."),
        #     ("Totalmente Deficiente", "red", "El docente no cumple con las expectativas mínimas en este criterio, lo que compromete la calidad del proceso educativo. Es imprescindible un plan de mejora urgente, con acciones correctivas específicas y seguimiento continuo.")
        # ]

        # for level, color, description in achievement_levels:
        #     elements.append(Paragraph(
        #         f"<b><font color='{color}'>{level}:</font></b> {description}",
        #         ParagraphStyle(
        #             'LevelStyle', parent=styles['Normal'], spaceAfter=10, leftIndent=10)
        #     ))

        # elements.append(Spacer(1, 0.2*inch))

        # # Add UCB logo/image
        # try:
        #     elements.append(Paragraph("UCB Teacher Evaluation System",
        #                               ParagraphStyle(
        #                                   'MidTitle',
        #                                   parent=styles['Heading3'],
        #                                   alignment=1,  # Center
        #                                   textColor=colors.darkblue
        #                               )))

        #     image_path = "/Users/josejesuscp/Workspace/reports-ucb/output.png"
        #     if os.path.exists(image_path):
        #         elements.append(Spacer(1, 0.2*inch))
        #         img = Image(image_path, width=5*inch)
        #         img.hAlign = 'CENTER'  # Center the image
        #         elements.append(img)
        #         elements.append(Spacer(1, 0.2*inch))
        # except Exception as e:
        #     elements.append(
        #         Paragraph(f"Could not add image: {str(e)}", styles['Normal']))

        # Add a separator
        elements.append(Paragraph("<hr/>", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))

        # For each subject, add the specific sections
        for (teacher, asignatura), row in docente_data.iterrows():
            # Add subject heading
            subject_style = ParagraphStyle(
                'SubjectTitle',
                parent=styles['Heading2'],
                textColor=colors.darkblue,
                borderColor=colors.darkblue,
                borderWidth=1,
                borderPadding=5,
                borderRadius=2,
                spaceAfter=0.2*inch
            )
            elements.append(PageBreak())

            elements.append(
                Paragraph(f"Asignatura: {asignatura}", subject_style))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("Plan de Asignatura", section_style))
            docente_asignatura_data = data[(data['DOCENTE'] == docente) &
                                           (data['ASIGNATURA'] == asignatura)]

            if 'plan_asignatura' in docente_asignatura_data.columns:
                plan_counts = docente_asignatura_data['plan_asignatura'].value_counts(
                ).sort_index()

                # Create a new figure for plan_asignatura counts
                fig_plan, ax_plan = plt.subplots(figsize=(10, 6))
                plan_counts.plot(kind='bar', ax=ax_plan)
                plt.title(f'Plan Asignatura Counts: {docente} - {asignatura}')
                plt.xlabel('Plan Asignatura Responses')
                plt.ylabel('Count')
                plt.xticks(rotation=45)
                plt.tight_layout()

                plan_img_path = utils.save_figure_to_temp(
                    fig_plan, f"plan_{docente}_{asignatura}")
                if os.path.exists(plan_img_path):
                    max_img_width = content_width * 0.9

                    elements.append(Spacer(1, 0.2*inch))
                    img = Image(plan_img_path, width=max_img_width *
                                0.8, height=0.6*content_width)
                    img.hAlign = 'CENTER'  # Center the image
                    elements.append(img)
                    elements.append(Spacer(1, 0.2*inch))

                plt.close(fig_plan)

            elements.append(PageBreak())

            elements.append(Paragraph("Desempeno del docente", section_style))

            ratings = row.unstack()

            # Plot the data
            fig, ax = plt.subplots(figsize=(10, 6))
            ratings.plot(kind='bar', ax=ax)
            plt.title(
                f'Rating Summary for {docente} - {asignatura}')
            plt.xlabel('Rating Categories')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            plt.tight_layout()
            desempeno_img_path = utils.save_figure_to_temp(
                fig, f"desempeno_{docente}_{asignatura}")

            if os.path.exists(desempeno_img_path):
                max_img_width = content_width * 0.9

                elements.append(Spacer(1, 0.2*inch))
                img = Image(desempeno_img_path, width=max_img_width *
                            0.8, height=0.6*content_width)
                img.hAlign = 'CENTER'  # Center the image
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))

            plt.close(fig)

            elements.append(PageBreak())

            elements.append(
                Paragraph("Distribucion general de la evaluacion docente", section_style))
            # Filter the original data for this docente and asignatura
            docente_asignatura_data = data[(data['DOCENTE'] == docente) & (
                data['ASIGNATURA'] == asignatura)]

            # Count occurrences of each rating in evaluacion_docente_general
            if 'evaluacion_docente_general' in docente_asignatura_data.columns:
                general_eval_counts = docente_asignatura_data['evaluacion_docente_general'].value_counts(
                ).sort_index()

                # Create a new figure for general evaluation counts
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                general_eval_counts.plot(kind='bar', ax=ax2)
                plt.title(
                    f'Evaluación General del Docente: {docente} - {asignatura}')
                plt.xlabel('Evaluación')
                plt.ylabel('Cantidad')
                plt.xticks(rotation=45)
                plt.tight_layout()

                general_img_path = utils.save_figure_to_temp(
                    fig2, f"general_{docente}_{asignatura}")

                if os.path.exists(general_img_path):
                    max_img_width = content_width * 0.9

                    elements.append(Spacer(1, 0.2*inch))
                    img = Image(general_img_path, width=max_img_width *
                                0.8, height=0.6*content_width)
                    img.hAlign = 'CENTER'  # Center the image
                    elements.append(img)
                    elements.append(Spacer(1, 0.2*inch))

                plt.close(fig2)  # Close the figure to free memory

            elements.append(PageBreak())

            elements.append(
                Paragraph("Resumen Generado por IA", section_style))

            if 'comentarios' in data.columns:
                try:
                    # Get all comments for this teacher and subject
                    docente_comments = data[(data['DOCENTE'] == docente) &
                                            (data['ASIGNATURA'] == asignatura)]['comentarios'].dropna()

                    if not docente_comments.empty:
                        comentarios_text = '.'.join(
                            docente_comments)

                        # Display a spinner while getting the summary
                        with st.spinner("Generating comments summary..."):
                            # API call to local LLM
                            import requests
                            import json
                            import re

                            url = "http://localhost:11434/api/generate"
                            headers = {
                                "accept": "application/json",
                                "Content-Type": "application/json"
                            }

                            prompt = f"""
                            Eres un asistente encargado de analizar comentarios de estudiantes sobre profesores y asignaturas.
                            Tu tarea es leer los siguientes comentarios y generar un resumen conciso de los puntos clave mencionados.

                            **Instrucción Importante: La respuesta DEBE estar escrita exclusivamente en español.**

                            Comentarios de los estudiantes para el docente {docente} en la asignatura {asignatura}:
                            {comentarios_text}

                            Resumen de los comentarios de los estudiantes sobre el docente para la asignatura:
                            """

                            payload = {
                                "model": "deepseek-r1:8b",
                                "prompt": prompt,
                                "temperature": 0.01,
                                "stream": False
                            }

                            try:
                                response = requests.post(
                                    url, json=payload, headers=headers)

                                if response.status_code == 200:
                                    response_text = response.text
                                    data_res = json.loads(
                                        response_text)
                                    summary = data_res["response"]
                                    cleaned_response = re.sub(
                                        r'<think>.*?</think>', '', summary, flags=re.DOTALL).strip()

                                    formatted_html = utils.markdown_to_reportlab_html(
                                        cleaned_response)

                                    html = markdown.markdown(cleaned_response)

                                    elements.append(Paragraph(
                                        formatted_html,
                                        ParagraphStyle(
                                            'LevelStyle', parent=styles['Normal'], spaceAfter=10, leftIndent=10)
                                    ))

                                else:
                                    st.error(
                                        f"Failed to generate summary. Status code: {response.status_code}")

                                    # Still show the raw comments
                                    with st.expander("View Original Comments"):
                                        for i, comment in enumerate(docente_comments):
                                            st.write(
                                                f"**Comment {i+1}:** {comment}")
                            except Exception as e:
                                st.error(
                                    f"Error connecting to local LLM API: {e}")
                                st.info(
                                    "Make sure your local LLM service is running at http://localhost:1147")

                                # Show raw comments as fallback
                                with st.expander("View Original Comments"):
                                    for i, comment in enumerate(docente_comments):
                                        st.write(
                                            f"**Comment {i+1}:** {comment}")
                    else:
                        st.info(
                            "No comments available for this teacher and subject.")
                except Exception as e:
                    st.error(f"Error processing comments: {e}")
            else:
                st.info("No 'comentarios' column found in the data.")

            elements.append(Spacer(1, 0.2*inch))

        # Add signature section for two people
        elements.append(Spacer(1, 1*inch))  # Space for signatures

        # Create a table for signatures
        signature_data = [
            ['________________________', '________________________'],
            ['\nLic. Vany Rosales \n Encargada de Calidad Academica',
             'VoBo Lic. Patricia Cabrera\n Jefe del Departamento de Diseño Curricular y \n Calidad Académica a.i.']
        ]
        signature_table = Table(signature_data, colWidths=[
                                2.75*inch, 2.75*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ]))
        elements.append(signature_table)

        # Build the PDF
        doc.build(elements)

        # Get the PDF content
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes
    except Exception as e:
        st.error(f"Error generating PDF with reportlab: {e}")
        buffer.close()
        return None


def main():
    # IMPORTANT: This must be the first Streamlit command
    st.set_page_config(layout="wide", page_title="Teacher Evaluation Reports")

    # Now display PDF generator warnings AFTER set_page_config
    if PDF_GENERATOR == "reportlab":
        st.sidebar.warning(
            "Using ReportLab for PDF generation (simplified report)")
    elif PDF_GENERATOR is None:
        st.sidebar.error("No PDF generation library available")

    st.title("Teacher Evaluation Dashboard")
    menu = ["Home", "Excel"]

    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Home")
        st.subheader("Teacher Evaluation Reports")
        file_name = st.file_uploader("Upload Excel with evaluation data")
        if file_name:
            df = pd.read_excel(file_name, engine="openpyxl")
            data = utils.process_columns(df)

            data_q2 = utils.analyze_data_q2(data)

            # Get unique docentes for filtering
            docentes = sorted(list(set([idx[0] for idx in data_q2.index])))

            # Add filter in sidebar
            selected_docente = st.sidebar.selectbox(
                "Select Teacher (Docente)",
                ["All"] + docentes
            )

            # Display overview data
            with st.expander("View Raw Data"):
                st.dataframe(data_q2)

            # Filter data based on selection
            if selected_docente != "All":
                filtered_data = data_q2[data_q2.index.get_level_values(
                    0) == selected_docente]
                docentes_to_show = [selected_docente]
            else:
                filtered_data = data_q2
                docentes_to_show = docentes

            # Add a button to generate all PDF reports at once
            if st.sidebar.button("Generate All PDF Reports"):
                with st.spinner("Generating PDFs for all teachers..."):
                    for doc in docentes:
                        doc_data = data_q2[data_q2.index.get_level_values(
                            0) == doc]
                        pdf_bytes = generate_pdf_report(data, doc, doc_data)
                        if pdf_bytes:
                            st.sidebar.markdown(
                                create_pdf_download_link(
                                    pdf_bytes, f"{doc}_report.pdf"),
                                unsafe_allow_html=True
                            )
                st.sidebar.success("All reports generated!")

    elif choice == "Excel":
        st.subheader("Teacher Evaluation Reports")
        file_name = st.file_uploader("Upload Excel with evaluation data")
        if file_name:
            try:
                xl_file = pd.ExcelFile(file_name)
                df = pd.read_excel(file_name, engine="openpyxl")
                data = utils.process_columns(df)

                data_q2 = utils.analyze_data_q2(data)

                # Get unique docentes for filtering
                docentes = sorted(list(set([idx[0] for idx in data_q2.index])))

                # Add filter in sidebar
                selected_docente = st.sidebar.selectbox(
                    "Select Teacher (Docente)",
                    ["All"] + docentes
                )

                # Display overview data
                with st.expander("View Raw Data"):
                    st.dataframe(data_q2)

                # Filter data based on selection
                if selected_docente != "All":
                    filtered_data = data_q2[data_q2.index.get_level_values(
                        0) == selected_docente]
                    docentes_to_show = [selected_docente]
                else:
                    filtered_data = data_q2
                    docentes_to_show = docentes

                # Add a button to generate all PDF reports at once
                if st.sidebar.button("Generate All PDF Reports"):
                    with st.spinner("Generating PDFs for all teachers..."):
                        for doc in docentes:
                            doc_data = data_q2[data_q2.index.get_level_values(
                                0) == doc]
                            pdf_bytes = generate_pdf_report(doc, doc_data)
                            if pdf_bytes:
                                st.sidebar.markdown(
                                    create_pdf_download_link(
                                        pdf_bytes, f"{doc}_report.pdf"),
                                    unsafe_allow_html=True
                                )
                    st.sidebar.success("All reports generated!")

                # Create reports for each docente
                for docente in docentes_to_show:
                    st.markdown(f"## 👨‍🏫 Teacher: {docente}")

                    # Generate PDF report button
                    docente_data = data_q2[data_q2.index.get_level_values(
                        0) == docente]
                    if st.button(f"Generate PDF Report", key=f"pdf_{docente}"):
                        with st.spinner("Generating PDF..."):
                            pdf_bytes = generate_pdf_report(
                                docente, docente_data)
                            if pdf_bytes:
                                st.markdown(
                                    create_pdf_download_link(
                                        pdf_bytes, f"{docente}_report.pdf"),
                                    unsafe_allow_html=True
                                )

                    # For each subject taught by this docente
                    for (_, asignatura), row in docente_data.iterrows():
                        st.markdown(f"### 📚 Subject: {asignatura}")

                        # Add plan_asignatura visualization
                        st.subheader("Plan Asignatura Rating Distribution")

                        # Filter the original data for this docente and asignatura
                        docente_asignatura_data = data[(data['DOCENTE'] == docente) &
                                                       (data['ASIGNATURA'] == asignatura)]

                        # Count occurrences of each rating in plan_asignatura
                        if 'plan_asignatura' in docente_asignatura_data.columns:
                            plan_counts = docente_asignatura_data['plan_asignatura'].value_counts(
                            ).sort_index()

                            # Create a new figure for plan_asignatura counts
                            fig_plan, ax_plan = plt.subplots(figsize=(10, 6))
                            plan_counts.plot(kind='bar', ax=ax_plan)
                            plt.title(
                                f'Plan Asignatura Counts: {docente} - {asignatura}')
                            plt.xlabel('Plan Asignatura Responses')
                            plt.ylabel('Count')
                            plt.xticks(rotation=45)
                            plt.tight_layout()

                            # Display in Streamlit
                            st.pyplot(fig_plan)
                            # Close the figure to free memory
                            plt.close(fig_plan)
                        else:
                            st.info(
                                "No 'plan_asignatura' column found in the data")

                        # Create visualization
                        ratings = row.unstack()
                        color_map = {
                            'Excelente': 'green',
                            'Bueno': 'blue',
                            'Regular': 'yellow',
                            'Algo Deficiente': 'orange',
                            'Totalmente Deficiente': 'red',
                        }

                        # Plot the data
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ratings.plot(kind='bar', ax=ax, color=[
                                     "blue", "orange", "green", "red", "yellow"])
                        plt.title(
                            f'Rating Summary for {docente} - {asignatura}')
                        plt.xlabel('Rating Categories')
                        plt.ylabel('Count')
                        plt.xticks(rotation=45)
                        plt.tight_layout()

                        # Display in Streamlit
                        st.pyplot(fig)
                        plt.close(fig)  # Close the figure to free memory

                        # Add general evaluation count visualization
                        st.subheader(
                            "Distribution of General Evaluation Ratings")

                        # Filter the original data for this docente and asignatura
                        docente_asignatura_data = data[(data['DOCENTE'] == docente) & (
                            data['ASIGNATURA'] == asignatura)]

                        # Count occurrences of each rating in evaluacion_docente_general
                        if 'evaluacion_docente_general' in docente_asignatura_data.columns:
                            general_eval_counts = docente_asignatura_data['evaluacion_docente_general'].value_counts(
                            ).sort_index()

                            # Create a new figure for general evaluation counts
                            fig2, ax2 = plt.subplots(figsize=(10, 6))
                            general_eval_counts.plot(kind='bar', ax=ax2)
                            plt.title(
                                f'Evaluación General del Docente: {docente} - {asignatura}')
                            plt.xlabel('Evaluación')
                            plt.ylabel('Cantidad')
                            plt.xticks(rotation=45)
                            plt.tight_layout()

                            # Display in Streamlit
                            st.pyplot(fig2)
                            plt.close(fig2)  # Close the figure to free memory
                        else:
                            st.info(
                                "No 'evaluacion_docente_general' column found in the data")

                        st.markdown("---")  # Add a separator between subjects

                        # Add comments analysis section
                        st.subheader("🗣️ Student Comments Analysis")

                        # Filter comments for this docente and asignatura
                        if 'comentarios' in data.columns:
                            try:
                                # Get all comments for this teacher and subject
                                docente_comments = data[(data['DOCENTE'] == docente) &
                                                        (data['ASIGNATURA'] == asignatura)]['comentarios'].dropna()

                                if not docente_comments.empty:
                                    comentarios_text = '.'.join(
                                        docente_comments)

                                    # Display a spinner while getting the summary
                                    with st.spinner("Generating comments summary..."):
                                        # API call to local LLM
                                        import requests
                                        import json
                                        import re

                                        url = "http://localhost:11434/api/generate"
                                        headers = {
                                            "accept": "application/json",
                                            "Content-Type": "application/json"
                                        }

                                        prompt = f"""
                                        Eres un asistente encargado de analizar comentarios de estudiantes sobre profesores y asignaturas.
                                        Tu tarea es leer los siguientes comentarios y generar un resumen conciso de los puntos clave mencionados.

                                        **Instrucción Importante: La respuesta DEBE estar escrita exclusivamente en español.**

                                        Comentarios de los estudiantes para el docente {docente} en la asignatura {asignatura}:
                                        {comentarios_text}

                                        Resumen de los comentarios de los estudiantes sobre el docente para la asignatura:
                                        """

                                        payload = {
                                            "model": "deepseek-r1:8b",
                                            "prompt": prompt,
                                            "temperature": 0.1,
                                            "stream": False
                                        }

                                        try:
                                            response = requests.post(
                                                url, json=payload, headers=headers)

                                            if response.status_code == 200:
                                                response_text = response.text
                                                data_res = json.loads(
                                                    response_text)
                                                summary = data_res["response"]
                                                cleaned_response = re.sub(
                                                    r'<think>.*?</think>', '', summary, flags=re.DOTALL).strip()

                                                # Display the summary in a nice format
                                                st.write(
                                                    "**AI-Generated Summary of Student Comments:**")
                                                st.info(cleaned_response)

                                                # Show raw comments in an expander
                                                with st.expander("View Original Comments"):
                                                    for i, comment in enumerate(docente_comments):
                                                        st.write(
                                                            f"**Comment {i+1}:** {comment}")
                                            else:
                                                st.error(
                                                    f"Failed to generate summary. Status code: {response.status_code}")

                                                # Still show the raw comments
                                                with st.expander("View Original Comments"):
                                                    for i, comment in enumerate(docente_comments):
                                                        st.write(
                                                            f"**Comment {i+1}:** {comment}")
                                        except Exception as e:
                                            st.error(
                                                f"Error connecting to local LLM API: {e}")
                                            st.info(
                                                "Make sure your local LLM service is running at http://localhost:1147")

                                            # Show raw comments as fallback
                                            with st.expander("View Original Comments"):
                                                for i, comment in enumerate(docente_comments):
                                                    st.write(
                                                        f"**Comment {i+1}:** {comment}")
                                else:
                                    st.info(
                                        "No comments available for this teacher and subject.")
                            except Exception as e:
                                st.error(f"Error processing comments: {e}")
                        else:
                            st.info("No 'comentarios' column found in the data.")

            except Exception as e:
                st.error(f"Error processing file: {e}")
                st.info("Please make sure your Excel file has the expected format.")


if __name__ == "__main__":
    if runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
