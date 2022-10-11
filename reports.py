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

    def df_writer(df, file_name,row,col,heading):
        template_file = file_name
        output_file = 'KPI_report.xlsx'  # What we are saving the template as

        # Copy Template.xlsx as Result.xlsx
        copyfile(template_file, output_file)
        wb = load_workbook(output_file)
        with pd.ExcelWriter(output_file, mode='a', engine='openpyxl',if_sheet_exists='overlay') as writer:
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

    df_merged = df_merged.rename(columns={'vslFleet': 'Fleet', 'delay_hr': 'Delay', 'downtime_hr': 'DnTime',
                                          'critical_eq_tf': 'CEq_fail', 'dispensation_tf': 'Disp',
                                          'coc_tf': 'COC', 'Overdue_status': 'OvDue', 'blackout_tf': 'Blackout',
                                          'docking_tf': 'Docking'})


    vsl_list_fleetwise = get_vessel_byfleet(1)
    dt_today = datetime.date.today()

    # dateFmTo = st.date_input('Select dates (ignore any errors when selecting dates)',[(dt_today - datetime.timedelta(days=180 * 1)), dt_today])
    # startDt = dateFmTo[0]
    # endDt = dateFmTo[1]

    fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(),
                             default=list(vsl_list_fleetwise.keys())[0])
    vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName],
                        [])  # get vsl names as per flt selected and flatten the list (sum)

    vsl_code = list(df_merged.vslCode.where(df_merged.ship_name.isin(vslListPerFlt)).unique())
    vsl_code = vsl_code[1:]

    # docking = st.checkbox('Include Docking Items')

    # if not docking:
    #     df_merged_currDRS = df_merged_currDRS[(df_merged_currDRS.ext_rsn != 'Docking')]

    df_merged[['Delay', 'DnTime']] = df_merged[['Delay', 'DnTime']].astype(float)
    df_merged[['Delay', 'DnTime']] = df_merged[['Delay', 'DnTime']].fillna(0)
    df_merged = df_merged.replace(to_replace='TRUE', value='True')
    df_merged = df_merged.replace(to_replace='FALSE', value='False')
    df_merged = df_merged.replace(to_replace='True', value=1)
    df_merged = df_merged.replace(to_replace='False', value=0)

    def makestats(name,df, fleet_name):
        df = df.loc[df.Fleet == fleet_name]
        return df


    # ----------------------------All overdue Items_______________________________________________________

    df_KPI = df_merged[
        ['Fleet', 'vslCode', 'dt_ocurred', 'Delay', 'DnTime', 'CEq_fail', 'Blackout', 'Docking', 'Disp', 'COC']]

    df_Rpt_by = df_merged[['Fleet', 'vslCode', 'rpt_by']]  # for report stats
    df_Rpt_by['rpt_by'] = df_Rpt_by['rpt_by'].str[2:]
    df_Ovd = df_merged[['Fleet','vslCode', 'status', 'OvDue', 'DRS_ID']]
    fleet_numbrs = df_vessels[['vslFleet', 'statusActiveInactive']]
    fleet_numbrs['statusActiveInactive'] = pd.to_numeric(fleet_numbrs['statusActiveInactive'])
    fleet_numbrs = pd.pivot_table(fleet_numbrs, index=['vslFleet'], aggfunc='sum')
    fleet_numbrs = fleet_numbrs.rename(columns={'statusActiveInactive': 'Vsl Nos'})

    last_update = df_merged[['vslCode', 'dummy2']]
    last_update['dummy2'] = last_update['dummy2']

    last_update.loc[last_update["dummy2"] == "NG", "dummy2"] = '2001-01-01 20:17:52.768623_unknown@mmstokyo.co.jp'
    last_update[['update_date', 'update_by']] = last_update['dummy2'].str.split('_', expand=True)
    last_update['update_date'] = last_update['update_date'].str[:10]
    last_update['update_date'] = last_update['update_date'].astype('M8[D]')
    # last_update["update_date"] = last_update["update_date"].apply(lambda x: x.replace(tzinfo=None))
    # st.write(last_update.applymap(type))
    # last_update=pd.pivot_table(last_update,index='vslCode',columns='update_date',aggfunc='max')
    # st.write(last_update)

    col1, col2, col3 = st.columns([3, 2, 3])
    df_KPI_flt = pd.pivot_table(df_KPI, index=['Fleet'], aggfunc='sum')
    flt = ['MMS-TOK', 'MMS-SG', 'MMS-SMI', 'Cargo Fleet (TOK)']
    with col1:
        st.header('KPI')
        st.write(df_KPI_flt.style.format(subset=['Delay', 'DnTime'], formatter='{:.2f}'), use_column_width=True)
        rw=2
        df_writer(df_KPI_flt, 'KPI_template.xlsx', rw, 0, 'a')
        for i,j in enumerate(flt):
            print(rw)
            a=st.write(j,' KPI')
            df_KPI_pvt = pd.pivot_table(makestats('df_KPI_pvt',df_KPI,j), index=['vslCode'], aggfunc='sum',margins=True)
            st.write(df_KPI_pvt.style.format(subset=['Delay', 'DnTime'], formatter='{:.2f}'), use_column_width=True)

            df_writer(df_KPI_pvt,'KPI_template.xlsx',rw,0,a)
            print('-----------------------------------------------------------------------------------------------------------------------------')
            rw=rw+len(df_KPI_pvt.index)+3
            print(rw)
        # df_KPI.replace(to_replace=0, value=pd.NA, inplace=True )
        # st.write(df_KPI_flt.style.format(subset=['Delay', 'DnTime'], formatter='{:.2f}'))
        #
        df_delay = df_KPI_pvt[['Delay', 'DnTime']]
        df_KPI = df_KPI_pvt[['CEq_fail', 'Disp', 'COC', 'Blackout']]
        # st.bar_chart(df_delay)
        # st.bar_chart(df_KPI_pvt)
    with col2:
        st.header('Overdue Status')
        st.write(fleet_numbrs)
        for i,j in enumerate(flt):
            st.write(j)
            Ovd = pd.pivot_table(makestats('Ovd',df_Ovd,j), index=['vslCode'], aggfunc='sum', columns=['status'], values='OvDue',margins=True)
            Ovd = Ovd.fillna(0)
            #Ovd = df_Ovd.astype(int)
            st.write(Ovd)

    with col3:
        st.header('Reported By')
        st.write(fleet_numbrs)
        for i,j in enumerate(flt):
            st.write(j)
            Rpt_by = pd.pivot_table(makestats('Rpt_by',df_Rpt_by,j), index=['vslCode'], aggfunc='count', columns=['rpt_by'],
                                    values='rpt_by')

            Rpt_by = Rpt_by.fillna(0)
            Rpt_by = Rpt_by.astype(int)
            st.write(Rpt_by)

        # st.write(df_Rpt_by)
        st.download_button(label='Download Report',
                           data=read_file('KPI_report.xlsx'),
                           file_name=str(date.today()) + 'Report.xlsx',
                           mime='application/vns.ms-excel')


def overdue_reports():
    st.title('Overdue Report')
    st.info('Under construction...')


if __name__ == '__main__':
    st.set_page_config(page_title='DR Sender', layout='wide')
    make_xlRpt()
