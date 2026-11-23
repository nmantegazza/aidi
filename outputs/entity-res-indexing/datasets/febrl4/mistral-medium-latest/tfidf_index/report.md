# Indexing Benchmark: febrl4 — TF-IDF Index

- **Domain**: synthetic
- **Strategy**: TF-IDF Index
- **Model**: mistral-medium-latest
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Recall | 0.9993 | 0.0009 |
| Precision | 0.1469 | 0.0632 |
| Reduction Ratio | 0.9985 | 0.0006 |
| Indexing Time (s) | 1.3859 | 0.1755 |
| Peak Memory (MB) | 23.47 | 4.75 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 4,797 |
| Completion Tokens | 12,872 |
| Total Tokens | 17,669 |
| Estimated Cost (USD) | $0.1037 |

## Iterations

| Iter | Status | Recall | Precision | Red. Ratio | Candidates | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.2172 | 0.9991 | 23021 | 1.5885 | 28.81 | 9377 | $0.0607 |  |
| 2 | SUCCESS | 0.9996 | 0.1289 | 0.9984 | 38762 | 1.2868 | 19.73 | 4180 | $0.0218 |  |
| 3 | SUCCESS | 0.9982 | 0.0947 | 0.9979 | 52722 | 1.2823 | 21.86 | 4112 | $0.0212 |  |
