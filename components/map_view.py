# components/map_view.py
import streamlit as st
import plotly.graph_objects as go

from data_layer import get_map_df

BG = "#0e1117"
MAP_SELECTED = "#b4e060"
MAP_UNSELECTED = "#1a1f2b"

def render_map(filters: dict):
    st.markdown("**Mapa (EUA)**")

    base_map = get_map_df(
        filters["start_date"],
        filters["end_date"],
        tuple(filters["products"]),
    )

    all_state_codes = base_map["StateCode"].tolist()

    # Regra: vazio = "Todos" (mapa inteiro verde na carga inicial)
    if not filters["states"]:
        selected_set = set(all_state_codes)
    else:
        selected_set = set([str(x).strip().upper() for x in filters["states"]])

    base_map["SelectedNum"] = base_map["StateCode"].apply(lambda x: 1 if x in selected_set else 0)

    colorscale = [
        [0.0, MAP_UNSELECTED],
        [0.4999, MAP_UNSELECTED],
        [0.5, MAP_SELECTED],
        [1.0, MAP_SELECTED],
    ]

    fig_map = go.Figure(
        go.Choropleth(
            locations=base_map["StateCode"],
            locationmode="USA-states",
            z=base_map["SelectedNum"],
            zmin=0,
            zmax=1,
            colorscale=colorscale,
            showscale=False,
            marker=dict(line=dict(color="#6c768a", width=0.8), opacity=1.0),
        )
    )

    fig_map.update_layout(
        geo=dict(scope="usa", bgcolor=BG),
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        margin=dict(l=0, r=0, t=0, b=0),
        height=255,
    )

    st.plotly_chart(
        fig_map,
        use_container_width=True,
        config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False},
        key=f"map_{hash(tuple(filters['products']))}_{hash(tuple(filters['states']))}_{filters['start_date']}_{filters['end_date']}",
    )

    st.caption("Selecionados: " + (", ".join(filters["states"]) if filters["states"] else "Todos"))
