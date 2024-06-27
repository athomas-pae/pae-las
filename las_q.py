import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def quality(las_file, well_data):
    st.title('Control de Calidad de .LAS')

    if las_file is not None and well_data is not None:
        # Display summary statistics of well data
        st.write('### Estadísticas del archivo LAS')
        st.write(well_data.describe())

        # Display the dataframe
        st.write('### Datos del archivo LAS')
        st.dataframe(well_data)

        # Correlation matrix
        st.write('### Matriz de Correlación')
        corr_matrix = well_data.corr()
        fig, ax = plt.subplots(figsize=(20, 16))  # Aumenta el tamaño de la figura
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax, annot_kws={"size": 6}, fmt=".2f", linewidths=0.5)
        plt.xticks(rotation=90, ha='center', fontsize=8)
        plt.yticks(fontsize=8)
        st.pyplot(fig)

        # Histograms of the well data
        st.write('### Histogramas de datos LAS')
        for column in well_data.columns:
            fig, ax = plt.subplots()
            sns.histplot(well_data[column], bins=30, kde=True, ax=ax)
            ax.set_title(f'Histograma de {column}')
            st.pyplot(fig)
        
        # Scatter plots to visualize relationships
        st.write('### Gráficos de Dispersión')
        columns = list(well_data.columns)
        selected_x = st.selectbox('Seleccione el eje X', columns)
        selected_y = st.selectbox('Seleccione el eje Y', columns)

        fig, ax = plt.subplots()
        sns.scatterplot(x=well_data[selected_x], y=well_data[selected_y], ax=ax)
        ax.set_title(f'Dispersión de {selected_x} vs {selected_y}')
        st.pyplot(fig)
        
        # Checkbox to show or hide missing data
        if st.checkbox('Mostrar datos faltantes'):
            st.write('### Datos Faltantes')
            missing_data = well_data.isnull().sum()
            st.write(missing_data[missing_data > 0])
            
        # Basic CBL analysis assuming CBL is in the data
        if 'CBL' in well_data.columns:
            st.write('### Análisis básico de CBL')
            cbl_data = well_data['CBL']
            fig, ax = plt.subplots()
            sns.histplot(cbl_data, bins=30, kde=True, ax=ax)
            ax.set_title('Histograma de CBL')
            st.pyplot(fig)
            
            # Descriptive statistics for CBL
            st.write('Estadísticas descriptivas de CBL')
            st.write(cbl_data.describe())
            
            # Scatter plot of CBL vs Depth
            if 'DEPTH' in well_data.columns:
                fig, ax = plt.subplots()
                sns.scatterplot(x=well_data['DEPTH'], y=cbl_data, ax=ax)
                ax.set_title('CBL vs DEPTH')
                st.pyplot(fig)
                
    else:
        st.warning('No se ha cargado un archivo LAS válido.')
