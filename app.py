import streamlit as st
from load_css import local_css
import lasio
import pandas as pd
import missingno as mno
from io import StringIO

# Local Imports
import home
import raw_data
import plotting
import header
import missingdata
import cbl

st.set_page_config(layout="wide", page_title='Analisis de .LAS v1.0')

local_css("style.css")


def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            bytes_data = uploaded_file.read()
            str_io = StringIO(bytes_data.decode('Windows-1252'))
            las_file = lasio.read(str_io)
            well_data = las_file.df()
            well_data['DEPTH'] = well_data.index

            # Identify and rename specific variables
            variable_mapping = {
                'CBLF': 'CBL',
                'AMP3FT': 'CBL'
            }

            well_data.rename(columns=variable_mapping, inplace=True)

        except UnicodeDecodeError as e:
            st.error(f"Error decoding log.las: {e}")
            las_file = None
            well_data = None
    else:
        las_file = None
        well_data = None

    return las_file, well_data


def missing_data():
    st.title('Informacion Faltante')
    missing_data = well_data.copy()
    missing = px.area(well_data, x='DEPTH', y='DT')
    st.plotly_chart(missing)

# Sidebar Options & File Uplaod
las_file=None
st.sidebar.image("https://www.0800telefono.org/wp-content/uploads/2018/03/panamerican-energy.jpg", width=300)
st.sidebar.write('# Explorador de .LAS')
st.sidebar.write('Para comenzar a usar la app, cargar el .LAS en la parte inferior.')

uploadedfile = st.sidebar.file_uploader(' ', type=['.las'])

if uploadedfile:
    st.sidebar.success('Archivo subido correctamente!')
    las_file, well_data = load_data(uploadedfile)
    st.sidebar.write(f'<b>Well Name</b>: {las_file.well.WELL.value}',unsafe_allow_html=True)


# Sidebar Navigation
st.sidebar.title('Menu')
options = st.sidebar.radio('Seleccionar Opciones:', 
    ['Home', 'Informacion de Encabezado', 'Informacion de Datos', 'Visualizacion de Datos', 'Visualizacion de datos faltantes', 'Analisis de Calidad de Cemento'])

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
    cbl.cbl(las_file, well_data)