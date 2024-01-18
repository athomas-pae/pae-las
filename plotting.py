import streamlit as st
import pandas as pd

# Plotly imports
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.figure_factory as ff
import plotly.express as px


def plot(las_file, well_data):
    st.title('Visualizador de .LAS')
    
    if not las_file:
        st.warning('Subir archivo .LAS')
    
    else:
        columns = list(well_data.columns)
        st.write('Expandir para visualizar la data del pozo.')
        
        with st.expander('Seleccionar curvas'):    
            curves = st.multiselect('Selecciona curvas para visualizar', columns)
            if len(curves) <= 1:
                st.warning('Selecciona almenos 2 variables')
            else:
                curve_index = 1
                fig = make_subplots(rows=1, cols= len(curves), subplot_titles=curves, shared_yaxes=True)

                for curve in curves:
                    fig.add_trace(go.Scatter(x=well_data[curve], y=well_data['DEPTH']), row=1, col=curve_index)
                    curve_index+=1
                
                fig.update_layout(height=1000, showlegend=False, yaxis={'title':'DEPTH','autorange':'reversed'})
                fig.layout.template='seaborn'
                st.plotly_chart(fig, use_container_width=True)

        with st.expander('Histograma'):
            col1_h, col2_h = st.columns(2)
            col1_h.header('Opciones')

            hist_curve = col1_h.selectbox('Seleccionar curvas', columns)
            log_option = col1_h.radio('Seleccionar escala linear o logaritmica', ('Lineal', 'Logaritmico'))
            hist_col = col1_h.color_picker('Seleccionar color de histograma')
            st.write('El color es'+hist_col)
            
            if log_option == 'Lineal':
                log_bool = False
            elif log_option == 'Logaritmico':
                log_bool = True
        

            histogram = px.histogram(well_data, x=hist_curve, log_x=log_bool)
            histogram.update_traces(marker_color=hist_col)
            histogram.layout.template='seaborn'
            col2_h.plotly_chart(histogram, use_container_width=True)

        with st.expander('Crossplot'):
            col1, col2 = st.columns(2)
            col1.write('Optiones')

            xplot_x = col1.selectbox('X-Axis', columns)
            xplot_y = col1.selectbox('Y-Axis', columns)
            xplot_col = col1.selectbox('Color por', columns)
            xplot_x_log = col1.radio('X Axis - Lineal o Logaritmico', ('Lineal', 'Logaritmico'))
            xplot_y_log = col1.radio('Y Axis - Lineal o Logaritmico', ('Lineal', 'Logaritmico'))

            if xplot_x_log == 'Lineal':
                xplot_x_bool = False
            elif xplot_x_log == 'Logaritmico':
                xplot_x_bool = True
            
            if xplot_y_log == 'Lineal':
                xplot_y_bool = False
            elif xplot_y_log == 'Logaritmico':
                xplot_y_bool = True

            col2.write('Crossplot')
           
            xplot = px.scatter(well_data, x=xplot_x, y=xplot_y, color=xplot_col, log_x=xplot_x_bool, log_y=xplot_y_bool)
            xplot.layout.template='seaborn'
            col2.plotly_chart(xplot, use_container_width=True)
