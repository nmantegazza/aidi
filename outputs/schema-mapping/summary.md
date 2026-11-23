# Schema Mapping Benchmark Report

- **Timestamp**: `2026-09-18T14:46:51.311379+00:00`
- **Models Evaluated**: gemini-3.8-flash, gpt-5.6-sol, mistral-medium-latest, deepseek-v4.1-flash
- **Category Scope**: `all`
- **Iterations per model**: `3`
- **Baselines Included**: `True`

## Experiment Configuration & Provenance

- **System Prompt Snapshot**: `2241 chars` (SHA256: `6b61bf8562ad`)
- **Instance Grounding Preview**: `Disabled`
- **Provider / Model**: `auto` / `gemini-3.8-flash`
- **Max Agent Retries**: `2`

## Macro-Averaged Results

### Single-Table Benchmarks Macro

| Method / Model | Type | Status | Precision | Recall | F1-Score | Latency (s) | Total Tokens | Cost (USD) | Retries |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `coma` | `baseline` | `SUCCESS (4/4)` | 0.8000 | 0.3248 | **0.4142** | 0.66s | - | - | - |
| `cupid` | `baseline` | `SUCCESS (4/4)` | 0.2500 | 0.1500 | **0.1875** | 0.54s | - | - | - |
| `distribution_based` | `baseline` | `SUCCESS (4/4)` | 0.5625 | 0.3415 | **0.3958** | 0.95s | - | - | - |
| `exact` | `baseline` | `SUCCESS (4/4)` | 0.2500 | 0.0375 | **0.0652** | 0.00s | - | - | - |
| `jaccard` | `baseline` | `SUCCESS (4/4)` | 0.8077 | 0.3499 | **0.4572** | 0.74s | - | - | - |
| `deepseek-v4.1-flash` | `llm` | `SUCCESS (12/12)` | 1.0000 | 1.0000 | **1.0000** | 21.37s | 127,569 | $0.0000 | 0 |
| `gemini-3.8-flash` | `llm` | `SUCCESS (12/12)` | 1.0000 | 1.0000 | **1.0000** | 12.37s | 69,300 | $0.1175 | 0 |
| `gpt-5.6-sol` | `llm` | `SUCCESS (12/12)` | 1.0000 | 1.0000 | **1.0000** | 12.22s | 64,357 | $0.4624 | 1 |
| `mistral-medium-latest` | `llm` | `SUCCESS (12/12)` | 0.9316 | 0.9807 | **0.9545** | 62.65s | 166,873 | $0.9423 | 0 |

### Multi-Table Benchmarks Macro

| Method / Model | Type | Status | Precision | Recall | F1-Score | Latency (s) | Total Tokens | Cost (USD) | Retries |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `exact` | `baseline` | `SUCCESS (3/3)` | 0.3333 | 0.0784 | **0.1270** | 0.00s | - | - | - |
| `deepseek-v4.1-flash` | `llm` | `SUCCESS (9/9)` | 0.7421 | 0.5708 | **0.6151** | 31.90s | 280,320 | $0.0000 | 0 |
| `gemini-3.8-flash` | `llm` | `SUCCESS (9/9)` | 0.8697 | 0.5327 | **0.6392** | 11.16s | 247,026 | $0.1871 | 1 |
| `gpt-5.6-sol` | `llm` | `SUCCESS (9/9)` | 0.7531 | 0.5844 | **0.6330** | 53.70s | 461,396 | $1.6331 | 9 |
| `mistral-medium-latest` | `llm` | `SUCCESS (9/9)` | 0.7561 | 0.5209 | **0.5915** | 106.72s | 474,698 | $1.5494 | 2 |

### Overall Suite Macro

| Method / Model | Type | Status | Precision | Recall | F1-Score | Latency (s) | Total Tokens | Cost (USD) | Retries |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `coma` | `baseline` | `SUCCESS (4/4)` | 0.8000 | 0.3248 | **0.4142** | 0.66s | - | - | - |
| `cupid` | `baseline` | `SUCCESS (4/4)` | 0.2500 | 0.1500 | **0.1875** | 0.54s | - | - | - |
| `distribution_based` | `baseline` | `SUCCESS (4/4)` | 0.5625 | 0.3415 | **0.3958** | 0.95s | - | - | - |
| `exact` | `baseline` | `SUCCESS (7/7)` | 0.2857 | 0.0550 | **0.0917** | 0.00s | - | - | - |
| `jaccard` | `baseline` | `SUCCESS (4/4)` | 0.8077 | 0.3499 | **0.4572** | 0.74s | - | - | - |
| `deepseek-v4.1-flash` | `llm` | `SUCCESS (21/21)` | 0.8895 | 0.8161 | **0.8350** | 25.88s | 407,889 | $0.0000 | 0 |
| `gemini-3.8-flash` | `llm` | `SUCCESS (21/21)` | 0.9441 | 0.7997 | **0.8454** | 11.85s | 316,326 | $0.3047 | 1 |
| `gpt-5.6-sol` | `llm` | `SUCCESS (21/21)` | 0.8942 | 0.8219 | **0.8427** | 30.00s | 525,753 | $2.0955 | 10 |
| `mistral-medium-latest` | `llm` | `SUCCESS (21/21)` | 0.8564 | 0.7836 | **0.7989** | 81.53s | 641,571 | $2.4916 | 2 |

## Per-Dataset Evaluation Results

