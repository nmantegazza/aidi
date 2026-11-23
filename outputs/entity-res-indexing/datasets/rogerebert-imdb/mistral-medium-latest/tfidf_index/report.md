# Indexing Benchmark: rogerebert-imdb — TF-IDF Index

- **Domain**: movies
- **Strategy**: TF-IDF Index
- **Model**: mistral-medium-latest
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Recall | 0.9972 | 0.0024 |
| Precision | 0.0031 | 0.0006 |
| Reduction Ratio | 0.9967 | 0.0006 |
| Indexing Time (s) | 1.8592 | 0.0157 |
| Peak Memory (MB) | 55.51 | 0.37 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 4,458 |
| Completion Tokens | 11,484 |
| Total Tokens | 15,942 |
| Estimated Cost (USD) | $0.0928 |

## Iterations

| Iter | Status | Recall | Precision | Red. Ratio | Candidates | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.0037 | 0.9974 | 64735 | 1.8727 | 55.08 | 6741 | $0.0416 |  |
| 2 | SUCCESS | 0.9959 | 0.0027 | 0.9964 | 88127 | 1.8630 | 55.73 | 3939 | $0.0206 |  |
| 3 | SUCCESS | 0.9959 | 0.0027 | 0.9964 | 88127 | 1.8420 | 55.72 | 5262 | $0.0305 |  |
