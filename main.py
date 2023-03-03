import datetime
from typing import List

import folium
import pandas as pd
import streamlit as st
from folium.plugins import Draw, MarkerCluster
from shapely.geometry import Polygon
from streamlit_folium import st_folium

from utils import read_html, kmb, ctb, gmb_emobility

CENTER_START = [22.302711, 114.177216]
ZOOM_START = 16

if "center" not in st.session_state:
    st.session_state["center"] = [22.302711, 114.177216]
if "zoom" not in st.session_state:
    st.session_state["zoom"] = 11


def init_session_state(reset=False):
    _list1 = ['routes', 'stops', 'markers', 'shapes', 'routes_data']
    _list2 = ['disabled', 'map_html']
    for l in _list1:
        if l not in st.session_state or reset:
            st.session_state[l] = []
    for l in _list2:
        if l not in st.session_state or reset:
            st.session_state[l] = False


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode( 'utf-8' )


def st_df_with_download(df, name):
    st.dataframe( df )
    st.download_button( 'Download', convert_df( df ), file_name=name + '.csv' if name[:-4] != '.csv' else name )


def to_read_html(shapes_data):
    if len( shapes_data['all_drawings'] ) > 0:
        for i, marker in enumerate( shapes_data['all_drawings'] ):
            marker_name = marker['type'] + ' #' + str( i )
            s = st.info( 'Retriving routes in ' + marker_name )
            coordinates = [x[::-1] for x in marker['geometry']['coordinates'][0]]
            polygon = Polygon( coordinates )
            routes, stops = read_html.routes_export_polygon_mode( Polygon( coordinates ) )

            read_html.map_html( stops=stops, aoi=polygon, id=i )
            st.session_state['routes'].append( routes )
            st.session_state['stops'].append( stops )
            s.empty()


def show_results():
    for i, (df1, df2) in enumerate( zip( st.session_state['routes'], st.session_state['stops'] ) ):
        marker_name = 'Feature #' + str( i )
        st.info( marker_name )
        with st.expander( marker_name + ' Routes' ):
            st_df_with_download( df1, marker_name + ' Routes' )
        with st.expander( marker_name + ' Stops' ):
            st_df_with_download( df2, marker_name + ' Stops' )

    if len( st.session_state['routes'] ) > 0:
        st.info( 'All Features Summary' )
        all_routes = pd.concat( st.session_state['routes'] ).drop_duplicates( ignore_index=True )
        all_stops = pd.concat( st.session_state['stops'] )
        with st.expander( 'All Routes' ):
            st_df_with_download( all_routes, 'All Routes' )
        with st.expander( 'All Stops' ):
            st_df_with_download( all_stops, 'All Stops' )


def _show_map(center: List[float], zoom: int) -> folium.Map:
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        control_scale=True,
        tiles="https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/basemap/WGS84/{z}/{x}/{y}.png",
        attr='<u target="_blank" class="copyrightDiv">&copy; The Government of the Hong Kong SAR</u><div style="width:28px;height:28px;display:inline-flex;background:url(https://api.hkmapservice.gov.hk/mapapi/landsdlogo.jpg);background-size:28px;"></div>'
    )

    folium.TileLayer( 'https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/label/hk/en/WGS84/{z}/{x}/{y}.png',
                      attr='LandsD' ).add_to( m )

    Draw(
        export=False,
        position="topleft",
        draw_options={
            "polyline": False,
            "poly": False,
            "circle": False,
            "polygon": True,
            "marker": False,
            "circlemarker": False,
            "rectangle": True,
        },
    ).add_to( m )

    fg1 = folium.FeatureGroup( name="Markers" )
    fg2 = folium.FeatureGroup( name="Shapes" )
    mc = MarkerCluster( disableClusteringAtZoom=16 )

    for s in st.session_state["shapes"]:
        fg2.add_child( s )
    for marker in st.session_state["markers"]:
        marker.add_to( mc )

    fg1.add_to( m )
    fg2.add_to( m )
    fg1.add_child( mc )

    st.session_state['map_html'] = m._repr_html_()

    return m