| Dataset | Category | Domain | Scenario | Method / Model | Status | Precision | Recall | F1-Score | TP / FP / FN | Latency (s) | Tokens | Cost (USD) | Retries |
|---|---|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `bank1-bank2` | `multi_table` | Financial & Banking | Multi-Table Relational Schema | `exact` | `SUCCESS (1/1)` | 1.0000 | 0.2353 | **0.3810** | 4 / 0 / 13 | 0.00s | - | - | - |
| `imdb-sakila` | `multi_table` | Media & Entertainment | Multi-Table Relational Schema | `exact` | `SUCCESS (1/1)` | 0.0000 | 0.0000 | **0.0000** | 0 / 0 / 35 | 0.00s | - | - | - |
| `synthea-omop` | `multi_table` | Clinical & Healthcare | Multi-Table Relational Schema | `exact` | `SUCCESS (1/1)` | 0.0000 | 0.0000 | **0.0000** | 0 / 0 / 124 | 0.00s | - | - | - |
| `Musicians_unionable` | `single_table` | Wikidata | Real-World Web Graph | `exact` | `SUCCESS (1/1)` | 1.0000 | 0.1500 | **0.2609** | 3 / 0 / 17 | 0.00s | - | - | - |
| `assays_both_0_70_ac3_av` | `single_table` | ChEMBL | View-Unionable (Noise) | `exact` | `SUCCESS (1/1)` | 0.0000 | 0.0000 | **0.0000** | 0 / 0 / 16 | 0.00s | - | - | - |
| `miller2_both_50_50_ac5_av` | `single_table` | OpenData | Semantically-Joinable (Full Noise) | `exact` | `SUCCESS (1/1)` | 0.0000 | 0.0000 | **0.0000** | 0 / 0 / 25 | 0.00s | - | - | - |
| `prospect_both_50_50_ac5_av` | `single_table` | TPC-DI | Semantically-Joinable (Full Noise) | `exact` | `SUCCESS (1/1)` | 0.0000 | 0.0000 | **0.0000** | 0 / 0 / 11 | 0.00s | - | - | - |
| `Musicians_unionable` | `single_table` | Wikidata | Real-World Web Graph | `jaccard` | `SUCCESS (1/1)` | 1.0000 | 0.7000 | **0.8235** | 14 / 0 / 6 | 1.30s | - | - | - |
| `assays_both_0_70_ac3_av` | `single_table` | ChEMBL | View-Unionable (Noise) | `jaccard` | `SUCCESS (1/1)` | 1.0000 | 0.1250 | **0.2222** | 2 / 0 / 14 | 0.25s | - | - | - |
| `miller2_both_50_50_ac5_av` | `single_table` | OpenData | Semantically-Joinable (Full Noise) | `jaccard` | `SUCCESS (1/1)` | 0.2308 | 0.1200 | **0.1579** | 3 / 10 / 22 | 0.32s | - | - | - |
| `prospect_both_50_50_ac5_av` | `single_table` | TPC-DI | Semantically-Joinable (Full Noise) | `jaccard` | `SUCCESS (1/1)` | 1.0000 | 0.4545 | **0.6250** | 5 / 0 / 6 | 1.07s | - | - | - |
| `Musicians_unionable` | `single_table` | Wikidata | Real-World Web Graph | `cupid` | `SUCCESS (1/1)` | 1.0000 | 0.6000 | **0.7500** | 12 / 0 / 8 | 1.71s | - | - | - |
| `assays_both_0_70_ac3_av` | `single_table` | ChEMBL | View-Unionable (Noise) | `cupid` | `SUCCESS (1/1)` | 0.0000 | 0.0000 | **0.0000** | 0 / 0 / 16 | 0.10s | - | - | - |
| `miller2_both_50_50_ac5_av` | `single_table` | OpenData | Semantically-Joinable (Full Noise) | `cupid` | `SUCCESS (1/1)` | 0.0000 | 0.0000 | **0.0000** | 0 / 0 / 25 | 0.23s | - | - | - |
| `prospect_both_50_50_ac5_av` | `single_table` | TPC-DI | Semantically-Joinable (Full Noise) | `cupid` | `SUCCESS (1/1)` | 0.0000 | 0.0000 | **0.0000** | 0 / 1 / 11 | 0.15s | - | - | - |
| `Musicians_unionable` | `single_table` | Wikidata | Real-World Web Graph | `distribution_based` | `SUCCESS (1/1)` | 1.0000 | 0.9000 | **0.9474** | 18 / 0 / 2 | 1.71s | - | - | - |
| `assays_both_0_70_ac3_av` | `single_table` | ChEMBL | View-Unionable (Noise) | `distribution_based` | `SUCCESS (1/1)` | 0.5000 | 0.0625 | **0.1111** | 1 / 1 / 15 | 0.22s | - | - | - |
| `miller2_both_50_50_ac5_av` | `single_table` | OpenData | Semantically-Joinable (Full Noise) | `distribution_based` | `SUCCESS (1/1)` | 0.0833 | 0.0400 | **0.0541** | 1 / 11 / 24 | 1.34s | - | - | - |
| `prospect_both_50_50_ac5_av` | `single_table` | TPC-DI | Semantically-Joinable (Full Noise) | `distribution_based` | `SUCCESS (1/1)` | 0.6667 | 0.3636 | **0.4706** | 4 / 2 / 7 | 0.54s | - | - | - |
| `Musicians_unionable` | `single_table` | Wikidata | Real-World Web Graph | `coma` | `SUCCESS (1/1)` | 1.0000 | 0.8500 | **0.9189** | 17 / 0 / 3 | 0.34s | - | - | - |
| `assays_both_0_70_ac3_av` | `single_table` | ChEMBL | View-Unionable (Noise) | `coma` | `SUCCESS (1/1)` | 1.0000 | 0.1875 | **0.3158** | 3 / 0 / 13 | 0.19s | - | - | - |
| `miller2_both_50_50_ac5_av` | `single_table` | OpenData | Semantically-Joinable (Full Noise) | `coma` | `SUCCESS (1/1)` | 0.2000 | 0.0800 | **0.1143** | 2 / 8 / 23 | 1.78s | - | - | - |
| `prospect_both_50_50_ac5_av` | `single_table` | TPC-DI | Semantically-Joinable (Full Noise) | `coma` | `SUCCESS (1/1)` | 1.0000 | 0.1818 | **0.3077** | 2 / 0 / 9 | 0.32s | - | - | - |
| `bank1-bank2` | `multi_table` | Financial & Banking | Multi-Table Relational Schema | `gemini-3.8-flash` | `SUCCESS (3/3)` | 1.0000 | 0.9020 | **0.9482** | 15 / 0 / 2 | 7.17s | 25,449 | $0.0273 | 0 |
| `bank1-bank2` | `multi_table` | Financial & Banking | Multi-Table Relational Schema | `gpt-5.6-sol` | `SUCCESS (3/3)` | 1.0000 | 0.9412 | **0.9697** | 16 / 0 / 1 | 21.80s | 47,497 | $0.1766 | 3 |
| `bank1-bank2` | `multi_table` | Financial & Banking | Multi-Table Relational Schema | `mistral-medium-latest` | `SUCCESS (3/3)` | 0.9608 | 0.9412 | **0.9507** | 16 / 1 / 1 | 50.17s | 46,427 | $0.2183 | 0 |
| `bank1-bank2` | `multi_table` | Financial & Banking | Multi-Table Relational Schema | `deepseek-v4.1-flash` | `SUCCESS (3/3)` | 0.7852 | 0.9412 | **0.8532** | 16 / 2 / 1 | 25.73s | 41,838 | $0.0000 | 0 |
| `imdb-sakila` | `multi_table` | Media & Entertainment | Multi-Table Relational Schema | `gemini-3.8-flash` | `SUCCESS (3/3)` | 0.8059 | 0.3143 | **0.4521** | 11 / 3 / 24 | 7.40s | 53,143 | $0.0350 | 1 |
| `imdb-sakila` | `multi_table` | Media & Entertainment | Multi-Table Relational Schema | `gpt-5.6-sol` | `SUCCESS (3/3)` | 0.8154 | 0.3334 | **0.4728** | 12 / 3 / 23 | 32.08s | 78,059 | $0.2672 | 3 |
| `imdb-sakila` | `multi_table` | Media & Entertainment | Multi-Table Relational Schema | `mistral-medium-latest` | `SUCCESS (3/3)` | 0.7552 | 0.2667 | **0.3937** | 8 / 3 / 27 | 85.20s | 73,804 | $0.3443 | 0 |
| `imdb-sakila` | `multi_table` | Media & Entertainment | Multi-Table Relational Schema | `deepseek-v4.1-flash` | `SUCCESS (3/3)` | 0.7508 | 0.3143 | **0.4430** | 11 / 4 / 24 | 23.81s | 53,681 | $0.0000 | 0 |
| `synthea-omop` | `multi_table` | Clinical & Healthcare | Multi-Table Relational Schema | `gemini-3.8-flash` | `SUCCESS (3/3)` | 0.8031 | 0.3817 | **0.5172** | 46 / 11 / 78 | 18.91s | 168,434 | $0.1249 | 0 |
| `synthea-omop` | `multi_table` | Clinical & Healthcare | Multi-Table Relational Schema | `gpt-5.6-sol` | `SUCCESS (3/3)` | 0.4438 | 0.4785 | **0.4564** | 63 / 43 / 61 | 107.22s | 335,840 | $1.1893 | 3 |
| `synthea-omop` | `multi_table` | Clinical & Healthcare | Multi-Table Relational Schema | `mistral-medium-latest` | `SUCCESS (3/3)` | 0.5523 | 0.3548 | **0.4302** | 45 / 48 / 79 | 184.79s | 354,467 | $0.9868 | 2 |
| `synthea-omop` | `multi_table` | Clinical & Healthcare | Multi-Table Relational Schema | `deepseek-v4.1-flash` | `SUCCESS (3/3)` | 0.6904 | 0.4570 | **0.5490** | 53 / 33 / 71 | 46.15s | 184,801 | $0.0000 | 0 |
| `Musicians_unionable` | `single_table` | Wikidata | Real-World Web Graph | `gemini-3.8-flash` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 20 / 0 / 0 | 10.29s | 14,451 | $0.0241 | 0 |
| `Musicians_unionable` | `single_table` | Wikidata | Real-World Web Graph | `gpt-5.6-sol` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 20 / 0 / 0 | 11.97s | 17,941 | $0.1188 | 1 |
| `Musicians_unionable` | `single_table` | Wikidata | Real-World Web Graph | `mistral-medium-latest` | `SUCCESS (3/3)` | 1.0000 | 0.9833 | **0.9915** | 20 / 0 / 0 | 25.74s | 23,630 | $0.1073 | 0 |
| `Musicians_unionable` | `single_table` | Wikidata | Real-World Web Graph | `deepseek-v4.1-flash` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 20 / 0 / 0 | 6.26s | 17,722 | $0.0000 | 0 |
| `assays_both_0_70_ac3_av` | `single_table` | ChEMBL | View-Unionable (Noise) | `gemini-3.8-flash` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 16 / 0 / 0 | 13.28s | 15,093 | $0.0259 | 0 |
| `assays_both_0_70_ac3_av` | `single_table` | ChEMBL | View-Unionable (Noise) | `gpt-5.6-sol` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 16 / 0 / 0 | 9.88s | 12,890 | $0.0951 | 0 |
| `assays_both_0_70_ac3_av` | `single_table` | ChEMBL | View-Unionable (Noise) | `mistral-medium-latest` | `SUCCESS (3/3)` | 0.8889 | 1.0000 | **0.9412** | 16 / 2 / 0 | 94.72s | 52,577 | $0.3258 | 0 |
| `assays_both_0_70_ac3_av` | `single_table` | ChEMBL | View-Unionable (Noise) | `deepseek-v4.1-flash` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 16 / 0 / 0 | 21.27s | 30,955 | $0.0000 | 0 |
| `miller2_both_50_50_ac5_av` | `single_table` | OpenData | Semantically-Joinable (Full Noise) | `gemini-3.8-flash` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 25 / 0 / 0 | 14.40s | 25,668 | $0.0424 | 0 |
| `miller2_both_50_50_ac5_av` | `single_table` | OpenData | Semantically-Joinable (Full Noise) | `gpt-5.6-sol` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 25 / 0 / 0 | 18.78s | 22,474 | $0.1755 | 0 |
| `miller2_both_50_50_ac5_av` | `single_table` | OpenData | Semantically-Joinable (Full Noise) | `mistral-medium-latest` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 25 / 0 / 0 | 70.65s | 51,855 | $0.2820 | 0 |
| `miller2_both_50_50_ac5_av` | `single_table` | OpenData | Semantically-Joinable (Full Noise) | `deepseek-v4.1-flash` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 25 / 0 / 0 | 31.68s | 47,583 | $0.0000 | 0 |
| `prospect_both_50_50_ac5_av` | `single_table` | TPC-DI | Semantically-Joinable (Full Noise) | `gemini-3.8-flash` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 11 / 0 / 0 | 11.49s | 14,088 | $0.0250 | 0 |
| `prospect_both_50_50_ac5_av` | `single_table` | TPC-DI | Semantically-Joinable (Full Noise) | `gpt-5.6-sol` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 11 / 0 / 0 | 8.25s | 11,052 | $0.0730 | 0 |
| `prospect_both_50_50_ac5_av` | `single_table` | TPC-DI | Semantically-Joinable (Full Noise) | `mistral-medium-latest` | `SUCCESS (3/3)` | 0.8376 | 0.9394 | **0.8853** | 10 / 2 / 1 | 59.48s | 38,811 | $0.2271 | 0 |
| `prospect_both_50_50_ac5_av` | `single_table` | TPC-DI | Semantically-Joinable (Full Noise) | `deepseek-v4.1-flash` | `SUCCESS (3/3)` | 1.0000 | 1.0000 | **1.0000** | 11 / 0 / 0 | 26.26s | 31,309 | $0.0000 | 0 |

## Failures & Errors

:white_check_mark: Zero iteration failures recorded across all evaluated datasets and models.


## Detailed Dataset Inspection & Field Diagnostics

### Dataset: `bank1-bank2` (Category: `multi_table`, Model: `gemini-3.8-flash`)

