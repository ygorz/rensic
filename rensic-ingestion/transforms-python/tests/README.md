# Running ingestion unit tests

These tests cover pure helpers and CSV integrity. They do not run Foundry Spark.

From transforms-python:

    pip install pytest
    PYTHONPATH=src pytest tests -q
