import streamlit as st
import pandas as pd
import plotly.express as px

from db import get_conn, get_metadata, load_sales_by_state, load_sales_filtered

# =========================
# Config
# =========================
st.set_page_config(page_title="Painel de Vendas", layout="wide")
st.title("Painel de Vendas")

BG = "#0e1117"
MAP_SELECTED = "#b4e060"
MAP_UNSELECTED = "#1a1f2b"

# =========================
# Conexão (1 por sessão)
# =========================
@st.cache_resource
def conn():
    return get_conn()

cn = conn()

# =========================
# Metadata
# =========================
@st.cache_data(ttl=3600)
def metadata():
    return get_metadata(cn)

min_date, max_date, state_df_all, products_all = metadata()

# =========================
# Estado único de filtros
# =========================
if "filters" not in st.session_state:
    st.session_state.filters = {
        "start_date": min_date,
        "end_date": max_date,
        "products": list(products_all),
        "states": [],  # StateCode
    }

f = st.session_state.filters

# =========================
# Topo: MAPA + FILTROS
# =========================
map_col, filters_col = st.columns([1.0, 1.75], gap="large")

with map_col:
    st.markdown("**Mapa (EUA)**")

    # OBS: o mapa é visual (passivo). Precisamos que SEMPRE redesenhe quando filtro muda.
    # Vamos:
    # - construir um DF com TODOS os estados
    # - criar uma coluna numérica 0/1 para o Plotly pintar com escala contínua travada
    @st.cache_data(ttl=600)
    def map_df_build(start_date, end_date, products_sel, states_sel):
        sales_df = load_sales_by_state(cn, start_date, end_date, products_sel).copy()

        base = state_df_all[["StateCode"]].drop_duplicates().copy()
        base = base.merge(sales_df, on="StateCode", how="left")
        base["SalesValue"] = base["SalesValue"].fillna(0)

        states_set = set(states_sel)
        base["SelectedNum"] = base["StateCode"].apply(lambda x: 1 if x in states_set else 0)

        return base

    map_df = map_df_build(
        f["start_date"],
        f["end_date"],
        tuple(f["products"]),
        tuple(f["states"]),
    )

    # Escala contínua "travada" em 0/1 usando as tuas duas cores
    # Isso elimina qualquer ambiguidade de bool/categoria e garante "fill".
    two_color_scale = [
        (0.0, MAP_UNSELECTED),
        (0.4999, MAP_UNSELECTED),
        (0.5, MAP_SELECTED),
        (1.0, MAP_SELECTED),
    ]

    fig = px.choropleth(
        map_df,
        locations="StateCode",
        locationmode="USA-states",
        color="SelectedNum",
        scope="usa",
        range_color=(0, 1),
        color_continuous_scale=two_color_scale,
    )

    fig.update_traces(
        marker_line_width=0.8,
        marker_line_color="#6c768a",
    )

    fig.update_layout(
        template="plotly_dark",
        height=255,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        showlegend=False,
        coloraxis_showscale=False,  # remove barra de cor
    )
    fig.update_geos(bgcolor=BG, showcountries=False, showcoastlines=False)

    # Key variável força o Streamlit a redesenhar o componente quando filtro muda
    map_key = f"map_{f['start_date']}_{f['end_date']}_{hash(tuple(f['products']))}_{hash(tuple(f['states']))}"
    st.plotly_chart(fig, use_container_width=True, key=map_key)

    st.caption(
        "Selecionados: "
        + (", ".join(f["states"]) if f["states"] else "Todos")
    )

