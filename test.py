
import plotly.express as px
import streamlit as st, pandas as pd
from load_Data import get_data
import sqlite3
df_drsend = get_data(r'database/mms_master.sqlite','drsend')
df_vessel = get_data(r'database/mms_master.sqlite','vessels')
df_fleet = get_data(r'database/mms_master.sqlite','fleet')
flt_list=dict(df_fleet[['fltLocalName','fltNameUID']].values)


df_merged = pd.merge(df_drsend,df_vessel[['vsl_imo','statusActiveInactive','vslFleet']], on = 'vsl_imo',how = 'left') # brig col from vessel to drsend dataframe
df_merged.drop(df_merged.index[df_merged['statusActiveInactive'] == 0], inplace = True)
st.write(flt_list)
group_wise = {list(flt_list.keys())[i]:sorted(list(df_merged.loc[df_merged['vslFleet'] == str(list(flt_list.values())[i])
,'ship_name'].unique())) for i in range(len(flt_list))} # all vesssel fleet wise using dict comprehension
st.write(group_wise)

