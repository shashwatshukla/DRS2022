import streamlit as st, pandas as pd
import sqlite3 as sq
st.set_page_config(page_title='DR Sender', layout='wide')
from GetNewDRS import make_NewDRS
from filter_Data import filtered_Data
from UploadDRS import upload_drs
from Dashboard_drs import dashboard
conn=sq.connect(r'database/mms_master.sqlite')
df_mailid=pd.read_sql_query('select siName,siEmail from si', conn)
conn.close()
col1, col2,col3=st.columns(3)
allmailid = df_mailid['siEmail'].tolist()

mailid = st.sidebar.text_input("MMS email id",value='@mmstokyo.co.jp')
#if 'id' not in st.session_state:
st.session_state.id = mailid
# allmailid = df_mailid['siEmail'].tolist()
# mailid = st.text_input("MMS email id", value='@mmstokyo.co.jp')
person = df_mailid[df_mailid['siEmail'] == mailid]

# if "emailid" not in st.session_state:
#     with col3:
#         if (len(person)==1):
#             st.session_state.emailid = mailid
# else:
#     mailid = st.session_state.emailid
#     person = df_mailid[df_mailid['siEmail']== mailid]

# st.write(person)
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
