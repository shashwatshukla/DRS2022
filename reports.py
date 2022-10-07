import streamlit as st
import pandas as pd
from helpers import get_data, get_vessel_byfleet
import datetime
from datetime import timedelta
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
import numpy as np


def dummy():
    def df_writer(df_list, sheets, file_name):
        with pd.ExcelWriter(file_name, mode="a", engine="openpyxl", if_sheet_exists='overlay') as writer:
            row = 0
            for idx, dataframe in enumerate(df_list):
                col = len(dataframe.columns)
                # if idx==0:

                if idx == 1:
                    row = 29
                if idx == 2:
                    row = 69
                dataframe.to_excel(writer, sheet_name=sheets, startrow=row, startcol=0, index=True)

    curr_year = str(datetime.datetime.now().year)
    todaydt = str(pd.Timestamp('today').date())
    db = r'assets/mms_master.sqlite'
    # _______________Data collection_______________________

    df_rawDRS = get_data(db, 'drsend')
    df_vessels = get_data(db, 'vessels')
    df_merged = pd.merge(df_rawDRS, df_vessels[
        ['vsl_imo', 'vslCode', 'statusActiveInactive', 'vslFleet', 'vslMarSI', 'vslTechSI']], on='vsl_imo',
                         how='left')

    df_merged = df_merged.dropna(subset=['statusActiveInactive'])
    df_merged["statusActiveInactive"]=pd.to_numeric(df_merged["statusActiveInactive"])
    print(df_merged.dtypes)
    df_merged = df_merged.loc[df_merged["statusActiveInactive"] == 1]
    st.write(df_merged)
    df_active_ships = df_merged  # drop inactive ships
    df_active_ships = df_active_ships.drop(
        df_active_ships[(df_active_ships.dt_ocurred < '2019-12-23')].index)  # Drop all entries before
    vsl_list_fleetwise = get_vessel_byfleet(1)
    dt_today = datetime.date.today()

    dateFmTo = st.date_input('Select dates (ignore any errors when selecting dates)',
                             [(dt_today - datetime.timedelta(days=180 * 1)), dt_today])
    startDt = dateFmTo[0]
    endDt = dateFmTo[1]

    fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(),
                             default=list(vsl_list_fleetwise.keys())[0])
    vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName],
                        [])  # get vsl names as per flt selected and flatten the list (sum)

    vsl_code = list(df_active_ships.vslCode.where(df_active_ships.ship_name.isin(vslListPerFlt)).unique())
    vsl_code = vsl_code[1:]
    vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt))

    docking = st.checkbox('Include Docking Items')

    df_currDRS = df_active_ships.query(
        "ship_name == @vslName and (dt_ocurred.str.contains(@curr_year) or done_dt.str.contains(@curr_year) or status.str.contains('OPEN'))",
        engine='python')
    df_active_ships_currDRS = df_active_ships.query("ship_name == @vslName and (dt_ocurred.str.contains(@curr_year)"
                                                    " or done_dt.str.contains(@curr_year) or status.str.contains('OPEN'))",
                                                    engine='python')

    if not docking:
        df_active_ships_currDRS = df_active_ships_currDRS[(df_active_ships_currDRS.ext_rsn != 'Docking')]

    df_active_ships_currDRS['dt_today'] = todaydt  # add today date col for overdue calc.
    df_active_ships_currDRS[["delay_hr", "downtime_hr"]] = df_active_ships_currDRS[["delay_hr", "downtime_hr"]].astype(
        float)
    df_active_ships_currDRS[["delay_hr", "downtime_hr"]] = df_active_ships_currDRS[["delay_hr", "downtime_hr"]].fillna(
        0)
    df_active_ships_currDRS = df_active_ships_currDRS.replace(to_replace="TRUE", value="True")
    df_active_ships_currDRS = df_active_ships_currDRS.replace(to_replace="FALSE", value="False")
    df_active_ships_currDRS = df_active_ships_currDRS.replace(to_replace="True", value=1)
    df_active_ships_currDRS = df_active_ships_currDRS.replace(to_replace="False", value=0)

    def convert(dt):  # To convert string date to date time
        return datetime.datetime.strptime(dt, "%Y-%m-%d")

    df_active_ships_currDRS['dt_ocurred'] = df_active_ships_currDRS['dt_ocurred'].apply(
        convert)  # convert report date to datetime
    df_active_ships_currDRS['dt_today'] = df_active_ships_currDRS['dt_today'].apply(convert)
    # df_active_ships_currDRS_within_ext = df_active_ships_currDRS[(df_active_ships_currDRS.status == 'OPEN') & (df_active_ships_currDRS.ext_dt > df_active_ships_currDRS.dt_today)]  # ext. date is more than today and OPEN

    # df_active_ships_currDRS = df_active_ships_currDRS[~df_active_ships_currDRS.DRS_ID.isin(df_active_ships_currDRS_within_ext.DRS_ID)]  # Drop all those where ext. date is more than today and OPEN
    # _________________________________ Filters for overdue

    # ----------------------------All overdue Items_______________________________________________________

    mask1 = (df_active_ships_currDRS.ship_name.isin(vslName)) \
            & (df_active_ships_currDRS.target_dt == '') \
            & (df_active_ships_currDRS.done_dt == '') \
            & (df_active_ships_currDRS.dt_ocurred + timedelta(
        days=90) < df_active_ships_currDRS.dt_today)  # no target date & no close date & more than 90 days.

    mask2 = (df_active_ships_currDRS.ship_name.isin(vslName)) \
            & (df_active_ships_currDRS.target_dt != '') \
            & (df_active_ships_currDRS.done_dt == '') \
            & (
                        df_active_ships_currDRS.dt_today > df_active_ships_currDRS.target_dt)  # no close date & past target date.

    mask3 = (df_active_ships_currDRS.ship_name.isin(vslName)) \
            & (df_active_ships_currDRS.done_dt != '') \
            & (df_active_ships_currDRS.done_dt > df_active_ships_currDRS.dt_ocurred + timedelta(
        days=90))  # close >90 days.

    conditions = [mask1, mask2, mask3]
    values = [1, 1, 1]
    df_active_ships_currDRS['Overdue_status'] = np.select(conditions, values)
    # df_active_ships_currDRS.Overdue_status = df_active_ships_currDRS.Overdue_status.replace('0', 'Not Overdue')

    # overdue_group = df_active_ships_currDRS.groupby(['vslFleet', 'ship_name', 'Overdue_status'])['DRS_ID'].count()
    #
    # mask_dt = (df_active_ships_currDRS['dt_ocurred'] >= str(startDt)) & (
    #             df_active_ships_currDRS['dt_ocurred'] <= str(endDt))
    # df_active_ships_currDRS=df_active_ships_currDRS[mask_dt]

    df1 = df_active_ships_currDRS[
        ['vslCode', 'dt_ocurred', "delay_hr", "downtime_hr", 'critical_eq_tf', "blackout_tf", "docking_tf",
         "dispensation_tf", "coc_tf"]]
    # df1=df1[mask_dt]
    df2 = df_active_ships_currDRS[['dt_ocurred', 'vslCode', 'rpt_by']]
    df3 = df_active_ships_currDRS[['vslCode', 'status', 'Overdue_status', 'DRS_ID']]
    df3 = pd.pivot_table(df3, index=['vslCode'], aggfunc='sum', columns=['status'], values='Overdue_status')
    df3 = df3.fillna(0)
    df3 = df3.astype(int)
    df2 = pd.pivot_table(df2, index=['vslCode'], aggfunc='count', columns=['rpt_by'], values='rpt_by')
    df2 = df2.fillna(0)
    df2 = df2.astype(int)
    col1, col2, col3 = st.columns([3, 1, 2])
    with col2:
        st.header('Overdue Stats')
        st.write(df3)

    gb = GridOptionsBuilder.from_dataframe(df1)
    gb.configure_pagination()
    gb.configure_side_bar()
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
    gridOptions = gb.build()

    # AgGrid(df1, gridOptions=gridOptions, enable_enterprise_modules=True)
    st.write(df1)
    df1 = pd.pivot_table(df1, index=['vslCode'], aggfunc='sum')

    df1 = df1.rename(columns={'delay_hr': 'Delay(h)', 'downtime_hr': 'Downtime(h)',
                              'critical_eq_tf': 'Critical', 'dispensation_tf': 'Dispensation',
                              'coc_tf': 'COC', 'Overdue_status': 'Overdue', 'blackout_tf': 'Blackouts',
                              'docking_tf': 'Docking'})

    with col1:
        st.header('KPI Stats')
        # df1.replace(to_replace=0, value=pd.NA, inplace=True )
        # st.write(df1)
        st.write(df1.style.format(subset=['Delay(h)', 'Downtime(h)'], formatter="{:.2f}"))
        df_delay = df1[['Delay(h)', 'Downtime(h)']]
        df_KPI = df1[['Critical', 'Dispensation', 'COC', 'Blackouts']]
        st.bar_chart(df_delay)
        st.bar_chart(df_KPI)
    dfs = [df1, df2, df3]
    with col3:
        st.header('Reporting Stats')
        st.write(df2)
        write_to_file = st.button('Generate excel report')
    if write_to_file:
        df_writer(dfs, 'output', 'KPI_report.xlsx')


def overdue_reports():
    st.title('Overdue Report')
    st.info('Under construction...')


if __name__ == '__main__':
    st.set_page_config(page_title='DR Sender', layout='wide')
    dummy()
