import streamlit as st
import welly
import pandas as pd
import matplotlib.pyplot as plt

def load_data(uploaded_file):
    if uploaded_file is not None:
        las_file = welly.Well.from_lasio(uploaded_file)
        well_data = las_file.df()
        return las_file, well_data
    return None, None

def identify_cuplas(well_data, ccl_upper_limit_auto, dist_promedio=9.6, tolerancia=1):
    well_data.reset_index(drop=True, inplace=True)
    well_data['EsCupla'] = well_data['CCL'] > ccl_upper_limit_auto
    
    cuplas_table = pd.DataFrame(columns=['Profundidad', 'Valido'])
    
    for idx, row in well_data.iterrows():
        if row['EsCupla']:
            window = well_data.iloc[:idx+1][well_data['DEPTH'] >= row['DEPTH'] - dist_promedio]
            max_ccl = window['CCL'].max()
            
            next_point_idx = idx + 1
            next_point = well_data.iloc[next_point_idx] if next_point_idx < len(well_data) else None
            if next_point is not None and next_point['EsCupla'] and abs(next_point['DEPTH'] - row['DEPTH']) <= tolerancia:
                continue
            
            if len(cuplas_table) > 0:
                min_depth = row['DEPTH'] - 1
                max_depth = row['DEPTH'] + 1
                if ((cuplas_table['Profundidad'] >= min_depth) & (cuplas_table['Profundidad'] <= max_depth)).any():
                    continue
            
            cuplas_table.loc[len(cuplas_table)] = {'Profundidad': row['DEPTH'], 'Valido': 'Valido'}
    
    cuplas_table = cuplas_table.sort_values(by='Profundidad', ascending=True).reset_index(drop=True)
    cuplas_table['Nro de Cupla'] = ['C.' + str(i) for i in range(1, len(cuplas_table) + 1)]
    
    # Identificar los valores "SD" como anomalías
    sd_values = well_data[well_data['CCL'] == 'SD']
    if not sd_values.empty:
        for idx, row in sd_values.iterrows():
            cuplas_table.loc[len(cuplas_table)] = {'Profundidad': row['DEPTH'], 'Valido': 'SD'}
    
    return cuplas_table

def classify_cbl(cbl_value, max_cbl):
    percentage = (cbl_value / max_cbl) * 100
    if percentage >= 90:
        return 'LIBRE'
    elif 90 > percentage >= 60:
        return 'AGARRE'
    elif 60 > percentage >= 25:
        return 'CUPLA'
    else:
        return 'CUERPO'

def colorize_cbl(cbl_category):
    if cbl_category == 'LIBRE':
        return 'green'
    elif cbl_category == 'AGARRE':
        return 'orange'
    elif cbl_category == 'CUPLA':
        return 'blue'
    else:
        return 'red'

def highlight_cuplas(cuplas_table, well_data, ax, dist_promedio, tolerancia):
    last_valid_depth = None
    last_valid_cupla_depth = None
    first_detection = True  # Variable para indicar la primera detección

    for i, row in cuplas_table[::-1].iterrows():  # Iterar en orden inverso
        depth = row['Profundidad']
        label = row['Nro de Cupla']
        valid = True

        # Obtener el valor de CBL clasificado
        cbl_classified = classify_cbl(well_data.loc[well_data['DEPTH'] == depth, 'CBL'].iloc[0], well_data['CBL'].max())

        # Verificar si el valor de CBL clasificado es 'CUERPO'
        if cbl_classified == 'CUERPO':
            ax.text(0.95, depth, 'SD', horizontalalignment='center', verticalalignment='center', transform=ax.get_yaxis_transform(), fontsize=8, color='orange')
            continue  # Saltar al siguiente punto sin marcar como una cupla válida

        # Verificar el distanciamiento y tolerancia
        if last_valid_depth is not None:
            depth_diff = last_valid_depth - depth  # Cambiar el cálculo a restar la profundidad actual de la anterior
            if not (dist_promedio - tolerancia <= depth_diff <= dist_promedio + tolerancia) or abs(depth - last_valid_cupla_depth) <= 1:
                valid = False

        # Marcar la cupla como válida o no válida en el gráfico
        if valid:
            if first_detection:  # Si es la primera detección
                ax.text(0.95, depth, label, horizontalalignment='center', verticalalignment='center', transform=ax.get_yaxis_transform(), fontsize=8, color='green')
                first_detection = False  # Cambiar la variable para indicar que ya se ha detectado la primera cupla
            else:
                last_valid_depth = depth
                last_valid_cupla_depth = depth
                ax.text(0.95, depth, label, horizontalalignment='center', verticalalignment='center', transform=ax.get_yaxis_transform(), fontsize=8, color='green')
        else:
            last_valid_depth = None  # Reiniciar la última profundidad válida

    return cuplas_table

