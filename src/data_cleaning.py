"""Load and clean the original Online Retail transactions."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = (
    "InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate",
    "UnitPrice", "CustomerID", "Country",
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_raw_data(raw_path: Path) -> pd.DataFrame:
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    df = pd.read_csv(raw_path, encoding="ISO-8859-1", low_memory=False)
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    return df


def clean_transactions(raw: pd.DataFrame) -> pd.DataFrame:
    """Keep identifiable sales and returns, preserving their original dates."""
    df = raw.copy()
    # Parse the source timestamp directly; no date offset is applied.
    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"], format="%m/%d/%Y %H:%M", errors="coerce"
    )
    for column in ("Quantity", "UnitPrice", "CustomerID"):
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=[
        "InvoiceNo", "StockCode", "Quantity", "InvoiceDate", "UnitPrice",
        "CustomerID", "Country",
    ]).copy()
    # Keep negative quantities so refunds can reduce net sales.
    df = df[df["Quantity"].ne(0) & df["UnitPrice"].gt(0)]
    df = df[df["CustomerID"].mod(1).eq(0)].copy()
    df["CustomerID"] = df["CustomerID"].astype("int64")
    for column in ("InvoiceNo", "StockCode", "Country"):
        df[column] = df[column].astype(str).str.strip()
    df = df[df[["InvoiceNo", "StockCode", "Country"]].ne("").all(axis=1)]
    df["Description"] = df["Description"].fillna("Unknown product").astype(str).str.strip()
    df.loc[df["Description"].eq(""), "Description"] = "Unknown product"

    # Store gross sales and returns separately for unambiguous KPIs.
    amount = df["Quantity"] * df["UnitPrice"]
    df["GrossSales"] = amount.clip(lower=0)
    df["ReturnAmount"] = (-amount).clip(lower=0)
    df["NetSales"] = amount
    df["TransactionType"] = df["Quantity"].lt(0).map({True: "Return", False: "Sale"})
    return df.reset_index(drop=True)
