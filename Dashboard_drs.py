import datetime
import plotly.express as px
import streamlit as st
import pandas as pd
import sqlite3 as sq
from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import os

def dashboard():
    global allShips  # to hold list of all tanker shipnames for making graphs
    db = r'database/mms_master.sqlite'
    # ___________________________Declarations_____________________________
    disp_cols = ['ship_name', 'dt_ocurred', 'target_dt', 'ext_dt', 'nc_detail', 'ext_rsn', 'ext_cmnt', 'co_eval',
                 'ser_no',
                 'req_num', 'est_cause_ship',
                 'init_action_ship', 'init_action_ship_dt',
                 'final_action_ship', 'final_action_ship_dt', 'corr_action', 'rpt_by', 'insp_by',
                 'insp_detail',
                 'update_by', 'update_dt']

    # _______________Data collection_______________________
    conn = sq.connect(db)
    df_openDRS = pd.read_sql_query("select * from drsend where status='OPEN'", conn)  # get DR sender data
    df_vsl = pd.read_sql_query(
        "select vslName, vslCode, vsl_imo, vslTechSI, vslMarSI from vessels where statusActiveInactive = '1'",
        conn)  # Get active tanker fleet vessel names and IMO
    df_SI = pd.read_sql_query("select SI_UID, siEmail from si where statusActiveInactive = '1'", conn)  # Get active SI

    # _________________Data cleaning_________________________
    df_openDRS[['delay_hr', 'downtime_hr', 'VET_risk']] = df_openDRS[['delay_hr', 'downtime_hr', 'VET_risk']] \
        .apply(pd.to_numeric, errors='coerce', axis=1)  # convert to numeric
    df_openDRS['vsl_imo'] = df_openDRS['vsl_imo'].astype(int)  # convert IMO number to int
    # SI_mailid = {row.SI_UID: row.siEmail for (index, row) in
    #              df_SI.iterrows()}  # convert SI uniqeid and email to dictionary dunno why i did this
    imoactive = (df_vsl['vsl_imo'])  # Tuple of active tanker vessel IMO
    flt_active = df_openDRS['vsl_imo'].isin(imoactive)
    df_active = df_openDRS[flt_active]  # Active tanker vessels in dataframe

    allShips = pd.DataFrame(df_active['ship_name'].unique())  # For using in graph
    allshipCode = dict(zip(df_vsl.vslName, df_vsl.vslCode))
    allshipCode["Centennial Sapporo"]="CSA"
    toCorrect = ['dt_ocurred', 'ext_dt', 'target_dt', 'final_action_ship_dt', 'done_dt', 'update_dt']
    for someCol in toCorrect:
        df_active[someCol] = pd.to_datetime(df_active[someCol]).apply(lambda x: x.date())
        # convert str to date
    # -------------logic for overdue (today > target and today > ext)
    mask = (pd.to_datetime('today') > df_active['target_dt']) & (pd.to_datetime('today') > df_active['ext_dt'])  # ext date is before
    df_active = df_active.loc[mask]
    # -------------------------------------------------------------------
    uniqShips = list(df_active['ship_name'].unique())  # get list of unique ships from DB
    fltList = {'All vessels': uniqShips,
               'Tanker1': sorted(
                   ['Tokio', 'Taiga', 'Tsushima', 'BW Tokyo', 'BW Kyoto', 'Marvel Kite',
                    'Takasago', 'Tenma', 'Esteem Astro', 'Esteem Explorer', 'Metahne Mickie Harper',
                    'Methane Patricia Camila', 'Red Admiral']),
               'Tanker2 SMI': sorted(
                   ['Ginga Hawk', 'Ginga Kite', 'Ginga Merlin', 'Centennial Misumi',
                    'Centennial Matsuyama', 'Argent Daisy', 'Eagle Sapporo', 'Eagle Melbourne',
                    'Challenge Prospect II', 'St Clemens', 'St Pauli', 'Esteem Houston',
                    'Esteem Energy',
                    'Esteem Discovery', 'Esteem Endeavour', 'Solar Katherine', 'Solar Melissa',
                    'Solar Madelein', 'Solar Claire', 'Esteem Sango']),
               'Tanker2 SIN': sorted(['Hafnia Nordica',
                                      'Peace Victoria', 'Orient Challenge', 'Orient Innovation', 'Crimson Jade',
                                      'Crimson Pearl', 'Hafnia Hong Kong', 'Hafnia Shanghai', 'San Jack',
                                      'Hafnia Shenzhen', 'HARRISBURG', 'Hafnia Nanjing'])
               }

    # _______________________UI elements and logic_____________________

    # ____________________AGgrid_________________

    grid_height = st.sidebar.number_input("Grid height", min_value=200, max_value=800, value=300)
    grid_theme = st.sidebar.selectbox('Grid theme', options=['streamlit', 'light', 'dark', 'blue', 'fresh', 'material'],
                                      index=0)
    filterContainer = st.expander('Overdue deficiencies past extension date')
    col1, col2 = filterContainer.columns(2)
    with col1:
        fltName = st.multiselect('Select the Fleet', options=fltList.keys(), default='All vessels')

        with filterContainer:
            vslListPerFlt = sum([fltList[x] for x in fltName],
                                [])  # get vsl names as per flt selected and flatten the list (sum)
            vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt))
            # df_sel_vsl_counts = (df_counts[df_counts['ship_name'].isin(vslName)])
            # st.write(df_sel_vsl_counts)
            # fig = px.bar(df_sel_vsl_counts, x="ship_name", y=["Closed", "Open"], barmode='stack', height=400)
            # st.plotly_chart(fig)

        with filterContainer:
            #  now filter the dataframe using all above filter settings
            df_active = df_active.query("ship_name == @vslName")  # & status == @statusNow & brkdn_tf == @brkdn "
            # "& critical_eq_tf == @criticalEq & docking_tf == @docking & blackout_tf == @blackout"
            # "& coc_tf == @coc & overdue == @overDueStat & Severity == @severity & rpt_by == @rptBy")

            # dfFiltered = dfFiltered[dfFiltered['nc_detail'].str.contains(searchText, regex=False)]  # search on text entered
            df_active = df_active[disp_cols]
            gb = GridOptionsBuilder.from_dataframe(df_active)
            # gb.configure_selection(selection_mode='multiple', use_checkbox=True, groupSelectsChildren=True,
            # groupSelectsFiltered=True)
            # gb.configure_pagination()
            gb.configure_side_bar()
            gb.configure_default_column(groupable=False, value=True, enableRowGroup=True, aggFunc="sum", editable=True)

            gridOptions = gb.build()
            # st.header(tbl_name+' Data')

            response = AgGrid(df_active, editable=True, fit_columns_on_grid_load=False, conversion_errors='coerce',
                              gridOptions=gridOptions, enable_enterprise_modules=True,
                              height=grid_height, theme=grid_theme)
            # st.write("data")

            # st.write(df_active[disp_cols], height=600)

        #
        with col2:  # download button and file
            csv = df_active.to_csv().encode('utf-8')  # write df to csv
            btnMsg = 'Download ' + str(df_active.shape[0]) + ' Records as CSV'
            st.download_button(btnMsg, csv, "DRS-file.csv", "text/csv", key='download-csv')
        # _____________________________Graphs Section______________________________
        with filterContainer:
            allShips['Count'] = 0  # add col Count with val 0 in all cells
            allShips.columns = ['ship_name', 'Count']  # Rename columns

            data = df_active['ship_name'].value_counts()
            data2 = df_active['ext_rsn'].value_counts()
            df_graph = pd.DataFrame({'ship_name': data.index,
                                     'Count': data.values})  # create dataframe of ship name and count of open overdue def
            df_xaxis = pd.merge(allShips, df_graph, how='outer',
                                on='ship_name')  # merge dataframes to include ships with no overdue def
            df_xaxis = df_xaxis.fillna(0)
            df_xaxis['Count'] = df_xaxis['Count_x'] + df_xaxis['Count_y']
            df_xaxis.drop(['Count_x', 'Count_y'], axis=1, inplace=True)

            df_xaxis.sort_values(by='ship_name')  # sort
            df_xaxis = df_xaxis.replace({'ship_name': allshipCode})

            fig = px.bar(df_xaxis, x='ship_name', y='Count', height=400, width=1200, color='Count',
                         labels={"ship_name": "Vessel", "Count": "Number of def. past the extension date"},
                         title="<b>Count of extended overdue not closed till today</b>",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            # color_continuous_scale=px.colors.sequential.Burg)

            fig2 = px.bar(df_active, y=["ship_name"], x="ext_rsn", height=500, width=1200, color='ext_rsn',
                          title="<b>Reason for Extended overdue not closed till today</b>",
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(legend_orientation='h')
            fig.update_xaxes(categoryorder='array',
                             categoryarray=sorted(df_xaxis['ship_name']))
            #fig2.update_layout(legend_orientation='h')
            fig2.update_layout()
            st.plotly_chart(fig)
            st.plotly_chart(fig2)
            #fig3 = px.colors.sequential.swatches()
            # fig4 = px.colors.qualitative.swatches()
            #st.plotly_chart(fig3)
            # st.plotly_chart(fig4)
