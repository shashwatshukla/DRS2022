import streamlit as st, pandas as pd
from load_Data import get_data
import sqlite3


def upload_drs():
    upldcol1,upldcol2,upldcol3=st.columns(3)

    df = get_data(r'database/mms_master.sqlite', 'drsend')
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
            toCorrect = [
                "dt_ocurred",
                "init_action_ship_dt",
                "target_dt",
                "final_action_ship_dt",
                "done_dt",
                "update_dt",
                "ext_dt",
                "PSC_picdt",
                "PSC_info2ownr_dt",
                "PSC_info2chrtr_dt",
                "PSC_info2rtshp_dt",
                "PSC_info2oilmaj_dt",
                "PSC_info2mmstpmgmt_dt",
                "PSC_sndr_offimport_dt"
            ]
            for someCol in toCorrect:
                dfVslDrs[someCol] = pd.to_datetime(dfVslDrs[someCol]).apply(lambda x: x.date())
                # convert long datetime to date
            drsID = dfVslDrs["DRS_ID"].tolist()  # get list of DRS_ID for checking new data
            newRecords=dfVslDrs[~dfVslDrs['DRS_ID'].isin(df['DRS_ID'])]
            dfNoCommon = df[~df['DRS_ID'].isin(drsID)]  # filter OUT all rows with common DRS_ID
            dfUpdated = pd.concat([dfNoCommon, dfVslDrs], ignore_index=True)  # add all the new rows to dataframe
            st.dataframe(dfVslDrs)  # display DF
            dfdtype = get_data(r'database/mms_master.sqlite', 'drsend_schema')
            drs_schema = dict(zip(dfdtype.col_name, dfdtype.d_type))
            conn = sqlite3.connect(r'database/mms_master.sqlite')  # write complete df to new database for check


#---Check and remove entries with the word delete in serial number---------------------------------------------------------

            dtete_exists=(dfUpdated['ser_no'].str.contains('delete', case=False)).any()
            if dtete_exists:
                df = get_data(r'database/mms_master.sqlite', 'drsend')
                new_records = len(dfVslDrs[~dfVslDrs['DRS_ID'].isin(df['DRS_ID'])])
                old_records=len(dfVslDrs)-len(dfVslDrs[~dfVslDrs['DRS_ID'].isin(df['DRS_ID'])])
                df_deleted = dfUpdated.loc[dfUpdated['ser_no'].str.contains('delete', case=False)]
                dfUpdated = dfUpdated.loc[~dfUpdated['ser_no'].str.contains('delete', case=False)]
                st.info('Following DR sender items will be deleted from the database. Do you wish to continue?')
                delete_btn=st.button('Upload and delete')
                st.write(df_deleted)
                if delete_btn:
                    dfUpdated.to_sql('drsend', conn, if_exists='replace', index=False, dtype=drs_schema)
                    df_deleted.to_sql('drsend_deleted', conn, if_exists='replace', index=False, dtype=drs_schema)
                    deleted_record=len(df_deleted)
                    st.info(f"{old_records} old records and {new_records} new records uploaded with latest info.\n {deleted_record} record deleted from database")
            else:
                st.
                dfUpdated.to_sql('drsend', conn, if_exists='replace', index=False, dtype=drs_schema)
                st.info(str(len(df[df['DRS_ID'].isin(drsID)])) + f" old records and {len(newRecords)} new records uploaded with latest info." )
            conn.close()
        else:
            st.warning('Uploaded File is not a valid DR Sender file. \nPlease try again!')
