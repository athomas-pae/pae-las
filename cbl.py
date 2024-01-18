import streamlit as st
import lasio
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import StringIO
from scipy.signal import savgol_filter
import numpy as np

# Definir la función verificar_calidad_cemento
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

# Función para cargar la tabla copiada
def cargar_tabla_copiada(tabla_copiada):
    # Crea un DataFrame a partir de la tabla copiada
    df1 = pd.read_csv(StringIO(tabla_copiada), delimiter='\t', header=None)

    # Asigna nombres a las columnas utilizando la primera fila
    df1.columns = ['TOPE', 'BASE']

    return df1 

def cbl (las_file, well_data):
    st.title('Analisis de Calidad de Cemento')

    if las_file is not None:
        amplitud_caneria_libre_especifica = st.sidebar.text_input('Amplitud de Cañería Libre Específica', '72')
        toc_teorico = st.sidebar.text_input('TOC Teórico', '1500')
        # Añadir widgets al sidebar
        ampliacion_rango = st.sidebar.slider('Ampliación de Rango', min_value=1, max_value=20, value=5)
        amplitud_caneria_libre_especifica = float(amplitud_caneria_libre_especifica)
        toc_teorico = float(toc_teorico)

        well_data['calidad_cemento'] = well_data.apply(verificar_calidad_cemento, args=(amplitud_caneria_libre_especifica,), axis=1)
        rango_analizado = well_data[(well_data['DEPTH'] >= toc_teorico) & (well_data['DEPTH'] <= well_data['DEPTH'].max())]

        # Check if TOC teórico is greater than TOC calculado en el rango
        toc_candidates_rango = rango_analizado[rango_analizado['calidad_cemento'] == 'Malo']
        toc_candidates_rango = toc_candidates_rango[toc_candidates_rango['CBL'] > 10].nlargest(10, 'DEPTH')['DEPTH']
        toc_calculado_rango = toc_candidates_rango.mean()

        if toc_teorico > toc_calculado_rango:
            st.warning("El TOC teórico es mayor que el TOC calculado en el rango. Verifique los valores ingresados.")

        fig, ax = plt.subplots(figsize=(6, 10))
        scatter = sns.scatterplot(data=well_data, x='CBL', y='DEPTH', hue='calidad_cemento', palette='viridis', s=30, ax=ax)
        ax.invert_yaxis()

        # Línea vertical para TOC_calculado_rango
        toc_candidates_rango = rango_analizado[rango_analizado['calidad_cemento'] == 'Malo']
        toc_candidates_rango = toc_candidates_rango[toc_candidates_rango['CBL'] > 10].nlargest(10, 'DEPTH')['DEPTH']
        toc_calculado_rango = toc_candidates_rango.mean()
        plt.axhline(y=toc_calculado_rango, color='blue', linestyle='--', label='TOC Calculado en el Rango')

        # Línea punteada para el inicio del rango analizado
        plt.axhline(y=rango_analizado['DEPTH'].min(), color='green', linestyle='--', label='Inicio del Rango Analizado')

        # Línea punteada para el fin del rango analizado
        plt.axhline(y=rango_analizado['DEPTH'].max(), color='orange', linestyle='--', label='Fin del Rango Analizado')

        # Identificar el resultado predominante y su porcentaje actualizado
        calidad_cemento_rango = rango_analizado['calidad_cemento'].value_counts(normalize=True) * 100
        resultado_predominante = calidad_cemento_rango.idxmax()
        porcentaje_predominante = calidad_cemento_rango.max()

        # Etiqueta con el resultado predominante y su porcentaje
        plt.annotate(f'{resultado_predominante} - {porcentaje_predominante:.2f}%', 
                     xy=(0.02, 0.98), xycoords='axes fraction',
                     ha='left', va='top',
                     fontsize=12, color='red', weight='bold')

        # Nota sobre el TOC_teorico
        plt.annotate(f'TOC Teórico: {toc_teorico} m', 
                     xy=(0.02, 0.93), xycoords='axes fraction',
                     ha='left', va='top',
                     fontsize=10, color='blue')

        # Nota sobre el rango analizado en el gráfico de barras
        plt.annotate(f'Rango Analizado: {toc_teorico:.2f} m a {well_data["DEPTH"].max():.2f} m', 
                     xy=(1.02, 0.5), xycoords='axes fraction',
                     ha='left', va='center',
                     fontsize=10, color='black', rotation='vertical')

        # Etiqueta con el TOC calculado en el rango
        plt.annotate(f'TOC Calculado en el Rango: {toc_calculado_rango:.2f} m', 
                     xy=(0.02, 0.83), xycoords='axes fraction',
                     ha='left', va='top',
                     fontsize=10, color='blue')

        # Check if 'Malo' key exists in calidad_cemento_rango before accessing it
        if 'Malo' in calidad_cemento_rango.index:
            malo_percentage = calidad_cemento_rango['Malo']
        else:
            malo_percentage = 0.0
        
        with st.expander("Datos del Rango Analizado"):
            # Display the table in the expander
            table_data = [['Rango Analizado', f'{toc_teorico:.2f} m - {well_data["DEPTH"].max():.2f} m'],
                          ['Calidad Bueno', f'{calidad_cemento_rango["Bueno"]:.2f}%'],
                          ['Calidad Malo', f'{malo_percentage:.2f}%'],  # Use the obtained percentage
                          ['Calidad Regular', f'{calidad_cemento_rango["Regular"]:.2f}%']]

        
        table = plt.table(cellText=table_data, colLabels=None, cellLoc='left', loc='bottom', bbox=[0.2, -0.3, 0.8, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(10)

        with st.expander("Tabla del Rango Analizado"):
            # Display the table in the expander
            st.table(rango_analizado)

        # Encabezados y leyenda
        plt.xlabel('Amplitud de CBL')
        plt.ylabel('Profundidad (DEPTH)')
        plt.title('Relación entre Calidad del Cemento, CBL y Profundidad')

        # Leyenda
        plt.legend(title='Calidad del Cemento', bbox_to_anchor=(1.05, 1), loc='upper left')

        # Show the plot using Streamlit
        st.pyplot(fig)
    # Agrega un área de texto para que los usuarios peguen la tabla de Excel
    tabla_copiada = st.text_area("Pegar tabla de Excel (2 columnas):", "")

    # Botón para cargar la tabla copiada
    if st.button("Cargar Tabla Copiada"):
        if tabla_copiada:
            # Carga la tabla copiada en un nuevo DataFrame
            pzdo_df = cargar_tabla_copiada(tabla_copiada)

            # Puedes realizar operaciones adicionales con el nuevo DataFrame si es necesario

            # Muestra el nuevo DataFrame
            st.write("Nuevo DataFrame a partir de la tabla copiada:")
            st.dataframe(pzdo_df)
        else:
            st.warning("Por favor, ingrese una tabla copiada válida.")
        
        # Definir lista para almacenar resultados predominantes
        resultados_predominantes = []
        

        # Iterar sobre cada fila de pzdo_df y generar el rango de análisis
        for index, row in pzdo_df.iterrows():
            tope_rango = float(row['TOPE'].replace(',', '.')) - ampliacion_rango
            base_rango = float(row['BASE'].replace(',', '.')) + ampliacion_rango

            # Filtrar well_data para el rango específico
            rango_analizado = well_data[(well_data['DEPTH'] >= tope_rango) & (well_data['DEPTH'] <= base_rango)]

            # Verificar calidad del cemento y obtener el valor predominante
            well_data['calidad_cemento'] = well_data.apply(
                verificar_calidad_cemento, args=(amplitud_caneria_libre_especifica,), axis=1)
            calidad_cemento_rango = rango_analizado['calidad_cemento'].value_counts(normalize=True) * 100
            resultado_predominante = calidad_cemento_rango.idxmax()

            # Agregar el resultado predominante a la lista
            resultados_predominantes.append(resultado_predominante)

        # Crear una nueva columna en pzdo_df con los resultados predominantes
        pzdo_df['Resultado_Predominante'] = resultados_predominantes

        # Crear tabla con valores predominantes en cada rango
        tabla_predominantes = pd.DataFrame({
            'TOPE': pzdo_df['TOPE'],
            'BASE': pzdo_df['BASE'],
            'Resultado Predominante': pzdo_df['Resultado_Predominante']
        })

        # Visualizar la tabla de resultados predominantes
        st.write("Tabla de analisis de calidad de cemento en un rango de 5m del punzado:")
        st.table(tabla_predominantes)

        # Crear gráfico de líneas para la curva CBL con suavizado
        fig, ax = plt.subplots(figsize=(8, 6))

        # Suavizar la curva CBL usando savgol_filter
        cbl_smooth = savgol_filter(well_data['CBL'], window_length=5, polyorder=3)

        # Plot de la curva CBL suavizada
        color = 'tab:red'
        ax.set_xlabel('Amplitud de CBL')
        ax.set_ylabel('Profundidad (DEPTH)')
        ax.plot(cbl_smooth, well_data['DEPTH'], color=color, label='CBL (Suavizado)', linewidth=0.5)
        ax.tick_params(axis='x', labelrotation=90)  # Rotar etiquetas del eje x
        ax.invert_yaxis()

        # Configurar el eje x para que vaya de 0 a 100
        ax.set_xlim(0, 100)
        ax.set_ylim(well_data['DEPTH'].max(), toc_teorico)

        # Resaltar los rangos de la tabla copiada
        for index, row in pzdo_df.iterrows():
            tope_rango = float(row['TOPE'].replace(',', '.')) - 5
            base_rango = float(row['BASE'].replace(',', '.')) + 5

            # Colorear según el resultado predominante
            if row['Resultado_Predominante'] == 'Bueno':
                color = 'green'
            elif row['Resultado_Predominante'] == 'Regular':
                color = 'yellow'
            elif row['Resultado_Predominante'] == 'Malo':
                color = 'red'

            # Dibujar el rango
            ax.axhspan(tope_rango, base_rango, alpha=0.3, color=color, label=f'Rango - {row["Resultado_Predominante"]}')

       

        # Agregar cuadro de texto con información
        info_text = f'Valores Analizados:\n{tabla_predominantes.to_string(index=False)}'
        ax.text(1.4, 0.98, info_text, transform=ax.transAxes, fontsize=8, verticalalignment='top', horizontalalignment='left', backgroundcolor='white')

        fig.tight_layout()

        st.write("Analisis de Cemento vs Punzados")
        # Mostrar el gráfico usando Streamlit
        st.pyplot(fig)
   
if __name__ == '__main__':
    main()
        