"""Customer metrics at one explicit snapshot date."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Score 1–5 while giving equal values the same score."""
    # Average ranks prevent customers with the same frequency from splitting.
    percentile = series.rank(method="average", pct=True, ascending=True)
    score = np.ceil(percentile * 5).clip(1, 5).astype("int64")
    return score if higher_is_better else 6 - score


def calculate_rfm(transactions: pd.DataFrame, churn_days: int = 180) -> pd.DataFrame:
    if churn_days <= 0:
        raise ValueError("churn_days must be positive")
    if transactions.empty:
        raise ValueError("No valid transactions to segment")

    # RFM is a snapshot one day after the last observed transaction.
    snapshot_date = transactions["InvoiceDate"].max().normalize() + pd.Timedelta(days=1)
    purchases = transactions[transactions["TransactionType"].eq("Sale")]
    customers = pd.DataFrame({"CustomerID": sorted(transactions["CustomerID"].unique())})
    purchase_metrics = purchases.groupby("CustomerID").agg(
        LastPurchase=("InvoiceDate", "max"),
        Frequency=("InvoiceNo", "nunique"),
    )
    # Frequency uses purchases; Monetary includes refunds.
    net_spend = transactions.groupby("CustomerID")["NetSales"].sum().rename("Monetary")
    rfm = customers.join(purchase_metrics, on="CustomerID").join(net_spend, on="CustomerID")
    rfm["Recency"] = (snapshot_date - rfm["LastPurchase"]).dt.days.astype("Int64")
    rfm["Frequency"] = rfm["Frequency"].fillna(0).astype("int64")
    rfm["R_Score"] = 0
    has_purchase = rfm["Frequency"].gt(0)
    rfm.loc[has_purchase, "R_Score"] = _score(
        rfm.loc[has_purchase, "Recency"].astype("int64"), higher_is_better=False
    )
    rfm["F_Score"] = _score(rfm["Frequency"])
    rfm["M_Score"] = _score(rfm["Monetary"])
    threshold = rfm["Monetary"].quantile(0.8)
    rfm["Is_Top_20"] = np.where(rfm["Monetary"].ge(threshold), "High-Value", "Standard")
    rfm["Status"] = np.select(
        [~has_purchase, rfm["Recency"].gt(churn_days).fillna(False)],
        ["No Purchase", "Churned"],
        default="Active",
    )
    rfm["SnapshotDate"] = snapshot_date.date().isoformat()
    return rfm.drop(columns="LastPurchase")
