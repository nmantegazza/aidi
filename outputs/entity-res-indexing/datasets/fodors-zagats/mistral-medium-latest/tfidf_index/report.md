# Indexing Benchmark: fodors-zagats — TF-IDF Index

- **Domain**: restaurants
- **Strategy**: TF-IDF Index
- **Model**: mistral-medium-latest
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Recall | 1.0000 | 0.0000 |
| Precision | 0.0189 | 0.0017 |
| Reduction Ratio | 0.9662 | 0.0032 |
| Indexing Time (s) | 0.2757 | 0.0216 |
| Peak Memory (MB) | 2.16 | 0.09 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 3,999 |
| Completion Tokens | 13,184 |
| Total Tokens | 17,183 |
| Estimated Cost (USD) | $0.1049 |

## Iterations

| Iter | Status | Recall | Precision | Red. Ratio | Candidates | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.0198 | 0.9680 | 5646 | 0.2635 | 2.11 | 4730 | $0.0275 |  |
| 2 | SUCCESS | 1.0000 | 0.0198 | 0.9680 | 5646 | 0.2630 | 2.11 | 6052 | $0.0374 |  |
| 3 | SUCCESS | 1.0000 | 0.0169 | 0.9625 | 6623 | 0.3006 | 2.26 | 6401 | $0.0400 |  |
