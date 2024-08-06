import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import StringIO
from scipy.signal import savgol_filter
import numpy as np
import os
from app import generate_report  # Importar la función desde app.py

def verificar_calidad_cemento(row, amplitud_caneria_libre_especifica):
    limite_amplitud_cbl_bueno = 0.1 * amplitud_caneria_libre_especifica
    if row['CBL'] < limite_amplitud_cbl_bueno:
        return "Bueno"
    elif row['CBL'] > 0.5 * amplitud_caneria_libre_especifica:
        return "Malo"
    elif 0.1 * row['CBL'] <= row['CBL'] <= 0.5 * amplitud_caneria_libre_especifica:
        return "Regular"
    elif row['CBL'] == 0.0:
        return "SD"
    else:
        return "Regular"

def cargar_tabla_copiada(tabla_copiada):
    df1 = pd.read_csv(StringIO(tabla_copiada), delimiter='\t', header=None)
    df1.columns = ['TOPE', 'BASE']
    return df1 

def safe_replace_comma(value):
    """Reemplaza comas por puntos si el valor es una cadena."""
    if isinstance(value, str):
        return value.replace(',', '.')
    return value

def convert_column_to_float(df, column_name):
    """Convierte una columna de un DataFrame a float, manejando cadenas con comas como separadores decimales."""
    df[column_name] = df[column_name].apply(safe_replace_comma).astype(float)

