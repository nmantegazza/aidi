# Schema Integration Alignment Benchmark Report

**Run ID**: `run_20260917_150754`  
**Generated**: 2026-09-18 10:48:22 UTC  
**Iterations per Dataset**: 3  
**Evaluated Models**: `gemini-3.8-flash`, `gpt-5.6-sol`, `mistral-medium-latest`, `deepseek-v4.1-flash`  
**Evaluated Datasets**: 3 datasets  

## Macro-Averaged Model Performance

| Model | Status | Completeness (Cov_attr) | Structural Integrity (S_rel) | Intra-Table Uniqueness (M_unique) | Mean Latency | Total Tokens |
| :--- | :---: | :---: | :---: | :---: | :---: | ---: |
| `gemini-3.8-flash` | `SUCCESS (9/9)` | 0.7746 | 0.6421 | 0.9875 | 126.80s | 326,747 |
| `gpt-5.6-sol` | `SUCCESS (9/9)` | 0.8414 | 0.7866 | 0.9932 | 82.93s | 277,274 |
| `mistral-medium-latest` | `PARTIAL (8/9)` | 0.7487 | 0.6063 | 0.9821 | 339.81s | 608,227 |
| `deepseek-v4.1-flash` | `SUCCESS (9/9)` | 0.9178 | 0.8044 | 0.9913 | 94.64s | 517,688 |

## Per-Dataset Evaluation Results

| Dataset | Domain | Model | Status | Completeness | Structural (I) | Uniqueness | Latency (s) | Tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bank1-bank2` | Financial & Banking | `gemini-3.8-flash` | `SUCCESS (3/3)` | 0.92 ± 0.00 | 0.83 ± 0.00 | 0.99 ± 0.01 | 22.36s | 35,349 |
| `bank1-bank2` | Financial & Banking | `gpt-5.6-sol` | `SUCCESS (3/3)` | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.99 ± 0.01 | 60.09s | 37,526 |
| `bank1-bank2` | Financial & Banking | `mistral-medium-latest` | `SUCCESS (3/3)` | 0.92 ± 0.06 | 0.84 ± 0.11 | 1.00 ± 0.00 | 471.57s | 155,693 |
| `bank1-bank2` | Financial & Banking | `deepseek-v4.1-flash` | `SUCCESS (3/3)` | 0.98 ± 0.00 | 0.99 ± 0.03 | 1.00 ± 0.00 | 56.82s | 72,035 |
| `imdb-sakila` | Media & Entertainment | `gemini-3.8-flash` | `SUCCESS (3/3)` | 0.97 ± 0.02 | 0.99 ± 0.02 | 1.00 ± 0.00 | 42.36s | 61,938 |
| `imdb-sakila` | Media & Entertainment | `gpt-5.6-sol` | `SUCCESS (3/3)` | 1.00 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 | 83.11s | 60,262 |
| `imdb-sakila` | Media & Entertainment | `mistral-medium-latest` | `SUCCESS (3/3)` | 0.72 ± 0.18 | 0.45 ± 0.34 | 1.00 ± 0.00 | 279.68s | 260,488 |
| `imdb-sakila` | Media & Entertainment | `deepseek-v4.1-flash` | `SUCCESS (3/3)` | 0.99 ± 0.01 | 1.00 ± 0.00 | 1.00 ± 0.00 | 106.39s | 180,929 |
| `synthea-omop` | Clinical & Healthcare | `gemini-3.8-flash` | `SUCCESS (3/3)` | 0.43 ± 0.16 | 0.11 ± 0.03 | 0.97 ± 0.01 | 315.69s | 229,460 |
| `synthea-omop` | Clinical & Healthcare | `gpt-5.6-sol` | `SUCCESS (3/3)` | 0.52 ± 0.05 | 0.36 ± 0.07 | 0.99 ± 0.01 | 105.60s | 179,486 |
| `synthea-omop` | Clinical & Healthcare | `mistral-medium-latest` | `PARTIAL (2/3)` | 0.62 ± 0.07 | 0.53 ± 0.10 | 0.95 ± 0.02 | 268.17s | 192,046 |
| `synthea-omop` | Clinical & Healthcare | `deepseek-v4.1-flash` | `SUCCESS (3/3)` | 0.78 ± 0.23 | 0.43 ± 0.20 | 0.98 ± 0.01 | 120.73s | 264,724 |

## Failures & Errors

> [!WARNING]
> **1 iteration failure(s) recorded**. Use `--retry-run run_20260917_150754` to re-execute failed iterations in-place.

| Dataset | Model | Iteration | Error Message |
| --- | --- | --- | --- |
| `synthea-omop` | `mistral-medium-latest` | 2 | `ReadTimeout` |
