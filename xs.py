import streamlit as st
import pandas as pd
from helpers import get_data, get_vessel_byfleet
import datetime
from datetime import timedelta, date
import numpy as np
from openpyxl import load_workbook
from io import BytesIO
from shutil import copyfile


def make_xlRpt():
    def convert(dt):  # To convert string date to date time

        return datetime.datetime.strptime(dt, '%Y-%m-%d')

    def df_writer(df, file_name, row, col, heading):
        template_file = file_name
        output_file = 'KPI_report.xlsx'  # What we are saving the template as

        # Copy Template.xlsx as Result.xlsx
        copyfile(template_file, output_file)
        wb = load_workbook(output_file)
        with pd.ExcelWriter(output_file, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
            df.to_excel(writer, sheet_name='output', startrow=row, startcol=col, index=True)
            wb.save(output_file)

    def read_file(fyle):
        with open(fyle, 'rb') as filetoread:
            xlsmbyte = filetoread.read()
            return xlsmbyte

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
    df_merged['statusActiveInactive'] = pd.to_numeric(df_merged['statusActiveInactive'])
    df_merged = df_merged.loc[df_merged['statusActiveInactive'] == 1]
    df_merged = df_merged.query(
        '(dt_ocurred.str.contains(@curr_year) or done_dt.str.contains(@curr_year) or status.str.contains("OPEN"))',
        engine='python')
    # df_merged = df_merged.drop(df_merged[(df_merged.dt_ocurred < '2021-01-01')].index)  # Drop all entries before the date
    df_merged['dt_today'] = todaydt  # add today date col for overdue calc.
    df_merged['dt_ocurred'] = df_merged['dt_ocurred'].apply(convert)  # convert report date to datetime
    df_merged['dt_today'] = df_merged['dt_today'].apply(convert)

    mask1 = (df_merged.target_dt == '') \
            & (df_merged.done_dt == '') \
            & (df_merged.dt_ocurred + timedelta(
        days=90) < df_merged.dt_today)  # no target date & no close date & more than 90 days.

    mask2 = (df_merged.target_dt != '') \
            & (df_merged.done_dt == '') \
            & (df_merged.dt_today > df_merged.target_dt)  # no close date & past target date.

    mask3 = (df_merged.done_dt != '') \
            & (df_merged.done_dt > df_merged.dt_ocurred + timedelta(days=90))  # close >90 days.

    conditions = [mask1, mask2, mask3]
    values = [1, 1, 1]
    df_merged['Overdue_status'] = np.select(conditions, values)

    df_merged = df_merged.rename(columns={'vslFleet': 'Fleet', 'delay_hr': '1. Delay', 'downtime_hr': '2. DnTime',
                                          'critical_eq_tf': '4. CEq_fail', 'dispensation_tf': '7. Disp',
                                          'coc_tf': '6. COC', 'Overdue_status': 'OvDue', 'blackout_tf': '3. Blackout',
                                          'docking_tf': '5. Docking'})

    vsl_list_fleetwise = get_vessel_byfleet(1)
    dt_today = datetime.date.today()

    # dateFmTo = st.date_input('Select dates (ignore any errors when selecting dates)',[(dt_today - datetime.timedelta(days=180 * 1)), dt_today])
    # startDt = dateFmTo[0]
    # endDt = dateFmTo[1]

    # fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(),
    # default=list(vsl_list_fleetwise.keys())[0])
    fltName = vsl_list_fleetwise.keys()
    vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName],
                        [])  # get vsl names as per flt selected and flatten the list (sum)

    vsl_code = list(df_merged.vslCode.where(df_merged.ship_name.isin(vslListPerFlt)).unique())
    vsl_code = vsl_code[1:]

    df_merged[['1. Delay', '2. DnTime']] = df_merged[['1. Delay', '2. DnTime']].astype(float)
    df_merged[['1. Delay', '2. DnTime']] = df_merged[['1. Delay', '2. DnTime']].fillna(0)
    df_merged = df_merged.replace(to_replace='TRUE', value='True')
    df_merged = df_merged.replace(to_replace='FALSE', value='False')
    df_merged = df_merged.replace(to_replace='True', value=1)
    df_merged = df_merged.replace(to_replace='False', value=0)
    df_merged['rpt_by'] = df_merged['rpt_by'].str[2:]

    num_vessels_in_fleet = df_vessels[['vslFleet', 'statusActiveInactive']]
    num_vessels_in_fleet['statusActiveInactive'] = pd.to_numeric(num_vessels_in_fleet['statusActiveInactive'])
    num_vessels_in_fleet = pd.pivot_table(num_vessels_in_fleet, index=['vslFleet'], aggfunc='sum')
    num_vessels_in_fleet = num_vessels_in_fleet.rename(columns={'statusActiveInactive': 'Vsl Nos'})
    st.write(num_vessels_in_fleet)
    st.info('Fleet total')
    def makestats(name, df, fleet_name):
        df = df.loc[df.Fleet == fleet_name]
        return df

    # ----------------------------All overdue Items_______________________________________________________

    df_KPI = df_merged[
        ['Fleet', 'vslCode', 'dt_ocurred', '1. Delay', '2. DnTime', '4. CEq_fail', '3. Blackout', '7. Disp', '6. COC',
         'rpt_by', 'status', 'OvDue', '5. Docking']]

    table_fleet_KPI = pd.pivot_table(df_KPI, index=['Fleet'],
                                     values=['1. Delay', '2. DnTime', '4. CEq_fail', '3. Blackout', '7. Disp', '6. COC',
                                             'status', '5. Docking'],
                                     aggfunc='sum', fill_value=0,margins=True)
    table_fleet_KPI['1. Delay'] = table_fleet_KPI['1. Delay'].map('{:,.2f}'.format)
    table_fleet_KPI['2. DnTime'] = table_fleet_KPI['2. DnTime'].map('{:,.2f}'.format)

    table_KPI = pd.pivot_table(df_KPI, index=['Fleet', 'vslCode'],
                               values=['1. Delay', '2. DnTime', '4. CEq_fail', '3. Blackout', '7. Disp', '6. COC',
                                       'status', '5. Docking'],
                               aggfunc='sum', fill_value=0)
    table_KPI['1. Delay'] = table_KPI['1. Delay'].map('{:,.2f}'.format)
    table_KPI['2. DnTime'] = table_KPI['2. DnTime'].map('{:,.2f}'.format)

    table_fleet_ovd=pd.pivot_table(df_KPI, index=['Fleet'], aggfunc='sum', columns=['status'], values='OvDue',
                               margins=True)
    table_ovd = pd.pivot_table(df_KPI, index=['Fleet', 'vslCode'], aggfunc='sum', columns=['status'], values='OvDue',
                               margins=True)
    table_ovd = table_ovd.fillna(0)

    tbl_fleet_rpt_by=pd.pivot_table(df_KPI[['Fleet', 'rpt_by']], index=['Fleet'],
                                  aggfunc='count', columns=['rpt_by'], values='rpt_by',margins=True)
    tbl_fleet_rpt_by = tbl_fleet_rpt_by.fillna(0)
    tbl_fleet_rpt_by = tbl_fleet_rpt_by.astype(int)

    table_rpt_by = pd.pivot_table(df_KPI[['Fleet', 'vslCode', 'rpt_by', 'dt_ocurred']], index=['Fleet', 'vslCode'],
                                  aggfunc='count', columns=['rpt_by'], values='rpt_by')
    table_rpt_by = table_rpt_by.fillna(0)
    table_rpt_by = table_rpt_by.astype(int)
    flt = ['MMS-TOK', 'MMS-SG', 'MMS-SMI', 'Cargo Fleet (TOK)']
    dfs=[]



    col1, col2, col3 = st.columns([4, 2, 3])
    with col1:
        st.write(table_fleet_KPI)
        st.info('Fleet KPI breakup')
        for fleet in table_KPI.index.get_level_values(0).unique():
            KPI = table_KPI.xs(fleet, level=0)
            st.write(fleet, KPI)
    with col2:
        st.write(table_fleet_ovd)
        st.info('Fleet Overdue breakup')
        for fleet2 in table_ovd.index.get_level_values(0).unique():
            ovd = table_ovd.xs(fleet2, level=0)
            st.write(fleet2, ovd)
    with col3:
        st.write(tbl_fleet_rpt_by)
        st.info('Fleet Reporting breakup')
        for fleet3 in table_rpt_by.index.get_level_values(0).unique():
            ovd = table_rpt_by.xs(fleet3, level=0)
            st.write(fleet3, ovd)


def overdue_reports():
    st.title('Overdue Report')
    st.info('Under construction...')


if __name__ == '__main__':
    st.set_page_config(page_title='DR Sender', layout='wide')
    make_xlRpt()