def posibles_cortes(well_data_filtered, cuplas_table, ax):
    cbl_max = well_data_filtered['CBL'].max()
    posible_cortes = []

    cupla_indices = cuplas_table.index[cuplas_table['Valido'] == 'Valido'].tolist()
    cupla_indices.sort(key=lambda x: cuplas_table.loc[x, 'Profundidad'], reverse=True)
    
    for i, cupla_idx in enumerate(cupla_indices):
        cupla_depth = cuplas_table.loc[cupla_idx, 'Profundidad']
        
        depth_range = well_data_filtered[(well_data_filtered['DEPTH'] <= cupla_depth) & (well_data_filtered['DEPTH'] > cupla_depth - 4)]
        
        agarre_percentage = (depth_range['CBL'].apply(lambda x: classify_cbl(x, cbl_max)) == 'AGARRE').mean() * 100
        libre_percentage = (depth_range['CBL'].apply(lambda x: classify_cbl(x, cbl_max)) == 'LIBRE').mean() * 100
        
        if libre_percentage > agarre_percentage:
            proposed_cupla_idx = cupla_idx
            inicio_rango = cupla_depth - 4
            fin_rango = cupla_depth
            posible_cortes.append({'Inicio Rango': inicio_rango, 'Fin Rango': fin_rango, 'Porcentaje Agarre': agarre_percentage, 'Porcentaje Libre': libre_percentage, 'Cupla Identificada': 'SI'})
    
    if posible_cortes:
        posible_corte_valido = max(posible_cortes, key=lambda x: x['Fin Rango'])
        proposed_cupla_depth = posible_corte_valido['Fin Rango']
        proposed_corte_depth = proposed_cupla_depth - 1.5
        
        # Dibujar la línea punteada
        ax.axhline(y=proposed_corte_depth, color='red', linestyle='--')
        
        # Actualizar el texto del cuadro fuera del gráfico
        ax.text(-0.1, -0.1, f'Corte propuesto: {proposed_corte_depth:.2f} m', transform=ax.transAxes,
                fontsize=15, color='black', bbox=dict(facecolor='white', alpha=0.5))
        

    posible_cortes_df = pd.DataFrame(posible_cortes)
    
    return posible_cortes_df

