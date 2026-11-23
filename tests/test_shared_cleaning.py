import pytest
import pandas as pd
import numpy as np
import unicodedata
from shared.cleaning.engine import clean_data, clean_source_data
from shared.cleaning.models import CleaningReport
from shared.schema_models import TableResource, TableSchema, TableField, DataPackage
from shared.ingestion import SourceData

@pytest.fixture
def simple_resource():
    fields = [
        TableField(name="name", type="string"),
        TableField(name="city", type="string"),
        TableField(name="price", type="number")
    ]
    return TableResource(
        name="test_table",
        schema=TableSchema(fields=fields)
    )

class TestSharedCleaning:
    def test_string_normalization_native(self, simple_resource):
        # Native implementation strips punctuation and lowercases
        df = pd.DataFrame({"name": [" John DOE! ", "JANE-smith"], "city": ["NYC", "L.A."]})
        cleaned, report = clean_data(df)
        
        # "John DOE!" -> NFC -> lower -> strip accents -> strip punctuation -> "john doe"
        assert cleaned.iloc[0]["name"] == "john doe"
        # "JANE-smith" -> "janesmith" (punctuations like '-' are stripped by our regex)
        assert cleaned.iloc[1]["name"] == "janesmith"
        assert report.rows_before == 2

    def test_numeric_columns_preserved(self, simple_resource):
        df = pd.DataFrame({"price": [10.5, 20.0, None]})
        # Cast to object to simulate dirty loading
        df["price"] = df["price"].astype(object)
        cleaned, _ = clean_data(df)
        
        # Should be preserved or promoted to numeric if sampled
        assert pd.api.types.is_numeric_dtype(cleaned["price"])
        assert cleaned.iloc[0]["price"] == 10.5
        assert pd.isna(cleaned.iloc[2]["price"])

    def test_accent_stripping_native(self, simple_resource):
        # Verify native unicodedata stripping
        df = pd.DataFrame({"name": ["José", "Niño"]})
        cleaned, report = clean_data(df)
        assert cleaned.iloc[0]["name"] == "jose"
        assert cleaned.iloc[1]["name"] == "nino"
        assert any(e.operation == "text_normalization" for e in report.examples)

    def test_unicode_normalization_native(self, simple_resource):
        # 'e' + combining acute accent (decomposed NFD)
        decomposed = "e" + "\u0301" 
        df = pd.DataFrame({"name": [decomposed]})
        cleaned, _ = clean_data(df)
        # Should be normalized then accent-stripped to 'e'
        assert cleaned.iloc[0]["name"] == "e"

    def test_whitespace_only_to_nan(self, simple_resource):
        df = pd.DataFrame({"name": ["Alice", "  "], "city": ["NYC", "   "]})
        cleaned, report = clean_data(df)
        assert pd.isna(cleaned.iloc[1]["name"])
        assert pd.isna(cleaned.iloc[1]["city"])
        assert report.whitespace_cells_nullified == 2
        assert any(e.operation == "whitespace_to_nan" for e in report.examples)

    def test_duplicate_rows_removed(self, simple_resource):
        df = pd.DataFrame({"name": ["Alice", "Alice", "Bob"], "city": ["A", "A", "B"]})
        cleaned, report = clean_data(df)
        assert len(cleaned) == 2
        assert report.duplicates_removed == 1
        # Data is also lowercased during cleaning
        assert list(cleaned["name"]) == ["alice", "bob"]

    def test_clean_source_data_helper(self):
        df = pd.DataFrame({"name": [" ALICE "]})
        resource = TableResource(
            name="t1",
            schema=TableSchema(fields=[TableField(name="name", type="string")])
        )
        package = DataPackage(schema_name="src1", resources=[resource])
        source = SourceData(package=package, tables={"t1": df}, base_path=None)
        
        cleaned_source, reports = clean_source_data(source)
        
        assert "t1" in cleaned_source.tables
        assert cleaned_source.tables["t1"].iloc[0]["name"] == "alice"
        assert reports["t1"].rows_before == 1

    def test_type_promotion_inference(self, simple_resource):
        # Test that object columns that look like numbers get promoted
        df = pd.DataFrame({"name": ["100", "200", "300"]}) # mapped as string in simple_resource
        cleaned, report = clean_data(df)
        # In engine.py, we call _infer_column_type which sees >80% numbers
        assert pd.api.types.is_numeric_dtype(cleaned["name"])
        assert cleaned.iloc[0]["name"] == 100
