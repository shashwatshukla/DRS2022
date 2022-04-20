import pandas as pd, sqlite3, datetime, streamlit as st, plotly_express as px

def filtered_Data():
    df = []
    sql3db = r'database/mms_master.sqlite'  # destination db
    st.header('DR Sender 2022')
    #  Load dataframe
    # shutil.copyfile(r'mms_master.sqlite',sql3db)
    conn = sqlite3.connect(sql3db)
    df = pd.read_sql_query('select * from drsend', conn)
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

    df[['delay_hr', 'downtime_hr', 'VET_risk']] = df[['delay_hr', 'downtime_hr', 'VET_risk']] \
        .apply(pd.to_numeric, errors='coerce', axis=1)  # make the three cols numeric
    drsHeaders = df.columns.values
    # st.dataframe(drsHeaders)

    dfSelected = df[
        ['ship_name', 'dt_ocurred', 'ser_no', 'def_code', 'rpt_by', 'insp_detail', 'nc_detail', 'init_action_ship',
         'final_action_ship', 'reason_rc', 'co_eval', 'corr_action', 'target_dt', 'done_dt', 'status', 'delay_hr',
         'downtime_hr', 'Severity', 'overdue', 'ext_rsn', 'ext_dt', 'ext_cmnt', 'brkdn_tf', 'critical_eq_tf',
         'blackout_tf',
         'docking_tf', 'coc_tf', 'est_cause_ship', 'init_action_ship_dt', 'final_action_ship_dt', 'insp_by',
         'update_by', 'update_dt', 'req_num', 'sys_code', 'eq_code']]

    filterContainer = st.expander('Filter the data and download here')
    col1, col2, col3, col4 = filterContainer.columns(4)

    with col2:
        uniqShips = list(dfSelected['ship_name'].unique())  # get list of unique ships from DB
        fltList = {'All vessels': uniqShips,
                   'Cargo': sorted(
                       ['Luminous Ace', 'Siam Ocean', 'Ken San', 'Comet Ace', 'Ken Goh', 'Ken Ryu', 'Progress Ace',
                        'Ken Mei', 'Paradise Ace', 'Ken Rei', 'Ken Toku', 'Southern Star', 'Andromeda Spirit',
                        'Kariyushi Leader', 'Ken Hope', 'Morning Clara', 'Ocean Phoenix', 'Green Phoenix',
                        'Pacific Hero', 'Glorious Ace', 'Global Phoenix', 'AM BREMEN', 'Coral Opal', 'Paraburdoo',
                        'Bulk Phoenix', 'African Teist', 'Robin Wind', 'Andes Queen', 'Loch Shuna', 'Global Coral',
                        'Blue Akihabara', 'Mi Harmony', 'Federal Tokoro', 'Santa Francesca', 'IVS Phoenix',
                        'Loch Ness', 'Loch Nevis', 'Pavo Bright', 'GT DEMETER', 'Antares Leader', 'Aries Karin',
                        'Aries Sumire', 'Ikan Bawal', 'Jubilant Devotion', 'Pavo Brave', 'Stardom Wave',
                        'Vanguardia']),
                   'Tanker1': sorted(
                       ['Tokio', 'Taiga', 'Tsushima', 'BW Tokyo', 'BW Kyoto', 'Marvel Kite',
                        'Takasago', 'Tenma', 'Esteem Astro', 'Esteem Explorer', 'Metahne Mickie Harper',
                        'Methane Patricia Camila', 'Red Admiral']),
                   'Tanker2 SMI': sorted(
                       ['Ginga Hawk', 'Ginga Kite', 'Ginga Merlin', 'Centennial Misumi',
                        'Centennial Matsuyama', 'Argent Daisy', 'Eagle Sapporo', 'Eagle Melbourne',
                        'Challenge Prospect II', 'St Clemens', 'St Pauli', 'Esteem Houston',
                        'Esteem Energy',
                        'Esteem Discovery', 'Esteem Endeavour', 'Solar Katherine', 'Solar Melissa',
                        'Solar Madelein', 'Solar Claire', 'Esteem Sango']),
                   'Tanker2 SIN': sorted(['Hafnia Nordica',
                                          'Peace Victoria', 'Orient Challenge', 'Orient Innovation', 'Crimson Jade',
                                          'Crimson Pearl', 'Hafnia Hong Kong', 'Hafnia Shanghai', 'San Jack',
                                          'Hafnia Shenzhen', 'HARRISBURG', 'Hafnia Nanjing'])
                   }

        fltName = st.multiselect('Select the Fleet', options=fltList.keys(), default='Tanker1')
        statusNow = st.multiselect('Status:', options=('OPEN', 'CLOSE'), default=('OPEN'))
        docking = st.multiselect("Docking", options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))

    with filterContainer:
        vslListPerFlt = sum([fltList[x] for x in fltName],
                            [])  # get vsl names as per flt selected and flatten the list (sum)
        vslName = st.multiselect('Select the vessel:', options=vslListPerFlt, default=vslListPerFlt)
        df_sel_vsl_counts = (df_counts[df_counts['ship_name'].isin(vslName)])
        # st.write(df_sel_vsl_counts)
        fig = px.bar(df_sel_vsl_counts, x="ship_name", y=["Closed", "Open"], barmode='stack', height=400)
        st.plotly_chart(fig)

    with col3:
        criticalEq = st.multiselect('Critical Equipment', options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))
        blackout = st.multiselect('Blackout', options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))
        brkdn = st.multiselect('Breakdown', options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))

    with col4:
        severity = st.multiselect('Severity:', options=dfSelected['Severity'].unique(),
                                  default=dfSelected['Severity'].unique())
        coc = st.multiselect('CoC', options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))
        searchText = st.text_input('Search')

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
    with st.expander("Report Generator"):
        col1,col2,col3=st.columns(3)
        with col1:
            st.date_input("Select dates")