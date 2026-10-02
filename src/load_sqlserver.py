"""Load the exported star schema into a local SQL Server Docker container."""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import tempfile
import uuid
from decimal import Decimal
from pathlib import Path

from data_cleaning import project_root
from star_schema import TABLES


EXPECTED_COLUMNS = {
    "dim_date": ("date_key", "date", "year", "quarter", "month", "day"),
    "dim_customer": ("customer_key", "customer_id", "recency_days", "frequency",
                     "monetary_net", "r_score", "f_score", "m_score", "value_tier",
                     "status", "snapshot_date"),
    "dim_product": ("product_key", "stock_code", "description"),
    "dim_country": ("country_key", "country"),
    "fact_transactions": ("transaction_line_key", "invoice_no", "invoice_datetime",
                          "date_key", "customer_key", "product_key", "country_key",
                          "transaction_type", "quantity", "unit_price", "gross_sales",
                          "return_amount", "net_sales"),
}
DECIMAL_COLUMNS = {
    "dim_customer": ("monetary_net",),
    "fact_transactions": ("unit_price", "gross_sales", "return_amount", "net_sales"),
}
SQL_DECIMAL_UNIT = Decimal("0.000001")


def inspect_exports(out_dir: Path) -> tuple[dict[str, int], Decimal]:
    """Check CSV shape and collect values used to verify the database load."""
    counts: dict[str, int] = {}
    net_sales = Decimal("0")
    for table in TABLES:
        path = out_dir / f"{table}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Missing ETL output: {path}")
        with path.open(newline="", encoding="utf-8") as source:
            reader = csv.reader(source)
            header = tuple(next(reader, ()))
            if header != EXPECTED_COLUMNS[table]:
                raise ValueError(f"Unexpected column order in {path}: {header}")
            count = 0
            for row in reader:
                if len(row) != len(header):
                    raise ValueError(f"Wrong number of columns in {path}, row {count + 2}")
                count += 1
                if table == "fact_transactions":
                    net_sales += Decimal(row[-1]).quantize(SQL_DECIMAL_UNIT)
            if count == 0:
                raise ValueError(f"ETL output is empty: {path}")
            counts[table] = count
    return counts, net_sales


def prepare_csv_for_sql(table: str, source: Path, destination: Path) -> None:
    """Write fixed-point decimals so BULK INSERT can parse tiny float residues."""
    columns = DECIMAL_COLUMNS.get(table, ())
    with source.open(newline="", encoding="utf-8") as incoming, \
            destination.open("w", newline="", encoding="utf-8") as outgoing:
        reader = csv.DictReader(incoming)
        writer = csv.DictWriter(outgoing, fieldnames=reader.fieldnames,
                                lineterminator="\n")
        writer.writeheader()
        for row in reader:
            for column in columns:
                row[column] = format(Decimal(row[column]).quantize(SQL_DECIMAL_UNIT), "f")
            writer.writerow(row)


