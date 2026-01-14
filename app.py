# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from db import get_conn, get_metadata, load_sales_by_state, load_sales_filtered

# =========================
# Config
# =========================
st.set_page_config(page_title="Painel de Vendas", layout="wide")
st.title("Painel de Vendas")

BG = "#0e1117"
MAP_SELECTED = "#b4e060"   # <- cor exigida
MAP_UNSELECTED = "#1a1f2b"

# =========================
# Conexão
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

# Normaliza StateCode (defensivo)
state_df_all = state_df_all.copy()
state_df_all["StateCode"] = state_df_all["StateCode"].astype(str).str.strip().str.upper()

# =========================
# Estado único de filtros
# =========================
if "filters" not in st.session_state:
    st.session_state.filters = {
        "start_date": min_date,
        "end_date": max_date,
        "products": list(products_all),
        "states": [],  # IMPORTANTE: vazio = "todos" para o mapa
    }

f = st.session_state.filters

# =========================
# Layout: MAPA + FILTROS
# =========================
map_col, filters_col = st.columns([1.0, 1.75], gap="large")

# =========================
# MAPA (robusto + sem toolbar)
# =========================
with map_col:
    st.markdown("**Mapa (EUA)**")

    @st.cache_data(ttl=600)
    def map_df_build(start_date, end_date, products_sel):
        # Vendas (pode vir faltando estados)
        sales_df = load_sales_by_state(cn, start_date, end_date, products_sel).copy()
        if not sales_df.empty:
            sales_df["StateCode"] = sales_df["StateCode"].astype(str).str.strip().str.upper()

        # Base com TODOS os estados (do metadata)
        base = state_df_all[["StateCode"]].drop_duplicates().copy()
        base = base.merge(sales_df, on="StateCode", how="left")
        if "SalesValue" not in base.columns:
            base["SalesValue"] = 0
        base["SalesValue"] = base["SalesValue"].fillna(0)

        return base

    base_map = map_df_build(
        f["start_date"],
        f["end_date"],
        tuple(f["products"]),
    )

    # Regra: states vazio = todos selecionados (mapa todo verde na carga inicial)
    all_state_codes = base_map["StateCode"].tolist()
    selected_states = f["states"]

    if not selected_states:
        selected_set = set(all_state_codes)
    else:
        selected_set = set([str(x).strip().upper() for x in selected_states])

    base_map["SelectedNum"] = base_map["StateCode"].apply(lambda x: 1 if x in selected_set else 0)

    # Escala travada (0 = escuro, 1 = verde)
    colorscale = [
        [0.0, MAP_UNSELECTED],
        [0.4999, MAP_UNSELECTED],
        [0.5, MAP_SELECTED],
        [1.0, MAP_SELECTED],
    ]

    fig = go.Figure(
        go.Choropleth(
            locations=base_map["StateCode"],
            locationmode="USA-states",
            z=base_map["SelectedNum"],
            zmin=0,
            zmax=1,
            colorscale=colorscale,
            showscale=False,
            marker=dict(
                line=dict(color="#6c768a", width=0.8),
                opacity=1.0,
            ),
        )
    )

    fig.update_layout(
        geo=dict(scope="usa", bgcolor=BG),
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        margin=dict(l=0, r=0, t=0, b=0),
        height=255,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "scrollZoom": False,
            "doubleClick": False,
        },
        key=f"map_{hash(tuple(f['products']))}_{hash(tuple(f['states']))}_{f['start_date']}_{f['end_date']}",
    )

    # Descrição (como você pediu)
    st.caption(
        "Selecionados: "
        + (", ".join(f["states"]) if f["states"] else "Todos")
    )

# =========================
# FILTROS
# =========================
with filters_col:
    st.subheader("Filtros")

    col_state, col_prod, col_actions = st.columns([1.0, 1.0, 0.6], gap="large")

    # ---------- ESTADOS ----------
    with col_state:
        st.markdown("**Estado (checkbox)**")

        b1, b2 = st.columns(2)
        if b1.button("Selecionar todos", key="states_select_all", use_container_width=True):
            st.session_state.filters["states"] = state_df_all["StateCode"].tolist()
            st.session_state.pop("regions_editor", None)
            st.rerun()

        if b2.button("Selecionar nenhum", key="states_select_none", use_container_width=True):
            st.session_state.filters["states"] = []
            st.session_state.pop("regions_editor", None)
            st.rerun()

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

    # ---------- PRODUTOS ----------
    with col_prod:
        st.markdown("**Produtos (checkbox)**")

        p1, p2 = st.columns(2)
        if p1.button("Selecionar todos", key="products_select_all", use_container_width=True):
            st.session_state.filters["products"] = list(products_all)
            st.session_state.pop("products_editor", None)
            st.rerun()

        if p2.button("Selecionar nenhum", key="products_select_none", use_container_width=True):
            st.session_state.filters["products"] = []
            st.session_state.pop("products_editor", None)
            st.rerun()

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

    # ---------- AÇÕES ----------
    with col_actions:
        st.markdown("**Ações**")

        if st.button("Aplicar", key="apply_filters", use_container_width=True):
            st.session_state.filters["states"] = selected_states_from_table
            st.session_state.filters["products"] = selected_products_from_table
            st.rerun()

        if st.button("Reset geral", key="reset_all", use_container_width=True):
            st.session_state.filters = {
                "start_date": min_date,
                "end_date": max_date,
                "products": list(products_all),
                "states": [],
            }
            st.session_state.pop("regions_editor", None)
            st.session_state.pop("products_editor", None)
            st.rerun()

# =========================
# RESULTADOS
# =========================
st.divider()

@st.cache_data(ttl=600)
def sales_data(start_date, end_date, states_sel, products_sel):
    return load_sales_filtered(cn, start_date, end_date, states_sel, products_sel)

f = st.session_state.filters
df = sales_data(
    f["start_date"],
    f["end_date"],
    tuple(f["states"]),
    tuple(f["products"]),
)

st.subheader("Resultados")

total_sales = float(df["SalesValue"].sum()) if not df.empty else 0.0
k1, k2, k3 = st.columns(3)
k1.metric("Vendas (R$)", f"{total_sales:,.2f}")
k2.metric("Linhas", f"{len(df):,}")
k3.metric("Estados filtrados", f"{len(f['states']) if f['states'] else 'Todos'}")

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
        by_month = pd.DataFrame(columns=["Month", "SalesValue"])
    else:
        tmp = df.copy()
        tmp["Month"] = tmp["OrderDate"].dt.to_period("M").astype(str)
        by_month = (
            tmp.groupby("Month", as_index=False)["SalesValue"]
            .sum()
            .sort_values("Month")
        )
    st.dataframe(by_month, use_container_width=True, height=300)
