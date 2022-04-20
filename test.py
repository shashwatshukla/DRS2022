import goto
import streamlit as st, pandas as pd
from load_Data import get_data
import sqlite3
df_drsend = get_data(r'database/mms_master.sqlite','drsend')
df_vessel = get_data(r'database/mms_master.sqlite','vessels')
df_fleet = get_data(r'database/mms_master.sqlite','fleet')
flt_list=dict(df_fleet[['fltLocalName','fltNameUID']].values)


df_merged = pd.merge(df_drsend,df_vessel[['vsl_imo','statusActiveInactive','vslFleet']], on = 'vsl_imo',how = 'left') # brig col from vessel to drsend dataframe
df_merged.drop(df_merged.index[df_merged['statusActiveInactive'] == 0], inplace = True)
# df_nan = df_merged[df_merged['statusActiveInactive'].isna()] # chceck ships status not listed in DB
# df_nan2 = df_merged[df_merged['vslFleet'].isna()] # chceck ships fleet not listed in DB
# missingships = list(df_nan['ship_name'].unique()) # check for missing ships in DB
st.write(df_merged)
#st.write(df_nan)
#st.write(df_nan2)
#st.write(missingships)
# missingfleet = list(df_nan2['ship_name'].unique())
#st.write(missingfleet)
group_wise={list(flt_list.keys())[i]:sorted(list(df_merged.loc[df_merged['vslFleet'] == str(list(flt_list.values())[i])
,'ship_name'].unique())) for i in range(len(flt_list))} # all vesssel fleet wise using dict comprehension
st.write(group_wise)

