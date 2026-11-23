class DataIngestionError(Exception):
    """Base class for ingestion errors."""
    pass

class DataPackageNotFound(DataIngestionError):
    """Raised when datapackage.json is missing."""
    pass

class ResourceFileNotFound(DataIngestionError):
    """Raised when a parquet file is missing."""
    pass

class SchemaMismatchError(DataIngestionError):
    """Raised when dataframe columns don't match the schema."""
    pass
