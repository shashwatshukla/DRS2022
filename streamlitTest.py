import pandas as pd
import streamlit as st
import sqlite3, datetime, shutil, dateutil, openpyxl
sql3db = 'drsend1.sqlite' # destination db
import xlwings as xw
import plotly.express as px

st.set_page_config(page_title='DR Sender', layout='wide')
st.header('DR Sender 2022')
df=[]
#  Load dataframe
shutil.copyfile(r'C:\Shares\drsapp\drsend.sqlite',sql3db)
conn = sqlite3.connect(sql3db)
df = pd.read_sql_query('select * from dr_sender', conn)
df_counts = pd.read_sql_query("SELECT ship_name, "
                              "SUM (CASE WHEN status= 'OPEN' then 1 ELSE 0 END) as 'Open',"
                              "SUM (CASE WHEN status= 'CLOSE' then 1 ELSE 0 END) as 'Closed' "
                              "from dr_sender GROUP by ship_name", conn)
# df_overdue - pd.read_sql_query("SELECT ship_name, "
#                               "SUM (CASE WHEN overdue= 'Yes' then 1 ELSE 0 END) as 'Overdue',"
#                               "SUM (CASE WHEN status= 'No' then 1 ELSE 0 END) as 'OK' "
#                               "from dr_sender GROUP by ship_name", conn)
conn.close()
conn = sqlite3.connect('master.sqlite')
dfvslMaster = pd.read_sql_query('select vslName, vslIMO, vslCode, vslFleet, cast(statusActiveInactive as text) from vessels',conn)
dffltMaster = pd.read_sql_query('select fltNameUID, fltMainName, fltLocalName from fleet',conn)
conn.close()

disp_cols = ['ship_name', 'dt_ocurred','target_dt','done_dt', 'ser_no','nc_detail','est_cause_ship', 'init_action_ship','init_action_ship_dt',
             'final_action_ship','final_action_ship_dt', 'co_eval',
             'reason_rc','corr_action','rpt_by','insp_by','insp_detail','update_by', 'update_dt',
             'ext_dt','ext_rsn', 'req_num','ext_cmnt', 'sys_code', 'eq_code']

df[['delay_hr', 'downtime_hr', 'VET_risk']] = df[['delay_hr', 'downtime_hr', 'VET_risk']]\
    .apply(pd.to_numeric, errors='coerce', axis=1) # make the three cols numeric
drsHeaders = df.columns.values
# st.dataframe(drsHeaders)

dfSelected = df[['ship_name', 'dt_ocurred', 'ser_no', 'def_code', 'rpt_by', 'insp_detail', 'nc_detail', 'init_action_ship',
                 'final_action_ship', 'reason_rc', 'co_eval', 'corr_action', 'target_dt', 'done_dt', 'status', 'delay_hr',
                 'downtime_hr', 'Severity', 'overdue', 'ext_rsn', 'ext_dt', 'ext_cmnt', 'brkdn_tf', 'critical_eq_tf', 'blackout_tf',
                 'docking_tf', 'coc_tf','est_cause_ship', 'init_action_ship_dt', 'final_action_ship_dt', 'insp_by',
                 'update_by', 'update_dt', 'req_num', 'sys_code', 'eq_code']]

filterContainer = st.expander('Filter the data and download here')
col1, col2, col3, col4 = filterContainer.columns(4)

with col2:
    uniqShips = list(dfSelected['ship_name'].unique()) # get list of unique ships from DB
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
    criticalEq = st.multiselect('Critical Equipment',options=('TRUE','FALSE'),default=('TRUE','FALSE'))
    blackout = st.multiselect('Blackout',options=('TRUE','FALSE'),default=('TRUE','FALSE'))
    brkdn = st.multiselect('Breakdown', options=('TRUE', 'FALSE'), default=('TRUE', 'FALSE'))

with col4:
    severity = st.multiselect('Severity:', options=dfSelected['Severity'].unique(),
                              default=dfSelected['Severity'].unique())
    coc = st.multiselect('CoC',options=('TRUE','FALSE'),default=('TRUE','FALSE'))
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
                           default=['C MMS','F Vessel'])
    overDueStat = st.multiselect('Overdue Status', options=['Yes', 'No'], default=['Yes', 'No'])

