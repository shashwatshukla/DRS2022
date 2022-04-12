
import pandas as pd
import streamlit as st
import sqlite3

#@st.cache (allow_output_mutation=True)
#experimental memo@st.experimental_memo
def get_data(db, tbl):
    conn = sqlite3.connect(db)
    df_data = pd.read_sql_query(f'select * from {tbl}', conn)
    conn.close()
    # df_data[['delay_hr', 'downtime_hr', 'VET_risk']] = df_data[['delay_hr', 'downtime_hr', 'VET_risk']] \
    #     .apply(pd.to_numeric, errors='coerce', axis=1)  # make the three cols numeric
    return df_data

def save_data(df,db,tbl):
    # Create your connection.
    conn = sqlite3.connect(db)
    df.to_sql(name=tbl, con=conn, if_exists='replace',index=False)
    conn.close()

# @st.cache (allow_output_mutation=True)
@st.experimental_memo
def get_table_name(db):
    con = sqlite3.connect(db)
    data = pd.read_sql_query('SELECT name from sqlite_master where type= "table";', con)
    return data

