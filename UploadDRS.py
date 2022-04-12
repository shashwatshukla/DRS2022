import streamlit as st, pandas as pd
from load_Data import get_data
import sqlite3


def upload_drs():

    df = get_data(r'database/mms_master.sqlite', 'drsend')
    st.write(df.DRS_ID)
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
            # drs_schema={'DRS_ID':'text','dt_ocurred':'DATE','ser_no':'text','rpt_by':'text','moge':'text','hoge':'text',
            #            'insp_by':'text','insp_detail':'text','def_code':'text','def_short':'text','item_code':'text',
            #            'item_short':'text','brkdn_yn':'text','nc_detail':'text','est_cause_ship':'text',
            #            'init_action_ship':'text','init_action_ship_dt':'DATE','target_dt':'DATE',
            #            'final_action_ship':'text','final_action_ship_dt':'DATE','lti_hr':'text','stop_hr':'text',
            #            'fit':'text','co_eval':'text','maj_min':'text','rca':'text','reason_rc':'text',
            #            'corr_action':'text','done_dt':'DATE','status':'text','update_by':'text','dummy1':'text',
            #            'dummy2':'text','Severity':'text','delay_tf':'text','delay_hr':'REAL','downtime_tf':'text',
            #            'downtime_hr':'REAL','brkdn_tf':'text','critical_eq_tf':'text','blackout_tf':'text',
            #            'docking_tf':'text','dispensation_tf':'text','coc_tf':'text','major':'text','alert_req':'text',
            #            'vsl_imo':'text','ship_name':'text','ship_drs_code':'text','update_dt':'DATE','capt_name':'text',
            #            'sys_code':'text','eq_code':'text','psc_def_ch':'text','psc_def_code':'text',
            #            'sire_def_ch':'text','sire_def_code':'text','ext_rsn':'text','ext_dt':'DATE',
            #            'fleet_alert':'text','req_num':'text','ext_cmnt':'text','overdue':'text',
            #            'Insp_id':'text','PSC_mou':'text','country':'TEXT','port':'text','grp':'text',
            #            'type':'text','age':'text','choff':'text','cheng':'text','fengr':'text','chrtr':'text',
            #            'owner':'text','flag':'text','class':'text','PSC_detain':'text','PSC_info2panama':'text',
            #            'PSC_pic':'text','PSC_picdt':'DATE','PSC_info2ownr':'text','PSC_info2ownr_dt':'DATE',
            #            'PSC_info2chrtr':'text','PSC_info2chrtr_dt':'DATE','PSC_info2rtshp':'text',
            #            'PSC_info2rtshp_dt':'DATE','PSC_info2oilmaj':'text','PSC_info2oilmaj_dt':'DATE',
            #            'PSC_info2mmstpmgmt':'text','PSC_info2mmstpmgmt_dt':'DATE','PSC_sndr_offimport':'text',
            #            'PSC_sndr_offimport_dt':'DATE','VET_oilmaj':'text','VET_oilmaj_co':'text',
            #            'VET_offattnd':'text','VET_risk':'INTEGER','VET_repupload':'text','VET_repfinalby':'text',
            #            'VET_Q88upload':'text'}

            dfdtype = get_data(r'database/mms_master.sqlite', 'drs_schema')
            drs_schema=dict(zip(dfdtype.col_name, dfdtype.d_type))

            conn = sqlite3.connect(r'database/mms_master.sqlite')  # write complete df to new database for check
            dfUpdated.to_sql('drsend', conn, if_exists='replace', index=False, dtype=drs_schema)
            conn.close()
        else:
            st.warning('Uploaded File is not a valid DR Sender file. \nPlease try again!')
