import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
import io

st.set_page_config(page_title='Job Master', layout='wide')

def to_excel(df) -> bytes:
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, sheet_name="Sheet1")
    writer.save()
    processed_data = output.getvalue()
    return processed_data

lst=st.file_uploader("Upload",type="xlsx")

if lst is not None:
    df1=pd.read_excel(lst, sheet_name=None,dtype='str',na_filter="")
    st.write(list(df1.keys())[0])
    sheets=st.selectbox('Select sheet',options=list(df1.keys()))
    df=df1[sheets]
    st.write(df.columns)
    col_selector=st.multiselect('select columns',options=[df.columns],default=[df.columns])
    gb = GridOptionsBuilder.from_dataframe(df)
    #gb.configure_pagination()
    gb.configure_side_bar()
    gb.configure_auto_height(autoHeight=False)
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
    gridOptions = gb.build()
    output=AgGrid(df, gridOptions=gridOptions, enable_enterprise_modules=True)
    out_df = output["data"]
    st.write(out_df)
    st.download_button("Download as excel",data=to_excel(out_df),file_name="output.xlsx",mime="application/vnd.ms-excel")