import pandas as pd
import sqlite3
import streamlit as st
import time

conn = sqlite3.connect(r'assets/mms_master.sqlite')
df = pd.read_sql('select * from drsend',conn)

cast_dict = {'rpt_by':'category', 'insp_by':'category' , 'ship_name':'category' ,'ship_drs_code':'category' ,
             'vsl_imo':'category' ,'def_code':'category' , 'def_short':'category' , 'item_code':'category' ,
             'item_short':'category', 'ext_rsn':'category', 'eq_code':'category', 'sys_code':'category',
             'status':'category'}

df = df.astype(cast_dict)
boolcat={"rca": "category", "brkdn_yn": "category", "delay_tf": "category", "downtime_tf": "category",
 "brkdn_tf": "category", "critical_eq_tf": "category", "blackout_tf": "category",
 "docking_tf": "category", "dispensation_tf": "category", "coc_tf": "category", "alert_req": "category"}

df[boolcat.keys()] = df[boolcat.keys()].map({'FALSE': False, 'False': False, 'True': True, 'TRUE': True})
df['coc_tf'] = df['coc_tf'].astype('category')

df['delay_hr'] = pd.to_numeric(df['delay_hr'])
df['downtime_hr'] = pd.to_numeric( df['downtime_hr'])
df['VET_risk'] = pd.to_numeric(df['VET_risk'])
df['VET_risk'] = df['VET_risk'].astype('float16')
df['delay_hr'] = pd.to_numeric(df['delay_hr'])
df['dt_ocurred'] = pd.to_datetime(df['dt_ocurred'])

df.drop(['moge', 'hoge'], axis=1, inplace=True)
st.dataframe(df.astype('object'))

df.to_parquet('mms_master.parquet', engine='fastparquet')
df.to_pickle('mms_master.pickle')
df.to_feather('mms_master.feather')

time.sleep(2)
df1 = pd.read_parquet('mms_master.parquet', engine='fastparquet')
st.write('-------------Parquet--------------')
st.write(df1.info())
st.write(df1.dtypes)
print('---------------------------')

df2 = pd.read_pickle('mms_master.pickle')
st.write('-------------PICKLE--------------')
st.write(df2.info())
st.write(df2.dtypes)
print('---------------------------')

df3 = pd.read_feather('mms_master.feather')
st.write('-------------FEATHER--------------')
st.write(df3.info())
st.write(df3.dtypes)
print('---------------------------')