- **Domain / Scenario**: Financial & Banking / Multi-Table Relational Schema
- **Source Tables**: 9 (27 columns)
- **Target Tables**: 9 (36 columns)
- **Ground Truth Pairs**: 17
- **True Positives**: 15
- **False Positives**: 0
- **False Negatives**: 2

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `branch.branch_id` | `MATCH (TP)` | branch.branch_id | branch.branch_id |
| `branch.branch_name` | `MATCH (TP)` | branch.name | branch.name |
| `branch.assets` | `UNMAPPED` | *(none)* | *(none)* |
| `branch.branch_address` | `MATCH (TP)` | branch.address | branch.address |
| `banker_info.banker_id` | `UNMAPPED` | *(none)* | *(none)* |
| `banker_info.banker_name` | `UNMAPPED` | *(none)* | *(none)* |
| `banker_info.branch_id` | `UNMAPPED` | *(none)* | *(none)* |
| `account.account_id` | `MATCH (TP)` | account.account_no | account.account_no |
| `account.account_type` | `MATCH (TP)` | account.acc_type | account.acc_type |
| `account.account_balance` | `MATCH (TP)` | account.balance | account.balance |
| `account.branch_id` | `MATCH (TP)` | account.branch_id | account.branch_id |
| `transaction.transaction_id` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.amount` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.account_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.customer_id` | `PARTIAL MATCH` | customer.custid, hold_by.custid | customer.custid |
| `customer.customer_name` | `MATCH (TP)` | customer.name | customer.name |
| `customer.mobileno` | `MATCH (TP)` | customer.phone | customer.phone |
| `customer.dob` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.account_id` | `MISSED (FN)` | hold_by.account_no | *(none)* |
| `customer_credit_card.credit_card_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.expiry_date` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.card_limit` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.account_id` | `UNMAPPED` | *(none)* | *(none)* |
| `loan.loan_id` | `MATCH (TP)` | loan.loan_id | loan.loan_id |
| `loan.issued_amount` | `MATCH (TP)` | loan.amount | loan.amount |
| `loan.remaining_amount` | `UNMAPPED` | *(none)* | *(none)* |
| `loan.branch_id` | `MATCH (TP)` | loan.branch_id | loan.branch_id |
| `loan.account_id` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 36 target fields)*


### Dataset: `bank1-bank2` (Category: `multi_table`, Model: `gpt-5.6-sol`)

- **Domain / Scenario**: Financial & Banking / Multi-Table Relational Schema
- **Source Tables**: 9 (27 columns)
- **Target Tables**: 9 (36 columns)
- **Ground Truth Pairs**: 17
- **True Positives**: 16
- **False Positives**: 0
- **False Negatives**: 1

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `branch.branch_id` | `MATCH (TP)` | branch.branch_id | branch.branch_id |
| `branch.branch_name` | `MATCH (TP)` | branch.name | branch.name |
| `branch.assets` | `UNMAPPED` | *(none)* | *(none)* |
| `branch.branch_address` | `MATCH (TP)` | branch.address | branch.address |
| `banker_info.banker_id` | `UNMAPPED` | *(none)* | *(none)* |
| `banker_info.banker_name` | `UNMAPPED` | *(none)* | *(none)* |
| `banker_info.branch_id` | `UNMAPPED` | *(none)* | *(none)* |
| `account.account_id` | `MATCH (TP)` | account.account_no | account.account_no |
| `account.account_type` | `MATCH (TP)` | account.acc_type | account.acc_type |
| `account.account_balance` | `MATCH (TP)` | account.balance | account.balance |
| `account.branch_id` | `MATCH (TP)` | account.branch_id | account.branch_id |
| `transaction.transaction_id` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.amount` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.account_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.customer_id` | `PARTIAL MATCH` | customer.custid, hold_by.custid | customer.custid |
| `customer.customer_name` | `MATCH (TP)` | customer.name | customer.name |
| `customer.mobileno` | `MATCH (TP)` | customer.phone | customer.phone |
| `customer.dob` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.account_id` | `MATCH (TP)` | hold_by.account_no | hold_by.account_no |
| `customer_credit_card.credit_card_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.expiry_date` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.card_limit` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.account_id` | `UNMAPPED` | *(none)* | *(none)* |
| `loan.loan_id` | `MATCH (TP)` | loan.loan_id | loan.loan_id |
| `loan.issued_amount` | `MATCH (TP)` | loan.amount | loan.amount |
| `loan.remaining_amount` | `UNMAPPED` | *(none)* | *(none)* |
| `loan.branch_id` | `MATCH (TP)` | loan.branch_id | loan.branch_id |
| `loan.account_id` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 36 target fields)*


### Dataset: `bank1-bank2` (Category: `multi_table`, Model: `mistral-medium-latest`)

