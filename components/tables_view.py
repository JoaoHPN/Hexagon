# components/tables_view.py
import streamlit as st
import pandas as pd

def render_tables(df: pd.DataFrame):
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
