# Data Fusion Benchmarking Report

- **Run ID**: `run_20260920_081348`
- **Timestamp**: `2026-09-20T08:28:04.749242+00:00`
- **Datasets**: books, flights, stocks
- **Models / Strategies**: deepseek-v4.1-flash, gemini-3.8-flash, gpt-5.6-sol, mistral-medium-latest, trust_a, trust_b
- **Iterations**: 3
- **Failed Iterations**: 0 / 54

## Macro-Averaged Results

| Model / Strategy | Abs Precision | Abs Recall | Abs F1 | Reach Precision | Reach Recall | Reach F1 | Mean Latency (s) | Total Tokens | Cost (USD) | Consensus | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4.1-flash | 0.7805 | 0.7866 | 0.7824 | 0.7805 | 0.9068 | 0.8373 | 23.61s | 68,138 | $0.0000 | 81.22% | 9/9 OK |
| gemini-3.8-flash | 0.7864 | 0.7866 | 0.7861 | 0.7864 | 0.9131 | 0.8414 | 7.00s | 26,576 | $0.0352 | 75.93% | 9/9 OK |
| gpt-5.6-sol | 0.7827 | 0.8000 | 0.7912 | 0.7827 | 0.9270 | 0.8466 | 16.63s | 28,004 | $0.2108 | 96.30% | 9/9 OK |
| mistral-medium-latest | 0.7864 | 0.8049 | 0.7955 | 0.7864 | 0.9328 | 0.8512 | 36.31s | 77,682 | $0.4408 | 85.65% | 9/9 OK |
| trust_a | 0.7499 | 0.6281 | 0.6740 | 0.7499 | 0.7048 | 0.7205 | 0.35s | 0 | $0.0000 | 100.00% | 9/9 OK |
| trust_b | 0.8110 | 0.8059 | 0.8081 | 0.8110 | 0.9310 | 0.8656 | 0.37s | 0 | $0.0000 | 100.00% | 9/9 OK |

## Per-Dataset Breakdown

| Dataset | Model / Strategy | Abs F1 (Mean ± Std) | Reach F1 (Mean ± Std) | Latency (s) | Tokens (Total/Reasoning) | Cost (USD) | Consensus | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| books | deepseek-v4.1-flash | 0.9370 ± 0.0047 | 0.9467 ± 0.0046 | 10.49s | 12,897 (3,895) | $0.0000 | 88.89% | 3/3 OK |
| books | gemini-3.8-flash | 0.9291 ± 0.0144 | 0.9390 ± 0.0141 | 7.89s | 7,650 (0) | $0.0119 | 77.78% | 3/3 OK |
| books | gpt-5.6-sol | 0.9401 ± 0.0000 | 0.9499 ± 0.0000 | 12.53s | 7,341 (1,075) | $0.0538 | 88.89% | 3/3 OK |
| books | mistral-medium-latest | 0.9362 ± 0.0033 | 0.9460 ± 0.0034 | 16.33s | 14,313 (0) | $0.0694 | 77.78% | 3/3 OK |
| books | trust_a | 0.9128 ± 0.0000 | 0.9231 ± 0.0000 | 0.01s | 0 (0) | $0.0000 | 100.00% | 3/3 OK |
| books | trust_b | 0.9394 ± 0.0000 | 0.9493 ± 0.0000 | 0.01s | 0 (0) | $0.0000 | 100.00% | 3/3 OK |
| flights | deepseek-v4.1-flash | 0.6270 ± 0.0820 | 0.7268 ± 0.0878 | 19.84s | 21,326 (8,745) | $0.0000 | 71.43% | 3/3 OK |
| flights | gemini-3.8-flash | 0.6744 ± 0.0000 | 0.7775 ± 0.0000 | 8.01s | 9,654 (0) | $0.0124 | 100.00% | 3/3 OK |
| flights | gpt-5.6-sol | 0.6744 ± 0.0000 | 0.7775 ± 0.0000 | 20.36s | 10,489 (1,684) | $0.0824 | 100.00% | 3/3 OK |
| flights | mistral-medium-latest | 0.6744 ± 0.0000 | 0.7775 ± 0.0000 | 36.25s | 26,709 (0) | $0.1485 | 100.00% | 3/3 OK |
| flights | trust_a | 0.3556 ± 0.0000 | 0.4317 ± 0.0000 | 0.48s | 0 (0) | $0.0000 | 100.00% | 3/3 OK |
| flights | trust_b | 0.6514 ± 0.0000 | 0.7556 ± 0.0000 | 0.50s | 0 (0) | $0.0000 | 100.00% | 3/3 OK |
| stocks | deepseek-v4.1-flash | 0.7833 ± 0.0219 | 0.8383 ± 0.0233 | 40.50s | 33,915 (22,055) | $0.0000 | 83.33% | 3/3 OK |
| stocks | gemini-3.8-flash | 0.7547 ± 0.0000 | 0.8078 ± 0.0000 | 5.10s | 9,272 (0) | $0.0108 | 50.00% | 3/3 OK |
| stocks | gpt-5.6-sol | 0.7590 ± 0.0074 | 0.8124 ± 0.0079 | 16.99s | 10,174 (1,566) | $0.0746 | 100.00% | 3/3 OK |
| stocks | mistral-medium-latest | 0.7758 ± 0.0204 | 0.8303 ± 0.0218 | 56.35s | 36,660 (0) | $0.2229 | 79.17% | 3/3 OK |
| stocks | trust_a | 0.7535 ± 0.0000 | 0.8066 ± 0.0000 | 0.56s | 0 (0) | $0.0000 | 100.00% | 3/3 OK |
| stocks | trust_b | 0.8335 ± 0.0000 | 0.8920 ± 0.0000 | 0.59s | 0 (0) | $0.0000 | 100.00% | 3/3 OK |
