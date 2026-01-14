# components/charts_view.py
import streamlit as st
import pandas as pd
import plotly.express as px

BG = "#0e1117"

def render_charts(df: pd.DataFrame):
    g1, g2 = st.columns(2, gap="large")

    # 1) Barras - vendas por produto
    with g1:
        st.markdown("**Gráfico de Barras — Vendas por Produto**")
        if df.empty:
            st.info("Sem dados para os filtros selecionados.")
        else:
            sales_by_product = (
                df.groupby("Product", as_index=False)["SalesValue"]
                .sum()
                .sort_values("SalesValue", ascending=False)
            )
            fig_bar = px.bar(
                sales_by_product,
                x="Product",
                y="SalesValue",
                text_auto=".2s",
                labels={"Product": "Produto", "SalesValue": "Vendas"},
            )
            fig_bar.update_layout(
                template="plotly_dark",
                paper_bgcolor=BG,
                plot_bgcolor=BG,
                xaxis_tickangle=-45,
                height=420,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # 2) Linha - vendas ao longo do tempo (Ano/Mês)
    with g2:
        st.markdown("**Gráfico de Linhas — Vendas ao Longo do Tempo**")

        granularity = st.selectbox(
            "Visualizar por",
            ["Mês", "Ano"],
            index=0,
            key="time_granularity",
        )

        if df.empty:
            st.info("Sem dados para os filtros selecionados.")
        else:
            df_time = df.copy()

            if granularity == "Mês":
                df_time["Period"] = df_time["OrderDate"].dt.to_period("M").astype(str)  # YYYY-MM
                period_label = "Mês"
                sales_over_time = (
                    df_time.groupby("Period", as_index=False)["SalesValue"]
                    .sum()
                    .sort_values("Period")
                )
            else:
                df_time["Period"] = df_time["OrderDate"].dt.year.astype(int)
                period_label = "Ano"
                sales_over_time = (
                    df_time.groupby("Period", as_index=False)["SalesValue"]
                    .sum()
                    .sort_values("Period")
                )
                sales_over_time["Period"] = sales_over_time["Period"].astype(str)

            fig_line = px.line(
                sales_over_time,
                x="Period",
                y="SalesValue",
                markers=True,
                labels={"Period": period_label, "SalesValue": "Vendas"},
            )
            fig_line.update_layout(
                template="plotly_dark",
                paper_bgcolor=BG,
                plot_bgcolor=BG,
                height=420,
            )
            st.plotly_chart(fig_line, use_container_width=True)
