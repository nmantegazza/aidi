# Indexing Benchmark: fodors-zagats — TF-IDF Index

- **Domain**: restaurants
- **Strategy**: TF-IDF Index
- **Model**: gemini-3.8-flash
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Recall | 1.0000 | 0.0000 |
| Precision | 0.0164 | 0.0000 |
| Reduction Ratio | 0.9614 | 0.0000 |
| Indexing Time (s) | 0.2435 | 0.0137 |
| Peak Memory (MB) | 2.18 | 0.06 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 3,882 |
| Completion Tokens | 1,634 |
| Total Tokens | 5,516 |
| Estimated Cost (USD) | $0.0090 |

## Iterations

| Iter | Status | Recall | Precision | Red. Ratio | Candidates | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.0164 | 0.9614 | 6810 | 0.2593 | 2.25 | 2021 | $0.0037 |  |
| 2 | SUCCESS | 1.0000 | 0.0164 | 0.9614 | 6810 | 0.2367 | 2.15 | 1726 | $0.0026 |  |
| 3 | SUCCESS | 1.0000 | 0.0164 | 0.9614 | 6810 | 0.2347 | 2.15 | 1769 | $0.0028 |  |
