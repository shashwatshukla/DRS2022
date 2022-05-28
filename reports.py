import plotly.express as px
import streamlit as st
import pandas as pd


from helpers import get_data, get_vessel_byfleet
import datetime
from datetime import timedelta
import seaborn as sns
st.set_page_config(page_title='DR Sender', layout='wide')

# ___________________________Declarations_____________________________
curr_year = str(datetime.datetime.now().year)
todaydt=pd.Timestamp('today').date()
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
df_active_ships_currDRS = df_active_ships.query("ship_name == @vslName and (dt_ocurred.str.contains(@curr_year)"
                              " or done_dt.str.contains(@curr_year) or status.str.contains('OPEN'))", engine='python')
df_active_ships_currDRS['dt_today']=str(todaydt) # add today date col for comparison
def convert(dt):
    return datetime.datetime.strptime(dt, "%Y-%m-%d")
df_active_ships_currDRS['dt_ocurred']=df_active_ships_currDRS['dt_ocurred'].apply(convert)
df_active_ships_currDRS['dt_today']=df_active_ships_currDRS['dt_today'].apply(convert)
#df_active_ships_currDRS['done_dt']=df_active_ships_currDRS['done_dt'].apply(convert)
#df_active_ships_currDRS['ext_dt']=df_active_ships_currDRS['ext_dt'].apply(convert)
df_open_past_target=df_active_ships_currDRS.query("ship_name == @vslName and target_dt<dt_today and status=='OPEN'", engine='python')
df_open_past_90=df_active_ships_currDRS[(df_active_ships_currDRS.ship_name.isin(vslName))
                                        & (df_active_ships_currDRS.dt_ocurred+timedelta(days=90)<df_active_ships_currDRS.dt_today)
                                        & (df_active_ships_currDRS.status=='OPEN')]
df_closed_od=df_active_ships_currDRS[(df_active_ships_currDRS.ship_name.isin(vslName))
                                     & (df_active_ships_currDRS.dt_ocurred+timedelta(days=90)<df_active_ships_currDRS.done_dt)
                                     & (df_active_ships_currDRS.status=='CLOSE')]

cnt_open_past_90=df_open_past_90['ship_name'].value_counts().rename_axis('Vessels').reset_index(name='Count of Open > 90 days')


#st.write(df_open_past_90.groupby("ship_name")["status"].count())

fig=px.bar(cnt_open_past_90,color='Vessels',x='Vessels',y='Count of Open > 90 days')
df_open_past_90.nc_detail=df_open_past_90.nc_detail.str.wrap(50)
df_open_past_90.nc_detail=df_open_past_90.nc_detail.apply(lambda x : x.replace('\n','<br>') )
fig2=px.bar(df_open_past_90,x='ship_name',y=df_open_past_90['nc_detail'].value_counts(),hover_data=['dt_ocurred','rpt_by','nc_detail','status'],color='ship_name')
st.plotly_chart(fig2,use_container_width=True)
