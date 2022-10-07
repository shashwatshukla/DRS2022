import numpy as np
import pandas as pd
import streamlit as st
st.set_page_config(page_title='Linked list', layout='wide')


def df_writer(df_list, sheets, file_name, spaces):
    writer = pd.ExcelWriter(file_name,engine='xlsxwriter')
    row = 0
    for dataframe in df_list:
        dataframe.to_excel(writer,sheet_name=sheets,startrow=row , startcol=0,index=False)
        row = row + len(dataframe.index) + spaces + 1
    writer.save()

df=pd.read_excel('LL.xlsx')

col_l1=df.l1.unique() # define columns for level 1 table
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
df_l2.sort_values(by=list(col_l2))
st.write(df_l2)

col_l3=df.l3.unique()
dict_l3={}
for item3 in col_l3:
    if type(item3)!=np.nan:
        val3=set(list(df['l4'].where(df.l3==item3)))
        val3 = sorted([x for x in val3 if type(x) == str])
        dict_l3[item3]=val3
        st.write(item3)
df_l3=pd.DataFrame(dict_l3.values(),dict_l3.keys())
df_l3=df_l3.transpose()

st.write(df_l3)
dfs = [df_l1,df_l2,df_l3]
df_writer(dfs, 'val', 'output.xlsx', 1)