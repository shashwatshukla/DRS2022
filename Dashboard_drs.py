import plotly.express as px
import streamlit as st
import pandas as pd
from helpers import get_data, get_vessel_byfleet


def dashboard():
    st.title('Dashboard', anchor=None)
    # ___________________________Declarations_____________________________
    global allShips  # to hold list of all fleet shipnames for making graphs
    db = r'database/mms_master.sqlite'
    disp_cols = ['ship_name', 'dt_ocurred', 'target_dt', 'ext_dt', 'nc_detail', 'ext_rsn', 'ext_cmnt', 'co_eval',
                 'ser_no',
                 'req_num', 'est_cause_ship',
                 'init_action_ship', 'init_action_ship_dt',
                 'final_action_ship', 'final_action_ship_dt', 'corr_action', 'rpt_by', 'insp_by',
                 'insp_detail',
                 'update_by', 'update_dt']  # list of cols to be displayed on the screen

    # _______________Data collection_______________________
    df_raw = get_data(db, 'drsend')
    df_openDRS = df_raw.loc[df_raw.status == 'OPEN']  # get DR sender data

    df_fleet = get_data(r'database/mms_master.sqlite',
                        'fleet')  # get list of fleet names for selecting vesssels fleetwise

    df_vsl = get_data(db, 'vessels')  # Get active  fleet vessel names and IMO
    df_vsl_active = df_vsl.loc[df_vsl.statusActiveInactive == '1']

    df_si = get_data(db, 'si')  # Get active SI

    # _________________Data cleaning_________________________

    imo_active = (df_vsl_active['vsl_imo'])  # Tuple of active tanker vessel IMO
    df_active_drs = df_openDRS.loc[df_openDRS['vsl_imo'].isin(imo_active)]  # Active vessels in dataframe

    allShips = pd.DataFrame(df_active_drs['ship_name'].unique())  # For using in graph
    allshipCode = dict(zip(df_vsl_active.vslName, df_vsl_active.vslCode))
    allshipCode["Centennial Sapporo"] = "CSA"
    toCorrect = ["dt_ocurred", "init_action_ship_dt", "target_dt", "final_action_ship_dt", "done_dt",
                 "update_dt", "ext_dt", "PSC_picdt", "PSC_info2ownr_dt", "PSC_info2chrtr_dt", "PSC_info2rtshp_dt",
                 "PSC_info2oilmaj_dt", "PSC_info2mmstpmgmt_dt", "PSC_sndr_offimport_dt"]
    for someCol in toCorrect:
        df_active_drs[someCol] = pd.to_datetime(df_active_drs[someCol]).apply(lambda x: x.date())
        # convert str to date
    # -------------logic for overdue (today > target and today > ext)
    mask = (pd.to_datetime('today') > df_active_drs['target_dt']) & (
                pd.to_datetime('today') > df_active_drs['ext_dt'])  # ext date is before
    df_active = df_active_drs.loc[mask]
    # -------------------------------------------------------------------



    # _______________________UI elements and logic_____________________

    filterContainer = st.expander('Overdue deficiencies past extension date')
    col1, col2,col3 = filterContainer.columns(3)
    with col3:
        csv = df_active.to_csv().encode('utf-8')  # write df to csv
        btnMsg = 'Download ' + str(df_active.shape[0]) + ' Records as CSV'
        st.download_button(btnMsg, csv, "DRS-file.csv", "text/csv", key='download-csv')
    with col2:
        active_vsl = st.radio('Select Vessels', ('All', 'Active'))
        if active_vsl == 'All':
            vsl_list_fleetwise = get_vessel_byfleet(0)
        else:
            vsl_list_fleetwise = get_vessel_byfleet(1)
    with col1:
        fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(), default='All vessels',key='fleet_exp1')
        docking = st.checkbox("Remove DD Jobs", value=True)

        with filterContainer:
            vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName], []) # get vsl names as per flt selected and flatten the list (sum)
            vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt),key='vessel_exp1')

        with filterContainer:
            if docking:
                df_active = df_active.loc[df_active['ext_rsn'] != 'Docking']
            df_active = df_active.query("ship_name == @vslName")
            df_active = df_active[disp_cols]
            st.write(df_active)
            # gb = GridOptionsBuilder.from_dataframe(df_active)
            # # gb.configure_selection(selection_mode='multiple', use_checkbox=True, groupSelectsChildren=True,
            # # groupSelectsFiltered=True)
            # # gb.configure_pagination()
            # gb.configure_side_bar()
            # gb.configure_default_column(groupable=False, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
            #
            # gridOptions = gb.build()
            #
            # response = AgGrid(df_active, editable=True, fit_columns_on_grid_load=False, conversion_errors='coerce',
            #                   gridOptions=gridOptions, enable_enterprise_modules=True,
            #                   height=grid_height, theme=grid_theme)



        # _____________________________Graphs Section______________________________
        with filterContainer:
            allShips['Count'] = 0  # add col Count with val 0 in all cells
            allShips.columns = ['ship_name', 'Count']  # Rename columns
            data = df_active['ship_name'].value_counts()  # Pandas series
            df_graph = pd.DataFrame({'ship_name': data.index,
                                     'Count': data.values})  # create dataframe of ship name and count of open overdue def
            df_xaxis = pd.merge(allShips, df_graph, how='outer',
                                on='ship_name')  # merge dataframes to include ships with no overdue def
            df_xaxis = df_xaxis.fillna(0)

            df_xaxis['Count'] = df_xaxis['Count_x'] + df_xaxis['Count_y']
            df_xaxis.drop(['Count_x', 'Count_y'], axis=1, inplace=True)

            df_xaxis.sort_values(by='ship_name')  # sort
            filter1 = df_xaxis['ship_name'].isin(vslName)
            df_xaxis = df_xaxis[filter1]
            df_xaxis = df_xaxis.replace({'ship_name': allshipCode})
            fig = px.bar(df_xaxis, x='ship_name', y='Count', height=400, width=1200, color='Count',
                         labels={"ship_name": "Vessel", "Count": "Number of def. past the extension date"},
                         title="<b>Count of extended overdue not closed till today</b>",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            # color_continuous_scale=px.colors.sequential.Burg)
            df_active = df_active.sort_values(by='ship_name')
            df_active = df_active.replace({'ship_name': allshipCode})

            fig2 = px.bar(df_active, y=["ship_name"], x="ext_rsn", height=500, width=1200, color='ext_rsn',
                          title="<b>Reason for Extended overdue not closed till today</b>",
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(legend_orientation='h')
            fig.update_xaxes(categoryorder='array',
                             categoryarray=sorted(df_xaxis['ship_name']))
            # fig2.update_layout(legend_orientation='h')
            fig2.update_layout()
            st.plotly_chart(fig)
            st.plotly_chart(fig2)
            # fig3 = px.colors.sequential.swatches()
            # fig4 = px.colors.qualitative.swatches()
            # st.plotly_chart(fig3)
            # st.plotly_chart(fig4)

