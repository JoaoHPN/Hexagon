# data_layer.py
import pandas as pd
import streamlit as st

from db import get_conn, get_metadata, load_sales_by_state, load_sales_filtered

# =========================
# Conexão (1 por sessão)
# =========================
@st.cache_resource
def get_conn_cached():
    return get_conn()

# =========================
# Metadata (1h)
# =========================
@st.cache_data(ttl=3600)
def get_metadata_cached():
    cn = get_conn_cached()
    return get_metadata(cn)

def get_state_df_all():
    _, _, state_df_all, _ = get_metadata_cached()
    state_df_all = state_df_all.copy()
    state_df_all["StateCode"] = state_df_all["StateCode"].astype(str).str.strip().str.upper()
    return state_df_all

def get_products_all():
    _, _, _, products_all = get_metadata_cached()
    return list(products_all)

# =========================
# Helpers
# =========================
def _in_clause(values):
    return ", ".join(["?"] * len(values))

# =========================
# Dataframe do mapa (com TODOS os estados)
# =========================
@st.cache_data(ttl=600)
def get_map_df(start_date, end_date, products_sel):
    cn = get_conn_cached()
    state_df_all = get_state_df_all()

    sales_df = load_sales_by_state(cn, start_date, end_date, products_sel).copy()
    if not sales_df.empty:
        sales_df["StateCode"] = sales_df["StateCode"].astype(str).str.strip().str.upper()

    base = state_df_all[["StateCode"]].drop_duplicates().copy()
    base = base.merge(sales_df, on="StateCode", how="left")

    if "SalesValue" not in base.columns:
        base["SalesValue"] = 0
    base["SalesValue"] = base["SalesValue"].fillna(0)

    return base

# =========================
# Dados filtrados (tabelas/gráficos existentes)
# =========================
@st.cache_data(ttl=600)
def get_sales_df(start_date, end_date, states_sel, products_sel):
    cn = get_conn_cached()
    return load_sales_filtered(cn, start_date, end_date, states_sel, products_sel)

# =========================
# NOVO: Top 10 Vendedores e Lojas (valor de vendas), respeitando filtros
# =========================
@st.cache_data(ttl=600)
def get_top_sellers_and_stores(start_date, end_date, states_sel, products_sel, top_n=10):
    """
    Retorna dois dataframes:
      - top_sellers_df: colunas [SalesPerson, SalesValue]
      - top_stores_df:  colunas [Store, SalesValue]
    Respeita filtros de data, produtos e estados.
    """
    cn = get_conn_cached()

    if not products_sel:
        empty_sellers = pd.DataFrame(columns=["SalesPerson", "SalesValue"])
        empty_stores = pd.DataFrame(columns=["Store", "SalesValue"])
        return empty_sellers, empty_stores

    # Filtros dinâmicos
    product_filter = f"AND p.Name IN ({_in_clause(products_sel)})"
    params_base = [start_date, end_date, *products_sel]

    state_filter = ""
    params_states = []
    if states_sel:
        state_filter = f"AND spv.StateProvinceCode IN ({_in_clause(states_sel)})"
        params_states = [*states_sel]

    # -------------------------
    # TOP SELLERS
    # -------------------------
    sql_sellers = f"""
    SELECT
        COALESCE(pp.FirstName + ' ' + pp.LastName, '(Sem vendedor)') AS SalesPerson,
        SUM(sod.LineTotal) AS SalesValue
    FROM Sales.SalesOrderHeader soh
    JOIN Sales.SalesOrderDetail sod ON soh.SalesOrderID = sod.SalesOrderID
    JOIN Production.Product p ON sod.ProductID = p.ProductID
    JOIN Person.Address a ON soh.ShipToAddressID = a.AddressID
    JOIN Person.StateProvince spv ON a.StateProvinceID = spv.StateProvinceID
    LEFT JOIN Sales.SalesPerson sp ON soh.SalesPersonID = sp.BusinessEntityID
    LEFT JOIN Person.Person pp ON sp.BusinessEntityID = pp.BusinessEntityID
    WHERE
        spv.CountryRegionCode = 'US'
        AND CAST(soh.OrderDate AS DATE) BETWEEN ? AND ?
        {product_filter}
        {state_filter}
    GROUP BY
        COALESCE(pp.FirstName + ' ' + pp.LastName, '(Sem vendedor)')
    ORDER BY
        SalesValue DESC;
    """

    params_sellers = params_base + params_states
    top_sellers_df = pd.read_sql(sql_sellers, cn, params=params_sellers)
    top_sellers_df["SalesValue"] = pd.to_numeric(top_sellers_df["SalesValue"], errors="coerce").fillna(0)
    top_sellers_df = top_sellers_df.head(int(top_n))

    # -------------------------
    # TOP STORES
    # -------------------------
    sql_stores = f"""
    SELECT
        COALESCE(s.Name, '(Sem loja)') AS Store,
        SUM(sod.LineTotal) AS SalesValue
    FROM Sales.SalesOrderHeader soh
    JOIN Sales.SalesOrderDetail sod ON soh.SalesOrderID = sod.SalesOrderID
    JOIN Production.Product p ON sod.ProductID = p.ProductID
    JOIN Person.Address a ON soh.ShipToAddressID = a.AddressID
    JOIN Person.StateProvince spv ON a.StateProvinceID = spv.StateProvinceID
    LEFT JOIN Sales.Customer c ON soh.CustomerID = c.CustomerID
    LEFT JOIN Sales.Store s ON c.StoreID = s.BusinessEntityID
    WHERE
        spv.CountryRegionCode = 'US'
        AND CAST(soh.OrderDate AS DATE) BETWEEN ? AND ?
        {product_filter}
        {state_filter}
    GROUP BY
        COALESCE(s.Name, '(Sem loja)')
    ORDER BY
        SalesValue DESC;
    """

    params_stores = params_base + params_states
    top_stores_df = pd.read_sql(sql_stores, cn, params=params_stores)
    top_stores_df["SalesValue"] = pd.to_numeric(top_stores_df["SalesValue"], errors="coerce").fillna(0)
    top_stores_df = top_stores_df.head(int(top_n))

    return top_sellers_df, top_stores_df
