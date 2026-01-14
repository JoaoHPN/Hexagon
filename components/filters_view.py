# components/filters_view.py
import streamlit as st
import pandas as pd

from data_layer import get_metadata_cached, get_state_df_all, get_products_all

def render_filters(filters: dict):
    min_date, max_date, _, _ = get_metadata_cached()
    state_df_all = get_state_df_all()
    products_all = get_products_all()

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
            # Pelo requisito atual: vazio = "Todos" no mapa
            st.session_state.filters["states"] = []
            st.session_state.pop("regions_editor", None)
            st.rerun()

        region_tbl = state_df_all.copy()
        region_tbl["Selecionar"] = region_tbl["StateCode"].isin(filters["states"])

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
        prod_tbl["Selecionar"] = prod_tbl["Product"].isin(filters["products"])

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