def corte(las_file, well_data):
    st.title('Analizador de Cortes')

    gain_percentage = st.sidebar.number_input('Umbral [%]', value=15, min_value=0, max_value=100, step=1)
    Gain = gain_percentage / 100

    min_ccl = well_data['CCL'].min()
    mean_ccl = well_data['CCL'].mean()
    max_ccl = well_data['CCL'].max()

    ccl_upper_limit_auto = Gain * (max_ccl - mean_ccl)
    ccl_lower_limit_auto = Gain * (min_ccl - mean_ccl)
    
    valid_depths = well_data[(~well_data['CCL'].isnull()) & (well_data['CCL'] != -999.25) & (~well_data['CBL'].isnull()) & (well_data['CBL'] != -999.25)]
    if valid_depths.empty:
        st.error('No se encontraron datos válidos para iniciar el análisis.')
        return

    cuplas_table = identify_cuplas(well_data, ccl_upper_limit_auto)

    start_depth = cuplas_table['Profundidad'].min()
    end_depth = cuplas_table['Profundidad'].max()

    well_data_filtered = well_data[(well_data['DEPTH'] >= start_depth) & (well_data['DEPTH'] <= end_depth)]
    well_data_filtered = well_data_filtered.rename(columns={'CBL': 'CBL', 'CCL': 'CCL'})

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(8, 16))

    axes[0].plot(well_data_filtered['CCL'], well_data_filtered['DEPTH'], color='blue', label='CCL')
    axes[0].set_xlabel('Amplitud CCL')
    axes[0].set_ylabel('Profundidad')
    axes[0].invert_yaxis()
    axes[0].legend()

    axes[0].axvline(x=ccl_upper_limit_auto, color='gray', linestyle='--')
    axes[0].axvline(x=ccl_lower_limit_auto, color='gray', linestyle='--')

    cuplas_table = identify_cuplas(well_data_filtered, ccl_upper_limit_auto)
    cupla_count = highlight_cuplas(cuplas_table, well_data_filtered, axes[0], dist_promedio=9.6, tolerancia=1)

    posibles_cortes(well_data_filtered, cuplas_table, axes[0])  # Se llama a la función sin almacenar el resultado

    cbl_max = well_data_filtered['CBL'].max()
    for i, row in well_data_filtered.iterrows():
        cbl_category = classify_cbl(row['CBL'], cbl_max)
        color = colorize_cbl(cbl_category)
        axes[1].scatter(row['CBL'], row['DEPTH'], color=color, s=5)

    axes[1].set_xlim(0, 100)
    axes[1].set_xlabel('Amplitud CBL')
    axes[1].set_ylabel('Profundidad')
    axes[1].invert_yaxis()

    plt.tight_layout()

    # Obtener el nombre del pozo del archivo LAS
    well_name = las_file.well.WELL.value if hasattr(las_file, 'well') and 'WELL' in las_file.well.keys() else "SD"
    fig.suptitle(f'POZO - {well_name}', fontsize=16, fontweight='bold')

    # Cuadro de leyenda de colores de CBL
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', label='LIBRE', markerfacecolor='green', markersize=5),
        plt.Line2D([0], [0], marker='o', color='w', label='AGARRE', markerfacecolor='orange', markersize=5),
        plt.Line2D([0], [0], marker='o', color='w', label='CUPLA', markerfacecolor='blue', markersize=5),
        plt.Line2D([0], [0], marker='o', color='w', label='CUERPO', markerfacecolor='red', markersize=5)
    ]

    # Ajustar leyenda al gráfico y colocarla en la esquina inferior derecha fuera del gráfico
    fig.legend(handles=legend_elements, loc='lower right', fontsize='small', title='CBL Categories')
    plt.subplots_adjust(top=0.92, bottom=0.08, left=0.10, right=0.90, hspace=0.25, wspace=0.35)

    st.pyplot(fig)
    
    # Desplegable para la tabla de cuplas identificadas
    with st.expander("Tabla de Cuplas Identificadas"):
        st.table(cuplas_table)
    
    # Desplegable para mostrar solo los valores detectados como "SD"
    with st.expander("Anomalías Identificadas"):
        sd_values = well_data_filtered[well_data_filtered['CCL'] == 'SD']
        if not sd_values.empty:
            st.table(sd_values[['DEPTH', 'CCL']])
        else:
            st.write("No se encontraron anomalías identificadas (SD)")

def main():
    st.set_page_config(layout="wide", page_title='Analisis de .LAS v1.0')

    uploaded_file = st.file_uploader("Upload LAS file", type=["las"])

    las_file, well_data = load_data(uploaded_file)

    if las_file is not None and well_data is not None:
        corte(las_file, well_data)

if __name__ == "__main__":
    main()
