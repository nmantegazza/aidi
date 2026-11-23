# Indexing Benchmark: rogerebert-imdb — TF-IDF Index

- **Domain**: movies
- **Strategy**: TF-IDF Index
- **Model**: gpt-5.6-sol
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Recall | 0.9986 | 0.0024 |
| Precision | 0.0041 | 0.0019 |
| Reduction Ratio | 0.9973 | 0.0010 |
| Indexing Time (s) | 1.7086 | 0.2272 |
| Peak Memory (MB) | 41.98 | 23.96 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 3,978 |
| Completion Tokens | 1,652 |
| Total Tokens | 5,630 |
| Estimated Cost (USD) | $0.0415 |

## Iterations

| Iter | Status | Recall | Precision | Red. Ratio | Candidates | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.0034 | 0.9971 | 70999 | 1.8635 | 55.88 | 1888 | $0.0177 |  |
| 2 | SUCCESS | 1.0000 | 0.0062 | 0.9984 | 38599 | 1.4478 | 14.32 | 1869 | $0.0118 |  |
| 3 | SUCCESS | 0.9959 | 0.0027 | 0.9964 | 88177 | 1.8143 | 55.73 | 1873 | $0.0119 |  |
