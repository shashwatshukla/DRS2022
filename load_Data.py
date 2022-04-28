import logging, sys,traceback
import pandas as pd
import streamlit as st
import sqlite3

#@st.cache (allow_output_mutation=True)
#experimental memo@st.experimental_memo
def get_data(db, tbl):
    conn = sqlite3.connect(db)
    df_data = pd.read_sql_query(f'select * from {tbl}', conn)
    conn.close()
    if tbl=='drsend':
        df_data[['delay_hr', 'downtime_hr', 'VET_risk']] = df_data[['delay_hr', 'downtime_hr', 'VET_risk']] \
            .apply(pd.to_numeric, errors='coerce', axis=1)  # make the three cols numeric
        toCorrect = ["dt_ocurred", "init_action_ship_dt","target_dt", "final_action_ship_dt", "done_dt",
                      "update_dt", "ext_dt", "PSC_picdt", "PSC_info2ownr_dt", "PSC_info2chrtr_dt", "PSC_info2rtshp_dt",
                      "PSC_info2oilmaj_dt", "PSC_info2mmstpmgmt_dt", "PSC_sndr_offimport_dt"]#
        for someCol in toCorrect:
            df_data[someCol] = pd.to_datetime(df_data[someCol],errors='coerce').apply(lambda x: x.date())#, format="%Y/%m/%d")#.dt.date
    df_data.replace({pd.NaT: ''}, inplace=True) #remove the NaT values in missing dates
    df_data=df_data.applymap(str)
    return df_data

def save_data(df,db,tbl,lookup_key):

    conn = sqlite3.connect(db)
    dfDB= pd.read_sql_query(f'select * from {tbl}', conn) #  read data from database in dataframe
    idkeys=df[lookup_key].tolist()
    dfnotCommon=dfDB[~dfDB[lookup_key].isin(idkeys)]
    dfUpdated = pd.concat([dfnotCommon, df])
    dfUpdated.to_sql(name=tbl, con=conn, if_exists='replace',index=False)
    conn.close()

def save_data_by_kwery(db,tbl,df):
    dbHeaders=df.columns.values
    conn1 = sqlite3.connect(db)
    cursor = conn1.cursor()
    cursor.execute('BEGIN TRANSACTION;')

    try:
        columns = dbHeaders
        # firstRow = True
        # if firstRow:  # Process the Headers row and make new table if none exists
        #     s1 = f"CREATE TABLE if not exists {tbl} ("
        #     s2 = ', '.join(
        #         ['"%s" text' % column for column in columns])  # join ' text' type to each column name
        #     s3 = s1 + s2 + ', PRIMARY KEY ("DRS_ID"), UNIQUE ("DRS_ID"));'  # define DRS_ID as unique and primary key for the table if creating
        #     cursor.execute(s3)
        #     conn1.commit()
        for count, row in df.iterrows():  # enumerate(df1, start=1):  # reading all other rows
            if count == 1:
                vslName = row[47]
                print('----', vslName, '----')
                logging.info( ' -------------------  ' + vslName)
            query = 'INSERT OR REPLACE INTO "%s" ({0}) VALUES ({1})' % tbl  # Make SQL query with (headers / col name) VALUES (values, for now '?') for each row
            query = query.format(','.join(columns), ','.join('?' * len(columns)))  # = column names, followed by same number of '?'
            c = "Row # %d updated: ID %s" % (count, row[0])
            #st.write(c)
            logging.info(c)
            logging.info(f'updated. ID: {row[0]}')
            cursor.execute(query, list(row))  # run the qyery with actual values which will get imported

            conn1.commit()
            #st.info(f'DB updated. No errors found for{vslName}')
    except sqlite3.Error as er:
        st.write('SQLite error: %s' % (' '.join(er.args)))
        st.write("Exception class is: ", er.__class__)
        st.write('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        st.write(traceback.format_exception(exc_type, exc_value, exc_tb))

    except Exception as e:
        st.write('Some error occurred!')
        st.write(e)
        # logging.error(e)
    finally:
        conn1.close()


def run_kwery(database,qry):
    conn1 = sqlite3.connect(database)
    cursor = conn1.cursor()
    cursor.execute('BEGIN TRANSACTION;')
    query = 'DELETE FROM drsend WHERE EXISTS (SELECT * FROM drsend_deleted WHERE drsend_deleted.DRS_ID = drsend.DRS_ID);'
    cursor.execute(qry)
    conn1.commit()
    conn1.close

def get_table_name(db):
    con = sqlite3.connect(db)
    data = pd.read_sql_query('SELECT name from sqlite_master where type= "table";', con)
    return data

