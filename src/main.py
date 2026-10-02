"""Run the ETL from the original raw CSV to a star schema."""

from __future__ import annotations

import argparse
from pathlib import Path

from data_cleaning import clean_transactions, load_raw_data, project_root
from rfm_segmentation import calculate_rfm
from star_schema import build_star_schema, export_star_schema


def run_pipeline(raw_path: Path | None = None, out_dir: Path | None = None,
                 churn_days: int = 180):
    root = project_root()
    raw_path = raw_path if raw_path is not None else root / "data/raw/data.csv"
    out_dir = out_dir if out_dir is not None else root / "data/processed"
    # Extract, transform, validate, then export the five star-schema tables.
    raw = load_raw_data(raw_path)
    transactions = clean_transactions(raw)
    rfm = calculate_rfm(transactions, churn_days=churn_days)
    tables = build_star_schema(transactions, rfm)
    workbook_path = export_star_schema(tables, out_dir)

    fact = tables["fact_transactions"]
    print(f"Raw rows: {len(raw):,}; fact rows: {len(fact):,}")
    print(f"Dates: {tables['dim_date']['date'].min()} to {tables['dim_date']['date'].max()}")
    print(f"Customers: {len(rfm):,}; products: {len(tables['dim_product']):,}; "
          f"countries: {len(tables['dim_country']):,}")
    print(f"Gross sales: {fact['gross_sales'].sum():,.2f}; "
          f"returns: {fact['return_amount'].sum():,.2f}; "
          f"net sales: {fact['net_sales'].sum():,.2f}")
    print(f"Excel workbook: {workbook_path}")
    print(f"Five import-ready CSVs: {out_dir}")
    return tables


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the e-commerce star schema")
    parser.add_argument("--raw", type=Path, help="Raw CSV (default: data/raw/data.csv)")
    parser.add_argument("--out", type=Path, help="Output folder (default: data/processed)")
    parser.add_argument("--churn-days", type=int, default=180,
                        help="Inactivity threshold for customer status (default: 180)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.raw, args.out, args.churn_days)
