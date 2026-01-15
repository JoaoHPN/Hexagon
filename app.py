import streamlit as st

from data_layer import get_metadata_cached, get_sales_df
from components.filters_view import render_filters
from components.map_view import render_map
from components.tables_view import render_tables
from components.charts_view import render_charts
from components.sellers_stores_view import render_sellers_and_stores

# =========================
# Config
# =========================
st.set_page_config(page_title="Hexagon", layout="wide")

GREEN = "#b4e060"

# =========================
# Header: Logo + Nome
# =========================
header_col1, header_col2 = st.columns([0.05, 0.92], vertical_alignment="center")

with header_col1:
    st.image("logo.png", width=55)

with header_col2:
    st.markdown(
        """
        <div style="display:flex; align-items:center; height:100%;">
            <h1 style="margin:0; padding:0;">Hexagon</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    "<hr style='margin-top:0.5rem; margin-bottom:1.5rem;'>",
    unsafe_allow_html=True,
)

# =========================
# Estado do app (session_state)
# =========================
if "filters" not in st.session_state:
    min_date, max_date, _, products_all = get_metadata_cached()
    st.session_state.filters = {
        "start_date": min_date,
        "end_date": max_date,
        "products": list(products_all),
        "states": [],  # vazio = "Todos" no mapa
    }

f = st.session_state.filters

# =========================
# Layout: Mapa + Filtros
# =========================
map_col, filters_col = st.columns([1.0, 1.75], gap="large")

with map_col:
    render_map(f)

with filters_col:
    render_filters(f)

st.divider()

# =========================
# Dados filtrados finais
# =========================
df = get_sales_df(
    f["start_date"],
    f["end_date"],
    tuple(f["states"]),
    tuple(f["products"]),
)

# =========================
# RESULTADOS (VERDE)
# =========================
st.markdown(
    f"<h2 style='color:{GREEN}; margin-bottom:0.5rem;'>Resultados</h2>",
    unsafe_allow_html=True,
)

total_sales = float(df["SalesValue"].sum()) if not df.empty else 0.0
k1, k2, k3 = st.columns(3)
k1.metric("Vendas (R$)", f"{total_sales:,.2f}")
k2.metric("Linhas", f"{len(df):,}")
k3.metric("Estados filtrados", f"{len(f['states']) if f['states'] else 'Todos'}")

render_tables(df)

st.divider()

# =========================
# VISUALIZAÇÕES (AGORA O TÍTULO + BOTÃO FICAM DENTRO DO COMPONENTE)
# =========================
render_charts(df)

st.divider()

render_sellers_and_stores(f, top_n=10)

