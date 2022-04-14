import streamlit as st, pandas as pd
import sqlite3 as sq
st.set_page_config(page_title='DR Sender', layout='wide')
from GetNewDRS import make_NewDRS
from filter_Data import filtered_Data
from UploadDRS import upload_drs
from Dashboard_drs import dashboard
conn=sq.connect(r'database/mms_master.sqlite')
df_mailid=pd.read_sql_query('select siEmail from si', conn)
conn.close()
col1, col2,col3=st.columns(3)
with col1:
    mailid = st.text_input("Please enter your MMS mail id to continue")
allmailid = df_mailid['siEmail'].tolist()
if(mailid in allmailid):

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

