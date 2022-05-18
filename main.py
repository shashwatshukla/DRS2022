import streamlit as st, pandas as pd, sqlite3
from GetNewDRS import make_NewDRS
from filter_Data import filtered_Data
from UploadDRS import upload_drs
from Dashboard_drs import dashboard
from helpers import get_data

st.set_page_config(page_title='DR Sender', layout='wide')
df_mailid = get_data(r'database/mms_master.sqlite','si')
df_mailid=df_mailid[['siName','siEmail']]

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

col1, col2,col3=st.columns(3)
allmailid = df_mailid['siEmail'].tolist()
st.sidebar.image('MMS Logo.png')
mailid = st.sidebar.text_input("MMS email id",value='@mmstokyo.co.jp')
st.session_state.id = mailid
person = df_mailid[df_mailid['siEmail'] == mailid]

if len(person==1):

    st.sidebar.info(f'Welcome {person.iloc[0, 0]}')
    sb_sel = st.sidebar.radio('Select Page', options=['View/Filter Data', 'Download DR sender', 'Upload DR sender',
                                                      'Dashboard(In progress)'])
    if sb_sel == 'Download DR sender':
        make_NewDRS()
    if sb_sel == 'View/Filter Data':
        filtered_Data()
    if sb_sel == 'Upload DR sender':
        upload_drs()
    if sb_sel == 'Dashboard(In progress)':
        dashboard()
else:
    st.sidebar.info('MMS mail id required to proceed......')
