# app.py
import streamlit as st

from data_layer import get_metadata_cached, get_sales_df
from components.filters_view import render_filters
from components.map_view import render_map
from components.tables_view import render_tables
from components.charts_view import render_charts
from components.sellers_stores_view import render_sellers_and_stores

st.set_page_config(page_title="Painel de Vendas", layout="wide")
st.title("Painel de Vendas")

# =========================
# Estado do app (session_state)
# =========================
if "filters" not in st.session_state:
    min_date, max_date, _, products_all = get_metadata_cached()
    st.session_state.filters = {
        "start_date": min_date,
        "end_date": max_date,
        "products": list(products_all),
        "states": [],  # vazio = "Todos" no mapa (conforme requisito)
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
# KPIs + Tabelas
# =========================
st.subheader("Resultados")

total_sales = float(df["SalesValue"].sum()) if not df.empty else 0.0
k1, k2, k3 = st.columns(3)
k1.metric("Vendas (R$)", f"{total_sales:,.2f}")
k2.metric("Linhas", f"{len(df):,}")
k3.metric("Estados filtrados", f"{len(f['states']) if f['states'] else 'Todos'}")

render_tables(df)

st.divider()

# =========================
# Visualizações
# =========================
st.subheader("Visualizações")

# 2 gráficos originais (Produto + Série temporal Ano/Mês)
render_charts(df)

st.divider()

# NOVO: Top 10 Vendedores e Lojas
render_sellers_and_stores(f, top_n=10)
