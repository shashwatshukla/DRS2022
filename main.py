import streamlit as st
st.set_page_config(page_title='DR Sender', layout='wide')
from GetNewDRS import make_NewDRS
from filter_Data import filtered_Data
from UploadDRS import upload_drs
from Dashboard_drs import dashboard

sb_sel = st.sidebar.radio('Select Page',options=['View/Filter Data','Download DR sender','Upload DR sender', 'Dashboard(In progress)'])

if sb_sel == 'Download DR sender':
    make_NewDRS()
if sb_sel == 'View/Filter Data':
    filtered_Data()
if sb_sel=='Upload DR sender':
    upload_drs()
if sb_sel=='Dashboard(In progress)':
    dashboard()


