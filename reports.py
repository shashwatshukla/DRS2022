import plotly.express as px
import streamlit as st
import pandas as pd
from helpers import get_data, get_vessel_byfleet
import datetime
st.set_page_config(page_title='DR Sender', layout='wide')
# ___________________________Declarations_____________________________
curr_year = str(datetime.datetime.now().year)
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

filter_cont1 = st.expander('Filters')
with filter_cont1:
    col1, col2, col3 = st.columns(3)
    with col1:
        docking = st.checkbox("Remove DD Jobs", value=True)
        dt_today = datetime.date.today()
        dateFmTo = st.date_input('Select dates (ignore any errors when selecting dates)',
                                 [(dt_today - datetime.timedelta(days=365 * 1)), dt_today])
        startDt = dateFmTo[0]
        endDt = dateFmTo[1]
    with col2:
        overdue1 = st.checkbox("Open > 90d", key=1)
        overdue2 = st.checkbox("Open > Target dt", key=2)
        overdue3 = st.checkbox("Close > 90d", key=3)

    with col3:
        # active_vsl = st.radio('Select Vessels', ('Active','All' ))
        # if active_vsl == 'All':
        #     vsl_list_fleetwise = get_vessel_byfleet(0)
        # else:
        vsl_list_fleetwise = get_vessel_byfleet(1)
        fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(), default='All vessels',
                                 key='fleet_exp1')

    vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName],
                        [])  # get vsl names as per flt selected and flatten the list (sum)
    vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt),
                             key='vessel_exp1')

df_active_ships = df_active_ships.query(
    "ship_name == @vslName and (dt_ocurred.str.contains(@curr_year) or done_dt.str.contains(@curr_year) or status.str.contains('OPEN'))",engine='python')


toCorrect = ["dt_ocurred", "init_action_ship_dt", "target_dt", "final_action_ship_dt", "done_dt",
                     "update_dt", "ext_dt", "PSC_picdt", "PSC_info2ownr_dt", "PSC_info2chrtr_dt", "PSC_info2rtshp_dt",
                     "PSC_info2oilmaj_dt", "PSC_info2mmstpmgmt_dt", "PSC_sndr_offimport_dt"]  #
for someCol in toCorrect:
    df_active_ships[someCol] = pd.to_datetime(df_active_ships[someCol], errors='coerce').apply(
                lambda x: x.date())  # , format="%Y/%m/%d")#.dt.date
df_active_ships_overdue=df_active_ships[df_active_ships['overdue']=="Yes"]
df_active_ships=df_active_ships[disp_cols]


st.write(df_active_ships)