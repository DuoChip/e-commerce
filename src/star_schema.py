"""Build and validate a transaction-line star schema."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook


TABLES = ("dim_date", "dim_customer", "dim_product", "dim_country", "fact_transactions")


def build_star_schema(transactions: pd.DataFrame, rfm: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # One date row per calendar day; the full timestamp stays in the fact.
    dates = pd.Series(transactions["InvoiceDate"].dt.normalize().unique()).sort_values()
    dim_date = pd.DataFrame({"date": dates.dt.strftime("%Y-%m-%d")})
    dim_date.insert(0, "date_key", dates.dt.strftime("%Y%m%d").astype("int64").to_numpy())
    dim_date["year"] = dates.dt.year.to_numpy()
    dim_date["quarter"] = dates.dt.quarter.to_numpy()
    dim_date["month"] = dates.dt.month.to_numpy()
    dim_date["day"] = dates.dt.day.to_numpy()

    dim_customer = rfm.rename(columns={
        "CustomerID": "customer_id", "Recency": "recency_days",
        "Frequency": "frequency", "Monetary": "monetary_net",
        "R_Score": "r_score", "F_Score": "f_score", "M_Score": "m_score",
        "Is_Top_20": "value_tier", "Status": "status", "SnapshotDate": "snapshot_date",
    }).sort_values("customer_id").reset_index(drop=True)
    dim_customer.insert(0, "customer_key", np.arange(1, len(dim_customer) + 1))
    # Keep CSV column order aligned with SQL Server BULK INSERT table order.
    dim_customer = dim_customer[[
        "customer_key", "customer_id", "recency_days", "frequency", "monetary_net",
        "r_score", "f_score", "m_score", "value_tier", "status", "snapshot_date",
    ]]

    # Pick the most common description when a stock code has several names.
    descriptions = (transactions.groupby(["StockCode", "Description"]).size()
                    .reset_index(name="count")
                    .sort_values(["StockCode", "count", "Description"],
                                 ascending=[True, False, True])
                    .drop_duplicates("StockCode"))
    dim_product = descriptions[["StockCode", "Description"]].rename(columns={
        "StockCode": "stock_code", "Description": "description",
    }).reset_index(drop=True)
    dim_product.insert(0, "product_key", np.arange(1, len(dim_product) + 1))

    dim_country = pd.DataFrame({"country": sorted(transactions["Country"].unique())})
    dim_country.insert(0, "country_key", np.arange(1, len(dim_country) + 1))

    # Fact grain: one source invoice line, including return lines.
    fact = pd.DataFrame({
        "transaction_line_key": np.arange(1, len(transactions) + 1),
        "invoice_no": transactions["InvoiceNo"],
        "invoice_datetime": transactions["InvoiceDate"].dt.strftime("%Y-%m-%d %H:%M:%S"),
        "date_key": transactions["InvoiceDate"].dt.strftime("%Y%m%d").astype("int64"),
        "customer_key": transactions["CustomerID"].map(
            dim_customer.set_index("customer_id")["customer_key"]),
        "product_key": transactions["StockCode"].map(
            dim_product.set_index("stock_code")["product_key"]),
        "country_key": transactions["Country"].map(
            dim_country.set_index("country")["country_key"]),
        "transaction_type": transactions["TransactionType"],
        "quantity": transactions["Quantity"],
        "unit_price": transactions["UnitPrice"],
        "gross_sales": transactions["GrossSales"],
        "return_amount": transactions["ReturnAmount"],
        "net_sales": transactions["NetSales"],
    })
    # Every fact key must resolve before files can be exported.
    keys = ["date_key", "customer_key", "product_key", "country_key"]
    if fact[keys].isna().any().any():
        raise ValueError("Fact contains an unmatched dimension key")
    fact[keys] = fact[keys].astype("int64")

    tables = dict(dim_date=dim_date, dim_customer=dim_customer,
                  dim_product=dim_product, dim_country=dim_country,
                  fact_transactions=fact)
    validate_star_schema(tables, transactions)
    return tables


def validate_star_schema(tables: dict[str, pd.DataFrame], transactions: pd.DataFrame) -> None:
    fact = tables["fact_transactions"]
    if len(fact) != len(transactions):
        raise ValueError("Fact row count differs from cleaned transaction count")
    for dimension, key in (("dim_date", "date_key"), ("dim_customer", "customer_key"),
                           ("dim_product", "product_key"), ("dim_country", "country_key")):
        values = tables[dimension][key]
        if not values.is_unique or not fact[key].isin(values).all():
            raise ValueError(f"Invalid foreign key: {key}")
    for fact_col, source_col in (("gross_sales", "GrossSales"),
                                 ("return_amount", "ReturnAmount"),
                                 ("net_sales", "NetSales")):
        if not np.isclose(fact[fact_col].sum(), transactions[source_col].sum(),
                          rtol=0, atol=0.01):
            raise ValueError(f"Measure mismatch: {fact_col}")
    if not np.isclose(fact["gross_sales"].sum() - fact["return_amount"].sum(),
                      fact["net_sales"].sum(), rtol=0, atol=0.01):
        raise ValueError("Gross sales minus returns does not equal net sales")


def export_star_schema(tables: dict[str, pd.DataFrame], out_dir: Path) -> Path:
    """Export one Excel workbook and separate CSVs for later SQL Server import."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in TABLES:
        tables[name].to_csv(out_dir / f"{name}.csv", index=False)

    workbook_path = out_dir / "ecommerce_star.xlsx"
    temp_path = out_dir / "ecommerce_star.tmp.xlsx"
    temp_path.unlink(missing_ok=True)
    try:
        # Streaming mode keeps the 400k-row fact sheet from filling RAM.
        workbook = Workbook(write_only=True)
        for name in TABLES:
            frame = tables[name]
            if len(frame) + 1 > 1_048_576:
                raise ValueError(f"{name} exceeds the Excel worksheet row limit")
            sheet = workbook.create_sheet(name)
            sheet.append(list(frame.columns))
            for row in frame.itertuples(index=False, name=None):
                sheet.append([None if pd.isna(value) else
                              value.item() if isinstance(value, np.generic) else value
                              for value in row])
        workbook.save(temp_path)
        temp_path.replace(workbook_path)
    finally:
        temp_path.unlink(missing_ok=True)
    return workbook_path
