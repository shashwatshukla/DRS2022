import plotly.express as px
import streamlit as st
import pandas as pd
import sqlite3 as sq
from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from helpers import get_data, get_vessel_byfleet
import datetime



# ___________________________Declarations_____________________________
curr_year = str(datetime.datetime.now().year)
global allShips  # to hold list of all fleet shipnames for making graphs
db = r'database/mms_master.sqlite'
disp_cols = ['ship_name', 'dt_ocurred', 'target_dt', 'ext_dt', 'nc_detail', 'ext_rsn', 'ext_cmnt', 'co_eval',
             'ser_no',
             'req_num', 'est_cause_ship',
             'init_action_ship', 'init_action_ship_dt',
             'final_action_ship', 'final_action_ship_dt', 'corr_action', 'rpt_by', 'insp_by',
             'insp_detail',
             'update_by', 'update_dt']  # list of cols to be displayed on the screen

# _______________Data collection_______________________
df_rawDRS = get_data(db, 'drsend')


filter_cont1=st.expander('Filters')
with filter_cont1:
    col1,col2,col3=st.columns(3)
    with col1:

        docking = st.checkbox("Remove DD Jobs", value=True)


    with col2:
        status=st.radio('Status',('OPEN','CLOSE','ALL'))
    with col3:
        active_vsl = st.radio('Select Vessels', ('All', 'Active'),index=1)
        if active_vsl == 'All':
            vsl_list_fleetwise = get_vessel_byfleet(0)
        else:
            vsl_list_fleetwise = get_vessel_byfleet(1)
        fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(), default='All vessels',
                                 key='fleet_exp1')

    vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName], []) # get vsl names as per flt selected and flatten the list (sum)
    vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt),key='vessel_exp1')


df_currDRS = df_rawDRS.query("ship_name == @vslName and (dt_ocurred.str.contains(@curr_year) or done_dt.str.contains(@curr_year) or status.str.contains('OPEN'))", engine='python')