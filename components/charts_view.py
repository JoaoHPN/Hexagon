import streamlit as st
import pandas as pd
import plotly.express as px

BG = "#0e1117"
GREEN = "#b4e060"

CHART_HEIGHT = 420

# Margens fixas e iguais nos dois gráficos
# (b controla exatamente onde fica a "linha base" do eixo X)
COMMON_MARGIN = dict(l=0, r=0, t=20, b=110)

def _freeze_axis_margins(fig):
    """
    Impede o Plotly de "inventar" margens diferentes entre gráficos.
    Isso é o que causa desalinhamento visual quando um gráfico tem
    labels mais longas/rotacionadas que o outro.
    """
    fig.update_layout(
        height=CHART_HEIGHT,
        margin=COMMON_MARGIN,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        template="plotly_dark",
    )
    fig.update_xaxes(automargin=False)
    fig.update_yaxes(automargin=False)
    return fig

def render_charts(df: pd.DataFrame):
    # =========================
    # Estado de interação (exclusivo)
    # =========================
    if "viz_selected_product" not in st.session_state:
        st.session_state.viz_selected_product = None

    if "viz_selected_period" not in st.session_state:
        st.session_state.viz_selected_period = None

    if "viz_period_granularity" not in st.session_state:
        st.session_state.viz_period_granularity = "Mês"

    # =========================
    # Header: título + botão reset (direita)
    # =========================
    title_col, button_col = st.columns([0.8, 0.2], vertical_alignment="center")

    with title_col:
        st.markdown(
            f"<h2 style='color:{GREEN}; margin:0;'>Visualizações</h2>",
            unsafe_allow_html=True,
        )

    with button_col:
        if st.button(
            "🔄 Voltar ao filtro original",
            use_container_width=True,
            disabled=(
                st.session_state.viz_selected_product is None
                and st.session_state.viz_selected_period is None
            ),
            key="viz_reset_btn",
        ):
            st.session_state.viz_selected_product = None
            st.session_state.viz_selected_period = None
            st.rerun()

    # =========================
    # Controle: "Visualizar por" embaixo do botão (canto direito, estreito)
    # =========================
    ctrl_left, ctrl_right = st.columns([0.8, 0.2], vertical_alignment="center")
    with ctrl_left:
        st.write("")  # espaço proposital para manter alinhamento e não ocupar a tela toda

    with ctrl_right:
        granularity = st.selectbox(
            "Visualizar por",
            ["Mês", "Ano"],
            index=0,
            key="time_granularity_viz",
        )

    st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

    # Se mudou a granularidade, o filtro de período pode ficar inválido
    if st.session_state.viz_period_granularity != granularity:
        st.session_state.viz_period_granularity = granularity
        st.session_state.viz_selected_period = None

    # =========================
    # Aplicação do cross-filter (exclusivo)
    # =========================
    df_for_bar = df
    df_for_line = df

    # Clique em produto -> filtra linha por produto
    if st.session_state.viz_selected_product:
        df_for_line = df_for_line[
            df_for_line["Product"] == st.session_state.viz_selected_product
        ]

    # Clique em período -> filtra barras por período
    if st.session_state.viz_selected_period:
        tmp = df_for_bar.copy()
        if granularity == "Mês":
            tmp["__Period"] = tmp["OrderDate"].dt.to_period("M").astype(str)  # YYYY-MM
        else:
            tmp["__Period"] = tmp["OrderDate"].dt.year.astype(int).astype(str)  # YYYY

        df_for_bar = tmp[tmp["__Period"] == st.session_state.viz_selected_period].drop(
            columns=["__Period"]
        )

    # =========================
    # Layout: 2 gráficos (alinhados)
    # =========================
    g1, g2 = st.columns(2, gap="large")

    # -------------------------
    # 1) Barras — Vendas por Produto (clicável)
    # -------------------------
    with g1:
        st.markdown("**Gráfico de Barras — Vendas por Produto**")

        if df_for_bar.empty:
            st.info("Sem dados para os filtros selecionados.")
        else:
            sales_by_product = (
                df_for_bar.groupby("Product", as_index=False)["SalesValue"]
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
            fig_bar.update_xaxes(tickangle=-45)  # rótulos longos
            fig_bar = _freeze_axis_margins(fig_bar)

            bar_event = st.plotly_chart(
                fig_bar,
                use_container_width=True,
                selection_mode="points",
                on_select="rerun",
                key="viz_bar_chart",
            )

            # Clique exclusivo (produto)
            if (
                bar_event
                and bar_event.selection
                and bar_event.selection.get("points")
                and len(bar_event.selection["points"]) > 0
            ):
                point = bar_event.selection["points"][0]
                clicked_product = point.get("x")
                if clicked_product:
                    st.session_state.viz_selected_product = clicked_product
                    st.session_state.viz_selected_period = None

    # -------------------------
    # 2) Linha — Vendas ao Longo do Tempo (clicável)
    # -------------------------
    with g2:
        st.markdown("**Gráfico de Linhas — Vendas ao Longo do Tempo**")

        if df_for_line.empty:
            st.info("Sem dados para os filtros selecionados.")
        else:
            df_time = df_for_line.copy()

            if granularity == "Mês":
                df_time["Period"] = df_time["OrderDate"].dt.to_period("M").astype(str)
                period_label = "Mês"
                sales_over_time = (
                    df_time.groupby("Period", as_index=False)["SalesValue"]
                    .sum()
                    .sort_values("Period")
                )
            else:
                df_time["Period"] = df_time["OrderDate"].dt.year.astype(int).astype(str)
                period_label = "Ano"
                sales_over_time = (
                    df_time.groupby("Period", as_index=False)["SalesValue"]
                    .sum()
                    .sort_values("Period")
                )

            fig_line = px.line(
                sales_over_time,
                x="Period",
                y="SalesValue",
                markers=True,
                labels={"Period": period_label, "SalesValue": "Vendas"},
            )
            fig_line = _freeze_axis_margins(fig_line)

            line_event = st.plotly_chart(
                fig_line,
                use_container_width=True,
                selection_mode="points",
                on_select="rerun",
                key="viz_line_chart",
            )

            # Clique exclusivo (período)
            if (
                line_event
                and line_event.selection
                and line_event.selection.get("points")
                and len(line_event.selection["points"]) > 0
            ):
                point = line_event.selection["points"][0]
                clicked_period = point.get("x")
                if clicked_period:
                    st.session_state.viz_selected_period = clicked_period
                    st.session_state.viz_selected_product = None
