import streamlit as st, pandas as pd
from load_Data import get_data
import sqlite3


def upload_drs():

    df = get_data(r'database/mms_master.sqlite', 'drsend')
    drsHeaders = df.columns.values
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
            toCorrect = ['dt_ocurred', 'init_action_ship_dt', 'target_dt', 'final_action_ship_dt', 'done_dt',
                         'update_dt']
            for someCol in toCorrect:
                dfVslDrs[someCol] = pd.to_datetime(dfVslDrs[someCol]).apply(lambda x: x.date())
                # convert long datetime to date
            drsID = dfVslDrs["DRS_ID"].tolist()  # get list of DRS_ID for checking new data
            print(drsID)
            dfNoCommon = df[~df['DRS_ID'].isin(drsID)] # filter OUT all rows with common DRS_ID

            st.write(len(df[df['DRS_ID'].isin(drsID)]), "common items found and updated with latest info.", )
            dfUpdated = pd.concat([dfNoCommon, dfVslDrs], ignore_index=True)  # add all the new rows to dataframe
            st.dataframe(dfVslDrs)  # display DF
            st.write(dfUpdated.dtypes)
            dfdtype = get_data(r'database/mms_master.sqlite', 'drs_schema')
            drs_schema=dict(zip(dfdtype.col_name, dfdtype.d_type))

            conn = sqlite3.connect(r'database/mms_master.sqlite')  # write complete df to new database for check
            dfUpdated.to_sql('drsend', conn, if_exists='replace', index=False, dtype=drs_schema)
            conn.close()
        else:
            st.warning('Uploaded File is not a valid DR Sender file. \nPlease try again!')
