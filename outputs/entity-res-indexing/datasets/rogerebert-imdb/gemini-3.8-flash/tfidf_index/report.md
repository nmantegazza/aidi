# Indexing Benchmark: rogerebert-imdb — TF-IDF Index

- **Domain**: movies
- **Strategy**: TF-IDF Index
- **Model**: gemini-3.8-flash
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Recall | 1.0000 | 0.0000 |
| Precision | 0.0054 | 0.0000 |
| Reduction Ratio | 0.9982 | 0.0000 |
| Indexing Time (s) | 1.4050 | 0.0308 |
| Peak Memory (MB) | 17.06 | 0.05 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 4,410 |
| Completion Tokens | 957 |
| Total Tokens | 5,367 |
| Estimated Cost (USD) | $0.0069 |

## Iterations

| Iter | Status | Recall | Precision | Red. Ratio | Candidates | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.0054 | 0.9982 | 44445 | 1.3709 | 17.01 | 1843 | $0.0025 |  |
| 2 | SUCCESS | 1.0000 | 0.0054 | 0.9982 | 44759 | 1.4311 | 17.10 | 1672 | $0.0019 |  |
| 3 | SUCCESS | 1.0000 | 0.0054 | 0.9982 | 44565 | 1.4129 | 17.07 | 1852 | $0.0025 |  |
