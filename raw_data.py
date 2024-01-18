import streamlit as st
import pandas as pd

def raw_data(las_file, well_data):
    st.title('LAS File Data Info')
    if not las_file:
        st.warning('No file has been uploaded')
    else:
        st.write('**Curve Information**')
        for count, curve in enumerate(las_file.curves):
            # st.write(f"<b>Curve:</b> {curve.mnemonic}, <b>Units: </b>{curve.unit}, <b>Description:</b> {curve.descr}", unsafe_allow_html=True)
            st.write(f"   {curve.mnemonic} ({curve.unit}): {curve.descr}", unsafe_allow_html=True)
        st.write(f"<b>Hay un total de: {count+1} cuevas presentes en este archivo</b>", unsafe_allow_html=True)
        
        st.write('<b>Estadistica de curvas</b>', unsafe_allow_html=True)
        st.write(well_data.describe())
        st.write('<b>Valores de las columnas</b>', unsafe_allow_html=True)
        st.dataframe(data=well_data)