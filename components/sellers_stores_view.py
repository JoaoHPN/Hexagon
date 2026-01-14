# components/sellers_stores_view.py
import streamlit as st
import plotly.express as px
import pandas as pd

from data_layer import get_top_sellers_and_stores

BG = "#0e1117"

def render_sellers_and_stores(filters: dict, top_n: int = 10):
    st.markdown("### Melhores Vendedores e Lojas")

    top_sellers_df, top_stores_df = get_top_sellers_and_stores(
        filters["start_date"],
        filters["end_date"],
        tuple(filters["states"]),
        tuple(filters["products"]),
        top_n=top_n,
    )

    c1, c2 = st.columns(2, gap="large")

    # --------- Top sellers ----------
    with c1:
        st.markdown(f"**Top {top_n} Vendedores (R$)**")
        if top_sellers_df.empty:
            st.info("Sem dados para os filtros selecionados.")
        else:
            fig = px.bar(
                top_sellers_df.sort_values("SalesValue", ascending=True),
                x="SalesValue",
                y="SalesPerson",
                orientation="h",
                labels={"SalesPerson": "Vendedor", "SalesValue": "Vendas"},
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor=BG,
                plot_bgcolor=BG,
                height=420,
                margin=dict(l=0, r=0, t=20, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

    # --------- Top stores ----------
    with c2:
        st.markdown(f"**Top {top_n} Lojas (R$)**")
        if top_stores_df.empty:
            st.info("Sem dados para os filtros selecionados.")
        else:
            fig = px.bar(
                top_stores_df.sort_values("SalesValue", ascending=True),
                x="SalesValue",
                y="Store",
                orientation="h",
                labels={"Store": "Loja", "SalesValue": "Vendas"},
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor=BG,
                plot_bgcolor=BG,
                height=420,
                margin=dict(l=0, r=0, t=20, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
