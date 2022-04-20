# import goto
import streamlit as st, pandas as pd
from load_Data import get_data
import sqlite3
df_drsend = get_data(r'database/mms_master.sqlite','drsend')
df_vessel = get_data(r'database/mms_master.sqlite','vessels')
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
#m = df_merged['vslFleet']=='1'
#tanker1=df_merged['ship_name'].mask(m).dropna().unique()
tanker1={"Tanker 1":[df_merged.loc[df_merged['vslFleet'] == '1','ship_name'].unique()]}# and so on.....
st.write(tanker1)