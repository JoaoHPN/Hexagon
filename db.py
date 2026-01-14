import pyodbc
import pandas as pd

def get_conn():
    # MARS_Connection=yes resolve: "Conexão ocupada com os resultados de outro comando"
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=AdventureWorks2025;"
        "Trusted_Connection=yes;"
        "MARS_Connection=yes;"
    )

def _in_clause(values):
    return ", ".join(["?"] * len(values))

def get_metadata(conn):
    df_dates = pd.read_sql(
        """
        SELECT
            MIN(CAST(soh.OrderDate AS DATE)) AS MinDate,
            MAX(CAST(soh.OrderDate AS DATE)) AS MaxDate
        FROM Sales.SalesOrderHeader soh;
        """,
        conn,
    )
    min_date = df_dates.loc[0, "MinDate"]
    max_date = df_dates.loc[0, "MaxDate"]

    state_df = pd.read_sql(
        """
        SELECT DISTINCT
            sp.StateProvinceCode AS StateCode,
            sp.Name AS StateName
        FROM Sales.SalesOrderHeader soh
        JOIN Person.Address a ON soh.ShipToAddressID = a.AddressID
        JOIN Person.StateProvince sp ON a.StateProvinceID = sp.StateProvinceID
        WHERE sp.CountryRegionCode = 'US'
        ORDER BY sp.Name;
        """,
        conn,
    )

    prod_df = pd.read_sql(
        """
        SELECT DISTINCT p.Name AS Product
        FROM Sales.SalesOrderDetail sod
        JOIN Production.Product p ON sod.ProductID = p.ProductID
        ORDER BY p.Name;
        """,
        conn,
    )
    products = prod_df["Product"].tolist()

    return min_date, max_date, state_df, products

def load_sales_by_state(conn, start_date, end_date, products_sel):
    if not products_sel:
        return pd.DataFrame(columns=["StateCode", "SalesValue"])

    sql = f"""
    SELECT
        sp.StateProvinceCode AS StateCode,
        SUM(sod.LineTotal) AS SalesValue
    FROM Sales.SalesOrderHeader soh
    JOIN Sales.SalesOrderDetail sod ON soh.SalesOrderID = sod.SalesOrderID
    JOIN Production.Product p ON sod.ProductID = p.ProductID
    JOIN Person.Address a ON soh.ShipToAddressID = a.AddressID
    JOIN Person.StateProvince sp ON a.StateProvinceID = sp.StateProvinceID
    WHERE
        sp.CountryRegionCode = 'US'
        AND CAST(soh.OrderDate AS DATE) BETWEEN ? AND ?
        AND p.Name IN ({_in_clause(products_sel)})
    GROUP BY sp.StateProvinceCode;
    """
    params = [start_date, end_date, *products_sel]
    return pd.read_sql(sql, conn, params=params)

def load_sales_filtered(conn, start_date, end_date, states_sel, products_sel):
    if not products_sel:
        return pd.DataFrame(columns=["OrderDate", "StateCode", "State", "Product", "SalesValue"])

    state_filter_sql = ""
    params = [start_date, end_date, *products_sel]

    if states_sel:
        state_filter_sql = f" AND sp.StateProvinceCode IN ({_in_clause(states_sel)})"
        params = [start_date, end_date, *products_sel, *states_sel]

    sql = f"""
    SELECT
        CAST(soh.OrderDate AS DATE) AS OrderDate,
        sp.StateProvinceCode AS StateCode,
        sp.Name AS State,
        p.Name AS Product,
        SUM(sod.LineTotal) AS SalesValue
    FROM Sales.SalesOrderHeader soh
    JOIN Sales.SalesOrderDetail sod ON soh.SalesOrderID = sod.SalesOrderID
    JOIN Production.Product p ON sod.ProductID = p.ProductID
    JOIN Person.Address a ON soh.ShipToAddressID = a.AddressID
    JOIN Person.StateProvince sp ON a.StateProvinceID = sp.StateProvinceID
    WHERE
        sp.CountryRegionCode = 'US'
        AND CAST(soh.OrderDate AS DATE) BETWEEN ? AND ?
        AND p.Name IN ({_in_clause(products_sel)})
        {state_filter_sql}
    GROUP BY
        CAST(soh.OrderDate AS DATE),
        sp.StateProvinceCode,
        sp.Name,
        p.Name;
    """
    df = pd.read_sql(sql, conn, params=params)
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    return df