- **Domain / Scenario**: Financial & Banking / Multi-Table Relational Schema
- **Source Tables**: 9 (27 columns)
- **Target Tables**: 9 (36 columns)
- **Ground Truth Pairs**: 17
- **True Positives**: 16
- **False Positives**: 1
- **False Negatives**: 1

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `branch.branch_id` | `MATCH (TP)` | branch.branch_id | branch.branch_id |
| `branch.branch_name` | `MATCH (TP)` | branch.name | branch.name |
| `branch.assets` | `UNMAPPED` | *(none)* | *(none)* |
| `branch.branch_address` | `MATCH (TP)` | branch.address | branch.address |
| `banker_info.banker_id` | `UNMAPPED` | *(none)* | *(none)* |
| `banker_info.banker_name` | `UNMAPPED` | *(none)* | *(none)* |
| `banker_info.branch_id` | `UNMAPPED` | *(none)* | *(none)* |
| `account.account_id` | `MATCH (TP)` | account.account_no | account.account_no |
| `account.account_type` | `MATCH (TP)` | account.acc_type | account.acc_type |
| `account.account_balance` | `MATCH (TP)` | account.balance | account.balance |
| `account.branch_id` | `MATCH (TP)` | account.branch_id | account.branch_id |
| `transaction.transaction_id` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.amount` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.account_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.customer_id` | `PARTIAL MATCH` | customer.custid, hold_by.custid | customer.custid |
| `customer.customer_name` | `MATCH (TP)` | customer.name | customer.name |
| `customer.mobileno` | `MATCH (TP)` | customer.phone | customer.phone |
| `customer.dob` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.account_id` | `MATCH (TP)` | hold_by.account_no | hold_by.account_no |
| `customer_credit_card.credit_card_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.expiry_date` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.card_limit` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.account_id` | `UNMAPPED` | *(none)* | *(none)* |
| `loan.loan_id` | `MATCH (TP)` | loan.loan_id | loan.loan_id |
| `loan.issued_amount` | `MATCH (TP)` | loan.amount | loan.amount |
| `loan.remaining_amount` | `UNMAPPED` | *(none)* | *(none)* |
| `loan.branch_id` | `MATCH (TP)` | loan.branch_id | loan.branch_id |
| `loan.account_id` | `EXTRA (FP)` | *(none)* | maintain.account_no |

*(Showing first 30 of 36 target fields)*


### Dataset: `bank1-bank2` (Category: `multi_table`, Model: `deepseek-v4.1-flash`)

- **Domain / Scenario**: Financial & Banking / Multi-Table Relational Schema
- **Source Tables**: 9 (27 columns)
- **Target Tables**: 9 (36 columns)
- **Ground Truth Pairs**: 17
- **True Positives**: 16
- **False Positives**: 2
- **False Negatives**: 1

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `branch.branch_id` | `MATCH (TP)` | branch.branch_id | branch.branch_id |
| `branch.branch_name` | `MATCH (TP)` | branch.name | branch.name |
| `branch.assets` | `UNMAPPED` | *(none)* | *(none)* |
| `branch.branch_address` | `MATCH (TP)` | branch.address | branch.address |
| `banker_info.banker_id` | `EXTRA (FP)` | *(none)* | bank.code |
| `banker_info.banker_name` | `EXTRA (FP)` | *(none)* | bank.name |
| `banker_info.branch_id` | `UNMAPPED` | *(none)* | *(none)* |
| `account.account_id` | `MATCH (TP)` | account.account_no | account.account_no |
| `account.account_type` | `MATCH (TP)` | account.acc_type | account.acc_type |
| `account.account_balance` | `MATCH (TP)` | account.balance | account.balance |
| `account.branch_id` | `MATCH (TP)` | account.branch_id | account.branch_id |
| `transaction.transaction_id` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.amount` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `transaction.account_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.customer_id` | `PARTIAL MATCH` | customer.custid, hold_by.custid | customer.custid |
| `customer.customer_name` | `MATCH (TP)` | customer.name | customer.name |
| `customer.mobileno` | `MATCH (TP)` | customer.phone | customer.phone |
| `customer.dob` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.account_id` | `MATCH (TP)` | hold_by.account_no | hold_by.account_no |
| `customer_credit_card.credit_card_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.expiry_date` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.card_limit` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer_credit_card.account_id` | `UNMAPPED` | *(none)* | *(none)* |
| `loan.loan_id` | `MATCH (TP)` | loan.loan_id | loan.loan_id |
| `loan.issued_amount` | `MATCH (TP)` | loan.amount | loan.amount |
| `loan.remaining_amount` | `UNMAPPED` | *(none)* | *(none)* |
| `loan.branch_id` | `MATCH (TP)` | loan.branch_id | loan.branch_id |
| `loan.account_id` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 36 target fields)*


### Dataset: `imdb-sakila` (Category: `multi_table`, Model: `gemini-3.8-flash`)

- **Domain / Scenario**: Media & Entertainment / Multi-Table Relational Schema
- **Source Tables**: 7 (39 columns)
- **Target Tables**: 16 (90 columns)
- **Ground Truth Pairs**: 35
- **True Positives**: 11
- **False Positives**: 3
- **False Negatives**: 24

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `actor.actor_id` | `MATCH (TP)` | name_basics.nconst | name_basics.nconst |
| `actor.first_name` | `MATCH (TP)` | name_basics.primaryname | name_basics.primaryname |
| `actor.last_name` | `MATCH (TP)` | name_basics.primaryname | name_basics.primaryname |
| `actor.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address2` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address_id` | `UNMAPPED` | *(none)* | *(none)* |
| `address.city_id` | `UNMAPPED` | *(none)* | *(none)* |
| `address.district` | `UNMAPPED` | *(none)* | *(none)* |
| `address.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `address.location` | `UNMAPPED` | *(none)* | *(none)* |
| `address.phone` | `UNMAPPED` | *(none)* | *(none)* |
| `address.postal_code` | `UNMAPPED` | *(none)* | *(none)* |
| `category.category_id` | `MISSED (FN)` | title_basics.genres | *(none)* |
| `category.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `category.name` | `MATCH (TP)` | title_basics.genres | title_basics.genres |
| `city.city` | `UNMAPPED` | *(none)* | *(none)* |
| `city.city_id` | `UNMAPPED` | *(none)* | *(none)* |
| `city.country_id` | `UNMAPPED` | *(none)* | *(none)* |
| `city.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `country.country` | `UNMAPPED` | *(none)* | *(none)* |
| `country.country_id` | `UNMAPPED` | *(none)* | *(none)* |
| `country.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.active` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.address_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.create_date` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.email` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.first_name` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.last_name` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 90 target fields)*


### Dataset: `imdb-sakila` (Category: `multi_table`, Model: `gpt-5.6-sol`)

- **Domain / Scenario**: Media & Entertainment / Multi-Table Relational Schema
- **Source Tables**: 7 (39 columns)
- **Target Tables**: 16 (90 columns)
- **Ground Truth Pairs**: 35
- **True Positives**: 12
- **False Positives**: 3
- **False Negatives**: 23

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `actor.actor_id` | `MATCH (TP)` | name_basics.nconst | name_basics.nconst |
| `actor.first_name` | `MATCH (TP)` | name_basics.primaryname | name_basics.primaryname |
| `actor.last_name` | `MATCH (TP)` | name_basics.primaryname | name_basics.primaryname |
| `actor.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address2` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address_id` | `UNMAPPED` | *(none)* | *(none)* |
| `address.city_id` | `UNMAPPED` | *(none)* | *(none)* |
| `address.district` | `UNMAPPED` | *(none)* | *(none)* |
| `address.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `address.location` | `UNMAPPED` | *(none)* | *(none)* |
| `address.phone` | `UNMAPPED` | *(none)* | *(none)* |
| `address.postal_code` | `UNMAPPED` | *(none)* | *(none)* |
| `category.category_id` | `MATCH (TP)` | title_basics.genres | title_basics.genres |
| `category.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `category.name` | `MATCH (TP)` | title_basics.genres | title_basics.genres |
| `city.city` | `UNMAPPED` | *(none)* | *(none)* |
| `city.city_id` | `UNMAPPED` | *(none)* | *(none)* |
| `city.country_id` | `UNMAPPED` | *(none)* | *(none)* |
| `city.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `country.country` | `UNMAPPED` | *(none)* | *(none)* |
| `country.country_id` | `UNMAPPED` | *(none)* | *(none)* |
| `country.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.active` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.address_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.create_date` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.email` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.first_name` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.last_name` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 90 target fields)*


### Dataset: `imdb-sakila` (Category: `multi_table`, Model: `mistral-medium-latest`)

- **Domain / Scenario**: Media & Entertainment / Multi-Table Relational Schema
- **Source Tables**: 7 (39 columns)
- **Target Tables**: 16 (90 columns)
- **Ground Truth Pairs**: 35
- **True Positives**: 8
- **False Positives**: 3
- **False Negatives**: 27

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `actor.actor_id` | `MATCH (TP)` | name_basics.nconst | name_basics.nconst |
| `actor.first_name` | `MATCH (TP)` | name_basics.primaryname | name_basics.primaryname |
| `actor.last_name` | `MISSED (FN)` | name_basics.primaryname | *(none)* |
| `actor.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address2` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address_id` | `UNMAPPED` | *(none)* | *(none)* |
| `address.city_id` | `UNMAPPED` | *(none)* | *(none)* |
| `address.district` | `UNMAPPED` | *(none)* | *(none)* |
| `address.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `address.location` | `UNMAPPED` | *(none)* | *(none)* |
| `address.phone` | `UNMAPPED` | *(none)* | *(none)* |
| `address.postal_code` | `UNMAPPED` | *(none)* | *(none)* |
| `category.category_id` | `MISSED (FN)` | title_basics.genres | *(none)* |
| `category.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `category.name` | `MATCH (TP)` | title_basics.genres | title_basics.genres |
| `city.city` | `UNMAPPED` | *(none)* | *(none)* |
| `city.city_id` | `UNMAPPED` | *(none)* | *(none)* |
| `city.country_id` | `UNMAPPED` | *(none)* | *(none)* |
| `city.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `country.country` | `UNMAPPED` | *(none)* | *(none)* |
| `country.country_id` | `UNMAPPED` | *(none)* | *(none)* |
| `country.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.active` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.address_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.create_date` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.email` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.first_name` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.last_name` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 90 target fields)*


### Dataset: `imdb-sakila` (Category: `multi_table`, Model: `deepseek-v4.1-flash`)

- **Domain / Scenario**: Media & Entertainment / Multi-Table Relational Schema
- **Source Tables**: 7 (39 columns)
- **Target Tables**: 16 (90 columns)
- **Ground Truth Pairs**: 35
- **True Positives**: 11
- **False Positives**: 4
- **False Negatives**: 24

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `actor.actor_id` | `MATCH (TP)` | name_basics.nconst | name_basics.nconst |
| `actor.first_name` | `MATCH (TP)` | name_basics.primaryname | name_basics.primaryname |
| `actor.last_name` | `MATCH (TP)` | name_basics.primaryname | name_basics.primaryname |
| `actor.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address2` | `UNMAPPED` | *(none)* | *(none)* |
| `address.address_id` | `UNMAPPED` | *(none)* | *(none)* |
| `address.city_id` | `UNMAPPED` | *(none)* | *(none)* |
| `address.district` | `UNMAPPED` | *(none)* | *(none)* |
| `address.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `address.location` | `UNMAPPED` | *(none)* | *(none)* |
| `address.phone` | `UNMAPPED` | *(none)* | *(none)* |
| `address.postal_code` | `UNMAPPED` | *(none)* | *(none)* |
| `category.category_id` | `MISSED (FN)` | title_basics.genres | *(none)* |
| `category.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `category.name` | `MATCH (TP)` | title_basics.genres | title_basics.genres |
| `city.city` | `UNMAPPED` | *(none)* | *(none)* |
| `city.city_id` | `UNMAPPED` | *(none)* | *(none)* |
| `city.country_id` | `UNMAPPED` | *(none)* | *(none)* |
| `city.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `country.country` | `UNMAPPED` | *(none)* | *(none)* |
| `country.country_id` | `UNMAPPED` | *(none)* | *(none)* |
| `country.last_update` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.active` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.address_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.create_date` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.customer_id` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.email` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.first_name` | `UNMAPPED` | *(none)* | *(none)* |
| `customer.last_name` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 90 target fields)*


### Dataset: `synthea-omop` (Category: `multi_table`, Model: `gemini-3.8-flash`)

- **Domain / Scenario**: Clinical & Healthcare / Multi-Table Relational Schema
- **Source Tables**: 12 (111 columns)
- **Target Tables**: 39 (432 columns)
- **Ground Truth Pairs**: 124
- **True Positives**: 46
- **False Positives**: 11
- **False Negatives**: 78

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `care_site.care_site_id` | `EXTRA (FP)` | *(none)* | organizations.id |
| `care_site.care_site_name` | `MATCH (TP)` | organizations.name | organizations.name |
| `care_site.care_site_source_value` | `MATCH (TP)` | organizations.id | organizations.id |
| `care_site.location_id` | `UNMAPPED` | *(none)* | *(none)* |
| `care_site.place_of_service_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `care_site.place_of_service_source_value` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_etl_reference` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_holder` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_release_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_source_abbreviation` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_source_name` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_version` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_version_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_description` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_documentation_reference` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_release_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.vocabulary_version` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_definition_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_end_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_start_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.subject_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_description` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_name` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_syntax` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_initiation_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.definition_type_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.subject_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `concept.concept_class_id` | `UNMAPPED` | *(none)* | *(none)* |
| `concept.concept_code` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 432 target fields)*


### Dataset: `synthea-omop` (Category: `multi_table`, Model: `gpt-5.6-sol`)

- **Domain / Scenario**: Clinical & Healthcare / Multi-Table Relational Schema
- **Source Tables**: 12 (111 columns)
- **Target Tables**: 39 (432 columns)
- **Ground Truth Pairs**: 124
- **True Positives**: 63
- **False Positives**: 43
- **False Negatives**: 61

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `care_site.care_site_id` | `EXTRA (FP)` | *(none)* | organizations.id |
| `care_site.care_site_name` | `MATCH (TP)` | organizations.name | organizations.name |
| `care_site.care_site_source_value` | `MATCH (TP)` | organizations.id | organizations.id |
| `care_site.location_id` | `EXTRA (FP)` | *(none)* | organizations.id |
| `care_site.place_of_service_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `care_site.place_of_service_source_value` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_etl_reference` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_holder` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_release_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_source_abbreviation` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_source_name` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_version` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_version_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_description` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_documentation_reference` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_release_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.vocabulary_version` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_definition_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_end_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_start_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.subject_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_description` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_name` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_syntax` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_initiation_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.definition_type_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.subject_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `concept.concept_class_id` | `UNMAPPED` | *(none)* | *(none)* |
| `concept.concept_code` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 432 target fields)*


### Dataset: `synthea-omop` (Category: `multi_table`, Model: `mistral-medium-latest`)

- **Domain / Scenario**: Clinical & Healthcare / Multi-Table Relational Schema
- **Source Tables**: 12 (111 columns)
- **Target Tables**: 39 (432 columns)
- **Ground Truth Pairs**: 124
- **True Positives**: 45
- **False Positives**: 48
- **False Negatives**: 79

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `care_site.care_site_id` | `EXTRA (FP)` | *(none)* | organizations.id |
| `care_site.care_site_name` | `MATCH (TP)` | organizations.name | organizations.name |
| `care_site.care_site_source_value` | `MATCH (TP)` | organizations.id | organizations.id |
| `care_site.location_id` | `UNMAPPED` | *(none)* | *(none)* |
| `care_site.place_of_service_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `care_site.place_of_service_source_value` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_etl_reference` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_holder` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_release_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_source_abbreviation` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_source_name` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_version` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_version_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_description` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_documentation_reference` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_release_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.vocabulary_version` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_definition_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_end_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_start_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.subject_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_description` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_name` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_syntax` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_initiation_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.definition_type_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.subject_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `concept.concept_class_id` | `UNMAPPED` | *(none)* | *(none)* |
| `concept.concept_code` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 432 target fields)*


### Dataset: `synthea-omop` (Category: `multi_table`, Model: `deepseek-v4.1-flash`)

- **Domain / Scenario**: Clinical & Healthcare / Multi-Table Relational Schema
- **Source Tables**: 12 (111 columns)
- **Target Tables**: 39 (432 columns)
- **Ground Truth Pairs**: 124
- **True Positives**: 53
- **False Positives**: 33
- **False Negatives**: 71

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `care_site.care_site_id` | `EXTRA (FP)` | *(none)* | organizations.id |
| `care_site.care_site_name` | `MATCH (TP)` | organizations.name | organizations.name |
| `care_site.care_site_source_value` | `MATCH (TP)` | organizations.id | organizations.id |
| `care_site.location_id` | `UNMAPPED` | *(none)* | *(none)* |
| `care_site.place_of_service_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `care_site.place_of_service_source_value` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_etl_reference` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_holder` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_release_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_source_abbreviation` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_source_name` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_version` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.cdm_version_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_description` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_documentation_reference` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.source_release_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cdm_source.vocabulary_version` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_definition_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_end_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.cohort_start_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort.subject_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_description` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_name` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_definition_syntax` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.cohort_initiation_date` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.definition_type_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `cohort_definition.subject_concept_id` | `UNMAPPED` | *(none)* | *(none)* |
| `concept.concept_class_id` | `UNMAPPED` | *(none)* | *(none)* |
| `concept.concept_code` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 432 target fields)*


