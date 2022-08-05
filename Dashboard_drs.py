import plotly.express as px
import streamlit as st
import pandas as pd
from helpers import get_data, get_vessel_byfleet
from plotly.subplots import make_subplots
def dashboard():
    st.title('Dashboard', anchor=None)
    # ___________________________Declarations_____________________________
    global allShips  # to hold list of all fleet shipnames for making graphs
    db = r'assets/mms_master.sqlite'
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

    df_fleet = get_data(r'assets/mms_master.sqlite',
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

    # _______________________UI elements and logic_____________________
    graph_cont = st.container()
    col1, col2 = st.columns(2)
    #filterContainer = st.expander('Overdue deficiencies past extension date')
    rsn_list = df_active['ext_rsn'].unique()





    vsl_list_fleetwise = get_vessel_byfleet(1)

    #with col1:
    fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(), default='MMS-TOK',
                             key='fleet_exp1')
    vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName],
                        [])  # get vsl names as per flt selected and flatten the list (sum)


    vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt),
                                 key='vessel_exp1')
    ext_rsn = st.multiselect('Select Reasons:', options=rsn_list, default=rsn_list[0:5])
    df_active = df_active.query("ship_name == @vslName and ext_rsn==@ext_rsn")
    df_active[['ext_rsn']] = df_active[['ext_rsn']].fillna('Update ext. reason')
    df_active = df_active[disp_cols]
    vsl_list_fleetwise = get_vessel_byfleet(1)





    # _____________________________Graphs Section______________________________

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
    #df_xaxis = df_xaxis.replace({'ship_name': allshipCode})

    fig1 = px.bar(df_xaxis, x='ship_name', y='Count', height=400,
                 labels={"ship_name": "Vessel", "Count": "Number of def. past the extension date"},
                 title="<b>Count of overdue items past extension date</b>",text_auto=True)
    # color_continuous_scale=px.colors.sequential.Burg)
    df_active = df_active.sort_values(by='ship_name')
    #df_active = df_active.replace({'ship_name': allshipCode})
    #df_active.mask(df_active['ext_rsn'] == "", 'Update ext. Reason', inplace=True)
    df_active['ext_rsn'].loc[(df_active['ext_rsn']=="")]='update ext. reason'
    fig2 = px.bar(df_active, y=["ship_name"], x="ext_rsn", height=400, color='ext_rsn',
                  title="<b>Extended Items by Reason</b>",
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    fig1.update_layout(legend_orientation='h')
    fig1.update_xaxes(categoryorder='array',
                     categoryarray=sorted(df_xaxis['ship_name']))
    # fig2.update_layout(legend_orientation='h')
    fig2.update_layout()
    with col1:
        st.plotly_chart(fig1,usecontainerwidth=True)
    with col2:
        #docking = st.checkbox("Remove DD Jobs", value=True)
        st.plotly_chart(fig2,usecontainerwidth=True)
    st.write(df_active)
    csv = df_active.to_csv().encode('utf-8')  # write df to csv
    btnMsg = 'Download ' + str(df_active.shape[0]) + ' Records as CSV'
    st.download_button(btnMsg, csv, "DRS-file.csv", "text/csv", key='download-csv')


            # fig3 = px.colors.sequential.swatches()
            # fig4 = px.colors.qualitative.swatches()
            # st.plotly_chart(fig3)
            # st.plotly_chart(fig4)




























# import plotly.express as px
# import streamlit as st
# import pandas as pd
# from helpers import get_data, get_vessel_byfleet
# import datetime
#
#
# def dashboard():
#     st.title('Dashboard', anchor=None)
#     # ___________________________Declarations_____________________________
#     curr_year = str(datetime.datetime.now().year)
#     todaydt = str(pd.Timestamp('today').date())
#     db = r'assets/mms_master.sqlite'
#     disp_cols = ['ship_name', 'dt_ocurred', 'target_dt', 'ext_dt', 'nc_detail', 'ext_rsn', 'ext_cmnt', 'co_eval',
#                  'ser_no',
#                  'req_num', 'est_cause_ship',
#                  'init_action_ship', 'init_action_ship_dt',
#                  'final_action_ship', 'final_action_ship_dt', 'corr_action', 'rpt_by', 'insp_by',
#                  'insp_detail',
#                  'update_by', 'update_dt']  # list of cols to be displayed on the screen
#
#     # _______________Data collection_______________________
#     df_raw = get_data(db, 'drsend')
#
#     df_vessels = get_data(db, 'vessels')
#     df_merged = pd.merge(df_raw, df_vessels[
#         ['vsl_imo', 'vslCode', 'statusActiveInactive', 'vslFleet', 'vslMarSI', 'vslTechSI']], on='vsl_imo',
#                          how='left')
#     df_active_ships = df_merged.drop(df_merged.index[df_merged['statusActiveInactive'] == '0'])  # drop inactive ships
#     df_active_ships = df_active_ships.drop(df_active_ships[(df_active_ships.dt_ocurred < '2019-12-23')].index)  # Drop all entries before
#     vsl_list_fleetwise = get_vessel_byfleet(1)
#     fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(), default='MMS-TOK')
#     vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName],[])  # get vsl names as per flt selected and flatten the list (sum)
#
#     vsl_code = list(df_active_ships.vslCode.where(df_active_ships.ship_name.isin(vslListPerFlt)).unique())
#     st.write(vsl_code)
#     vsl_code = vsl_code[1:]
#     vsl_code.sort()
#     vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt))
#     col1, col2, col3 = st.columns(3)
#
#     rsn_list = df_active_ships['ext_rsn'].unique()
#     ext_rsn=st.multiselect('Select Overdue Reasons:',options=rsn_list,default=rsn_list[0:5])
#
#     with col3:
#         docking = st.checkbox('Include Docking Items')
#
#     df_active_ships_currDRS = df_active_ships.query("ship_name == @vslName and (dt_ocurred.str.contains(@curr_year)"
#                                                     " or done_dt.str.contains(@curr_year) or status.str.contains('OPEN'))",
#                                                     engine='python')
#     if not docking:
#         df_active_ships_currDRS = df_active_ships_currDRS[(df_active_ships_currDRS.ext_rsn != 'Docking')]
#
#     df_active_ships_currDRS['dt_today'] = todaydt  # add today date col for overdue calc.
#
#     def convert(dt):  # To convert string date to date time
#         return datetime.datetime.strptime(dt, "%Y-%m-%d")
#
#     df_active_ships_currDRS['dt_ocurred'] = df_active_ships_currDRS['dt_ocurred'].apply(
#         convert)  # convert report date to datetime
#     df_active_ships_currDRS['dt_today'] = df_active_ships_currDRS['dt_today'].apply(convert)
#
#
#
#     # _________________________________ Filters for overdue
#
#     mask1 = (df_active_ships_currDRS.status == 'OPEN') & (df_active_ships_currDRS.ship_name.isin(vslName)) & (df_active_ships_currDRS.target_dt < df_active_ships_currDRS.dt_today) & (df_active_ships_currDRS.ext_dt < df_active_ships_currDRS.dt_today)
#
#
#
#
#     # ----------------------------All overdue Items_______________________________________________________
#     df_active_ships_currDRS.nc_detail = df_active_ships_currDRS.nc_detail.str.wrap(50)
#     df_active_ships_currDRS.nc_detail = df_active_ships_currDRS.nc_detail.apply(lambda x: x.replace('\n', '<br>'))
#
#     df_all_overdue = df_active_ships_currDRS[mask1]
#
#     df_mask1 = df_active_ships_currDRS[mask1]
#     df_mask1[['ext_rsn']] = df_mask1[['ext_rsn']].fillna('Update ext. reason')
#     df_mask1 = df_mask1.query("ext_rsn==@ext_rsn")
#     df_mask1[['ext_rsn']]=df_mask1[['ext_rsn']].fillna('Update ext. reason')
#     fig_mask1 = px.bar(df_mask1, x='vslCode', y=df_mask1['DRS_ID'].value_counts()
#                        ,
#                        hover_data=['dt_ocurred', 'done_dt', 'target_dt', 'ext_dt', 'rpt_by', 'nc_detail', 'status',
#                                    'ext_rsn'],
#                        color_discrete_sequence=px.colors.qualitative.Pastel)
#     fig_mask1.update_layout(
#         title="Overdue Items past Extension date",
#         xaxis_title="Vessels",
#         yaxis_title="Count of Overdue",
#         showlegend=True, )
#     fig_mask1.update_xaxes(categoryorder='array', categoryarray=vsl_code)
#
#
#     # --------------------------Display graphs
#
#     # with col1:
#     st.plotly_chart(fig_mask1, use_container_width=True)
#     st.write(df_mask1[disp_cols])
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#     # df_openDRS = df_raw.loc[df_raw.status == 'OPEN']  # get DR sender data
#     #
#     # df_fleet = get_data(r'assets/mms_master.sqlite',
#     #                     'fleet')  # get list of fleet names for selecting vesssels fleetwise
#     #
#     # df_vsl = get_data(db, 'vessels')  # Get active  fleet vessel names and IMO
#     # df_vsl_active = df_vsl.loc[df_vsl.statusActiveInactive == '1']
#     #
#     # df_si = get_data(db, 'si')  # Get active SI
#     #
#     # # _________________Data cleaning_________________________
#     #
#     # imo_active = (df_vsl_active['vsl_imo'])  # Tuple of active tanker vessel IMO
#     # df_active_drs = df_openDRS.loc[df_openDRS['vsl_imo'].isin(imo_active)]  # Active vessels in dataframe
#     #
#     # allShips = pd.DataFrame(df_active_drs['ship_name'].unique())  # For using in graph
#     # allshipCode = dict(zip(df_vsl_active.vslName, df_vsl_active.vslCode))
#     # allshipCode["Centennial Sapporo"] = "CSA"
#     # toCorrect = ["dt_ocurred", "init_action_ship_dt", "target_dt", "final_action_ship_dt", "done_dt",
#     #              "update_dt", "ext_dt", "PSC_picdt", "PSC_info2ownr_dt", "PSC_info2chrtr_dt", "PSC_info2rtshp_dt",
#     #              "PSC_info2oilmaj_dt", "PSC_info2mmstpmgmt_dt", "PSC_sndr_offimport_dt"]
#     # for someCol in toCorrect:
#     #     df_active_drs[someCol] = pd.to_datetime(df_active_drs[someCol]).apply(lambda x: x.date())
#     #     # convert str to date
#     # # -------------logic for overdue (today > target and today > ext)
#     # mask = (pd.to_datetime('today') > df_active_drs['target_dt']) & (
#     #             pd.to_datetime('today') > df_active_drs['ext_dt'])  # ext date is before
#     # df_active = df_active_drs.loc[mask]
#     #
#     # # _______________________UI elements_____________________
#     #
#     # filterContainer = st.expander('Overdue deficiencies past extension date')
#     # col1, col2 = filterContainer.columns(2)
#     # with col2:
#     #     rsn_list = df_active['ext_rsn'].unique()
#     #     ext_rsn=st.multiselect('Select Reasons:',options=rsn_list,default=rsn_list[0:5])
#     #     # active_vsl = st.radio('Select Vessels', ('Active','All' ))
#     #     # if active_vsl == 'All':
#     #     #     vsl_list_fleetwise = get_vessel_byfleet(0)
#     #     # else:
#     #     vsl_list_fleetwise = get_vessel_byfleet(1)
#     # with col1:
#     #     fltName = st.multiselect('Select the Fleet', options=vsl_list_fleetwise.keys(), default='MMS-TOK',key='fleet_exp1')
#     #     docking = st.checkbox("Remove DD Jobs", value=True)
#     #
#     #     with filterContainer:
#     #         vslListPerFlt = sum([vsl_list_fleetwise[x] for x in fltName], []) # get vsl names as per flt selected and flatten the list (sum)
#     #         vslName = st.multiselect('Select the vessel:', options=sorted(vslListPerFlt), default=sorted(vslListPerFlt),key='vessel_exp1')
#     #
#     #     with filterContainer:
#     #         df_active = df_active.query("ship_name == @vslName and ext_rsn==@ext_rsn")
#     #         df_active[['ext_rsn']]=df_active[['ext_rsn']].fillna('Update ext. reason')
#     #         df_active = df_active[disp_cols]
#     #
#
#     #
#     #     # _____________________________Graphs Section______________________________
#     #     with filterContainer:
#     #         allShips['Count'] = 0  # add col Count with val 0 in all cells
#     #         allShips.columns = ['ship_name', 'Count']  # Rename columns
#     #         data = df_active['ship_name'].value_counts()  # Pandas series
#     #         df_graph = pd.DataFrame({'ship_name': data.index,
#     #                                  'Count': data.values})  # create dataframe of ship name and count of open overdue def
#     #         df_xaxis = pd.merge(allShips, df_graph, how='outer',
#     #                             on='ship_name')  # merge dataframes to include ships with no overdue def
#     #         df_xaxis = df_xaxis.fillna(0)
#     #
#     #         df_xaxis['Count'] = df_xaxis['Count_x'] + df_xaxis['Count_y']
#     #         df_xaxis.drop(['Count_x', 'Count_y'], axis=1, inplace=True)
#     #
#     #         df_xaxis.sort_values(by='ship_name')  # sort
#     #         filter1 = df_xaxis['ship_name'].isin(vslName)
#     #         df_xaxis = df_xaxis[filter1]
#     #         #df_xaxis = df_xaxis.replace({'ship_name': allshipCode})
#     #         fig = px.bar(df_xaxis, x='ship_name', y='Count', height=400,
#     #                      labels={"ship_name": "Vessel", "Count": "Number of def. past the extension date"},
#     #                      title="<b>Count of overdue items past extension date</b>",text_auto=True)
#     #         # color_continuous_scale=px.colors.sequential.Burg)
#     #         df_active = df_active.sort_values(by='ship_name')
#     #         #df_active = df_active.replace({'ship_name': allshipCode})
#     #         #df_active.mask(df_active['ext_rsn'] == "", 'Update ext. Reason', inplace=True)
#     #         df_active['ext_rsn'].loc[(df_active['ext_rsn']=="")]='update ext. reason'
#     #         fig2 = px.bar(df_active, y=["ship_name"], x="ext_rsn", height=400, color='ext_rsn',
#     #                       title="<b>Extended Items by Reason</b>",
#     #                       color_discrete_sequence=px.colors.qualitative.Pastel)
#     #         fig.update_layout(legend_orientation='h')
#     #         fig.update_xaxes(categoryorder='array',
#     #                          categoryarray=sorted(df_xaxis['ship_name']))
#     #         # fig2.update_layout(legend_orientation='h')
#     #         fig2.update_layout()
#     #         st.plotly_chart(fig, use_container_width=True)
#     #         st.plotly_chart(fig2, use_container_width=True)
#     #         st.write(df_active)
#     # csv = df_active.to_csv().encode('utf-8')  # write df to csv
#     # btnMsg = 'Download ' + str(df_active.shape[0]) + ' Records as CSV'
#     # st.download_button(btnMsg, csv, "DRS-file.csv", "text/csv", key='download-csv')
#     #
#     #         # fig3 = px.colors.sequential.swatches()
#     #         # fig4 = px.colors.qualitative.swatches()
#     #         # st.plotly_chart(fig3)
#     #         # st.plotly_chart(fig4)
#
