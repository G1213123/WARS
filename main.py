from typing import List

import folium
import pandas as pd
import streamlit as st
from folium.plugins import Draw
from shapely.geometry import Polygon
from streamlit_folium import st_folium

from utils import read_html


def to_read_html(shapes_data):
    all_routes, all_stops = None, None
    for i, marker in enumerate( shapes_data['all_drawings'] ):
        marker_name = marker['type'] + ' #' + str( i )
        st.info( 'retriving routes in ' + marker_name )
        coordinates = [x[::-1] for x in marker['geometry']['coordinates'][0]]
        routes, stops = read_html.routes_export_polygon_mode( Polygon( coordinates ) )
        with st.expander( marker_name + ' Routes' ):
            st.dataframe( routes )
        with st.expander( marker_name + ' Stops' ):
            st.dataframe( stops )
        all_routes = pd.concat( [all_routes, routes] )
        all_stops = pd.concat( [all_stops, stops] )
    st.info( 'Summary' )
    with st.expander( 'All Routes' ):
        st.dataframe( all_routes )
    with st.expander( 'All Stops' ):
        st.dataframe( all_stops )


def _show_map(center: List[float], zoom: int) -> folium.Map:
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        control_scale=True,
        tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
        # noqa: E501
    )
    Draw(
        export=False,
        position="topleft",
        draw_options={
            "polyline": False,
            "poly": False,
            "circle": False,
            "polygon": False,
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

    m = _show_map( center=[22.302711, 114.177216], zoom=11 )
    output = st_folium( m, key="init", width=1200, height=600 )
    if st.button( "Get Data" ):
        to_read_html( output )
