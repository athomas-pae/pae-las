# app.py

import streamlit as st
import lasio
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import StringIO
from scipy.signal import savgol_filter
import numpy as np
import os
from fpdf import FPDF
from datetime import datetime

# Importar otros módulos
import home
import raw_data
import plotting
import header
import missingdata
import cbl
import las_q

# Funciones de CSS local
def local_css(file_name):
    with open(file_name) as f:
        st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)

# Clase PDF para generar el reporte
class PDF(FPDF):
    def __init__(self, logo_path, well_name):
        super().__init__()
        self.logo_path = logo_path
        self.well_name = well_name

    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, f'Reporte de Análisis de Calidad de Cemento - {self.well_name}', 0, 1, 'C')
        self.image(self.logo_path, 10, 8, 25)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_subtitle(self, subtitle):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, subtitle, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 8, body)
        self.ln()

    def add_image(self, image_path, x, y, width, height=None):
        self.image(image_path, x=x, y=y, w=width, h=height)

    def add_table(self, data, x_start, col_widths, row_height, max_rows=None):
        self.set_xy(x_start, self.get_y())
        self.set_font('Arial', '', 8)
        row_count = 0
        for row in data:
            if max_rows and row_count >= max_rows:
                break
            for item, col_width in zip(row, col_widths):
                self.cell(col_width, row_height, str(item), border=1, align='C')
            self.ln(row_height)
            self.set_x(x_start)
            row_count += 1
        if max_rows and row_count < len(data):
            self.add_page()
            self.add_table(data[row_count:], x_start, col_widths, row_height, max_rows)

    def add_cover(self):
        self.add_page()
        self.set_font('Arial', 'B', 20)
        self.cell(0, 40, 'Reporte de Análisis de Cemento en Pozos', 0, 1, 'C')
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, f'Pozo: {self.well_name}', 0, 1, 'C')
        self.cell(0, 10, f'Fecha: {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'C')
        self.ln(20)

def generate_report(well_data, toc_teorico, toc_calculado_rango, resultados_predominantes, tabla_predominantes, params, logo_path, well_name):
    pdf = PDF(logo_path, well_name)
    
    # Agregar portada
    pdf.add_cover()

    # Segunda página: Parámetros e Informe de Calidad de Cemento
    pdf.add_page()
    pdf.chapter_title('Introducción')
    pdf.chapter_subtitle('Parámetros del Usuario')
    params_text = f"""Amplitud de Cañería Libre Específica: {params['Amplitud Cañería Libre Específica']}
TOC Teórico: {params['TOC Teórico']}
Ampliación de Rango: {params['Ampliación de Rango']}"""
    pdf.chapter_body(params_text)

    pdf.chapter_title('Análisis de Calidad de Cemento')

    # Crear gráfico de relación entre calidad de cemento, CBL y profundidad
    fig, ax = plt.subplots(figsize=(4, 6))
    scatter = sns.scatterplot(data=well_data, x='CBL', y='DEPTH', hue='calidad_cemento', palette='viridis', s=10, ax=ax)
    ax.invert_yaxis()
    plt.axhline(y=toc_calculado_rango, color='blue', linestyle='--', label='TOC Calculado en el Rango')
    plt.axhline(y=toc_teorico, color='red', linestyle='--', label='TOC Teórico')
    plt.axhline(y=well_data['DEPTH'].min(), color='green', linestyle='--', label='Inicio del Rango Analizado')
    plt.axhline(y=well_data['DEPTH'].max(), color='orange', linestyle='--', label='Fin del Rango Analizado')
    plt.legend(fontsize='x-small')
    fig_path = os.path.join('/tmp', 'scatter_plot.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Añadir gráfico a la izquierda
    pdf.add_image(fig_path, x=10, y=pdf.get_y(), width=60, height=90)
    
    # Añadir tabla de resultados a la derecha
    pdf.set_xy(110, pdf.get_y())
    pdf.chapter_subtitle('Resultados de Calidad de Cemento en el Rango Especificado')
    rango_analizado = well_data[(well_data['DEPTH'] >= toc_teorico) & (well_data['DEPTH'] <= well_data['DEPTH'].max())]
    calidad_cemento_rango = rango_analizado['calidad_cemento'].value_counts(normalize=True) * 100
    calidad_cemento_tabla = [["Calidad de Cemento", "Porcentaje"]] + \
                            [[index, f"{value:.2f}%"] for index, value in calidad_cemento_rango.items()]
    pdf.add_table(calidad_cemento_tabla, x_start=110, col_widths=[45, 45], row_height=8)

    # Ajustar la posición para la conclusión
    pdf.ln(20)
    pdf.set_xy(10, pdf.get_y() + 30)

    pdf.chapter_subtitle('Conclusión del Análisis de Calidad de Cemento')
    conclusion_cemento = generate_conclusion(calidad_cemento_rango.idxmax(), calidad_cemento_rango.max(), toc_calculado_rango)
    pdf.chapter_body(conclusion_cemento)

    # Tercera página: Análisis de Cemento vs Punzados
    pdf.add_page()
    pdf.chapter_title('Análisis de Cemento vs Punzados')

    # Crear gráfico de análisis de cemento vs punzados con los mismos parámetros que en la aplicación
    fig, ax = plt.subplots(figsize=(6, 8))
    cbl_smooth = savgol_filter(well_data['CBL'], window_length=5, polyorder=3)

    color = 'tab:red'
    ax.set_xlabel('Amplitud de CBL')
    ax.set_ylabel('Profundidad (DEPTH)')
    ax.plot(cbl_smooth, well_data['DEPTH'], color=color, label='CBL (Suavizado)', linewidth=0.5)
    ax.tick_params(axis='x', labelrotation=90)
    ax.invert_yaxis()

    # Ajustar la escala del eje y para que abarque todo el rango de profundidades
    max_depth = tabla_predominantes['BASE'].max() + params['Ampliación de Rango']
    min_depth = tabla_predominantes['TOPE'].min() - params['Ampliación de Rango']
    ax.set_xlim(0, 100)
    ax.set_ylim(max_depth, min_depth)

    # Añadir las zonas de análisis con colores
    for index, row in tabla_predominantes.iterrows():
        tope_rango = row['TOPE'] - params['Ampliación de Rango']
        base_rango = row['BASE'] + params['Ampliación de Rango']

        resultado_predominante = row['Resultado Predominante']
        color = 'green' if resultado_predominante == 'Bueno' else 'yellow' if resultado_predominante == 'Regular' else 'red'

        ax.axhspan(tope_rango, base_rango, alpha=0.3, color=color, label=f'Rango - {resultado_predominante}')

    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    fig_path = os.path.join('/tmp', 'range_analysis_plot.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Añadir gráfico a la izquierda
    pdf.add_image(fig_path, x=10, y=pdf.get_y(), width=60, height=90)

    # Añadir tabla a la derecha
    pdf.set_xy(110, pdf.get_y())
    pdf.chapter_subtitle('Nuevo DataFrame a partir de la tabla copiada')
    pdf.add_table(tabla_predominantes.values.tolist(), x_start=110, col_widths=[20, 20, 20], row_height=6)

    pdf.ln(20)
    pdf.set_xy(10, pdf.get_y() + 40)

    if 'Resultado Predominante' in tabla_predominantes.columns:
        pdf.chapter_subtitle('Conclusión del Análisis en el Rango Especificado')
        conclusion_rango = generate_conclusion(tabla_predominantes['Resultado Predominante'].mode()[0], None, None)
        pdf.chapter_body(conclusion_rango)
    else:
        st.error("La columna 'Resultado Predominante' no está presente en la tabla de datos.")
        pdf.chapter_body("No se pudo generar la conclusión debido a la falta de datos en la columna 'Resultado Predominante'.")

    # Generar el nombre del archivo con el formato deseado
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_filename = f'{well_name}_{date_str} - Reporte de calidad de cemento.pdf'
    report_path = os.path.join('/tmp', report_filename)
    pdf.output(report_path)

    return report_path

def generate_conclusion(calidad_predominante, porcentaje, toc_calculado_rango):
    if calidad_predominante == 'Bueno':
        conclusion = (
            f"El análisis de calidad de cemento en el rango especificado revela que la calidad predominante es "
            f"{calidad_predominante} con un {f'{porcentaje:.2f}%' if porcentaje is not None else ''} del total. "
            f"{f'El TOC calculado en el rango es {toc_calculado_rango:.2f} metros.' if toc_calculado_rango is not None else ''} "
            "Estos resultados sugieren que la integridad del cemento en este rango es excelente, lo que implica un sellado efectivo "
            "de la formación y una alta fiabilidad del pozo."
        )
    elif calidad_predominante == 'Regular':
        conclusion = (
            f"El análisis de calidad de cemento en el rango especificado revela que la calidad predominante es "
            f"{calidad_predominante} con un {f'{porcentaje:.2f}%' if porcentaje is not None else ''} del total. "
            f"{f'El TOC calculado en el rango es {toc_calculado_rango:.2f} metros.' if toc_calculado_rango is not None else ''} "
            "Estos resultados indican que la integridad del cemento en este rango es aceptable, pero podría requerir monitoreo adicional "
            "para asegurar la integridad a largo plazo del pozo."
        )
    elif calidad_predominante == 'Malo':
        conclusion = (
            f"El análisis de calidad de cemento en el rango especificado revela que la calidad predominante es "
            f"{calidad_predominante} con un {f'{porcentaje:.2f}%' if porcentaje is not None else ''} del total. "
            f"{f'El TOC calculado en el rango es {toc_calculado_rango:.2f} metros.' if toc_calculado_rango is not None else ''} "
            "Estos resultados sugieren que la integridad del cemento en este rango es deficiente, lo que podría implicar problemas "
            "potenciales de sellado y la necesidad de medidas correctivas para asegurar la integridad del pozo."
        )
    return conclusion

def safe_replace_comma(value):
    """Reemplaza comas por puntos si el valor es una cadena."""
    if isinstance(value, str):
        return value.replace(',', '.')
    return value

def convert_column_to_float(df, column_name):
    """Convierte una columna de un DataFrame a float, manejando cadenas con comas como separadores decimales."""
    df[column_name] = df[column_name].apply(safe_replace_comma).astype(float)

def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            bytes_data = uploaded_file.read()
            str_io = StringIO(bytes_data.decode('Windows-1252'))
            las_file = lasio.read(str_io)
            well_data = las_file.df()
            well_data['DEPTH'] = well_data.index

            # Identificar y renombrar variables específicas
            variable_mapping = {
                'CBLF': 'CBL',
                'AMP3FT': 'CBL',
                'AMP': 'CBL',
                'CBL': 'CBL'
            }

            # Renombrar las columnas según el mapeo
            well_data.rename(columns=variable_mapping, inplace=True)

            # Verificar si hay duplicados después de renombrar
            if 'CBL' in well_data.columns:
                # Priorizar la columna 'CBL' original y eliminar las demás
                cbl_columns = [col for col in well_data.columns if well_data[col].name == 'CBL']
                if len(cbl_columns) > 1:
                    # Eliminar todas las columnas CBL excepto la primera (que sería la original)
                    columns_to_keep = ['DEPTH'] + cbl_columns[:1]
                    well_data = well_data[columns_to_keep]
                else:
                    st.error("Error: No se pudo identificar la columna 'CBL'. Por favor, revise los datos.")
                    well_data = None

            # Verificar si la columna 'CBL' existe en los datos procesados
            if 'CBL' not in well_data.columns:
                st.error("La columna 'CBL' no está presente en los datos cargados.")
                st.write("Columnas disponibles:", well_data.columns.tolist())
                las_file = None
                well_data = None

        except UnicodeDecodeError as e:
            st.error(f"Error decoding log.las: {e}")
            las_file = None
            well_data = None
    else:
        las_file = None
        well_data = None

    return las_file, well_data

def main():
    st.set_page_config(layout="wide", page_title='Analisis de .LAS v1.0')

    local_css("style.css")

    st.sidebar.image("https://www.0800telefono.org/wp-content/uploads/2018/03/panamerican-energy.jpg", width=200)
    st.sidebar.write('# Explorador de .LAS')
    st.sidebar.write('Para comenzar a usar la app, cargar el .LAS en la parte inferior.')

    uploadedfile = st.sidebar.file_uploader(' ', type=['.las'])

    if uploadedfile:
        st.sidebar.success('Archivo subido correctamente!')
        las_file, well_data = load_data(uploadedfile)
        well_name = las_file.well.WELL.value
        st.sidebar.write(f'<b>Well Name</b>: {well_name}', unsafe_allow_html=True)

        st.sidebar.title('Menu')
        options = st.sidebar.radio('Seleccionar Opciones:', 
            ['Home', 'Informacion de Encabezado', 'Informacion de Datos', 'Visualizacion de Datos', 'Visualizacion de datos faltantes', 'Analisis de Calidad de Cemento', 'Analisis de Cortes', 'Calidad .LAS'])

        if options == 'Home':
            home.home()
        elif options == 'Informacion de Encabezado':
            header.header(las_file)
        elif options == 'Informacion de Datos':
            raw_data.raw_data(las_file, well_data)
        elif options == 'Visualizacion de Datos':
            plotting.plot(las_file, well_data)
        elif options == 'Visualizacion de datos faltantes':
            missingdata.missing(las_file, well_data)
        elif options == 'Analisis de Calidad de Cemento':
            cbl.cbl(las_file, well_data, well_name)  # Pasar well_name a la función
            st.write("Análisis de calidad de cemento completado.")

        elif options == 'Analisis de Cortes':
            # Llama a la función de análisis de cortes aquí
            pass
        elif options == 'Calidad .LAS':
            las_q.quality(las_file, well_data)

if __name__ == '__main__':
    main()
