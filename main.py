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
    _list2 = ['disabled']
    for l in _list1:
        if l not in st.session_state or reset:
            st.session_state[l] = []
    for l in _list2:
        if l not in st.session_state or reset:
            st.session_state[l] = False


def to_read_html(shapes_data):
    if len( shapes_data['all_drawings'] ) > 0:
        for i, marker in enumerate( shapes_data['all_drawings'] ):
            marker_name = marker['type'] + ' #' + str( i )
            s = st.info( 'Retriving routes in ' + marker_name )
            coordinates = [x[::-1] for x in marker['geometry']['coordinates'][0]]
            routes, stops = read_html.routes_export_polygon_mode( Polygon( coordinates ) )

            st.session_state['routes'].append( routes )
            st.session_state['stops'].append( stops )
            s.empty()


def show_results():
    for i, (df1, df2) in enumerate( zip( st.session_state['routes'], st.session_state['stops'] ) ):
        marker_name = 'Feature #' + str( i )
        st.info( marker_name )
        with st.expander( marker_name + ' Routes' ):
            st.dataframe( df1 )
        with st.expander( marker_name + ' Stops' ):
            st.dataframe( df2 )

    if len( st.session_state['routes'] ) > 0:
        st.info( 'All Feature Summary' )
        all_routes = pd.concat( st.session_state['routes'] ).drop_duplicates( ignore_index=True )
        all_stops = pd.concat( st.session_state['stops'] )
        with st.expander( 'All Routes' ):
            st.dataframe( all_routes )
        with st.expander( 'All Stops' ):
            st.dataframe( all_stops )


def _show_map(center: List[float], zoom: int) -> folium.Map:
    fg1 = folium.FeatureGroup( name="Markers" )
    fg2 = folium.FeatureGroup( name="Shapes" )
    mc = MarkerCluster( disableClusteringAtZoom=16 )
    for marker in st.session_state["markers"]:
        marker.add_to( mc )
    for s in st.session_state["shapes"]:
        fg2.add_child( s )
    fg1.add_child( mc )
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        control_scale=True,
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
        # noqa: E501
    )
    mc.add_to( (m) )
    fg2.add_to( m )
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

    def kmb(self, routeSP):
        kmb_headway = kmb.main( routeSP, am1=self.am1, am2=self.am2, pm1=self.pm1, pm2=self.pm2, day_type=self.day_type,
                                progress=self.progress )
        return kmb_headway

    def gmb(self, routeSP):
        gmb_headway = gmb_emobility.gmb_get_headway( routeSP, dist=self.variable2[:1].lower(),
                                                     am1=self.am1, am2=self.am2,
                                                     pm1=self.pm1,
                                                     pm2=self.pm2,
                                                     archive=self._archive )
        return gmb_headway.PT

    def ctb(self, routeSP):
        ctb_headway = ctb.main( routeSP, am1=self.am1, am2=self.am2, pm1=self.pm1, pm2=self.pm2,
                                progress=self.progress )
        return ctb_headway


def go_bus_web():
    SP = st.session_state['SP'].lower().split( '/' )[0]
    feature_list = [int( x.split( '_' )[1] ) for x in st.session_state['feature_list']]
    routes = pd.concat( [st.session_state['routes'][i] for i in feature_list] )
    extra_loading = 0
    if SP == 'ctb':
        routeSP = routes[
            (routes['Service Provider'].str.contains( 'CTB' )) | (routes['Service Provider'].str.contains( 'NWFB' ))][
            'Route']
        extra_loading = 3
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
        fg = folium.FeatureGroup( name="Markers" )
        for marker in st.session_state["markers"]:
            fg.add_child( marker )
        m = _show_map( center=st.session_state['center'], zoom=st.session_state['zoom'] )
        output = st_folium( m, key="init", width=1500, height=600, feature_group_to_add=fg,
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
        show_results()

    with tab2:
        col1, col2 = st.columns( [5, 1] )
        with col1:
            with st.form( 'inputs' ):
                feature_list = [x._name + '_' + str( i ) for i, x in enumerate( st.session_state['shapes'] )]
                features = st.multiselect( 'Select the Feature for Headway data retrival', feature_list, feature_list,
                                           key='feature_list' )
                SP_list = ['KMB', 'CTB/NWFB', 'GMB']
                SP = st.selectbox( 'Select the Service Provider Headway data retrival', ['KMB', 'CTB/NWFB', 'GMB'],
                                   key='SP' )
                col3, col4 = st.columns( [2, 2] )
                with col3:
                    am1 = st.time_input( 'AM Start', value=datetime.time( 7 ), key="am1",
                                         disabled=st.session_state.disabled )
                    pm1 = st.time_input( 'PM Start', value=datetime.time( 18 ), key="pm1",
                                         disabled=st.session_state.disabled )
                with col4:
                    period = st.number_input( 'Period', min_value=1, max_value=4, value=1, key='period' )

                if st.form_submit_button():
                    st.session_state['routes_data'] = go_bus_web()
        if st.session_state['routes_data'] is not None:
            st.dataframe( st.session_state['routes_data'] )

            with col2:
                v_spacer( 10 )
                st.markdown( "***" )
                st.checkbox( '24 hours', on_change=switch_time_input_onoff, key='24hours' )
                st.selectbox( 'Day Type', ['weekday', 'saturday', 'holiday'], key='day_type' )
