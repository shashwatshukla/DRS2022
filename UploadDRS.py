import streamlit as st, pandas as pd
from helpers import get_data, save_data_by_kwery, run_kwery


def upload_drs():
    st.title('Upload DR sender')
    mast_db = 'assets/mms_master.sqlite'

    upldcol1, upldcol2, upldcol3 = st.columns(3)

    df = get_data(r'assets/mms_master.sqlite', 'drsend')
    drsHeaders = df.columns.values
    with upldcol1:
        uploaded_file = st.file_uploader('Upload updated DR Sender.', type=['xlsm'])
    if uploaded_file is not None:

        dfVslDrs = pd.read_excel(uploaded_file, sheet_name='DRSEND', skiprows=6, dtype=str,
                                 na_filter=False, usecols='A:CV')
        filename = uploaded_file.name
        if dfVslDrs.iloc[-1, 0] == "ZZZ":  # (last line, 1st col) implemented crude check for a valid DRS file
            dfVslDrs.drop(dfVslDrs.index[-1], inplace=True)  # drop the last row - with ZZZ

            vsldfShape = dfVslDrs.shape
            st.markdown(f'Raw data from Vessel: \n{vsldfShape[0]} Records found in {filename}, '
                        f'(in {vsldfShape[1]} Columns)')
            dfVslDrs.columns = drsHeaders  # rename the headers for Vessel file, same as master db

            toCorrect = ["dt_ocurred", "init_action_ship_dt", "target_dt", "final_action_ship_dt", "done_dt",
                         "update_dt", "ext_dt", "PSC_picdt", "PSC_info2ownr_dt", "PSC_info2chrtr_dt",
                         "PSC_info2rtshp_dt",
                         "PSC_info2oilmaj_dt", "PSC_info2mmstpmgmt_dt", "PSC_sndr_offimport_dt"]  #
            for someCol in toCorrect:
                dfVslDrs[someCol] = pd.to_datetime(dfVslDrs[someCol], errors='coerce').apply(
                    lambda x: x.date())  # Remove time stamp from date cols
            dfVslDrs.replace({pd.NaT: ''}, inplace=True)  # Remove NaT valus in date columns
            dfVslDrs = dfVslDrs.applymap(str)  # Convert all dataframe values to string for writing back to SQlite DB
            dfVslDrs['dummy2'] = str(pd.datetime.now()) + " _ " + st.session_state.id  # write active username in col 'dummy2'

            # ---Check and remove entries with the word <delete> in co_eval ---------------------------------------------------------

            delete_exists = (dfVslDrs['co_eval'].str.contains('<delete>',case=False)).any()  # Check if <delete> exists in any row in uploaded
            new_records = len(dfVslDrs[~dfVslDrs['DRS_ID'].isin(df['DRS_ID'])])  # all rows which NOT exist in master DB (new records)
            old_records = len(dfVslDrs) - len(dfVslDrs[~dfVslDrs['DRS_ID'].isin(df['DRS_ID'])])  # all rows which exist in master DB
            df_updated = dfVslDrs.loc[~dfVslDrs['co_eval'].str.contains('<delete>', case=False)]  # all rows which do NOT contain <delete>
            df_to_delete = dfVslDrs.loc[dfVslDrs['co_eval'].str.contains('<delete>', case=False)]  # all rows which contain <delete>
            st.write(df_updated)
            if delete_exists:
                st.info('Following Rows will be deleted from the database. Do you wish to continue?')
                st.write(df_to_delete)  # display deleted rows
            update_btn = st.button('Update database')
            cancel_btn = st.button('Cancel')
            if update_btn:
                save_data_by_kwery(mast_db, 'drsend', df_updated)
                if delete_exists:
                    del_qry = 'DELETE FROM drsend WHERE EXISTS (SELECT * FROM drsend_deleted WHERE drsend_deleted.DRS_ID = drsend.DRS_ID);'  # query to remove records from master DB
                    save_data_by_kwery(mast_db, 'drsend_deleted', df_to_delete)
                    run_kwery(mast_db, del_qry)  # Call function to run query
                deleted_record = len(df_to_delete)
                st.info(f"{old_records} old records and {new_records} new records updated. {deleted_record} records deleted from database")
                st.legacy_caching.clear_cache()
            if cancel_btn:
                st.warning('No changes made to the Database. You may upload another DRS file')
        else:
            st.warning('Uploaded File is not a valid DR Sender file. Please try again!')