import plotly.express as px
import streamlit as st
import pandas as pd
from helpers import get_data, get_vessel_byfleet
import datetime
from datetime import timedelta

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
df_active_ships = df_merged.drop(df_merged.index[df_merged['statusActiveInactive'] == '0']) # drop inactive ships

vsl_list_fleetwise = get_vessel_byfleet(1)
fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(), default='MMS-TOK')
vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName], []) # get vsl names as per flt selected and flatten the list (sum)
vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt))

df_active_ships_currDRS = df_active_ships.query("ship_name == @vslName and (dt_ocurred.str.contains(@curr_year)"
                              " or done_dt.str.contains(@curr_year) or status.str.contains('OPEN'))", engine='python')
df_active_ships_currDRS['dt_today']=str(todaydt) # add today date col for overdue calc.
def convert(dt): # To convert string date to date time
    return datetime.datetime.strptime(dt, "%Y-%m-%d")

df_active_ships_currDRS['dt_ocurred']=df_active_ships_currDRS['dt_ocurred'].apply(convert) # convert report date to datetime
df_active_ships_currDRS['dt_today']=df_active_ships_currDRS['dt_today'].apply(convert)
#df_active_ships_currDRS['done_dt']=df_active_ships_currDRS['done_dt'].apply(convert)
#df_active_ships_currDRS['ext_dt']=df_active_ships_currDRS['ext_dt'].apply(convert)
df_active_ships_currDRS_within_ext=df_active_ships_currDRS[(df_active_ships_currDRS.status=='OPEN')
                                                            & (df_active_ships_currDRS.ext_dt>df_active_ships_currDRS.dt_today)] # ext. date is more than today and OPEN
# st.write(df_active_ships_currDRS.shape)
df_active_ships_currDRS=df_active_ships_currDRS[~df_active_ships_currDRS.DRS_ID.isin(df_active_ships_currDRS_within_ext.DRS_ID)]# Drop all those where ext. date is more than today and OPEN
# st.write(df_active_ships_currDRS.shape)
df_active_ships_currDRS_ext_past_today=df_active_ships_currDRS[(df_active_ships_currDRS.ship_name.isin(vslName))
                                                               & (df_active_ships_currDRS.dt_today>df_active_ships_currDRS.ext_dt)
                                                               & (df_active_ships_currDRS.dt_today>df_active_ships_currDRS.target_dt)
                                                               & (df_active_ships_currDRS.status=='OPEN')] # get OPEN items where ext. date has passed.

df_open_past_target=df_active_ships_currDRS[(df_active_ships_currDRS.ship_name.isin(vslName))
                                            & (df_active_ships_currDRS.target_dt<df_active_ships_currDRS.dt_today)
                                            & (df_active_ships_currDRS.status=='OPEN')] # OPEN and more than target date
df_open_past_90=df_active_ships_currDRS[(df_active_ships_currDRS.ship_name.isin(vslName))
                                        & (df_active_ships_currDRS.dt_ocurred+timedelta(days=90)<df_active_ships_currDRS.dt_today)
                                        & (df_active_ships_currDRS.status=='OPEN')
                                        & (df_active_ships_currDRS.ext_rsn=='')] # OPEN and more than 90 days without valid reason
df_closed_od=df_active_ships_currDRS[(df_active_ships_currDRS.ship_name.isin(vslName))
                                     & (df_active_ships_currDRS.dt_ocurred+timedelta(days=90)<df_active_ships_currDRS.done_dt)
                                     & (df_active_ships_currDRS.status=='CLOSE')] # CLOSED in more than 90 days
#st.write(df_open_past_90.groupby("ship_name")["status"].count())
#----------------------------Graph for OPEN and more than target date
df_open_past_target.nc_detail=df_open_past_target.nc_detail.str.wrap(50)
df_open_past_target.nc_detail=df_open_past_target.nc_detail.apply(lambda x : x.replace('\n','<br>') )
fig_open_past_target=px.bar(df_open_past_target,x='ship_name',y=df_open_past_target['DRS_ID'].value_counts()
            ,hover_data=['dt_ocurred','target_dt','ext_dt','rpt_by','nc_detail','status'],color_discrete_sequence=px.colors.qualitative.Safe)
fig_open_past_target.update_layout(
    title="Open Def. Past target date",
    xaxis_title="Vessels",
    yaxis_title="Count of Overdue",
    showlegend=False,
    font=dict(
        family="Lato",
        size=15,
        color="Black"
    ))