def switch_time_input_onoff():
    if st.session_state['24hours']:
        st.session_state.disabled = True
    else:
        st.session_state.disabled = False


def v_spacer(height, sb=False) -> None:
    for _ in range( height ):
        if sb:
            st.sidebar.write( '\n' )
        else:
            st.write( '\n' )


class GetHeadway():
    def __init__(self, progress):
        self.columns = ['id', 'route', 'info', 'headway_am', 'headway_pm', 'bound', 'period_am', 'period_pm']
        times = ['am1', 'pm1', 'period', 'day_type']
        for t in times:
            setattr( self, t, st.session_state[t] )
        self.am2 = datetime.datetime.combine( datetime.date.today(), self.am1 ) + datetime.timedelta( hours=period )
        self.am2 = self.am2.time()
        self.pm2 = datetime.datetime.combine( datetime.date.today(), self.pm1 ) + datetime.timedelta( hours=period )
        self.pm2 = self.pm2.time()
        self.progress = progress
        self.dist = st.session_state['dist'][0].lower() if 'dist' in st.session_state else ''

    def kmb(self, routeSP):
        kmb_headway = kmb.main( routeSP, am1=self.am1, am2=self.am2, pm1=self.pm1, pm2=self.pm2, day_type=self.day_type,
                                progress=self.progress )
        return kmb_headway

    def gmb(self, routeSP):
        gmb_headway = gmb_emobility.gmb_get_headway( routeSP, dist=self.dist, progress=self.progress,
                                                     day_type=self.day_type,
                                                     am1=self.am1, am2=self.am2,
                                                     pm1=self.pm1,
                                                     pm2=self.pm2, )
        return gmb_headway.PT

    def ctb(self, routeSP):
        ctb_headway = ctb.main( routeSP, am1=self.am1, am2=self.am2, pm1=self.pm1, pm2=self.pm2, day_type=self.day_type,
                                progress=self.progress )
        return ctb_headway


def all_day_breakfast(routes, SP, day_type, dist, progress):
    """
    Iterate the go_bus_web headway fetching operation for 24 hrs to get the daily variation
    Iteration beginned from 0am and stepping with 2 1-hour period
        (i.e. Iter 1: 0am-1am and 1am-2am,
                Iter 2: 2am-3am and 3am-4am
                    ...
                    )
    Subsequently combines all 2-hours periods to an all-day table
    :return:
    """
    all_day_headway = pd.DataFrame( columns=['route', 'info', 'bound'] )
    SP_functions = {'kmb': kmb.main,
                    'ctb': ctb.main,
                    'gmb': gmb_emobility.gmb_get_headway}

    for hr in range( 0, 23, 2 ):
        am1 = hr
        am2 = hr + 1
        pm1 = hr + 1
        pm2 = hr + 2 if hr < 22 else 0
        if SP != 'gmb':
            period_headway = SP_functions[SP]( routes, am1=am1, am2=am2, pm1=pm1, pm2=pm2, day_type=day_type,
                                               progress=progress )
        else:
            period_headway = SP_functions[SP]( routes, dist=dist, progress=progress,
                                               day_type=day_type,
                                               am1=am1, am2=am2,
                                               pm1=pm1,
                                               pm2=pm2, ).PT
        period_headway = period_headway[['route', 'info', 'bound', 'headway_am', 'headway_pm']]
        period_headway.columns = ['route', 'info', 'bound', str( hr ).rjust( 2, '0' ), str( hr + 1 ).rjust( 2, '0' ),
                                  ]
        if hr == 0:
            all_day_headway = pd.merge( all_day_headway, period_headway, how='right' )
        elif hr < 23:
            all_day_headway = all_day_headway.join( period_headway.iloc[:, 3:5] )

    return all_day_headway