### Dataset: `Musicians_unionable` (Category: `single_table`, Model: `gemini-3.8-flash`)

- **Domain / Scenario**: Wikidata / Real-World Web Graph
- **Source Tables**: 1 (20 columns)
- **Target Tables**: 1 (20 columns)
- **Ground Truth Pairs**: 20
- **True Positives**: 20
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `musicianID` | `MATCH (TP)` | musician | musician |
| `musicianName` | `MATCH (TP)` | musicianLabel | musicianLabel |
| `genderType` | `MATCH (TP)` | genderLabel | genderLabel |
| `birthDate` | `MATCH (TP)` | birthDate | birthDate |
| `city` | `MATCH (TP)` | cityLabel | cityLabel |
| `familyName` | `MATCH (TP)` | familyNameLabel | familyNameLabel |
| `forename` | `MATCH (TP)` | givenNameLabel | givenNameLabel |
| `fatherName` | `MATCH (TP)` | fatherLabel | fatherLabel |
| `motherName` | `MATCH (TP)` | motherLabel | motherLabel |
| `spouse` | `MATCH (TP)` | partner | partner |
| `NChildren` | `MATCH (TP)` | numberOfChildren | numberOfChildren |
| `kind` | `MATCH (TP)` | genreLabel | genreLabel |
| `webpage` | `MATCH (TP)` | websiteLabel | websiteLabel |
| `residence` | `MATCH (TP)` | residenceLabel | residenceLabel |
| `ethnicity` | `MATCH (TP)` | ethnicityLabel | ethnicityLabel |
| `religionLabel` | `MATCH (TP)` | religionLabel | religionLabel |
| `kickoff` | `MATCH (TP)` | activityStart | activityStart |
| `twitterUsername` | `MATCH (TP)` | twitterNameLabel | twitterNameLabel |
| `geniusNameLabel` | `MATCH (TP)` | geniusNameLabel | geniusNameLabel |
| `recordCompany` | `MATCH (TP)` | recordLabelLabel | recordLabelLabel |

### Dataset: `Musicians_unionable` (Category: `single_table`, Model: `gpt-5.6-sol`)

- **Domain / Scenario**: Wikidata / Real-World Web Graph
- **Source Tables**: 1 (20 columns)
- **Target Tables**: 1 (20 columns)
- **Ground Truth Pairs**: 20
- **True Positives**: 20
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `musicianID` | `MATCH (TP)` | musician | musician |
| `musicianName` | `MATCH (TP)` | musicianLabel | musicianLabel |
| `genderType` | `MATCH (TP)` | genderLabel | genderLabel |
| `birthDate` | `MATCH (TP)` | birthDate | birthDate |
| `city` | `MATCH (TP)` | cityLabel | cityLabel |
| `familyName` | `MATCH (TP)` | familyNameLabel | familyNameLabel |
| `forename` | `MATCH (TP)` | givenNameLabel | givenNameLabel |
| `fatherName` | `MATCH (TP)` | fatherLabel | fatherLabel |
| `motherName` | `MATCH (TP)` | motherLabel | motherLabel |
| `spouse` | `MATCH (TP)` | partner | partner |
| `NChildren` | `MATCH (TP)` | numberOfChildren | numberOfChildren |
| `kind` | `MATCH (TP)` | genreLabel | genreLabel |
| `webpage` | `MATCH (TP)` | websiteLabel | websiteLabel |
| `residence` | `MATCH (TP)` | residenceLabel | residenceLabel |
| `ethnicity` | `MATCH (TP)` | ethnicityLabel | ethnicityLabel |
| `religionLabel` | `MATCH (TP)` | religionLabel | religionLabel |
| `kickoff` | `MATCH (TP)` | activityStart | activityStart |
| `twitterUsername` | `MATCH (TP)` | twitterNameLabel | twitterNameLabel |
| `geniusNameLabel` | `MATCH (TP)` | geniusNameLabel | geniusNameLabel |
| `recordCompany` | `MATCH (TP)` | recordLabelLabel | recordLabelLabel |

### Dataset: `Musicians_unionable` (Category: `single_table`, Model: `mistral-medium-latest`)

- **Domain / Scenario**: Wikidata / Real-World Web Graph
- **Source Tables**: 1 (20 columns)
- **Target Tables**: 1 (20 columns)
- **Ground Truth Pairs**: 20
- **True Positives**: 20
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `musicianID` | `MATCH (TP)` | musician | musician |
| `musicianName` | `MATCH (TP)` | musicianLabel | musicianLabel |
| `genderType` | `MATCH (TP)` | genderLabel | genderLabel |
| `birthDate` | `MATCH (TP)` | birthDate | birthDate |
| `city` | `MATCH (TP)` | cityLabel | cityLabel |
| `familyName` | `MATCH (TP)` | familyNameLabel | familyNameLabel |
| `forename` | `MATCH (TP)` | givenNameLabel | givenNameLabel |
| `fatherName` | `MATCH (TP)` | fatherLabel | fatherLabel |
| `motherName` | `MATCH (TP)` | motherLabel | motherLabel |
| `spouse` | `MATCH (TP)` | partner | partner |
| `NChildren` | `MATCH (TP)` | numberOfChildren | numberOfChildren |
| `kind` | `MATCH (TP)` | genreLabel | genreLabel |
| `webpage` | `MATCH (TP)` | websiteLabel | websiteLabel |
| `residence` | `MATCH (TP)` | residenceLabel | residenceLabel |
| `ethnicity` | `MATCH (TP)` | ethnicityLabel | ethnicityLabel |
| `religionLabel` | `MATCH (TP)` | religionLabel | religionLabel |
| `kickoff` | `MATCH (TP)` | activityStart | activityStart |
| `twitterUsername` | `MATCH (TP)` | twitterNameLabel | twitterNameLabel |
| `geniusNameLabel` | `MATCH (TP)` | geniusNameLabel | geniusNameLabel |
| `recordCompany` | `MATCH (TP)` | recordLabelLabel | recordLabelLabel |

### Dataset: `Musicians_unionable` (Category: `single_table`, Model: `deepseek-v4.1-flash`)

- **Domain / Scenario**: Wikidata / Real-World Web Graph
- **Source Tables**: 1 (20 columns)
- **Target Tables**: 1 (20 columns)
- **Ground Truth Pairs**: 20
- **True Positives**: 20
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `musicianID` | `MATCH (TP)` | musician | musician |
| `musicianName` | `MATCH (TP)` | musicianLabel | musicianLabel |
| `genderType` | `MATCH (TP)` | genderLabel | genderLabel |
| `birthDate` | `MATCH (TP)` | birthDate | birthDate |
| `city` | `MATCH (TP)` | cityLabel | cityLabel |
| `familyName` | `MATCH (TP)` | familyNameLabel | familyNameLabel |
| `forename` | `MATCH (TP)` | givenNameLabel | givenNameLabel |
| `fatherName` | `MATCH (TP)` | fatherLabel | fatherLabel |
| `motherName` | `MATCH (TP)` | motherLabel | motherLabel |
| `spouse` | `MATCH (TP)` | partner | partner |
| `NChildren` | `MATCH (TP)` | numberOfChildren | numberOfChildren |
| `kind` | `MATCH (TP)` | genreLabel | genreLabel |
| `webpage` | `MATCH (TP)` | websiteLabel | websiteLabel |
| `residence` | `MATCH (TP)` | residenceLabel | residenceLabel |
| `ethnicity` | `MATCH (TP)` | ethnicityLabel | ethnicityLabel |
| `religionLabel` | `MATCH (TP)` | religionLabel | religionLabel |
| `kickoff` | `MATCH (TP)` | activityStart | activityStart |
| `twitterUsername` | `MATCH (TP)` | twitterNameLabel | twitterNameLabel |
| `geniusNameLabel` | `MATCH (TP)` | geniusNameLabel | geniusNameLabel |
| `recordCompany` | `MATCH (TP)` | recordLabelLabel | recordLabelLabel |

