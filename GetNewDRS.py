import datetime
import pandas as pd
import streamlit as st
from load_Data import get_data
import xlwings as xw
from datetime import date
from io import BytesIO
import os, time, pythoncom, win32com

disp_cols = []
output = BytesIO

def make_NewDRS():
    # st.set_page_config(page_title='Generate new DR sender', layout='wide')
    disp_cols = ['dt_ocurred','ser_no','status','nc_detail', 'target_dt', 'done_dt', 'est_cause_ship', 'init_action_ship',
                 'init_action_ship_dt',
                 'final_action_ship', 'final_action_ship_dt', 'co_eval',
                 'reason_rc', 'corr_action', 'rpt_by', 'insp_by', 'insp_detail', 'update_by', 'update_dt',
                 'ext_dt', 'ext_rsn', 'req_num', 'ext_cmnt', 'sys_code', 'eq_code', 'ship_name']
    # st.markdown('<style>.ReactVirtualized__Grid__innerScrollContainer div[class^="row"], .ReactVirtualized__Grid__innerScrollContainer div[class^="data row"]{ background:lightyellow; } </style>', unsafe_allow_html=True)
    def read_file(fyle):
        with open(fyle, "rb") as filetoread:
            xlsmbyte = filetoread.read()
            return xlsmbyte

    curr_year = str(datetime.datetime.now().year)
    print(curr_year,'--------------------------')
    st.markdown(f'Generate new **{curr_year} DR sender**')
    df_rawData = get_data(r'database/mms_master.sqlite', 'drsend')  # get raw data to work upon
    vsl_list = sorted(list(df_rawData['ship_name'].unique()))

    col1, col2, col3 = st.columns(3)
    with col1:
        shipName = st.selectbox('Select Vessel', vsl_list)# Choose vessel from list of shipnames
    bt=st.button('Proceed')
    if bt:
        st.markdown(f'{shipName} DR Sender being prepared. Please wait....')
        df_rawData[['delay_hr', 'downtime_hr', 'VET_risk']] = df_rawData[['delay_hr', 'downtime_hr', 'VET_risk']] \
            .apply(pd.to_numeric, errors='coerce', axis=1)  # Convert to prevent errors

        df_currDRS = df_rawData.query("ship_name == @shipName and (dt_ocurred.str.contains(@curr_year) or done_dt.str.contains(@curr_year) or status.str.contains('OPEN'))", engine='python')

        numberOfRows = len(df_currDRS)
        jobDone = st.progress(0)
        filename = r'_DRS V56.xlsm'  #
        xl = win32com.client.Dispatch("Excel.Application", pythoncom.CoInitialize())
        with xw.App(visible=False) as app:
            book = xw.Book(filename, password='mms@user')  # Get template file
            ws = book.sheets['DRSEND']
            # app = xw.apps.active
            for i in range(numberOfRows):
                ws.range('A8:CZ8').insert(shift='down',
                                          copy_origin='format_from_left_or_above')  # shift named ranges in excel to prevent overwriting
                jobDone.progress(int(i/numberOfRows*100))
            ws.range('C1').value = shipName
            f_name = str(date.today()) + ' ' + shipName + ' DRS56.xlsm'
            new_drs_file = os.path.join('temp', f_name)  # save in temp folder
            ws.range('A8').options(index=False, header=False).value = df_currDRS  # write dataframe to excel
            f = book.save(new_drs_file)  # save excel as new file
            book.close()
            print (f'saved: {new_drs_file}')
            jobDone.progress(100)
        # app.quit()

        with col2:
            st.info(f'Done... {shipName} DR Sender has {len(df_currDRS)} entries for {curr_year}.')

    #app.quit()
        st.download_button(label=f"Download {shipName} DR sender",
                           data=read_file(new_drs_file),
                           file_name=new_drs_file[4:],
                           mime='application/vns.ms-excel')
        st.write(df_currDRS[disp_cols])  # display only selected columns