def go_bus_web():
    SP = st.session_state['SP'].lower().split( '/' )[0]
    feature_list = [int( x.split( '_' )[1] ) for x in st.session_state['feature_list']]
    routes = pd.concat( [st.session_state['routes'][i] for i in feature_list] )
    if SP == 'ctb':
        routeSP = routes[
            (routes['Service Provider'].str.contains( 'CTB' )) | (routes['Service Provider'].str.contains( 'NWFB' ))][
            'Route']
    elif SP == 'kmb':
        routeSP = routes[
            (routes['Service Provider'].str.contains( 'KMB' )) | (routes['Service Provider'].str.contains( 'LWB' ))][
            'Route']
    else:
        routeSP = routes[routes['Service Provider'].str.contains( SP.upper() )]['Route']
    print( routeSP )
    routeSP = [str( i ) for i in list( dict.fromkeys( routeSP ) )]

    progress_text = "Operation in progress. Please wait."
    progress = st.progress( 0, text=progress_text )
    if st.session_state['24hours']:
        headway_data = all_day_breakfast( routeSP, st.session_state['SP'].lower().split( '/' )[0],
                                          st.session_state['day_type'],
                                          st.session_state['dist'][0].lower() if 'dist' in st.session_state else '',
                                          progress )
    else:
        GH = GetHeadway( progress )
        get_headway = getattr( GH, SP )
        headway_data = get_headway( routeSP )
    progress.empty()
    return headway_data


if __name__ == "__main__":
    st.set_page_config(
        page_title="mapa",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()
    tab1, tab2 = st.tabs( ["🗺️ Map", "⏳ Headway"] )

    with tab1:
        m = _show_map( center=st.session_state['center'], zoom=st.session_state['zoom'] )
        if len( st.session_state["shapes"] ) == 0:
            st.info( 'Draw the area with the polygon mode in left side panel of the map' )
        output = st_folium( m, key="init", width=1500, height=600,
                            center=st.session_state['center'],
                            zoom=st.session_state['zoom'] )
        if st.button( "Get Data" ):
            init_session_state( True )
            if 'center' in output.keys():
                st.session_state['center'] = list( output['center'].values() )
                st.session_state['zoom'] = output['zoom']
            if output['all_drawings'] is not None:
                to_read_html( output )
                st.experimental_rerun()
            else:
                st.error( 'No area marked in the map' )
        st.download_button( 'Download Map', data=st.session_state['map_html'],
                            file_name='Stops_Map_' + str( datetime.date.today() ) + '.html' )
        show_results()

    with tab2:
        col1, col2 = st.columns( [5, 1] )
        with col1:
            feature_list = [x._name + '_' + str( i ) for i, x in enumerate( st.session_state['shapes'] )]
            features = st.multiselect( 'Select the Feature for Headway data retrival', feature_list, feature_list,
                                       key='feature_list' )
            SP_list = ['KMB', 'CTB/NWFB', 'GMB']
            SP = st.selectbox( 'Select the Service Provider for Headway data retrival', ['KMB', 'CTB/NWFB', 'GMB'],
                               key='SP' )
            col3, col4 = st.columns( [2, 2] )
            with col3:
                am1 = st.time_input( 'AM Start', value=datetime.time( 7 ), key="am1",
                                     disabled=st.session_state.disabled )
                pm1 = st.time_input( 'PM Start', value=datetime.time( 18 ), key="pm1",
                                     disabled=st.session_state.disabled )
            with col4:
                period = st.number_input( 'Period', min_value=1, max_value=4, value=1, key='period' )

        with col2:
            if st.session_state['SP'] == 'GMB':
                st.selectbox( 'Select District', ['Hong Kong', 'Kowloon', 'New Territories'], key='dist' )
            else:
                v_spacer( 6 )

            st.selectbox( 'Day Type', ['weekday', 'saturday', 'holiday'], key='day_type' )
            v_spacer( 2 )
            st.checkbox( '24 hours', on_change=switch_time_input_onoff, key='24hours' )

            st.markdown( "***" )
            if st.button( 'Submit' ):
                st.session_state['routes_data'] = go_bus_web()

        if len( st.session_state['routes_data'] ) > 0:
            st_df_with_download( st.session_state['routes_data'], 'routes_data' )