### Dataset: `assays_both_0_70_ac3_av` (Category: `single_table`, Model: `gemini-3.8-flash`)

- **Domain / Scenario**: ChEMBL / View-Unionable (Noise)
- **Source Tables**: 1 (19 columns)
- **Target Tables**: 1 (20 columns)
- **Ground Truth Pairs**: 16
- **True Positives**: 16
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `ss_d` | `MATCH (TP)` | assay_id | assay_id |
| `tss_d` | `MATCH (TP)` | tissue_id | tissue_id |
| `b_frmt` | `MATCH (TP)` | bao_format | bao_format |
| `vrnt_d` | `MATCH (TP)` | variant_id | variant_id |
| `rltnshp_tp` | `MATCH (TP)` | relationship_type | relationship_type |
| `crtd_b` | `MATCH (TP)` | curated_by | curated_by |
| `ss_strn` | `MATCH (TP)` | assay_strain | assay_strain |
| `ss_cll_tp` | `MATCH (TP)` | assay_cell_type | assay_cell_type |
| `cll_d` | `MATCH (TP)` | cell_id | cell_id |
| `src_d` | `MATCH (TP)` | src_id | src_id |
| `ss_tss` | `MATCH (TP)` | assay_tissue | assay_tissue |
| `td` | `MATCH (TP)` | tid | tid |
| `ss_tst_tp` | `MATCH (TP)` | assay_test_type | assay_test_type |
| `dc_d` | `MATCH (TP)` | doc_id | doc_id |
| `ss_sbclllr_frctn` | `MATCH (TP)` | assay_subcellular_fraction | assay_subcellular_fraction |
| `chmbl_d` | `MATCH (TP)` | chembl_id | chembl_id |
| `ss_rgnsm` | `UNMAPPED` | *(none)* | *(none)* |
| `ss_tx_d` | `UNMAPPED` | *(none)* | *(none)* |
| `cnfdnc_scr` | `UNMAPPED` | *(none)* | *(none)* |
| `src_ss_d` | `UNMAPPED` | *(none)* | *(none)* |

### Dataset: `assays_both_0_70_ac3_av` (Category: `single_table`, Model: `gpt-5.6-sol`)

- **Domain / Scenario**: ChEMBL / View-Unionable (Noise)
- **Source Tables**: 1 (19 columns)
- **Target Tables**: 1 (20 columns)
- **Ground Truth Pairs**: 16
- **True Positives**: 16
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `ss_d` | `MATCH (TP)` | assay_id | assay_id |
| `tss_d` | `MATCH (TP)` | tissue_id | tissue_id |
| `b_frmt` | `MATCH (TP)` | bao_format | bao_format |
| `vrnt_d` | `MATCH (TP)` | variant_id | variant_id |
| `rltnshp_tp` | `MATCH (TP)` | relationship_type | relationship_type |
| `crtd_b` | `MATCH (TP)` | curated_by | curated_by |
| `ss_strn` | `MATCH (TP)` | assay_strain | assay_strain |
| `ss_cll_tp` | `MATCH (TP)` | assay_cell_type | assay_cell_type |
| `cll_d` | `MATCH (TP)` | cell_id | cell_id |
| `src_d` | `MATCH (TP)` | src_id | src_id |
| `ss_tss` | `MATCH (TP)` | assay_tissue | assay_tissue |
| `td` | `MATCH (TP)` | tid | tid |
| `ss_tst_tp` | `MATCH (TP)` | assay_test_type | assay_test_type |
| `dc_d` | `MATCH (TP)` | doc_id | doc_id |
| `ss_sbclllr_frctn` | `MATCH (TP)` | assay_subcellular_fraction | assay_subcellular_fraction |
| `chmbl_d` | `MATCH (TP)` | chembl_id | chembl_id |
| `ss_rgnsm` | `UNMAPPED` | *(none)* | *(none)* |
| `ss_tx_d` | `UNMAPPED` | *(none)* | *(none)* |
| `cnfdnc_scr` | `UNMAPPED` | *(none)* | *(none)* |
| `src_ss_d` | `UNMAPPED` | *(none)* | *(none)* |

### Dataset: `assays_both_0_70_ac3_av` (Category: `single_table`, Model: `mistral-medium-latest`)

- **Domain / Scenario**: ChEMBL / View-Unionable (Noise)
- **Source Tables**: 1 (19 columns)
- **Target Tables**: 1 (20 columns)
- **Ground Truth Pairs**: 16
- **True Positives**: 16
- **False Positives**: 2
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `ss_d` | `MATCH (TP)` | assay_id | assay_id |
| `tss_d` | `MATCH (TP)` | tissue_id | tissue_id |
| `b_frmt` | `MATCH (TP)` | bao_format | bao_format |
| `vrnt_d` | `MATCH (TP)` | variant_id | variant_id |
| `rltnshp_tp` | `MATCH (TP)` | relationship_type | relationship_type |
| `crtd_b` | `MATCH (TP)` | curated_by | curated_by |
| `ss_strn` | `MATCH (TP)` | assay_strain | assay_strain |
| `ss_cll_tp` | `MATCH (TP)` | assay_cell_type | assay_cell_type |
| `cll_d` | `MATCH (TP)` | cell_id | cell_id |
| `src_d` | `MATCH (TP)` | src_id | src_id |
| `ss_tss` | `MATCH (TP)` | assay_tissue | assay_tissue |
| `td` | `MATCH (TP)` | tid | tid |
| `ss_tst_tp` | `MATCH (TP)` | assay_test_type | assay_test_type |
| `dc_d` | `MATCH (TP)` | doc_id | doc_id |
| `ss_sbclllr_frctn` | `MATCH (TP)` | assay_subcellular_fraction | assay_subcellular_fraction |
| `chmbl_d` | `MATCH (TP)` | chembl_id | chembl_id |
| `ss_rgnsm` | `EXTRA (FP)` | *(none)* | description |
| `ss_tx_d` | `EXTRA (FP)` | *(none)* | assay_type |
| `cnfdnc_scr` | `UNMAPPED` | *(none)* | *(none)* |
| `src_ss_d` | `UNMAPPED` | *(none)* | *(none)* |

### Dataset: `assays_both_0_70_ac3_av` (Category: `single_table`, Model: `deepseek-v4.1-flash`)

- **Domain / Scenario**: ChEMBL / View-Unionable (Noise)
- **Source Tables**: 1 (19 columns)
- **Target Tables**: 1 (20 columns)
- **Ground Truth Pairs**: 16
- **True Positives**: 16
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `ss_d` | `MATCH (TP)` | assay_id | assay_id |
| `tss_d` | `MATCH (TP)` | tissue_id | tissue_id |
| `b_frmt` | `MATCH (TP)` | bao_format | bao_format |
| `vrnt_d` | `MATCH (TP)` | variant_id | variant_id |
| `rltnshp_tp` | `MATCH (TP)` | relationship_type | relationship_type |
| `crtd_b` | `MATCH (TP)` | curated_by | curated_by |
| `ss_strn` | `MATCH (TP)` | assay_strain | assay_strain |
| `ss_cll_tp` | `MATCH (TP)` | assay_cell_type | assay_cell_type |
| `cll_d` | `MATCH (TP)` | cell_id | cell_id |
| `src_d` | `MATCH (TP)` | src_id | src_id |
| `ss_tss` | `MATCH (TP)` | assay_tissue | assay_tissue |
| `td` | `MATCH (TP)` | tid | tid |
| `ss_tst_tp` | `MATCH (TP)` | assay_test_type | assay_test_type |
| `dc_d` | `MATCH (TP)` | doc_id | doc_id |
| `ss_sbclllr_frctn` | `MATCH (TP)` | assay_subcellular_fraction | assay_subcellular_fraction |
| `chmbl_d` | `MATCH (TP)` | chembl_id | chembl_id |
| `ss_rgnsm` | `UNMAPPED` | *(none)* | *(none)* |
| `ss_tx_d` | `UNMAPPED` | *(none)* | *(none)* |
| `cnfdnc_scr` | `UNMAPPED` | *(none)* | *(none)* |
| `src_ss_d` | `UNMAPPED` | *(none)* | *(none)* |

### Dataset: `miller2_both_50_50_ac5_av` (Category: `single_table`, Model: `gemini-3.8-flash`)