def cbl(las_file, well_data, well_name):
    st.title('Análisis de Calidad de Cemento')

    if las_file is not None:
        amplitud_caneria_libre_especifica = st.sidebar.text_input('Amplitud de Cañería Libre Específica', '72')
        toc_teorico = st.sidebar.text_input('TOC Teórico', '1500')
        ampliacion_rango = st.sidebar.selectbox('Ampliación de Rango', options=[5, 10, 15, 20])
        amplitud_caneria_libre_especifica = float(amplitud_caneria_libre_especifica)
        toc_teorico = float(toc_teorico)

        well_data['calidad_cemento'] = well_data.apply(verificar_calidad_cemento, args=(amplitud_caneria_libre_especifica,), axis=1)
        rango_analizado = well_data[(well_data['DEPTH'] >= toc_teorico) & (well_data['DEPTH'] <= well_data['DEPTH'].max())]

        toc_candidates_rango = rango_analizado[rango_analizado['calidad_cemento'] == 'Malo']
        toc_candidates_rango = toc_candidates_rango[toc_candidates_rango['CBL'] > 10].nlargest(10, 'DEPTH')['DEPTH']
        toc_calculado_rango = toc_candidates_rango.mean()

        if toc_teorico > toc_calculado_rango:
            st.warning("El TOC teórico es mayor que el TOC calculado en el rango. Verifique los valores ingresados.")

        fig, ax = plt.subplots(figsize=(6, 10))
        scatter = sns.scatterplot(data=well_data, x='CBL', y='DEPTH', hue='calidad_cemento', palette='viridis', s=30, ax=ax)
        ax.invert_yaxis()
        plt.axhline(y=toc_calculado_rango, color='blue', linestyle='--', label='TOC Calculado en el Rango')
        plt.axhline(y=rango_analizado['DEPTH'].min(), color='green', linestyle='--', label='Inicio del Rango Analizado')
        plt.axhline(y=rango_analizado['DEPTH'].max(), color='orange', linestyle='--', label='Fin del Rango Analizado')

        calidad_cemento_rango = rango_analizado['calidad_cemento'].value_counts(normalize=True) * 100
        resultado_predominante = calidad_cemento_rango.idxmax()
        porcentaje_predominante = calidad_cemento_rango.max()

        plt.annotate(f'{resultado_predominante} - {porcentaje_predominante:.2f}%', 
                     xy=(0.02, 0.98), xycoords='axes fraction',
                     ha='left', va='top',
                     fontsize=12, color='red', weight='bold')

        plt.annotate(f'TOC Teórico: {toc_teorico} m', 
                     xy=(0.02, 0.93), xycoords='axes fraction',
                     ha='left', va='top',
                     fontsize=10, color='blue')

        plt.annotate(f'Rango Analizado: {toc_teorico:.2f} m a {well_data["DEPTH"].max():.2f} m', 
                     xy=(1.02, 0.5), xycoords='axes fraction',
                     ha='left', va='center',
                     fontsize=10, color='black', rotation='vertical')

        plt.annotate(f'TOC Calculado en el Rango: {toc_calculado_rango:.2f} m', 
                     xy=(0.02, 0.83), xycoords='axes fraction',
                     ha='left', va='top',
                     fontsize=10, color='blue')

        malo_percentage = calidad_cemento_rango.get('Malo', 0.0)
        bueno_percentage = calidad_cemento_rango.get('Bueno', 0.0)
        regular_percentage = calidad_cemento_rango.get('Regular', 0.0)

        with st.expander("Datos del Rango Analizado"):
            table_data = [['Rango Analizado', f'{toc_teorico:.2f} m - {well_data["DEPTH"].max():.2f} m'],
                          ['Calidad Bueno', f'{bueno_percentage:.2f}%'],
                          ['Calidad Malo', f'{malo_percentage:.2f}%'],
                          ['Calidad Regular', f'{regular_percentage:.2f}%']]

        table = plt.table(cellText=table_data, colLabels=None, cellLoc='left', loc='bottom', bbox=[0.2, -0.3, 0.8, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(10)

        with st.expander("Tabla del Rango Analizado"):
            st.table(rango_analizado)

        plt.xlabel('Amplitud de CBL')
        plt.ylabel('Profundidad (DEPTH)')
        plt.title('Relación entre Calidad del Cemento, CBL y Profundidad')
        plt.legend(title='Calidad del Cemento', bbox_to_anchor=(1.05, 1), loc='upper left')

        st.pyplot(fig)
        
        tabla_copiada = st.text_area("Pegar tabla de Excel (2 columnas):", "")
        resultados_predominantes = []
        tabla_predominantes = pd.DataFrame()

        if st.button("Cargar Tabla Copiada"):
            if tabla_copiada:
                pzdo_df = cargar_tabla_copiada(tabla_copiada)
                st.write("Nuevo DataFrame a partir de la tabla copiada:")
                st.dataframe(pzdo_df)
                
                # Convertir las columnas 'TOPE' y 'BASE' a float manejando comas como separadores decimales
                convert_column_to_float(pzdo_df, 'TOPE')
                convert_column_to_float(pzdo_df, 'BASE')
                
                # Determinar los límites de profundidad en el nuevo dataframe
                min_depth = pzdo_df['TOPE'].min() - ampliacion_rango
                max_depth = pzdo_df['BASE'].max() + ampliacion_rango
                
                for index, row in pzdo_df.iterrows():
                    tope_rango = row['TOPE'] - ampliacion_rango
                    base_rango = row['BASE'] + ampliacion_rango

                    rango_analizado = well_data[(well_data['DEPTH'] >= tope_rango) & (well_data['DEPTH'] <= base_rango)]

                    well_data['calidad_cemento'] = well_data.apply(
                        verificar_calidad_cemento, args=(amplitud_caneria_libre_especifica,), axis=1)
                    calidad_cemento_rango = rango_analizado['calidad_cemento'].value_counts(normalize=True) * 100
                    resultado_predominante = calidad_cemento_rango.idxmax()

                    resultados_predominantes.append(resultado_predominante)

                pzdo_df['Resultado_Predominante'] = resultados_predominantes

                tabla_predominantes = pd.DataFrame({
                    'TOPE': pzdo_df['TOPE'],
                    'BASE': pzdo_df['BASE'],
                    'Resultado Predominante': pzdo_df['Resultado_Predominante']
                })

                st.write("Tabla de análisis de calidad de cemento en un rango de 5m del punzado:")
                st.table(tabla_predominantes)

                fig, ax = plt.subplots(figsize=(6, 8))

                cbl_smooth = savgol_filter(well_data['CBL'], window_length=5, polyorder=3)

                color = 'tab:red'
                ax.set_xlabel('Amplitud de CBL')
                ax.set_ylabel('Profundidad (DEPTH)')
                ax.plot(cbl_smooth, well_data['DEPTH'], color=color, label='CBL (Suavizado)', linewidth=0.5)
                ax.tick_params(axis='x', labelrotation=90)
                ax.invert_yaxis()

                # Ajustar la escala del eje y para que abarque todo el rango de profundidades
                ax.set_xlim(0, 100)
                ax.set_ylim(max_depth, min_depth)

                for index, row in pzdo_df.iterrows():
                    tope_rango = row['TOPE'] - ampliacion_rango
                    base_rango = row['BASE'] + ampliacion_rango

                    rango_analizado = well_data[(well_data['DEPTH'] >= tope_rango) & (well_data['DEPTH'] <= base_rango)]

                    resultado_predominante = row['Resultado_Predominante']

                    color = 'green' if resultado_predominante == 'Bueno' else 'yellow' if resultado_predominante == 'Regular' else 'red'

                    ax.axhspan(tope_rango, base_rango, alpha=0.3, color=color, label=f'Rango - {resultado_predominante}')

                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

                st.pyplot(fig)

                params = {
                    'Amplitud Cañería Libre Específica': amplitud_caneria_libre_especifica,
                    'TOC Teórico': toc_teorico,
                    'Ampliación de Rango': ampliacion_rango
                }
                
                # Asegurarse de que 'replace' solo se aplique si el valor es una cadena
                def safe_replace_comma(value):
                    if isinstance(value, str):
                        return value.replace(',', '.')
                    return value

                # Aplicar la conversión segura
                pzdo_df['TOPE'] = pzdo_df['TOPE'].apply(safe_replace_comma).astype(float)
                pzdo_df['BASE'] = pzdo_df['BASE'].apply(safe_replace_comma).astype(float)

                report_path = generate_report(well_data, toc_teorico, toc_calculado_rango, resultados_predominantes, tabla_predominantes, params, 'logo.png', well_name)
                st.success(f'Reporte generado exitosamente: {report_path}')

                # Extraer el nombre del archivo del path completo
                report_filename = os.path.basename(report_path)

                with open(report_path, "rb") as f:
                    st.download_button('Descargar reporte', f, file_name=report_filename)
