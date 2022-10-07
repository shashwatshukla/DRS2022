import plotly.express as px
import streamlit as st
import pandas as pd
from helpers import get_data, get_vessel_byfleet
import datetime
from datetime import timedelta
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

st.set_page_config(page_title='Linked list', layout='wide')

import numpy as np
db = r'assets/mms_master.sqlite'
df_db=get_data(db,'drsend')
df_vessels = get_data(db, 'vessels')
df_merged = pd.merge(df_db, df_vessels[['vsl_imo', 'vslCode', 'statusActiveInactive', 'vslFleet', 'vslMarSI', 'vslTechSI']], on='vsl_imo',how='left')

df_merged = df_merged.query("vslFleet!='Cargo Fleet (TOK)'")
df_merged = df_merged.dropna(subset=['statusActiveInactive'])
df_merged =df_merged.loc[df_merged["statusActiveInactive"]=='1']

df_merged =df_merged.rename(columns={'delay_hr': 'Delay(h)', 'downtime_hr': 'Downtime(h)',
                        'critical_eq_tf': 'Critical', 'dispensation_tf': 'Dispensation',
                        'coc_tf': 'COC', 'Overdue_status': 'Overdue', 'blackout_tf': 'Blackouts',
                        'docking_tf': 'Docking'})






gb = GridOptionsBuilder.from_dataframe(df_merged)
gb.configure_pagination()
gb.configure_side_bar()
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
gridOptions = gb.build()






AgGrid(df_merged, gridOptions=gridOptions, enable_enterprise_modules=True)

