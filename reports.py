import plotly.express as px
import streamlit as st
import pandas as pd
from helpers import get_data, get_vessel_byfleet
import datetime
from datetime import timedelta
from plotly.subplots import make_subplots
import numpy as np


def dummy():


    # ___________________________Declarations_____________________________
    curr_year = str(datetime.datetime.now().year)
    todaydt = str(pd.Timestamp('today').date())
    db = r'assets/mms_master.sqlite'
    st.info('Overdue Criteria:  \n'
            'The following criteria is applied for overdue calculations  \n'
            'Cat 1: The def is OPEN & not extended & more than 90 days have passed since the date reported & there is no target date.  \n'
            'Cat 2: The def is OPEN & not extended & target date has passed.  \n'
            'Cat 3: The def is OPEN & extension date has passed.  \n'
            'Cat 4: The def is CLOSED but it was closed beyond the extension date in case it was extended.  \n'
            'Cat 5: The def was not extended but it was closed in more than 90 days.')

    # _______________Data collection_______________________

    df_rawDRS = get_data(db, 'drsend')
    df_vessels = get_data(db, 'vessels')
    df_merged = pd.merge(df_rawDRS, df_vessels[
        ['vsl_imo', 'vslCode', 'statusActiveInactive', 'vslFleet', 'vslMarSI', 'vslTechSI']], on='vsl_imo',
                         how='left')
    df_active_ships = df_merged.drop(
        df_merged.index[df_merged['statusActiveInactive'] == '0'])  # drop inactive ships
    df_active_ships = df_active_ships.drop(
        df_active_ships[(df_active_ships.dt_ocurred < '2019-12-23')].index)  # Drop all entries before
    vsl_list_fleetwise = get_vessel_byfleet(1)
    fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(), default='MMS-TOK')
    vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName],
                        [])  # get vsl names as per flt selected and flatten the list (sum)

    vsl_code = df_active_ships.vslCode.where(df_active_ships.ship_name.isin(vslListPerFlt))

    vsl_code.dropna(axis=0, inplace=True, how=None)
    vsl_code.sort_values(ascending=True, inplace=True)

    vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt))
    col1, col2, col3 = st.columns(3)
    with col3:
        docking = st.checkbox('Include Docking Items')

    df_active_ships_currDRS = df_active_ships.query("ship_name == @vslName and (dt_ocurred.str.contains(@curr_year)"
                                                    " or done_dt.str.contains(@curr_year) or status.str.contains('OPEN'))",
                                                    engine='python')
    if not docking:
        df_active_ships_currDRS = df_active_ships_currDRS[(df_active_ships_currDRS.ext_rsn != 'Docking')]

    df_active_ships_currDRS['dt_today'] = todaydt  # add today date col for overdue calc.

    def convert(dt):  # To convert string date to date time
        return datetime.datetime.strptime(dt, "%Y-%m-%d")

    df_active_ships_currDRS['dt_ocurred'] = df_active_ships_currDRS['dt_ocurred'].apply(
        convert)  # convert report date to datetime
    df_active_ships_currDRS['dt_today'] = df_active_ships_currDRS['dt_today'].apply(convert)
    # df_active_ships_currDRS['done_dt']=df_active_ships_currDRS['done_dt'].apply(convert)
    # df_active_ships_currDRS['ext_dt']=df_active_ships_currDRS['ext_dt'].apply(convert)
    df_active_ships_currDRS_within_ext = df_active_ships_currDRS[(df_active_ships_currDRS.status == 'OPEN')
                                                                 & (
                                                                             df_active_ships_currDRS.ext_dt > df_active_ships_currDRS.dt_today)]  # ext. date is more than today and OPEN
    # st.write(df_active_ships_currDRS.shape)
    df_active_ships_currDRS = df_active_ships_currDRS[~df_active_ships_currDRS.DRS_ID.isin(
        df_active_ships_currDRS_within_ext.DRS_ID)]  # Drop all those where ext. date is more than today and OPEN
    # st.write(df_active_ships_currDRS.shape)

    # _________________________________ Filters for overdue

    mask1 = (df_active_ships_currDRS.ship_name.isin(vslName)) \
            & (df_active_ships_currDRS.status == 'OPEN') \
            & (df_active_ships_currDRS.ext_dt == '') \
            & (df_active_ships_currDRS.dt_ocurred + timedelta(days=90) < df_active_ships_currDRS.dt_today) \
            & (
                        df_active_ships_currDRS.target_dt == '')  # The def is OPEN & not extended & more than 90 days have passed since the date reported & there is no target date.

    mask2 = (df_active_ships_currDRS.ship_name.isin(vslName)) \
            & (df_active_ships_currDRS.status == 'OPEN') \
            & (df_active_ships_currDRS.ext_dt == '') \
            & (
                        df_active_ships_currDRS.dt_today > df_active_ships_currDRS.target_dt)  # The def is OPEN & not extended &
    # target date has passed.

    mask3 = (df_active_ships_currDRS.ship_name.isin(vslName)) \
            & (df_active_ships_currDRS.status == 'OPEN') \
            & (
                        df_active_ships_currDRS.dt_today > df_active_ships_currDRS.ext_dt)  # The def is OPEN & extension date
    # has passed.

    mask4 = (df_active_ships_currDRS.ship_name.isin(vslName)) \
            & (df_active_ships_currDRS.status == 'CLOSE') \
            & (df_active_ships_currDRS.ext_dt != '') \
            & (
                        df_active_ships_currDRS.ext_dt < df_active_ships_currDRS.done_dt)  # The def is CLOSED but it was closed beyond the extension date in case it was extended.

    mask5 = (df_active_ships_currDRS.ship_name.isin(vslName)) \
            & (df_active_ships_currDRS.status == 'CLOSE') \
            & (df_active_ships_currDRS.ext_dt == '') \
            & (df_active_ships_currDRS.done_dt > df_active_ships_currDRS.dt_ocurred + timedelta(
        days=90))  # The def was not extended but it was closed in more than 90 days.

    conditions = [mask1, mask2, mask3, mask4, mask5]
    values = ['cat1', 'cat2', 'cat3', 'cat4', 'cat5']
    df_active_ships_currDRS['overdue_cat'] = np.select(conditions, values)
    df_active_ships_currDRS.overdue_cat = df_active_ships_currDRS.overdue_cat.replace('0', 'not_od')

    # ----------------------------All overdue Items_______________________________________________________
    df_active_ships_currDRS.nc_detail = df_active_ships_currDRS.nc_detail.str.wrap(50)
    df_active_ships_currDRS.nc_detail = df_active_ships_currDRS.nc_detail.apply(lambda x: x.replace('\n', '<br>'))
    df_all_overdue = df_active_ships_currDRS[mask1 | mask2 | mask3 | mask4 | mask5]

    df_mask1 = df_active_ships_currDRS[mask1]
    df_mask2 = df_active_ships_currDRS[mask2]
    df_mask3 = df_active_ships_currDRS[mask3]
    df_mask4 = df_active_ships_currDRS[mask4]
    df_mask5 = df_active_ships_currDRS[mask5]
    fig_all_overdue = px.bar(df_all_overdue, x='vslCode', y=df_all_overdue['DRS_ID'].value_counts()
                             , hover_data=['dt_ocurred', 'done_dt', 'target_dt', 'ext_dt', 'rpt_by', 'nc_detail',
                                           'status', 'ext_rsn', 'overdue_cat'],
                             color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_all_overdue.update_layout(
        title="All overdue Items",
        xaxis_title="Vessels",
        yaxis_title="Count of Overdue",
        showlegend=True, )
    fig_all_overdue.update_xaxes(categoryorder='array',
                                 categoryarray=vsl_code)
    fig_mask1 = px.bar(df_mask1, x='vslCode', y=df_mask1['DRS_ID'].value_counts()
                       ,
                       hover_data=['dt_ocurred', 'done_dt', 'target_dt', 'ext_dt', 'rpt_by', 'nc_detail', 'status',
                                   'ext_rsn'],
                       color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_mask1.update_layout(
        title="Cat 1 Items",
        xaxis_title="Vessels",
        yaxis_title="Count of Overdue",
        showlegend=True, )
    fig_mask1.update_xaxes(categoryorder='array', categoryarray=vsl_code)

    fig_mask2 = px.bar(df_mask2, x='vslCode', y=df_mask2['DRS_ID'].value_counts()
                       ,
                       hover_data=['dt_ocurred', 'done_dt', 'target_dt', 'ext_dt', 'rpt_by', 'nc_detail', 'status',
                                   'ext_rsn'],
                       color_discrete_sequence=px.colors.qualitative.Pastel, color='rpt_by')
    fig_mask2.update_layout(
        title="Cat 2 Items",
        xaxis_title="Vessels",
        yaxis_title="Count of Overdue",
        showlegend=True, )
    fig_mask2.update_xaxes(categoryorder='array',
                           categoryarray=vsl_code)

    fig_mask3 = px.bar(df_mask3, x='vslCode', y=df_mask3['DRS_ID'].value_counts()
                       ,
                       hover_data=['dt_ocurred', 'done_dt', 'target_dt', 'ext_dt', 'rpt_by', 'nc_detail', 'status',
                                   'ext_rsn'],
                       color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_mask3.update_layout(
        title="Cat 3 Items",
        xaxis_title="Vessels",
        yaxis_title="Count of Overdue",
        showlegend=True, )
    fig_mask3.update_xaxes(categoryorder='array',
                           categoryarray=vsl_code)

    fig_mask4 = px.bar(df_mask4, x='vslCode', y=df_mask4['DRS_ID'].value_counts()
                       ,
                       hover_data=['dt_ocurred', 'done_dt', 'target_dt', 'ext_dt', 'rpt_by', 'nc_detail', 'status',
                                   'ext_rsn'],
                       color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_mask4.update_layout(
        title="Cat 4 Items",
        xaxis_title="Vessels",
        yaxis_title="Count of Overdue",
        showlegend=True, )
    fig_mask4.update_xaxes(categoryorder='array',
                           categoryarray=vsl_code)

    fig_mask5 = px.bar(df_mask5, x='vslCode', y=df_mask5['DRS_ID'].value_counts()
                       ,
                       hover_data=['dt_ocurred', 'done_dt', 'target_dt', 'ext_dt', 'rpt_by', 'nc_detail', 'status',
                                   'ext_rsn'],
                       color_discrete_sequence=px.colors.qualitative.Pastel)

    fig_mask5.update_layout(
        title="Cat 5 Items",
        xaxis_title="Vessels",
        yaxis_title="Count of Overdue",
        showlegend=True, )
    fig_mask5.update_xaxes(categoryorder='array',
                           categoryarray=vsl_code)

    # --------------------------Display graphs

    with col1:
        st.plotly_chart(fig_all_overdue, use_container_width=True)
        st.plotly_chart(fig_mask3, use_container_width=True)

    with col2:
        st.plotly_chart(fig_mask1, use_container_width=True)
        st.plotly_chart(fig_mask4, use_container_width=True)

    with col3:
        st.plotly_chart(fig_mask2, use_container_width=True)
        st.plotly_chart(fig_mask5, use_container_width=True)



def overdue_reports():
    st.title('Overdue Report')
    st.info('Under construction...')

if __name__ == '__main__':
    st.set_page_config(page_title='DR Sender', layout='wide')
    dummy()
