import streamlit as st
import pandas as pd
from helpers import get_data, get_vessel_byfleet
import datetime
from datetime import timedelta
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
import numpy as np
from openpyxl import load_workbook
from io import BytesIO


def make_xlRpt():
    def df_writer(df_list, file_name):
        wb = load_workbook(file_name)
        ws = wb['output']
        ws.delete_rows(2, 100)
        wb.save('KPI_report.xlsx')
        wb.close()
        with pd.ExcelWriter(file_name, mode="a", engine="openpyxl", if_sheet_exists='overlay') as writer:
            col = 0
            for dataframe in df_list:
                dataframe.to_excel(writer, sheet_name=sheets, startrow=1, startcol=col, index=True)
                col=col+len(dataframe.columns)+3
                st.write(col)


    def read_file(fyle):
        with open(fyle, "rb") as filetoread:
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
    df_merged["statusActiveInactive"]=pd.to_numeric(df_merged["statusActiveInactive"])
    print(df_merged.dtypes)
    df_merged = df_merged.loc[df_merged["statusActiveInactive"] == 1]

    mask1 = (df_merged.target_dt == '') \
            & (df_merged.done_dt == '') \
            & (df_merged.dt_ocurred + timedelta(
        days=90) < df_merged.dt_today)  # no target date & no close date & more than 90 days.

    mask2 = (df_merged.target_dt != '') \
            & (df_merged.done_dt == '') \
            & (df_merged.dt_today > df_merged.target_dt)  # no close date & past target date.

    mask3 = (df_merged.done_dt != '') \
            & (df_merged.done_dt > df_merged.dt_ocurred + timedelta(
        days=90))  # close >90 days.

    conditions = [mask1, mask2, mask3]
    values = [1, 1, 1]
    df_merged['Overdue_status'] = np.select(conditions, values)

    df_active_ships = df_merged  # drop inactive ships
    df_active_ships = df_active_ships.drop(
        df_active_ships[(df_active_ships.dt_ocurred < '2022-01-01')].index)  # Drop all entries before
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

    docking = st.checkbox('Include Docking Items')
    df_active_ships_currDRS = df_active_ships.query("(dt_ocurred.str.contains(@curr_year) or done_dt.str.contains(@curr_year))",engine='python')

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




    df_KPI = df_active_ships_currDRS[
        ['vslFleet','vslCode', 'dt_ocurred', "delay_hr", "downtime_hr", 'critical_eq_tf', "blackout_tf", "docking_tf",
         "dispensation_tf", "coc_tf"]]
    df_KPI = df_KPI.rename(columns={'delay_hr': 'Delay', 'downtime_hr': 'DnTime',
                                            'critical_eq_tf': 'CEq_fail', 'dispensation_tf': 'Disp',
                                            'coc_tf': 'COC', 'Overdue_status': 'OvDue', 'blackout_tf': 'Blackout',
                                            'docking_tf': 'Docking'})

    df_Rpt_by = df_active_ships_currDRS[['dt_ocurred', 'vslCode', 'rpt_by']]# for report stats
    df_Rpt_by['rpt_by']=df_Rpt_by['rpt_by'].str[2:]
    df_Ovd = df_active_ships_currDRS[['vslCode', 'status', 'Overdue_status', 'DRS_ID']]
    df_Ovd = pd.pivot_table(df_Ovd, index=['vslCode'], aggfunc='sum', columns=['status'], values='Overdue_status')
    df_Ovd = df_Ovd.fillna(0)
    df_Ovd = df_Ovd.astype(int)
    df_Rpt_by = pd.pivot_table(df_Rpt_by, index=['vslCode'], aggfunc='count', columns=['rpt_by'], values='rpt_by')
    df_Rpt_by = df_Rpt_by.fillna(0)
    df_Rpt_by = df_Rpt_by.astype(int)

    col1, col2, col3 = st.columns([3, 1, 2])
    with col2:
        st.header('Overdue Status')
        st.write(df_Ovd)

    gb = GridOptionsBuilder.from_dataframe(df_KPI)
    gb.configure_pagination()
    gb.configure_side_bar()
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
    gridOptions = gb.build()

    # AgGrid(df_KPI, gridOptions=gridOptions, enable_enterprise_modules=True)

    df_KPI_pvt = pd.pivot_table(df_KPI, index=['vslCode'], aggfunc='sum')
    df_KPI_flt = pd.pivot_table(df_KPI, index=['vslFleet'], aggfunc='sum')




    with col1:
        st.header('KPI')
        # df_KPI.replace(to_replace=0, value=pd.NA, inplace=True )
        st.write(df_KPI_flt.style.format(subset=['Delay', 'DnTime'], formatter="{:.2f}"))
        st.write(df_KPI_pvt.style.format(subset=['Delay', 'DnTime'], formatter="{:.2f}"))
        df_delay = df_KPI[['Delay', 'DnTime']]
        df_KPI = df_KPI[['CEq_fail', 'Disp', 'COC', 'Blackout']]
        st.bar_chart(df_delay)
        st.bar_chart(df_KPI)
    dfs = [df_KPI, df_Rpt_by, df_Ovd]
    df_writer(dfs, 'KPI_report.xlsx')

    def makestats(dataframe,fleet_name):
        dfA=pd.pivot_table(dataframe, index=['vslCode'], aggfunc='sum')


    with col3:
        st.header('Reported By')
        st.write(df_Rpt_by)
        st.download_button(label="Download Report",
                           data=read_file('KPI_report.xlsx'),
                           file_name='Report.xlsx',
                           mime='application/vns.ms-excel')




def overdue_reports():
    st.title('Overdue Report')
    st.info('Under construction...')


if __name__ == '__main__':
    st.set_page_config(page_title='DR Sender', layout='wide')
    make_xlRpt()
