import streamlit as st
import plotly.express as px

from data_layer import get_top_sellers_and_stores

BG = "#0e1117"
GREEN = "#b4e060"

def render_sellers_and_stores(filters: dict, top_n: int = 10):

    # =========================
    # Estado do clique (exclusivo)
    # =========================
    if "selected_seller" not in st.session_state:
        st.session_state.selected_seller = None

    if "selected_store" not in st.session_state:
        st.session_state.selected_store = None

    # =========================
    # Header: título + botão reset
    # =========================
    title_col, button_col = st.columns([0.8, 0.2], vertical_alignment="center")

    with title_col:
        st.markdown(
            f"<h2 style='color:{GREEN}; margin:0;'>Melhores Vendedores e Lojas</h2>",
            unsafe_allow_html=True,
        )

    with button_col:
        if st.button(
            "🔄 Voltar ao filtro original",
            use_container_width=True,
            disabled=(
                st.session_state.selected_seller is None
                and st.session_state.selected_store is None
            ),
        ):
            st.session_state.selected_seller = None
            st.session_state.selected_store = None
            st.rerun()

    st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)

    # =========================
    # Dados
    # =========================
    top_sellers_df, top_stores_df = get_top_sellers_and_stores(
        filters["start_date"],
        filters["end_date"],
        tuple(filters["states"]),
        tuple(filters["products"]),
        top_n=top_n,
        selected_seller=st.session_state.selected_seller,
        selected_store=st.session_state.selected_store,
    )

    c1, c2 = st.columns(2, gap="large")

    # =========================
    # TOP VENDEDORES (com valores)
    # =========================
    with c1:
        st.markdown("**Top Vendedores**")

        if top_sellers_df.empty:
            st.info("Sem dados para os filtros selecionados.")
        else:
            fig_sellers = px.bar(
                top_sellers_df.sort_values("SalesValue", ascending=True),
                x="SalesValue",
                y="SalesPerson",
                orientation="h",
                text="SalesValue",
            )

            fig_sellers.update_traces(
                texttemplate="%{text:.2s}",
                textposition="outside",
                cliponaxis=False,
            )

            fig_sellers.update_layout(
                template="plotly_dark",
                paper_bgcolor=BG,
                plot_bgcolor=BG,
                height=420,
                margin=dict(l=0, r=40, t=20, b=0),
            )

            sellers_event = st.plotly_chart(
                fig_sellers,
                use_container_width=True,
                selection_mode="points",
                on_select="rerun",
                key="sellers_chart",
            )

            if (
                sellers_event
                and sellers_event.selection
                and sellers_event.selection.get("points")
                and len(sellers_event.selection["points"]) > 0
            ):
                point = sellers_event.selection["points"][0]
                st.session_state.selected_seller = point.get("y")
                st.session_state.selected_store = None

    # =========================
    # TOP LOJAS (com valores)
    # =========================
    with c2:
        st.markdown("**Top Lojas**")

        if top_stores_df.empty:
            st.info("Sem dados para os filtros selecionados.")
        else:
            fig_stores = px.bar(
                top_stores_df.sort_values("SalesValue", ascending=True),
                x="SalesValue",
                y="Store",
                orientation="h",
                text="SalesValue",
            )

            fig_stores.update_traces(
                texttemplate="%{text:.2s}",
                textposition="outside",
                cliponaxis=False,
            )

            fig_stores.update_layout(
                template="plotly_dark",
                paper_bgcolor=BG,
                plot_bgcolor=BG,
                height=420,
                margin=dict(l=0, r=40, t=20, b=0),
            )

            stores_event = st.plotly_chart(
                fig_stores,
                use_container_width=True,
                selection_mode="points",
                on_select="rerun",
                key="stores_chart",
            )

            if (
                stores_event
                and stores_event.selection
                and stores_event.selection.get("points")
                and len(stores_event.selection["points"]) > 0
            ):
                point = stores_event.selection["points"][0]
                st.session_state.selected_store = point.get("y")
                st.session_state.selected_seller = None




