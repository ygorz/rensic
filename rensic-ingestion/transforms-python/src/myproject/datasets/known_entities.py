"""
Snapshot the in-repo public known-entity pack.

Spark reads the CSV from the conda package so the build does not download
the OFAC SDN XML (~100MB). See myproject/data/SOURCES.md.
"""
from pathlib import Path

import polars as pl
from transforms.api import Output, transform


def _pack_csv() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "data" / "known_entities.csv",
        here.parent / "data" / "known_entities.csv",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "known_entities.csv missing from package; expected myproject/data/known_entities.csv"
    )


@transform.using(
    known_entities=Output(
        "/George Gorzhiyev-a8216a/Rensic/data-integration/clean/known_entities"
    ),
)
def snapshot_known_entities(known_entities):
    df = pl.read_csv(_pack_csv())
    if "address" not in df.columns or "chain" not in df.columns:
        raise ValueError("known_entities.csv must include chain and address columns")
    df = df.with_columns(
        pl.col("chain").cast(pl.Utf8).str.strip_chars().str.to_lowercase(),
        pl.col("address").cast(pl.Utf8).str.strip_chars().str.to_lowercase(),
        pl.col("name").cast(pl.Utf8).str.strip_chars(),
        pl.col("category").cast(pl.Utf8).str.strip_chars().str.to_lowercase(),
        pl.col("source").cast(pl.Utf8),
        pl.col("source_url").cast(pl.Utf8),
    )
    if "secondary_category" in df.columns:
        df = df.with_columns(
            pl.col("secondary_category").cast(pl.Utf8).fill_null("").str.strip_chars()
        )
    if "tier" in df.columns:
        df = df.with_columns(
            pl.col("tier")
            .cast(pl.Utf8)
            .fill_null("official")
            .str.strip_chars()
            .str.to_lowercase()
        )
    else:
        df = df.with_columns(pl.lit("official").alias("tier"))
    df = df.filter(pl.col("address") != "")
    known_entities.write_table(df)
