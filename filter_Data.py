import pandas as pd, sqlite3, datetime, streamlit as st
import plotly.express as px
from load_Data import get_data
def filtered_Data():
    df = []
    master_db = r'database/mms_master.sqlite'  # destination db
    st.header('DR Sender 2022')
    #  Load dataframe
    conn = sqlite3.connect(master_db)
    df = get_data(master_db,'drsend')
    df_counts = pd.read_sql_query("SELECT ship_name, "
                                  "SUM (CASE WHEN status= 'OPEN' then 1 ELSE 0 END) as 'Open',"
                                  "SUM (CASE WHEN status= 'CLOSE' then 1 ELSE 0 END) as 'Closed' "
                                  "from drsend GROUP by ship_name", conn)
    # df_overdue - pd.read_sql_query("SELECT ship_name, "
    #                               "SUM (CASE WHEN overdue= 'Yes' then 1 ELSE 0 END) as 'Overdue',"
    #                               "SUM (CASE WHEN status= 'No' then 1 ELSE 0 END) as 'OK' "
    #                               "from drsend GROUP by ship_name", conn)
    conn.close()
    conn = sqlite3.connect(r'database/mms_master.sqlite')
    dfvslMaster = pd.read_sql_query(
        'select vslName, vsl_imo, vslCode, vslFleet, cast(statusActiveInactive as text) from vessels', conn)
    dffltMaster = pd.read_sql_query('select fltNameUID, fltMainName, fltLocalName from fleet', conn)
    conn.close()

    disp_cols = ['ship_name', 'dt_ocurred', 'target_dt', 'done_dt', 'ser_no', 'nc_detail', 'est_cause_ship',
                 'init_action_ship', 'init_action_ship_dt',
                 'final_action_ship', 'final_action_ship_dt', 'co_eval',
                 'reason_rc', 'corr_action', 'rpt_by', 'insp_by', 'insp_detail', 'update_by', 'update_dt',
                 'ext_dt', 'ext_rsn', 'req_num', 'ext_cmnt', 'sys_code', 'eq_code']

    drsHeaders = df.columns.values
    # st.dataframe(drsHeaders)

    dfSelected = df[
        ['ship_name','vsl_imo', 'dt_ocurred', 'ser_no', 'def_code', 'rpt_by', 'insp_detail', 'nc_detail', 'init_action_ship',
         'final_action_ship', 'reason_rc', 'co_eval', 'corr_action', 'target_dt', 'done_dt', 'status', 'delay_hr',
         'downtime_hr', 'Severity', 'overdue', 'ext_rsn', 'ext_dt', 'ext_cmnt', 'brkdn_tf', 'critical_eq_tf',
         'blackout_tf',
         'docking_tf', 'coc_tf', 'est_cause_ship', 'init_action_ship_dt', 'final_action_ship_dt', 'insp_by',
         'update_by', 'update_dt', 'req_num', 'sys_code', 'eq_code']]

    filterContainer = st.expander('Filter the data and download here')
    col1, col2, col3, col4 = filterContainer.columns(4)

    with col2:
        df_vessel = get_data(r'database/mms_master.sqlite', 'vessels')
        df_fleet = get_data(r'database/mms_master.sqlite', 'fleet')
        flt_list = dict(df_fleet[['fltLocalName', 'fltNameUID']].values)
        df_merged = pd.merge(dfSelected, df_vessel[['vsl_imo', 'statusActiveInactive', 'vslFleet']], on='vsl_imo',
                             how='left')  # brig col from vessel to drsend dataframe
        df_active_ships = df_merged.drop(df_merged.index[df_merged['statusActiveInactive'] == '0'])
        fltList = {
            list(flt_list.keys())[i]: sorted(list(df_active_ships.loc[df_active_ships['vslFleet'] == str(list(flt_list.values())[i])
            , 'ship_name'].unique())) for i in range(len(flt_list))}  # all vesssel fleet wise using dict comprehension
        uniqShips = list(df_active_ships['ship_name'].unique())  # get list of unique ships from DB

        fltList['All vessels']=sorted(uniqShips) # Added all ships manually to dict



        fltName = st.multiselect('Select the Fleet', options=fltList.keys(), default=list(flt_list.keys())[0])
        statusNow = st.multiselect('Status:', options=('OPEN', 'CLOSE'), default=('OPEN'))
        docking = st.multiselect("Docking", options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))

    with filterContainer:
        vslListPerFlt = sum([fltList[x] for x in fltName],
                            [])  # get vsl names as per flt selected and flatten the list (sum)
        vslName = st.multiselect('Select the vessel:', options=vslListPerFlt, default=vslListPerFlt)
        df_sel_vsl_counts = (df_counts[df_counts['ship_name'].isin(vslName)])
        #st.write(df_sel_vsl_counts)
        fig = px.bar(df_sel_vsl_counts, x="ship_name", y=["Closed", "Open"], barmode='stack', height=400)
        st.plotly_chart(fig)

    with col3:
        criticalEq = st.multiselect('Critical Equipment', options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))
        blackout = st.multiselect('Blackout', options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))
        brkdn = st.multiselect('Breakdown', options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))



    with col1:
        dt_today = datetime.date.today()
        dateFmTo = st.date_input('Select dates (ignore any errors when selecting dates)',
                                 [(dt_today - datetime.timedelta(days=365 * 1)), dt_today])
        startDt = dateFmTo[0]
        endDt = dateFmTo[1]
        # print(dateFmTo)
        # dt_slider = st.slider('choose dates', [datetime.date(year=2021,month=1,day=1),dt_today])
        mask = (df['dt_ocurred'] > str(startDt)) & (df['dt_ocurred'] <= str(endDt))
        dfSelected = dfSelected[mask]
        rptBy = st.multiselect('Reported by', options=sorted(dfSelected['rpt_by'].unique()),
                               default=['C MMS', 'F Vessel'])
        overDueStat = st.multiselect('Overdue Status', options=['Yes', 'No'], default=['Yes', 'No'])

        with col4:
            severity = st.multiselect('Severity:', options=dfSelected['Severity'].unique(),
                                      default=dfSelected['Severity'].unique())
            coc = st.multiselect('CoC', options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))
            searchText = st.text_input('Search')

    with filterContainer:
        #  now filter the dataframe using all above filter settings
        dfFiltered = dfSelected.query("ship_name == @vslName & status == @statusNow & brkdn_tf == @brkdn "
                                      "& critical_eq_tf == @criticalEq & docking_tf == @docking & blackout_tf == @blackout"
                                      "& coc_tf == @coc & overdue == @overDueStat & Severity == @severity & rpt_by == @rptBy")

        dfFiltered = dfFiltered[dfFiltered['nc_detail'].str.contains(searchText, regex=False)]  # search on text entered
        st.dataframe(dfFiltered[disp_cols], height=600)


    with col4:  # download button and file
        csv = dfFiltered.to_csv().encode('utf-8')  # write df to csv
        btnMsg = 'Download ' + str(dfFiltered.shape[0]) + ' Records as CSV'
        st.download_button(btnMsg, csv, "DRS-file.csv", "text/csv", key='download-csv')

    print('----------------')  # --------------------------------------------

    with st.expander('RAW DATA'):
        st.dataframe(df)
        csv = df.to_csv().encode('utf-8')  # write df to csv
        btnMsg = 'Download ALL Records as CSV'
        st.download_button(btnMsg, csv, "DRS-file.csv", "text/csv", key='download-csv')