- **Domain / Scenario**: OpenData / Semantically-Joinable (Full Noise)
- **Source Tables**: 1 (38 columns)
- **Target Tables**: 1 (38 columns)
- **Ground Truth Pairs**: 25
- **True Positives**: 25
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `miller2_fsclr` | `MATCH (TP)` | Fiscal year | Fiscal year |
| `miller2_stts` | `MATCH (TP)` | Status | Status |
| `miller2_clmtchngdpttn(mrkr)` | `MATCH (TP)` | Climate change adaptation (marker) | Climate change adaptation (marker) |
| `miller2_rgnlprgrm(mrkr)` | `MATCH (TP)` | Regional program (marker) | Regional program (marker) |
| `miller2_dvsnd` | `MATCH (TP)` | Division ID | Division ID |
| `miller2_prtcptrdvlpmntndgdgvrnnc` | `MATCH (TP)` | Participatory development and good governance | Participatory development and good governance |
| `miller2_nvrmntlsstnblt(mrkr)` | `MATCH (TP)` | Enviromental sustainability (marker) | Enviromental sustainability (marker) |
| `miller2_bdvrst(mrkr)` | `MATCH (TP)` | Biodiversity (marker) | Biodiversity (marker) |
| `miller2_cntnntnm` | `MATCH (TP)` | Continent name | Continent name |
| `miller2_clmtchngmtgtn(mrkr)` | `MATCH (TP)` | Climate change mitigation (marker) | Climate change mitigation (marker) |
| `miller2_brnchnm` | `MATCH (TP)` | Branch name | Branch name |
| `miller2_rgnstnsb-clss` | `MATCH (TP)` | Organisation sub-class | Organisation sub-class |
| `miller2_chldrnsss(mrkr)` | `MATCH (TP)` | Children issues (marker) | Children issues (marker) |
| `miller2_trddvlpmnt(mrkr)` | `MATCH (TP)` | Trade development (marker) | Trade development (marker) |
| `miller2_knwldgfrdvlpmnt(mrkr)` | `MATCH (TP)` | Knowledge for development (marker) | Knowledge for development (marker) |
| `miller2_mxmmcdcntrbtn(prjct-lvl)` | `MATCH (TP)` | Maximum CIDA contribution (project-level) | Maximum CIDA contribution (project-level) |
| `miller2_pbtp` | `MATCH (TP)` | PBA type | PBA type |
| `miller2_fndcntrnm` | `MATCH (TP)` | Fund centre name | Fund centre name |
| `miller2_prjctnmbr` | `MATCH (TP)` | Project number | Project number |
| `miller2_cdbsnssdlvrmdl(ld)` | `MATCH (TP)` | CIDA business delivery model (old) | CIDA business delivery model (old) |
| `miller2_cfl(mrkr)` | `MATCH (TP)` | CFLI (marker) | CFLI (marker) |
| `miller2_prgrmmngprcss(nw)` | `MATCH (TP)` | Programming process (new) | Programming process (new) |
| `miller2_ntdmnt(prjct-lvlbdgt)` | `MATCH (TP)` | Untied amount(Project-level budget) | Untied amount(Project-level budget) |
| `miller2_sctrd` | `MATCH (TP)` | Sector ID | Sector ID |
| `miller2_brnchd` | `MATCH (TP)` | Branch ID | Branch ID |
| `miller2_gndrqlt(mrkr)` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnd` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnnm` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstntp` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnclss` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 38 target fields)*


### Dataset: `miller2_both_50_50_ac5_av` (Category: `single_table`, Model: `gpt-5.6-sol`)

- **Domain / Scenario**: OpenData / Semantically-Joinable (Full Noise)
- **Source Tables**: 1 (38 columns)
- **Target Tables**: 1 (38 columns)
- **Ground Truth Pairs**: 25
- **True Positives**: 25
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `miller2_fsclr` | `MATCH (TP)` | Fiscal year | Fiscal year |
| `miller2_stts` | `MATCH (TP)` | Status | Status |
| `miller2_clmtchngdpttn(mrkr)` | `MATCH (TP)` | Climate change adaptation (marker) | Climate change adaptation (marker) |
| `miller2_rgnlprgrm(mrkr)` | `MATCH (TP)` | Regional program (marker) | Regional program (marker) |
| `miller2_dvsnd` | `MATCH (TP)` | Division ID | Division ID |
| `miller2_prtcptrdvlpmntndgdgvrnnc` | `MATCH (TP)` | Participatory development and good governance | Participatory development and good governance |
| `miller2_nvrmntlsstnblt(mrkr)` | `MATCH (TP)` | Enviromental sustainability (marker) | Enviromental sustainability (marker) |
| `miller2_bdvrst(mrkr)` | `MATCH (TP)` | Biodiversity (marker) | Biodiversity (marker) |
| `miller2_cntnntnm` | `MATCH (TP)` | Continent name | Continent name |
| `miller2_clmtchngmtgtn(mrkr)` | `MATCH (TP)` | Climate change mitigation (marker) | Climate change mitigation (marker) |
| `miller2_brnchnm` | `MATCH (TP)` | Branch name | Branch name |
| `miller2_rgnstnsb-clss` | `MATCH (TP)` | Organisation sub-class | Organisation sub-class |
| `miller2_chldrnsss(mrkr)` | `MATCH (TP)` | Children issues (marker) | Children issues (marker) |
| `miller2_trddvlpmnt(mrkr)` | `MATCH (TP)` | Trade development (marker) | Trade development (marker) |
| `miller2_knwldgfrdvlpmnt(mrkr)` | `MATCH (TP)` | Knowledge for development (marker) | Knowledge for development (marker) |
| `miller2_mxmmcdcntrbtn(prjct-lvl)` | `MATCH (TP)` | Maximum CIDA contribution (project-level) | Maximum CIDA contribution (project-level) |
| `miller2_pbtp` | `MATCH (TP)` | PBA type | PBA type |
| `miller2_fndcntrnm` | `MATCH (TP)` | Fund centre name | Fund centre name |
| `miller2_prjctnmbr` | `MATCH (TP)` | Project number | Project number |
| `miller2_cdbsnssdlvrmdl(ld)` | `MATCH (TP)` | CIDA business delivery model (old) | CIDA business delivery model (old) |
| `miller2_cfl(mrkr)` | `MATCH (TP)` | CFLI (marker) | CFLI (marker) |
| `miller2_prgrmmngprcss(nw)` | `MATCH (TP)` | Programming process (new) | Programming process (new) |
| `miller2_ntdmnt(prjct-lvlbdgt)` | `MATCH (TP)` | Untied amount(Project-level budget) | Untied amount(Project-level budget) |
| `miller2_sctrd` | `MATCH (TP)` | Sector ID | Sector ID |
| `miller2_brnchd` | `MATCH (TP)` | Branch ID | Branch ID |
| `miller2_gndrqlt(mrkr)` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnd` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnnm` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstntp` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnclss` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 38 target fields)*


### Dataset: `miller2_both_50_50_ac5_av` (Category: `single_table`, Model: `mistral-medium-latest`)

- **Domain / Scenario**: OpenData / Semantically-Joinable (Full Noise)
- **Source Tables**: 1 (38 columns)
- **Target Tables**: 1 (38 columns)
- **Ground Truth Pairs**: 25
- **True Positives**: 25
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `miller2_fsclr` | `MATCH (TP)` | Fiscal year | Fiscal year |
| `miller2_stts` | `MATCH (TP)` | Status | Status |
| `miller2_clmtchngdpttn(mrkr)` | `MATCH (TP)` | Climate change adaptation (marker) | Climate change adaptation (marker) |
| `miller2_rgnlprgrm(mrkr)` | `MATCH (TP)` | Regional program (marker) | Regional program (marker) |
| `miller2_dvsnd` | `MATCH (TP)` | Division ID | Division ID |
| `miller2_prtcptrdvlpmntndgdgvrnnc` | `MATCH (TP)` | Participatory development and good governance | Participatory development and good governance |
| `miller2_nvrmntlsstnblt(mrkr)` | `MATCH (TP)` | Enviromental sustainability (marker) | Enviromental sustainability (marker) |
| `miller2_bdvrst(mrkr)` | `MATCH (TP)` | Biodiversity (marker) | Biodiversity (marker) |
| `miller2_cntnntnm` | `MATCH (TP)` | Continent name | Continent name |
| `miller2_clmtchngmtgtn(mrkr)` | `MATCH (TP)` | Climate change mitigation (marker) | Climate change mitigation (marker) |
| `miller2_brnchnm` | `MATCH (TP)` | Branch name | Branch name |
| `miller2_rgnstnsb-clss` | `MATCH (TP)` | Organisation sub-class | Organisation sub-class |
| `miller2_chldrnsss(mrkr)` | `MATCH (TP)` | Children issues (marker) | Children issues (marker) |
| `miller2_trddvlpmnt(mrkr)` | `MATCH (TP)` | Trade development (marker) | Trade development (marker) |
| `miller2_knwldgfrdvlpmnt(mrkr)` | `MATCH (TP)` | Knowledge for development (marker) | Knowledge for development (marker) |
| `miller2_mxmmcdcntrbtn(prjct-lvl)` | `MATCH (TP)` | Maximum CIDA contribution (project-level) | Maximum CIDA contribution (project-level) |
| `miller2_pbtp` | `MATCH (TP)` | PBA type | PBA type |
| `miller2_fndcntrnm` | `MATCH (TP)` | Fund centre name | Fund centre name |
| `miller2_prjctnmbr` | `MATCH (TP)` | Project number | Project number |
| `miller2_cdbsnssdlvrmdl(ld)` | `MATCH (TP)` | CIDA business delivery model (old) | CIDA business delivery model (old) |
| `miller2_cfl(mrkr)` | `MATCH (TP)` | CFLI (marker) | CFLI (marker) |
| `miller2_prgrmmngprcss(nw)` | `MATCH (TP)` | Programming process (new) | Programming process (new) |
| `miller2_ntdmnt(prjct-lvlbdgt)` | `MATCH (TP)` | Untied amount(Project-level budget) | Untied amount(Project-level budget) |
| `miller2_sctrd` | `MATCH (TP)` | Sector ID | Sector ID |
| `miller2_brnchd` | `MATCH (TP)` | Branch ID | Branch ID |
| `miller2_gndrqlt(mrkr)` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnd` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnnm` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstntp` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnclss` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 38 target fields)*


### Dataset: `miller2_both_50_50_ac5_av` (Category: `single_table`, Model: `deepseek-v4.1-flash`)

