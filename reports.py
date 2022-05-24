import plotly.express as px
import streamlit as st
import pandas as pd
from helpers import get_data, get_vessel_byfleet
import datetime
st.set_page_config(page_title='DR Sender', layout='wide')
# ___________________________Declarations_____________________________
curr_year = str(datetime.datetime.now().year)
todaydt=pd.to_datetime('today').format("%yyyy-%mm-%dd")
st.write(todaydt)
db = r'assets/mms_master.sqlite'
disp_cols = ['ship_name','overdue', 'dt_ocurred', 'target_dt', 'ext_dt','done_dt','status', 'nc_detail', 'ext_rsn', 'ext_cmnt', 'co_eval',
             'ser_no',
             'req_num', 'est_cause_ship',
             'init_action_ship', 'init_action_ship_dt',
             'final_action_ship', 'final_action_ship_dt', 'corr_action', 'rpt_by', 'insp_by',
             'insp_detail',
             'update_by', 'update_dt']  # list of cols to be displayed on the screen

# _______________Data collection_______________________
df_rawDRS = get_data(db, 'drsend')
df_vessels = get_data(db, 'vessels')
df_merged = pd.merge(df_rawDRS, df_vessels[['vsl_imo', 'statusActiveInactive', 'vslFleet','vslMarSI','vslTechSI']], on='vsl_imo',how='left')
df_active_ships = df_merged.drop(df_merged.index[df_merged['statusActiveInactive'] == '0'])

vsl_list_fleetwise = get_vessel_byfleet(1)
fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(), default='MMS-TOK',key='fleet_exp1')
vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName], []) # get vsl names as per flt selected and flatten the list (sum)
vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt))

toCorrect = ["dt_ocurred", "init_action_ship_dt", "target_dt", "final_action_ship_dt", "done_dt",
                 "update_dt", "ext_dt", "PSC_picdt", "PSC_info2ownr_dt", "PSC_info2chrtr_dt", "PSC_info2rtshp_dt",
                 "PSC_info2oilmaj_dt", "PSC_info2mmstpmgmt_dt", "PSC_sndr_offimport_dt"]
df_active_ships_currDRS = df_active_ships.query("ship_name == @vslName and (dt_ocurred.str.contains(@curr_year)"
                              " or done_dt.str.contains(@curr_year) or status.str.contains('OPEN'))", engine='python')
for someCol in toCorrect:
    df_active_ships_currDRS[someCol] = pd.to_datetime(df_active_ships_currDRS[someCol]).apply(lambda x: x.date())


od_open_tgt=df_active_ships_currDRS.query("ship_name == @vslName and (@todaydt-dt_ocurred > 90) and (status.str.contains('OPEN'))")
st.write(od_open_tgt)