with filterContainer:
    #  now filter the dataframe using all above filter settings
    dfFiltered = dfSelected.query("ship_name == @vslName & status == @statusNow & brkdn_tf == @brkdn "
                                  "& critical_eq_tf == @criticalEq & docking_tf == @docking & blackout_tf == @blackout"
                                  "& coc_tf == @coc & overdue == @overDueStat & Severity == @severity & rpt_by == @rptBy")

    dfFiltered = dfFiltered[dfFiltered['nc_detail'].str.contains(searchText, regex=False)] # search on text entered
    st.dataframe(dfFiltered[disp_cols],height=600)


with col4: # download button and file
    csv = dfFiltered.to_csv().encode('utf-8')  # write df to csv
    btnMsg = 'Download ' + str(dfFiltered.shape[0]) + ' Records as CSV'
    st.download_button(btnMsg, csv,"DRS-file.csv","text/csv", key='download-csv')

print('----------------') #--------------------------------------------
upldSection = st.expander('Upload vessel DR Sender (under Construction)')
ucol1, ucol2, ucol3 = upldSection.columns(3)
with upldSection:
    uploaded_file = st.file_uploader('Choose a file')
    if uploaded_file is not None:
        dfVslDrs = pd.read_excel(uploaded_file, sheet_name='DRSEND', skiprows=6, dtype=str,
                                 na_filter=False,parse_dates=False, usecols='A:CV')
        # import data from excel with all col=str and do not put <NA> for missing data
        filename = uploaded_file.name
        dfVslDrs.drop(dfVslDrs.index[-1], inplace=True)  # drop the last row - with ZZZ
        vsldfShape = dfVslDrs.shape
        st.write('Raw data from Vessel:', (vsldfShape[0]), 'Records found in "',
                 filename,'" (', vsldfShape[1], 'Columns)' )
        dfVslDrs.columns = drsHeaders # rename the headers for Vessel file, same as master db
        toCorrect = ['dt_ocurred','init_action_ship_dt', 'target_dt','final_action_ship_dt','done_dt','update_dt']
        for someCol in toCorrect:
            dfVslDrs[someCol] = pd.to_datetime(dfVslDrs[someCol]).apply(lambda x: x.date())
            #convert long datetime to date
        drsID = list(dfVslDrs["DRS_ID"])  #get list of DRS_ID for checking new data
        dfNoCommon = df[~df['DRS_ID'].isin(drsID)] # filter OUT all rows with common DRS_ID
        st.write( len(df[df['DRS_ID'].isin(drsID)]), "common items found and updated with latest info.",)
        dfUpdated = pd.concat([dfNoCommon, dfVslDrs], ignore_index=True)  # add all the new rows to dataframe
        st.dataframe(dfVslDrs)   # diplay DF
        conn = sqlite3.connect(r'assets/new.sqlite')    # write complete data to new database for check
        dfUpdated.to_sql('dr_sender',conn,if_exists='replace', index=False)
        conn.close()

with st.expander('RAW DATA'):
    st.dataframe(df)
    csv = df.to_csv().encode('utf-8')  # write df to csv
    btnMsg = 'Download ALL Records as CSV'
    st.download_button(btnMsg, csv, "DRS-file.csv", "text/csv", key='download-csv')
    # conn1 = sqlite3.connect(sql3db)
    # currentDateTime = datetime.datetime.now()
    # date = currentDateTime.date()
    # curr_year = date.strftime("%Y") # get current year
    # query1 = r"SELECT * FROM dr_sender WHERE strftime('%Y', dt_ocurred ) ='"+curr_year+"\'"+r" OR strftime('%Y', done_dt ) ='"+curr_year+"\'" # query to get only reported or closed in current year
    # dfgen_DRS =  pd.read_sql_query(query1, conn1)
    # dfgen_DRS[['delay_hr', 'downtime_hr', 'VET_risk']] = dfgen_DRS[['delay_hr', 'downtime_hr', 'VET_risk']] \
    #     .apply(pd.to_numeric, errors='coerce', axis=1)
    # st.dataframe(dfgen_DRS)
    # conn1.close
    # wb = xw.Book('_DRS V55.xlsm')  # load as openpyxl workbook; useful to keep the original layout
    # # which is discarded in the following dataframe
    # #df = pd.read_excel('_DRS V55.xlsm')  # load as dataframe (modifications will be easier with pandas API!)
    # ws = wb.sheets['DRSEND']
    # #df.iloc[1, 1] = 'hello world'  # modify a few things
    # # rows = dataframe_to_rows(dfgen_DRS, index=False)
    # for r_idx in range(len(dfgen_DRS)):
    #     for c_idx, value in enumerate(list(dfgen_DRS.iloc[r_idx])):
    #         ws. ell(row=r_idx+7, column=c_idx, value=value)
    # wb.save('test2.xlsm')