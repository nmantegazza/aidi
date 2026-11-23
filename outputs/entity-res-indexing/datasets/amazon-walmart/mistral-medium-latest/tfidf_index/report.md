# Indexing Benchmark: amazon-walmart — TF-IDF Index

- **Domain**: e-commerce
- **Strategy**: TF-IDF Index
- **Model**: mistral-medium-latest
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Recall | 0.9945 | 0.0005 |
| Precision | 0.0077 | 0.0000 |
| Reduction Ratio | 0.9974 | 0.0000 |
| Indexing Time (s) | 23.7564 | 0.8931 |
| Peak Memory (MB) | 395.06 | 15.34 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 5,274 |
| Completion Tokens | 12,486 |
| Total Tokens | 17,760 |
| Estimated Cost (USD) | $0.1016 |

## Iterations

| Iter | Status | Recall | Precision | Red. Ratio | Candidates | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9948 | 0.0077 | 0.9973 | 149811 | 23.1943 | 386.75 | 6313 | $0.0368 |  |
| 2 | SUCCESS | 0.9948 | 0.0077 | 0.9973 | 149689 | 23.2886 | 385.67 | 4534 | $0.0235 |  |
| 3 | SUCCESS | 0.9939 | 0.0077 | 0.9974 | 148231 | 24.7862 | 412.76 | 6913 | $0.0413 |  |
