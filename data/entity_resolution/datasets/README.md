# Canonical Entity Resolution Dataset Specification

To enable clean, zero-guessing data loading, all datasets must follow a canonical directory structure and contain a `metadata.json` descriptor file.

## Canonical Layout

Each dataset resides in a self-contained directory containing:
1. `metadata.json`: The metadata file that defines the structure and locations of the tables, ground truth, and optional candidate pairs.
2. Table A CSV file (e.g., `table_a.csv`).
3. Table B CSV file (e.g., `table_b.csv`).
4. Ground truth CSV file (e.g., `ground_truth.csv`).
5. Optional candidates CSV file (e.g., `candidates.csv`).

Example layout:
```text
data/entity_resolution/datasets/DBLP-ACM/
├── metadata.json
├── table_a.csv
├── table_b.csv
└── ground_truth.csv
```

## `metadata.json` Schema

The `metadata.json` file must validate against the following fields:

- `name` (string, required): Unique name of the dataset.
- `domain` (string, required): Domain of the dataset (e.g., `e-commerce`, `citations`, `restaurants`, `movies`, `synthetic`).
- `ground_truth_type` (string, required): The evaluation type. Must be either `"exhaustive"` or `"sampled"`.
- `table_a` (object, required):
  - `file` (string, required): The filename of Table A (e.g., `"table_a.csv"`).
  - `id_column` (string, required): The primary ID column name inside Table A.
- `table_b` (object, required):
  - `file` (string, required): The filename of Table B (e.g., `"table_b.csv"`).
  - `id_column` (string, required): The primary ID column name inside Table B.
- `ground_truth` (object, required):
  - `file` (string, required): The filename of the ground truth (e.g., `"ground_truth.csv"`).
  - `column_a` (string, required): The column name in the ground truth file mapping to Table A's ID.
  - `column_b` (string, required): The column name in the ground truth file mapping to Table B's ID.
  - `label_column` (string or null, optional): The column name in the ground truth file containing the match label (usually `1` for match, `0` for non-match). If null, all records in the ground truth file are treated as matches.
- `candidates` (object or null, optional):
  - `file` (string, required): The filename of pre-computed/blocked candidate pairs (e.g., `"candidates.csv"`).
  - `column_a` (string, required): The column name mapping to Table A's ID.
  - `column_b` (string, required): The column name mapping to Table B's ID.

### Example `metadata.json`

```json
{
  "name": "DBLP-ACM",
  "domain": "citations",
  "ground_truth_type": "exhaustive",
  "table_a": {
    "file": "table_a.csv",
    "id_column": "id"
  },
  "table_b": {
    "file": "table_b.csv",
    "id_column": "id"
  },
  "ground_truth": {
    "file": "ground_truth.csv",
    "column_a": "id_a",
    "column_b": "id_b",
    "label_column": null
  },
  "candidates": null
}
```