fig_open_past_target.update_xaxes(categoryorder='array',
                             categoryarray=sorted(df_active_ships_currDRS['ship_name']))

#----------------------------Graph for OPEN and more than 90 days without valid reason
df_open_past_90.nc_detail=df_open_past_90.nc_detail.str.wrap(50)
df_open_past_90.nc_detail=df_open_past_90.nc_detail.apply(lambda x : x.replace('\n','<br>') )
fig_open_past_90=px.bar(df_open_past_90,x='ship_name',y=df_open_past_90['DRS_ID'].value_counts()
            ,hover_data=['dt_ocurred','target_dt','ext_dt','rpt_by','nc_detail','status'],color_discrete_sequence=px.colors.qualitative.Pastel1)
fig_open_past_90.update_layout(
    title="Open Def. Past 90 Days",
    xaxis_title="Vessels",
    yaxis_title="Count of Overdue",
    showlegend=False,
    font=dict(
        family="Lato",
        size=15,
        color="Black"
    ))
fig_open_past_90.update_xaxes(categoryorder='array',
                             categoryarray=sorted(df_active_ships_currDRS['ship_name']))

#----------------------------Graph for CLOSED in more than 90 days
df_closed_od.nc_detail=df_closed_od.nc_detail.str.wrap(50)
df_closed_od.nc_detail=df_closed_od.nc_detail.apply(lambda x : x.replace('\n','<br>') )
fig_closed_od=px.bar(df_closed_od,x='ship_name',y=df_closed_od['DRS_ID'].value_counts()
            ,hover_data=['dt_ocurred','done_dt','rpt_by','nc_detail','status'],color_discrete_sequence=px.colors.qualitative.Pastel)
fig_closed_od.update_layout(
    title="Closed but Ovrdue",
    xaxis_title="Vessels",
    yaxis_title="Count of Overdue",
    showlegend=False,
    font=dict(
        family="Lato",
        size=15,
        color="Black"
    ))

fig_closed_od.update_xaxes(categoryorder='array',
                             categoryarray=sorted(df_active_ships_currDRS['ship_name']))
#----------------------------Graph for OPEN items where ext. date has passed (count).
df_active_ships_currDRS_ext_past_today.nc_detail=df_active_ships_currDRS_ext_past_today.nc_detail.str.wrap(50)
df_active_ships_currDRS_ext_past_today.nc_detail=df_active_ships_currDRS_ext_past_today.nc_detail.apply(lambda x : x.replace('\n','<br>') )
fig_ext_past_today=px.bar(df_active_ships_currDRS_ext_past_today,x='ship_name',y=df_active_ships_currDRS_ext_past_today['DRS_ID'].value_counts()
            ,hover_data=['dt_ocurred','done_dt','rpt_by','nc_detail','status','ext_rsn'],color_discrete_sequence=px.colors.qualitative.Pastel)
fig_ext_past_today.update_layout(
    title="Extended and not closed within Extended Date",
    xaxis_title="Vessels",
    yaxis_title="Count of Overdue",
    showlegend=False,
    font=dict(
        family="Lato",
        size=15,
        color="Black"
    ))
fig_ext_past_today.update_xaxes(categoryorder='array',
                             categoryarray=sorted(df_active_ships_currDRS['ship_name']))
#----------------------------Graph for OPEN items where ext. date has passed (reason).
fig_ext_past_today2=px.bar(df_active_ships_currDRS_ext_past_today,y=["ship_name"], x="ext_rsn" # df_active_ships_currDRS_ext_past_today['DRS_ID'].value_counts()
            ,hover_data=['dt_ocurred','rpt_by','nc_detail','status','ext_rsn'],color='ext_rsn',color_discrete_sequence=px.colors.qualitative.Pastel)
fig_ext_past_today2.update_layout(
    title="Extended and not closed Reasons",
    xaxis_title="Vessels",
    yaxis_title="Count of Reason",
    showlegend=True,
    font=dict(
        family="Lato",
        size=15,
        color="Black"
    ),

)
fig_ext_past_today2.update_xaxes(categoryorder='array',
                             categoryarray=sorted(df_active_ships_currDRS['ship_name']))
col1,col2,col3 = st.columns(3)
with col1:
    st.plotly_chart(fig_open_past_target, use_container_width=True)
    st.plotly_chart(fig_ext_past_today, use_container_width=True)
with col2:
    st.plotly_chart(fig_open_past_90, use_container_width=True)
    st.plotly_chart(fig_ext_past_today2, use_container_width=True)
with col3:
    st.plotly_chart(fig_closed_od, use_container_width=True)