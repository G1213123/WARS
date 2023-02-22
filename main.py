from typing import List

import folium
import pandas as pd
import streamlit as st
from folium.plugins import Draw, MarkerCluster
from shapely.geometry import Polygon
from streamlit_folium import st_folium

from utils import read_html


def init_session_state(reset=False):
    _list = ['routes', 'stops', 'markers', 'shapes']
    for l in _list:
        if l not in st.session_state or reset:
            st.session_state[l] = []


def to_read_html(shapes_data):
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


if __name__ == "__main__":
    st.set_page_config(
        page_title="mapa",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()
    fg = folium.FeatureGroup( name="Markers" )
    for marker in st.session_state["markers"]:
        fg.add_child( marker )
    m = _show_map( center=[22.302711, 114.177216], zoom=11 )
    output = st_folium( m, key="init", width=1500, height=600, feature_group_to_add=fg, )
    if st.button( "Get Data" ):
        init_session_state( True )
        to_read_html( output )
        st.experimental_rerun()
    show_results()
