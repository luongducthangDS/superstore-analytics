"""Data quality and integrity tests for Superstore analytics model."""
from pathlib import Path
import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    c.execute("SET enable_progress_bar = false")
    c.execute(f"SET file_search_path = '{ROOT}'")
    c.execute((ROOT / "sql" / "00_model.sql").read_text())
    c.execute((ROOT / "sql" / "10_powerbi_export.sql").read_text())
    return c


def one(con, sql):
    return con.execute(sql).fetchone()[0]


def test_one_row_per_item(con):
    assert one(con, "SELECT count(*) FROM fct_sales") == 9_994
    assert one(con, "SELECT count(*) - count(DISTINCT row_id) FROM fct_sales") == 0


def test_no_nulls_in_core_metrics(con):
    assert one(con, "SELECT count(*) FROM fct_sales WHERE sales IS NULL OR profit IS NULL OR discount IS NULL") == 0


def test_cogs_reconciliation(con):
    gap = one(con, "SELECT sum(abs(sales - profit - cogs)) FROM fct_sales")
    assert gap < 0.01


def test_is_loss_matches_negative_profit(con):
    assert one(con, "SELECT count(*) FROM fct_sales WHERE is_loss <> (profit < 0)") == 0


def test_toxic_discount_flag_definition(con):
    assert one(con, "SELECT count(*) FROM fct_sales WHERE is_toxic_discount <> (discount > 0.20)") == 0


def test_powerbi_dimensions_unique_keys(con):
    dims = [
        ("pbi_dim_product", "product_id"),
        ("pbi_dim_customer", "customer_id"),
        ("pbi_dim_location", "location_id"),
        ("pbi_dim_date", "date"),
    ]
    for table, pk in dims:
        dups = one(con, f"SELECT count(*) - count(DISTINCT {pk}) FROM {table}")
        assert dups == 0, f"Duplicate keys in {table} on {pk}"


def test_referential_integrity(con):
    # Every fact record finds product, customer, location and date
    assert one(con, """
        SELECT count(*) FROM pbi_fact_sales f
        LEFT JOIN pbi_dim_product p USING (product_id)
        WHERE p.product_id IS NULL
    """) == 0

    assert one(con, """
        SELECT count(*) FROM pbi_fact_sales f
        LEFT JOIN pbi_dim_customer c USING (customer_id)
        WHERE c.customer_id IS NULL
    """) == 0

    assert one(con, """
        SELECT count(*) FROM pbi_fact_sales f
        LEFT JOIN pbi_dim_location l USING (location_id)
        WHERE l.location_id IS NULL
    """) == 0

    assert one(con, """
        SELECT count(*) FROM pbi_fact_sales f
        LEFT JOIN pbi_dim_date d ON f.order_date = d.date
        WHERE d.date IS NULL
    """) == 0
