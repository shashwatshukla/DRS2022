import pandas as pd
import streamlit as st
import xlrd

st.set_page_config(page_title='Linked list', layout='wide')


def read_file(fyle):
    with open(fyle, "rb") as filetoread:
        xlsmbyte = filetoread.read()
        return xlsmbyte

def df_writer(df_list, sheets, file_name):
    with pd.ExcelWriter(file_name, mode="a", engine="openpyxl", if_sheet_exists='overlay') as writer:
        row = 0
        for idx, dataframe in enumerate(df_list):
            col = len(dataframe.columns)
            # if idx==0:

            if idx == 1:
                row = 29
            if idx == 2:
                row = 69
            dataframe.to_excel(writer, sheet_name=sheets, startrow=row, startcol=0, index=False)


lst=st.file_uploader("Upload list",type="xlsx")
# xls = xlrd.open_workbook(lst, on_demand=True)
# xls.sheet_names()
if lst is not None:

    df=pd.read_excel(lst, sheet_name='List')

    # df['Storage Name'] = df['Storage Name'].str.replace('SUPERSTRUCTURE / ', '')
    # df['Storage Name'] = df['Storage Name'].str.strip()
    # f=len(df[df['Storage Name'].str.contains(" >")])
    # g=len(df[df['Storage Name'].str.contains("> ")])
    #
    # while f>0:
    #     df['Storage Name'] = df['Storage Name'].str.replace(" >", ">")
    #     f = len(df[df['Storage Name'].str.contains(" >")])
    # while g>0:
    #     df['Storage Name'] = df['Storage Name'].str.replace("> ", ">")
    #     g = len(df[df['Storage Name'].str.contains(" >")])
    #     st.write(g)
    st.write(df)
    df[['l1','l2','l3','l4']] = df['Storage Name'].str.split('>',expand=True)

    df=df[['l1','l2','l3','l4']]
    df[df.columns] = df.apply(lambda x: x.str.strip())

    col_l1=sorted(df.l1.unique()) # define columns for level 1 table
    st.write(col_l1)
    dict_l1={}
    for item in col_l1:
        val=list(set(list(df['l2'].where(df.l1==item))))
        val=sorted([x for x in val if type(x) ==str])

        dict_l1[item]=val
    df_l1=pd.DataFrame(dict_l1.values(),dict_l1.keys())

    df_l1=df_l1.transpose()
    st.write(df_l1)

    col_l2=df.l2.unique()
    dict_l2={}
    for item2 in col_l2:
        val2=set(list(df['l3'].where(df.l2==item2)))
        val2 = sorted([x for x in val2 if type(x) == str])
        dict_l2[item2]=val2
    df_l2=pd.DataFrame(dict_l2.values(),dict_l2.keys())
    df_l2=df_l2.transpose()

    st.write(df_l2)

    col_l3=df.l3.unique()
    dict_l3={}
    for item3 in col_l3:
        if type(item3)==str:
            val3=set(list(df['l4'].where(df.l3==item3)))
            val3 = sorted([x for x in val3 if type(x) == str])
            dict_l3[item3]=val3

    df_l3=pd.DataFrame(dict_l3.values(),dict_l3.keys())
    df_l3=df_l3.transpose()

    st.write(df_l3)
    dfs = [df_l1,df_l2,df_l3]
    df_writer(dfs, 'output', lst)
    with open(lst.name, 'wb') as f:
        f.write(lst.getbuffer())
    # st.download_button(label=f"Download List",data=read_file(f), mime='application/vns.ms-excel')
