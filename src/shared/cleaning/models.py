from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

class CleaningExample(BaseModel):
    """Represents a sample of a cleaning operation for transparency."""
    column: str
    operation: str
    before: Optional[str] = None
    after: Optional[str] = None

class CleaningReport(BaseModel):
    """Aggregated statistics and examples for a table-level cleaning run."""
    rows_before: int
    rows_after: int
    duplicates_removed: int
    whitespace_cells_nullified: int
    total_transformations: int = 0
    processing_time_ms: float = 0.0
    examples: List[CleaningExample] = Field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return (self.duplicates_removed > 0 or 
                self.whitespace_cells_nullified > 0 or 
                len(self.examples) > 0)