with filters_col:
    st.subheader("Filtros")

    col_state, col_prod, col_actions = st.columns([1.0, 1.0, 0.6], gap="large")

    with col_state:
        st.markdown("**Estado (checkbox)**")

        region_tbl = state_df_all.copy()
        region_tbl["Selecionar"] = region_tbl["StateCode"].isin(f["states"])

        edited_regions = st.data_editor(
            region_tbl[["Selecionar", "StateName", "StateCode"]],
            hide_index=True,
            disabled=["StateName", "StateCode"],
            use_container_width=True,
            height=220,
            key="regions_editor",
        )
        selected_states_from_table = edited_regions.loc[
            edited_regions["Selecionar"] == True, "StateCode"
        ].tolist()

    with col_prod:
        st.markdown("**Produtos (checkbox)**")

        prod_tbl = pd.DataFrame({"Product": products_all})
        prod_tbl["Selecionar"] = prod_tbl["Product"].isin(f["products"])

        edited_products = st.data_editor(
            prod_tbl[["Selecionar", "Product"]],
            hide_index=True,
            disabled=["Product"],
            use_container_width=True,
            height=220,
            key="products_editor",
        )
        selected_products_from_table = edited_products.loc[
            edited_products["Selecionar"] == True, "Product"
        ].tolist()

    with col_actions:
        st.markdown("**Ações**")

        if st.button("Aplicar", key="apply_filters", use_container_width=True):
            st.session_state.filters["states"] = selected_states_from_table
            st.session_state.filters["products"] = selected_products_from_table
            st.rerun()

        if st.button("Limpar estados", key="clear_states_btn", use_container_width=True):
            st.session_state.filters["states"] = []
            st.rerun()

        if st.button("Resetar produtos", key="reset_products_btn", use_container_width=True):
            st.session_state.filters["products"] = list(products_all)
            st.rerun()

        if st.button("Reset geral", key="reset_all_btn", use_container_width=True):
            st.session_state.filters = {
                "start_date": min_date,
                "end_date": max_date,
                "products": list(products_all),
                "states": [],
            }
            st.rerun()

st.divider()

# =========================
# Dados filtrados finais
# =========================
@st.cache_data(ttl=600)
def sales_data(start_date, end_date, states_sel, products_sel):
    return load_sales_filtered(cn, start_date, end_date, states_sel, products_sel)

f = st.session_state.filters
df = sales_data(f["start_date"], f["end_date"], tuple(f["states"]), tuple(f["products"]))

# =========================
# Resultados
# =========================
st.subheader("Resultados")

total_sales = float(df["SalesValue"].sum()) if not df.empty else 0.0
k1, k2, k3 = st.columns(3)
k1.metric("Vendas (R$)", f"{total_sales:,.2f}")
k2.metric("Linhas", f"{len(df):,}")
k3.metric("Estados filtrados", f"{len(f['states']) if f['states'] else 'Todos'}")

# Tabelas na mesma linha: Estado | Produto | Mês
t1, t2, t3 = st.columns(3, gap="large")

with t1:
    st.markdown("**Vendas por Estado**")
    if df.empty:
        by_region = pd.DataFrame(columns=["State", "SalesValue"])
    else:
        by_region = (
            df.groupby("State", as_index=False)["SalesValue"]
            .sum()
            .sort_values("SalesValue", ascending=False)
        )
    st.dataframe(by_region, use_container_width=True, height=300)

with t2:
    st.markdown("**Vendas por Produto**")
    if df.empty:
        by_product = pd.DataFrame(columns=["Product", "SalesValue"])
    else:
        by_product = (
            df.groupby("Product", as_index=False)["SalesValue"]
            .sum()
            .sort_values("SalesValue", ascending=False)
        )
    st.dataframe(by_product, use_container_width=True, height=300)

with t3:
    st.markdown("**Vendas por Mês (ano/mês)**")
    if df.empty:
        by_month = pd.DataFrame(columns=["Year", "Month", "SalesValue"])
    else:
        tmp = df.copy()
        tmp["Year"] = tmp["OrderDate"].dt.year
        tmp["Month"] = tmp["OrderDate"].dt.to_period("M").astype(str)
        by_month = (
            tmp.groupby(["Year", "Month"], as_index=False)["SalesValue"]
            .sum()
            .sort_values("Month")
        )
    st.dataframe(by_month, use_container_width=True, height=300)
