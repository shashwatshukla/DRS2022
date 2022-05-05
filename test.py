import streamlit as st, pandas as pd
from load_Data import get_data, save_data_by_query,run_kwery
import sqlite3
mast_db='database/mms_master.sqlite'

upldcol1,upldcol2,upldcol3=st.columns(3)

df = get_data(r'database/mms_master.sqlite', 'drsend')
drsHeaders = df.columns.values
with upldcol1:
    uploaded_file = st.file_uploader('Upload an updated DR Sender file here.', type=['xlsm'])
if uploaded_file is not None:

    dfVslDrs = pd.read_excel(uploaded_file, sheet_name='DRSEND', skiprows=6, dtype=str,
                             na_filter=False, usecols='A:CV')


    # dfVslDrs = pd.read_excel(uploaded_file, sheet_name='DRSEND', skiprows=6, dtype=str,
    #                          na_filter=False,date_parser=date_parser,parse_dates=['Unnamed: 1'], usecols='A:CV')
    # import data from excel with all col=str and do not put <NA> for missing data
    filename = uploaded_file.name
    if dfVslDrs.iloc[-1, 0] == "ZZZ":  # (last line, 1st col) implemented crude check for a valid DRS file
        dfVslDrs.drop(dfVslDrs.index[-1], inplace=True)  # drop the last row - with ZZZ

        vsldfShape = dfVslDrs.shape
        st.markdown(f'Raw data from Vessel: \n{vsldfShape[0]} Records found in {filename}, '
                    f'(in {vsldfShape[1]} Columns)')
        dfVslDrs.columns = drsHeaders  # rename the headers for Vessel file, same as master db

        toCorrect = ["dt_ocurred", "init_action_ship_dt", "target_dt", "final_action_ship_dt", "done_dt",
                                   "update_dt", "ext_dt", "PSC_picdt", "PSC_info2ownr_dt", "PSC_info2chrtr_dt", "PSC_info2rtshp_dt",
                                   "PSC_info2oilmaj_dt", "PSC_info2mmstpmgmt_dt", "PSC_sndr_offimport_dt"]#
        for someCol in toCorrect:
                         dfVslDrs[someCol] = pd.to_datetime(dfVslDrs[someCol],errors='coerce').apply(lambda x: x.date())  # Remove time stamp from date cols
        dfVslDrs.replace({pd.NaT:''},inplace=True) # Remove NaT valus in date columns
        dfVslDrs=dfVslDrs.applymap(str) # Convert all dataframe values to string for writing back to SQlite DB


        #---Check and remove entries with the word <delete> in co_eval ---------------------------------------------------------

        delete_exists = (dfVslDrs['co_eval'].str.contains('<delete>', case=False)).any() # Check if <delete> exists in any row in uploaded
        new_records = len(dfVslDrs[~dfVslDrs['DRS_ID'].isin(df['DRS_ID'])])  # all rows which NOT exist in master DB (new records)
        old_records = len(dfVslDrs)-len(dfVslDrs[~dfVslDrs['DRS_ID'].isin(df['DRS_ID'])])  # all rows which exist in master DB
        df_updated = dfVslDrs.loc[~dfVslDrs['co_eval'].str.contains('<delete>', case=False)]  # all rows which do NOT contain <delete>
        df_to_delete = dfVslDrs.loc[dfVslDrs['co_eval'].str.contains('<delete>', case=False)]  # all rows which contain <delete>
        st.write(df_updated)
        if delete_exists:
            st.info('Following Rows will be deleted from the database. Do you wish to continue?')
            #df_to_delete['dummy2'] = str(pd.datetime.now()) + " by " + st.session_state.id  # write active username in col 'dummy2'
            st.write(df_to_delete)  # display deleted rows
        update_btn = st.button('Update database')
        cancel_btn = st.button('Cancel')
        if update_btn:
            save_data_by_query(mast_db, 'drsend', df_updated)
            if delete_exists:
                del_qry= 'DELETE FROM drsend WHERE EXISTS (SELECT * FROM drsend_deleted WHERE drsend_deleted.DRS_ID = drsend.DRS_ID);' # query to remove records from master DB
                save_data_by_query(mast_db,'drsend_deleted',df_to_delete)
                run_kwery(mast_db,del_qry) # Call function to run query
            deleted_record = len(df_to_delete)
            st.info(f"{old_records} old records and {new_records} new records updated. {deleted_record} records deleted from database")
        if cancel_btn:
            st.warning('No changes made to the Database. You may upload another DRS file')
    else:
        st.warning('Uploaded File is not a valid DR Sender file. Please try again!')













#--------------------for getting vessel names from fleet
# df_drsend = get_data(r'database/mms_master.sqlite','drsend')
# df_vessel = get_data(r'database/mms_master.sqlite','vessels')
# df_fleet = get_data(r'database/mms_master.sqlite','fleet')
# flt_list=dict(df_fleet[['fltLocalName','fltNameUID']].values)
# df_merged = pd.merge(df_drsend,df_vessel[['vsl_imo','statusActiveInactive','vslFleet']], on = 'vsl_imo',how = 'left') # brig col from vessel to drsend dataframe
# df_merged.drop(df_merged.index[df_merged['statusActiveInactive'] == 0], inplace = True)
# st.write(df_merged)
# group_wise={list(flt_list.keys())[i]:sorted(list(df_merged.loc[df_merged['vslFleet'] == str(list(flt_list.values())[i])
# ,'ship_name'].unique())) for i in range(len(flt_list))} # all vesssel fleet wise using dict comprehension
# st.write(group_wise)