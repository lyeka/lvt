import streamlit as st
from streamlit_file_browser import st_file_browser

st.header('Analysis Report')
event = st_file_browser("report", key='AnalyzeReport',extentions=['.md'])
st.write(event)