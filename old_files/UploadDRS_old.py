import streamlit as st, pandas as pd
from helpers import get_data, save_data
import sqlite3

def upload_drs():
    upldcol1,upldcol2,upldcol3=st.columns(3)

    df = get_data(r'assets/mms_master.sqlite', 'drsend')
    drsHeaders = df.columns.values
    with upldcol1:
        uploaded_file = st.file_uploader('Upload an updated DR Sender file here.', type=['xlsm'])
    if uploaded_file is not None:
        dfVslDrs = pd.read_excel(uploaded_file, sheet_name='DRSEND', skiprows=6, dtype=str,
                                 na_filter=False, parse_dates=False, usecols='A:CV')
        # import data from excel with all col=str and do not put <NA> for missing data
        filename = uploaded_file.name
        if dfVslDrs.iloc[-1, 0] == "ZZZ":  # (last line, 1st col) implemented crude check for a valid DRS file
            dfVslDrs.drop(dfVslDrs.index[-1], inplace=True)  # drop the last row - with ZZZ

            vsldfShape = dfVslDrs.shape
            st.markdown(f'Raw data from Vessel: \n{vsldfShape[0]} Records found in {filename}, '
                        f'(in {vsldfShape[1]} Columns)')
            dfVslDrs.columns = drsHeaders  # rename the headers for Vessel file, same as master db
            dfVslDrs['dummy2'] = str(pd.datetime.now())+" by "+st.session_state.id
            # toCorrect = ["dt_ocurred", "init_action_ship_dt", "target_dt", "final_action_ship_dt", "done_dt",
            #     "update_dt", "ext_dt", "PSC_picdt", "PSC_info2ownr_dt", "PSC_info2chrtr_dt", "PSC_info2rtshp_dt",
            #     "PSC_info2oilmaj_dt", "PSC_info2mmstpmgmt_dt", "PSC_sndr_offimport_dt"]
            # for someCol in toCorrect:
            #     dfVslDrs[someCol] = pd.to_datetime(dfVslDrs[someCol]).apply(lambda x: x.date())
                # convert long datetime to date
            drsID = dfVslDrs["DRS_ID"].tolist()  # get list of DRS_ID for checking new data
            newRecords=dfVslDrs[~dfVslDrs['DRS_ID'].isin(df['DRS_ID'])] # get rows which are from vsl by NOT IN master
            dfNoCommon = df[~df['DRS_ID'].isin(drsID)]  # remove all rows with common DRS_ID from master
            dfUpdated = pd.concat([dfNoCommon, dfVslDrs], ignore_index=True)  # add all the new rows to dataframe
            st.dataframe(dfVslDrs)  # display DF
            dfdtype = get_data(r'assets/mms_master.sqlite', 'drsend_schema')
            drs_schema = dict(zip(dfdtype.col_name, dfdtype.d_type))
            conn = sqlite3.connect(r'../assets/mms_master.sqlite')  # write complete df to new database for check

            #---Check and remove entries with the word <delete> in co_eval ---------------------------------------------------------

            delete_exists = (dfUpdated['co_eval'].str.contains('<delete>', case=False)).any() # Check if <delete> exists in any row in uploaded
            new_records = len(dfVslDrs[~dfVslDrs['DRS_ID'].isin(df['DRS_ID'])])
            old_records = len(dfVslDrs)-len(dfVslDrs[~dfVslDrs['DRS_ID'].isin(df['DRS_ID'])])
            df_deleted = dfUpdated.loc[dfUpdated['co_eval'].str.contains('<delete>', case=False)]
            df_deleted['dummy2']=str(pd.datetime.now())+" by "+st.session_state.id
            dfUpdated = dfUpdated.loc[~dfUpdated['co_eval'].str.contains('<delete>', case=False)]
            if delete_exists:
                st.info('Following Rows will be deleted from the database. Do you wish to continue?')
                st.write(df_deleted)
            update_btn = st.button('Update database')
            cancel_btn = st.button('Cancel')
            if update_btn:
                dfUpdated.to_sql('drsend', conn, if_exists='replace', index=False, dtype=drs_schema)
                # done run query for updating the drsend_deleted tbl with new entries
                if delete_exists:
                    save_data(df_deleted,r'assets/mms_master.sqlite','drsend_deleted','DRS_ID')
                deleted_record = len(df_deleted)
                st.info(f"{old_records} old records and {new_records} new records updated. {deleted_record} records deleted from database")
            if cancel_btn:
                st.warning('No changes made to the Database. You may upload another DRS file')
            # else:
            #     upload_btn=st.button("Upload to database")
            #     if upload_btn:
            #         dfUpdated.to_sql('drsend', conn, if_exists='replace', index=False, dtype=drs_schema)
            #         st.info(str(len(df[df['DRS_ID'].isin(drsID)])) + f" old records and {len(newRecords)} new records uploaded with latest info." )
            conn.close()
        else:
            st.warning('Uploaded File is not a valid DR Sender file. Please try again!')