def build_load_sql(counts: dict[str, int], net_sales: Decimal,
                   import_dir: str, replace: bool) -> str:
    # A single transaction makes a failed bulk load leave the previous tables intact.
    lines = [
        "USE [ecommerce];",
        "SET NOCOUNT ON;",
        "SET XACT_ABORT ON;",
        "BEGIN TRY",
        "    BEGIN TRANSACTION;",
    ]
    if replace:
        for table in ("fact_transactions", "dim_customer", "dim_product",
                      "dim_country", "dim_date"):
            lines.append(f"    DELETE FROM [ecommerce].[{table}];")
    else:
        condition = " OR ".join(
            f"EXISTS (SELECT 1 FROM [ecommerce].[{table}])" for table in TABLES
        )
        lines.extend([
            f"    IF {condition}",
            "    BEGIN",
            "        THROW 51000, 'Target tables are not empty; use --replace for a full refresh.', 1;",
            "    END;",
        ])

    # Load dimensions first so the fact's foreign keys can be checked immediately.
    for table in TABLES:
        lines.extend([
            f"    BULK INSERT [ecommerce].[{table}]",
            f"    FROM '{import_dir}/{table}.csv'",
            "    WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '\"',",
            "          ROWTERMINATOR = '0x0a',",
            "          KEEPNULLS, CHECK_CONSTRAINTS, MAXERRORS = 0);",
            f"    IF (SELECT COUNT_BIG(*) FROM [ecommerce].[{table}]) <> {counts[table]}",
            "    BEGIN",
            f"        THROW 51001, 'Row count mismatch in {table}.', 1;",
            "    END;",
        ])
    lines.extend([
        "    IF ABS((SELECT SUM([net_sales]) FROM [ecommerce].[fact_transactions])",
        f"           - CAST({net_sales} AS DECIMAL(38, 6))) > CAST(0.01 AS DECIMAL(38, 6))",
        "    BEGIN",
        "        THROW 51002, 'Net sales mismatch after import.', 1;",
        "    END;",
        "    COMMIT TRANSACTION;",
        "END TRY",
        "BEGIN CATCH",
        "    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;",
        "    THROW;",
        "END CATCH;",
        "SELECT COUNT_BIG(*) AS fact_rows, ROUND(SUM(net_sales), 2) AS net_sales",
        "FROM [ecommerce].[fact_transactions];",
    ])
    return "\n".join(lines) + "\n"


def _run(*args: str) -> None:
    subprocess.run(args, check=True)


def _sqlcmd(container: str, sql_path: str) -> None:
    # The password is expanded only inside Docker; it is never passed from Python.
    command = (
        'exec /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa '
        '-P "$MSSQL_SA_PASSWORD" -C -b -l 30 -i ' + sql_path
    )
    _run("docker", "exec", container, "bash", "-lc", command)


def load_sqlserver(out_dir: Path, container: str = "sql-server",
                   replace: bool = False) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", container):
        raise ValueError("Invalid Docker container name")
    counts, net_sales = inspect_exports(out_dir)
    import_dir = f"/tmp/ecommerce_import_{uuid.uuid4().hex}"
    print(f"Validated CSVs: {counts}; net sales: {net_sales:,.2f}", flush=True)
    _run("docker", "exec", container, "mkdir", "-p", import_dir)
    try:
        schema_path = project_root() / "sql/star_schema.sql"
        _run("docker", "cp", str(schema_path), f"{container}:{import_dir}/schema.sql")
        with tempfile.TemporaryDirectory(prefix="ecommerce_sql_") as staging:
            for table in TABLES:
                prepared = Path(staging) / f"{table}.csv"
                prepare_csv_for_sql(table, out_dir / f"{table}.csv", prepared)
                _run("docker", "cp", str(prepared),
                     f"{container}:{import_dir}/{table}.csv")
        sql_path = out_dir / "sqlserver_load.tmp.sql"
        try:
            sql_path.write_text(build_load_sql(counts, net_sales, import_dir, replace))
            _run("docker", "cp", str(sql_path), f"{container}:{import_dir}/load.sql")
        finally:
            sql_path.unlink(missing_ok=True)
        _sqlcmd(container, f"{import_dir}/schema.sql")
        _sqlcmd(container, f"{import_dir}/load.sql")
        print("SQL Server load complete: [ecommerce].[fact_transactions] and four dimensions")
    finally:
        _run("docker", "exec", container, "rm", "-rf", import_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load exported CSVs into SQL Server Docker")
    parser.add_argument("--out", type=Path,
                        help="ETL output folder (default: data/processed)")
    parser.add_argument("--container", default="sql-server",
                        help="Docker container name (default: sql-server)")
    parser.add_argument("--replace", action="store_true",
                        help="Replace existing ecommerce table data in one transaction")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    load_sqlserver(args.out or project_root() / "data/processed",
                   args.container, args.replace)