- **Domain / Scenario**: OpenData / Semantically-Joinable (Full Noise)
- **Source Tables**: 1 (38 columns)
- **Target Tables**: 1 (38 columns)
- **Ground Truth Pairs**: 25
- **True Positives**: 25
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `miller2_fsclr` | `MATCH (TP)` | Fiscal year | Fiscal year |
| `miller2_stts` | `MATCH (TP)` | Status | Status |
| `miller2_clmtchngdpttn(mrkr)` | `MATCH (TP)` | Climate change adaptation (marker) | Climate change adaptation (marker) |
| `miller2_rgnlprgrm(mrkr)` | `MATCH (TP)` | Regional program (marker) | Regional program (marker) |
| `miller2_dvsnd` | `MATCH (TP)` | Division ID | Division ID |
| `miller2_prtcptrdvlpmntndgdgvrnnc` | `MATCH (TP)` | Participatory development and good governance | Participatory development and good governance |
| `miller2_nvrmntlsstnblt(mrkr)` | `MATCH (TP)` | Enviromental sustainability (marker) | Enviromental sustainability (marker) |
| `miller2_bdvrst(mrkr)` | `MATCH (TP)` | Biodiversity (marker) | Biodiversity (marker) |
| `miller2_cntnntnm` | `MATCH (TP)` | Continent name | Continent name |
| `miller2_clmtchngmtgtn(mrkr)` | `MATCH (TP)` | Climate change mitigation (marker) | Climate change mitigation (marker) |
| `miller2_brnchnm` | `MATCH (TP)` | Branch name | Branch name |
| `miller2_rgnstnsb-clss` | `MATCH (TP)` | Organisation sub-class | Organisation sub-class |
| `miller2_chldrnsss(mrkr)` | `MATCH (TP)` | Children issues (marker) | Children issues (marker) |
| `miller2_trddvlpmnt(mrkr)` | `MATCH (TP)` | Trade development (marker) | Trade development (marker) |
| `miller2_knwldgfrdvlpmnt(mrkr)` | `MATCH (TP)` | Knowledge for development (marker) | Knowledge for development (marker) |
| `miller2_mxmmcdcntrbtn(prjct-lvl)` | `MATCH (TP)` | Maximum CIDA contribution (project-level) | Maximum CIDA contribution (project-level) |
| `miller2_pbtp` | `MATCH (TP)` | PBA type | PBA type |
| `miller2_fndcntrnm` | `MATCH (TP)` | Fund centre name | Fund centre name |
| `miller2_prjctnmbr` | `MATCH (TP)` | Project number | Project number |
| `miller2_cdbsnssdlvrmdl(ld)` | `MATCH (TP)` | CIDA business delivery model (old) | CIDA business delivery model (old) |
| `miller2_cfl(mrkr)` | `MATCH (TP)` | CFLI (marker) | CFLI (marker) |
| `miller2_prgrmmngprcss(nw)` | `MATCH (TP)` | Programming process (new) | Programming process (new) |
| `miller2_ntdmnt(prjct-lvlbdgt)` | `MATCH (TP)` | Untied amount(Project-level budget) | Untied amount(Project-level budget) |
| `miller2_sctrd` | `MATCH (TP)` | Sector ID | Sector ID |
| `miller2_brnchd` | `MATCH (TP)` | Branch ID | Branch ID |
| `miller2_gndrqlt(mrkr)` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnd` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnnm` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstntp` | `UNMAPPED` | *(none)* | *(none)* |
| `miller2_rgnstnclss` | `UNMAPPED` | *(none)* | *(none)* |

*(Showing first 30 of 38 target fields)*


### Dataset: `prospect_both_50_50_ac5_av` (Category: `single_table`, Model: `gemini-3.8-flash`)

- **Domain / Scenario**: TPC-DI / Semantically-Joinable (Full Noise)
- **Source Tables**: 1 (16 columns)
- **Target Tables**: 1 (17 columns)
- **Ground Truth Pairs**: 11
- **True Positives**: 11
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `prospect_gncd` | `MATCH (TP)` | AgencyID | AgencyID |
| `prospect_ddrssln2` | `MATCH (TP)` | AddressLine2 | AddressLine2 |
| `prospect_ct` | `MATCH (TP)` | City | City |
| `prospect_nmbrcrs` | `MATCH (TP)` | NumberCars | NumberCars |
| `prospect_pstlcd` | `MATCH (TP)` | PostalCode | PostalCode |
| `prospect_mddlntl` | `MATCH (TP)` | MiddleInitial | MiddleInitial |
| `prospect_nmbrcrdtcrds` | `MATCH (TP)` | NumberCreditCards | NumberCreditCards |
| `prospect_ddrssln1` | `MATCH (TP)` | AddressLine1 | AddressLine1 |
| `prospect_frstnm` | `MATCH (TP)` | FirstName | FirstName |
| `prospect_g` | `MATCH (TP)` | Age | Age |
| `prospect_cntr` | `MATCH (TP)` | Country | Country |
| `prospect_nmbrchldrn` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_mrtlstts` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_crdtrtng` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_wnrrntflg` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_mplr` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_ntwrth` | `UNMAPPED` | *(none)* | *(none)* |

### Dataset: `prospect_both_50_50_ac5_av` (Category: `single_table`, Model: `gpt-5.6-sol`)

- **Domain / Scenario**: TPC-DI / Semantically-Joinable (Full Noise)
- **Source Tables**: 1 (16 columns)
- **Target Tables**: 1 (17 columns)
- **Ground Truth Pairs**: 11
- **True Positives**: 11
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `prospect_gncd` | `MATCH (TP)` | AgencyID | AgencyID |
| `prospect_ddrssln2` | `MATCH (TP)` | AddressLine2 | AddressLine2 |
| `prospect_ct` | `MATCH (TP)` | City | City |
| `prospect_nmbrcrs` | `MATCH (TP)` | NumberCars | NumberCars |
| `prospect_pstlcd` | `MATCH (TP)` | PostalCode | PostalCode |
| `prospect_mddlntl` | `MATCH (TP)` | MiddleInitial | MiddleInitial |
| `prospect_nmbrcrdtcrds` | `MATCH (TP)` | NumberCreditCards | NumberCreditCards |
| `prospect_ddrssln1` | `MATCH (TP)` | AddressLine1 | AddressLine1 |
| `prospect_frstnm` | `MATCH (TP)` | FirstName | FirstName |
| `prospect_g` | `MATCH (TP)` | Age | Age |
| `prospect_cntr` | `MATCH (TP)` | Country | Country |
| `prospect_nmbrchldrn` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_mrtlstts` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_crdtrtng` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_wnrrntflg` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_mplr` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_ntwrth` | `UNMAPPED` | *(none)* | *(none)* |

### Dataset: `prospect_both_50_50_ac5_av` (Category: `single_table`, Model: `mistral-medium-latest`)

- **Domain / Scenario**: TPC-DI / Semantically-Joinable (Full Noise)
- **Source Tables**: 1 (16 columns)
- **Target Tables**: 1 (17 columns)
- **Ground Truth Pairs**: 11
- **True Positives**: 10
- **False Positives**: 2
- **False Negatives**: 1

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `prospect_gncd` | `MATCH (TP)` | AgencyID | AgencyID |
| `prospect_ddrssln2` | `MATCH (TP)` | AddressLine2 | AddressLine2 |
| `prospect_ct` | `MATCH (TP)` | City | City |
| `prospect_nmbrcrs` | `MATCH (TP)` | NumberCars | NumberCars |
| `prospect_pstlcd` | `MATCH (TP)` | PostalCode | PostalCode |
| `prospect_mddlntl` | `MATCH (TP)` | MiddleInitial | MiddleInitial |
| `prospect_nmbrcrdtcrds` | `MATCH (TP)` | NumberCreditCards | NumberCreditCards |
| `prospect_ddrssln1` | `MATCH (TP)` | AddressLine1 | AddressLine1 |
| `prospect_frstnm` | `MATCH (TP)` | FirstName | FirstName |
| `prospect_g` | `MISMATCH (FP)` | Age | Gender |
| `prospect_cntr` | `MATCH (TP)` | Country | Country |
| `prospect_nmbrchldrn` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_mrtlstts` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_crdtrtng` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_wnrrntflg` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_mplr` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_ntwrth` | `EXTRA (FP)` | *(none)* | Income |

### Dataset: `prospect_both_50_50_ac5_av` (Category: `single_table`, Model: `deepseek-v4.1-flash`)

- **Domain / Scenario**: TPC-DI / Semantically-Joinable (Full Noise)
- **Source Tables**: 1 (16 columns)
- **Target Tables**: 1 (17 columns)
- **Ground Truth Pairs**: 11
- **True Positives**: 11
- **False Positives**: 0
- **False Negatives**: 0

#### Target Field Inspection Summary

| Target Column | Status | Expected Source | Predicted Source |
|---|:---:|---|---|
| `prospect_gncd` | `MATCH (TP)` | AgencyID | AgencyID |
| `prospect_ddrssln2` | `MATCH (TP)` | AddressLine2 | AddressLine2 |
| `prospect_ct` | `MATCH (TP)` | City | City |
| `prospect_nmbrcrs` | `MATCH (TP)` | NumberCars | NumberCars |
| `prospect_pstlcd` | `MATCH (TP)` | PostalCode | PostalCode |
| `prospect_mddlntl` | `MATCH (TP)` | MiddleInitial | MiddleInitial |
| `prospect_nmbrcrdtcrds` | `MATCH (TP)` | NumberCreditCards | NumberCreditCards |
| `prospect_ddrssln1` | `MATCH (TP)` | AddressLine1 | AddressLine1 |
| `prospect_frstnm` | `MATCH (TP)` | FirstName | FirstName |
| `prospect_g` | `MATCH (TP)` | Age | Age |
| `prospect_cntr` | `MATCH (TP)` | Country | Country |
| `prospect_nmbrchldrn` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_mrtlstts` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_crdtrtng` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_wnrrntflg` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_mplr` | `UNMAPPED` | *(none)* | *(none)* |
| `prospect_ntwrth` | `UNMAPPED` | *(none)* | *(none)* |
