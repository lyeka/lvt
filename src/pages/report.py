import streamlit as st
from streamlit_file_browser import st_file_browser


tab1, tab2 = st.tabs(["Single Stock", "Compare Stock"])

with tab1:
    st.header('Analysis Report')
    event = st_file_browser("report/single_stock", key='SingleStockReport',extentions=['.md'])
    st.write(event)
with tab2:
    st.header('Analysis Report')
    event = st_file_browser("report/compare_stock", key='CompareStockReport',extentions=['.md'])
    st.write(event)
