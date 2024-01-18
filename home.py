import streamlit as st

def home():
    

    st.title('Analis de .LAS - Version 1.0')
    st.write('## Bienvenido a la app de analisis de .LAS')
    st.write('### Creado por Angel Thomas')
    st.write('''Esta app fue creada para analizar de forma facil e intuitiva un .LAS generado por las cias de Wireline''')
    st.write('Para comenzar a usar la aplicación, cargue su archivo .LAS usando la opción de carga de archivos en la barra lateral. Una vez que haya hecho esto, puede navegar a las herramientas relevantes usando el menú de navegación.')
    st.write('\n')
    st.write('## Secciones')
    st.write('**Información del Encabezado:** Información del encabezado del archivo LAS.')
    st.write('**Información de datos:** Información sobre las curvas contenidas en el archivo LAS, incluidos nombres, estadísticas y valores de datos sin procesar.')
    st.write('**Visualización de datos:** Herramientas de visualización para ver los datos del archivo Las en un gráfico de registro, gráfico cruzado e histograma.')
    st.write('**Visualización de datos faltantes:** Las herramientas de visualización comprenden la extensión de los datos e identifican áreas con valores faltantes.')
    st.write('**Analisis de calidad de Cemento:** Seccion para determinar el estado del cemento en el pozo.')