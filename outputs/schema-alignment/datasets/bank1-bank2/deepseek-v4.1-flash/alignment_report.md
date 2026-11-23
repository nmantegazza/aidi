# Schema Alignment Diagnostic Report — bank1-bank2

## Summary Results



## Detailed Analysis

# Schema Alignment Diagnostic Report — bank1-bank2

- **Model**: `deepseek-v4.1-flash`
- **Domain**: Financial & Banking
- **Status**: `SUCCESS (3/3)`
- **Iterations**: `3`
- **Source A**: `bank1` (9 tables, 27 cols)
- **Source B**: `bank2` (9 tables, 36 cols)

## Schema Architectures (ER Diagrams)

### Source A Schema (`bank1`)

```mermaid
erDiagram
    bank {
        string code PK
        string name
        string address
    }
    branch {
        integer branch_id PK
        string name
        string address
        string bank_code FK
    }
    loan {
        integer loan_id PK
        string loan_type
        number amount
        integer branch_id FK
    }
    customer {
        integer custid PK
        string name
        string phone
        string address
    }
    account {
        integer account_no PK
        string acc_type
        number balance
        integer branch_id FK
    }
    offer {
        integer branch_id PK,FK
        integer loan_id PK,FK
    }
    maintain {
        integer branch_id PK,FK
        integer account_no PK,FK
    }
    availed_by {
        integer custid PK,FK
        integer loan_id PK,FK
    }
    hold_by {
        integer custid PK,FK
        integer account_no PK,FK
    }
    branch }o--|| bank : "bank_code"
    branch }o--|| bank : "Bank_Code"
    loan }o--|| branch : "branch_id"
    loan }o--|| branch : "Branch_id"
    account }o--|| branch : "branch_id"
    account }o--|| branch : "Branch_id"
    offer }o--|| branch : "branch_id"
    offer }o--|| loan : "loan_id"
    offer }o--|| branch : "Branch_id"
    offer }o--|| loan : "Loan_id"
    maintain }o--|| branch : "branch_id"
    maintain }o--|| account : "account_no"
    maintain }o--|| branch : "Branch_id"
    maintain }o--|| account : "Account_No"
    availed_by }o--|| customer : "custid"
    availed_by }o--|| loan : "loan_id"
    availed_by }o--|| customer : "Custid"
    availed_by }o--|| loan : "Loan_id"
    hold_by }o--|| customer : "custid"
    hold_by }o--|| account : "account_no"
    hold_by }o--|| customer : "Custid"
    hold_by }o--|| account : "Account_No"
```

### Source B Schema (`bank2`)

```mermaid
erDiagram
    branch {
        integer branch_id PK
        string branch_name
        integer assets
        string branch_address
    }
    banker_info {
        integer banker_id PK
        string banker_name
        integer branch_id FK
    }
    account {
        integer account_id PK
        string account_type
        integer account_balance
        integer branch_id FK
    }
    transaction {
        integer transaction_id PK
        integer amount
        integer customer_id FK
        integer account_id FK
    }
    customer {
        integer customer_id PK
        string customer_name
        string mobileno
        date dob
        integer account_id FK
    }
    customer_credit_card {
        integer credit_card_id PK
        date expiry_date
        integer card_limit
        integer customer_id FK
        integer account_id FK
    }
    loan {
        integer loan_id PK
        integer issued_amount
        integer remaining_amount
        integer branch_id FK
        integer account_id FK
    }
    loan_payment {
        integer loan_payment_id PK
        integer amount
        integer loan_id FK
    }
    borrower {
        integer borrower_id PK
        integer customer_id FK
        integer loan_id FK
    }
    banker_info }o--|| branch : "branch_id"
    banker_info }o--|| branch : "branch_id"
    account }o--|| branch : "branch_id"
    account }o--|| branch : "branch_id"
    transaction }o--|| customer : "customer_id"
    transaction }o--|| account : "account_id"
    transaction }o--|| customer : "customer_id"
    transaction }o--|| account : "account_id"
    customer }o--|| account : "account_id"
    customer }o--|| account : "account_id"
    customer_credit_card }o--|| customer : "customer_id"
    customer_credit_card }o--|| account : "account_id"
    customer_credit_card }o--|| customer : "customer_id"
    customer_credit_card }o--|| account : "account_id"
    loan }o--|| branch : "branch_id"
    loan }o--|| account : "account_id"
    loan }o--|| branch : "branch_id"
    loan }o--|| account : "account_id"
    loan_payment }o--|| loan : "loan_id"
    loan_payment }o--|| loan : "loan_id"
    borrower }o--|| loan : "loan_id"
    borrower }o--|| customer : "customer_id"
    borrower }o--|| loan : "loan_id"
    borrower }o--|| customer : "customer_id"
```

### Generated Unified Target Schemas per Iteration

> [!NOTE]
> Use the toggles below to view the target schema ER diagram generated in each iteration. The representative run is expanded by default.

<details>
<summary><b>Iteration 1 Target Schema (13 tables, S_rel: 0.9565)</b></summary>

```mermaid
erDiagram
    bank {
        string bank_code PK "Unique bank identifier"
        string bank_name "Bank name"
        string address "Bank head-office address"
    }
    branch {
        integer branch_id PK "Unique branch identifier"
        string branch_name "Branch name"
        string address "Branch address"
        number assets "Branch total assets (monetary amount)"
        string bank_code FK "Owning bank reference"
    }
    customer {
        integer customer_id PK "Unique customer identifier"
        string customer_name "Customer full name"
        string phone "Customer mobile phone number"
        string address "Customer address"
        date dob "Customer date of birth"
    }
    account {
        integer account_id PK "Unique account identifier"
        string account_type "Account category (e.g. savings, current)"
        number balance "Current account balance (monetary amo..."
        integer branch_id FK "Owning branch reference"
    }
    loan {
        integer loan_id PK "Unique loan identifier"
        string loan_type "Loan category"
        number issued_amount "Principal loan amount originally issu..."
        number remaining_amount "Outstanding loan amount (monetary amo..."
        integer branch_id FK "Originating branch reference"
        integer account_id FK "Disbursement account reference"
    }
    banker_info {
        integer banker_id PK "Unique banker/staff identifier"
        string banker_name "Banker name"
        integer branch_id FK "Assigned branch reference"
    }
    transaction {
        integer transaction_id PK "Unique transaction identifier"
        number amount "Transaction amount (monetary amount)"
        integer customer_id FK "Initiating customer reference"
        integer account_id FK "Affected account reference"
    }
    loan_payment {
        integer loan_payment_id PK "Unique loan payment identifier"
        number amount "Payment amount (monetary amount)"
        integer loan_id FK "Repaid loan reference"
    }
    customer_credit_card {
        integer credit_card_id PK "Unique credit card identifier"
        date expiry_date "Card expiry date"
        number card_limit "Card credit limit (monetary amount)"
        integer customer_id FK "Cardholder customer reference"
        integer account_id FK "Linked account reference"
    }
    customer_loan {
        integer customer_id PK,FK "Customer holding/availing the loan"
        integer loan_id PK,FK "Loan availed by the customer"
        integer borrower_id "Source-specific surrogate borrower id..."
    }
    branch_loan {
        integer branch_id PK,FK "Branch offering the loan"
        integer loan_id PK,FK "Loan offered by the branch"
    }
    branch_account {
        integer branch_id PK,FK "Maintaining branch"
        integer account_id PK,FK "Account maintained by the branch"
    }
    customer_account {
        integer customer_id PK,FK "Account holder customer"
        integer account_id PK,FK "Account held by the customer"
    }
    branch }o--|| bank : "bank_code"
    account }o--|| branch : "branch_id"
    loan }o--|| branch : "branch_id"
    loan }o--|| account : "account_id"
    banker_info }o--|| branch : "branch_id"
    transaction }o--|| customer : "customer_id"
    transaction }o--|| account : "account_id"
    loan_payment }o--|| loan : "loan_id"
    customer_credit_card }o--|| customer : "customer_id"
    customer_credit_card }o--|| account : "account_id"
    customer_loan }o--|| customer : "customer_id"
    customer_loan }o--|| loan : "loan_id"
    branch_loan }o--|| branch : "branch_id"
    branch_loan }o--|| loan : "loan_id"
    branch_account }o--|| branch : "branch_id"
    branch_account }o--|| account : "account_id"
    customer_account }o--|| customer : "customer_id"
    customer_account }o--|| account : "account_id"
```
</details>

<details>
<summary><b>Iteration 2 Target Schema (13 tables, S_rel: 1.0000)</b></summary>

```mermaid
erDiagram
    bank {
        string bank_code PK
        string name
        string address
    }
    branch {
        integer branch_id PK
        string name
        string address
        integer assets
        string bank_code FK
    }
    banker {
        integer banker_id PK
        string name
        integer branch_id FK
    }
    customer {
        integer customer_id PK
        string name
        string phone
        string address
        date dob
    }
    account {
        integer account_id PK
        string account_type
        number balance
        integer branch_id FK
    }
    loan {
        integer loan_id PK
        string loan_type
        number amount
        number issued_amount
        number remaining_amount
        integer branch_id FK
        integer account_id FK
    }
    customer_credit_card {
        integer credit_card_id PK
        date expiry_date
        number card_limit
        integer customer_id FK
        integer account_id FK
    }
    transaction {
        integer transaction_id PK
        number amount
        integer customer_id FK
        integer account_id FK
    }
    loan_payment {
        integer loan_payment_id PK
        number amount
        integer loan_id FK
    }
    offer {
        integer branch_id PK,FK
        integer loan_id PK,FK
    }
    maintain {
        integer branch_id PK,FK
        integer account_id PK,FK
    }
    customer_loan {
        integer customer_id PK,FK
        integer loan_id PK,FK
    }
    customer_account {
        integer customer_id PK,FK
        integer account_id PK,FK
    }
    branch }o--|| bank : "bank_code"
    banker }o--|| branch : "branch_id"
    account }o--|| branch : "branch_id"
    loan }o--|| branch : "branch_id"
    loan }o--|| account : "account_id"
    customer_credit_card }o--|| customer : "customer_id"
    customer_credit_card }o--|| account : "account_id"
    transaction }o--|| customer : "customer_id"
    transaction }o--|| account : "account_id"
    loan_payment }o--|| loan : "loan_id"
    offer }o--|| branch : "branch_id"
    offer }o--|| loan : "loan_id"
    maintain }o--|| branch : "branch_id"
    maintain }o--|| account : "account_id"
    customer_loan }o--|| customer : "customer_id"
    customer_loan }o--|| loan : "loan_id"
    customer_account }o--|| customer : "customer_id"
    customer_account }o--|| account : "account_id"
```
</details>

<details open>
<summary><b>Iteration 3 Target Schema (13 tables, S_rel: 1.0000) [Representative / Final Run]</b></summary>

```mermaid
erDiagram
    bank {
        string bank_code PK
        string name
        string address
    }
    branch {
        integer branch_id PK
        string name
        string address
        integer assets
        string bank_code FK
    }
    customer {
        integer customer_id PK
        string name
        string phone
        string address
        date dob
    }
    account {
        integer account_id PK
        string account_type
        number balance
        integer branch_id FK
    }
    loan {
        integer loan_id PK
        string loan_type
        number issued_amount
        number remaining_amount
        integer branch_id FK
        integer account_id FK
    }
    loan_payment {
        integer loan_payment_id PK
        number amount
        integer loan_id FK
    }
    transaction {
        integer transaction_id PK
        number amount
        integer customer_id FK
        integer account_id FK
    }
    credit_card {
        integer credit_card_id PK
        date expiry_date
        number card_limit
        integer customer_id FK
        integer account_id FK
    }
    banker {
        integer banker_id PK
        string name
        integer branch_id FK
    }
    customer_account {
        integer customer_id PK,FK
        integer account_id PK,FK
    }
    customer_loan {
        integer customer_id PK,FK
        integer loan_id PK,FK
    }
    branch_loan {
        integer branch_id PK,FK
        integer loan_id PK,FK
    }
    branch_account {
        integer branch_id PK,FK
        integer account_id PK,FK
    }
    branch }o--|| bank : "bank_code"
    account }o--|| branch : "branch_id"
    loan }o--|| branch : "branch_id"
    loan }o--|| account : "account_id"
    loan_payment }o--|| loan : "loan_id"
    transaction }o--|| customer : "customer_id"
    transaction }o--|| account : "account_id"
    credit_card }o--|| customer : "customer_id"
    credit_card }o--|| account : "account_id"
    banker }o--|| branch : "branch_id"
    customer_account }o--|| customer : "customer_id"
    customer_account }o--|| account : "account_id"
    customer_loan }o--|| customer : "customer_id"
    customer_loan }o--|| loan : "loan_id"
    branch_loan }o--|| branch : "branch_id"
    branch_loan }o--|| loan : "loan_id"
    branch_account }o--|| branch : "branch_id"
    branch_account }o--|| account : "account_id"
```
</details>

## Performance & Efficiency Summary

| Completeness (Cov_attr) | Structural Integrity (S_rel) | Intra-Table Uniqueness (M_unique) | Latency (s) | Total Tokens |
| --- | --- | --- | --- | --- |
| 0.9841 | 0.9855 | 0.9988 | 56.82s | 72,035 |

## Target Schema Detailed Specifications

### Target Table: `bank`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `bank_code` | string | PK | `bank1.bank.code` | - |
| `name` | string | - | `bank1.bank.name` | - |
| `address` | string | - | `bank1.bank.address` | - |

### Target Table: `branch`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `branch_id` | integer | PK | `bank1.branch.branch_id`, `bank2.branch.branch_id` | - |
| `name` | string | - | `bank1.branch.name`, `bank2.branch.branch_name` | - |
| `address` | string | - | `bank1.branch.address`, `bank2.branch.branch_address` | - |
| `assets` | integer | - | `bank2.branch.assets` | - |
| `bank_code` | string | FK -> `bank.bank_code` | `bank1.branch.bank_code` | - |

### Target Table: `customer`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `customer_id` | integer | PK | `bank1.customer.custid`, `bank2.customer.customer_id` | - |
| `name` | string | - | `bank1.customer.name`, `bank2.customer.customer_name` | - |
| `phone` | string | - | `bank1.customer.phone`, `bank2.customer.mobileno` | - |
| `address` | string | - | `bank1.customer.address` | - |
| `dob` | date | - | `bank2.customer.dob` | - |

### Target Table: `account`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `account_id` | integer | PK | `bank1.account.account_no`, `bank2.account.account_id` | - |
| `account_type` | string | - | `bank1.account.acc_type`, `bank2.account.account_type` | - |
| `balance` | number | - | `bank1.account.balance`, `bank2.account.account_balance` | - |
| `branch_id` | integer | FK -> `branch.branch_id` | `bank1.account.branch_id`, `bank2.account.branch_id` | - |

### Target Table: `loan`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `loan_id` | integer | PK | `bank1.loan.loan_id`, `bank2.loan.loan_id` | - |
| `loan_type` | string | - | `bank1.loan.loan_type` | - |
| `issued_amount` | number | - | `bank1.loan.amount`, `bank2.loan.issued_amount` | - |
| `remaining_amount` | number | - | `bank2.loan.remaining_amount` | - |
| `branch_id` | integer | FK -> `branch.branch_id` | `bank1.loan.branch_id`, `bank2.loan.branch_id` | - |
| `account_id` | integer | FK -> `account.account_id` | `bank2.loan.account_id` | - |

### Target Table: `loan_payment`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `loan_payment_id` | integer | PK | `bank2.loan_payment.loan_payment_id` | - |
| `amount` | number | - | `bank2.loan_payment.amount` | - |
| `loan_id` | integer | FK -> `loan.loan_id` | `bank2.loan_payment.loan_id` | - |

### Target Table: `transaction`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `transaction_id` | integer | PK | `bank2.transaction.transaction_id` | - |
| `amount` | number | - | `bank2.transaction.amount` | - |
| `customer_id` | integer | FK -> `customer.customer_id` | `bank2.transaction.customer_id` | - |
| `account_id` | integer | FK -> `account.account_id` | `bank2.transaction.account_id` | - |

### Target Table: `credit_card`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `credit_card_id` | integer | PK | `bank2.customer_credit_card.credit_card_id` | - |
| `expiry_date` | date | - | `bank2.customer_credit_card.expiry_date` | - |
| `card_limit` | number | - | `bank2.customer_credit_card.card_limit` | - |
| `customer_id` | integer | FK -> `customer.customer_id` | `bank2.customer_credit_card.customer_id` | - |
| `account_id` | integer | FK -> `account.account_id` | `bank2.customer_credit_card.account_id` | - |

### Target Table: `banker`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `banker_id` | integer | PK | `bank2.banker_info.banker_id` | - |
| `name` | string | - | `bank2.banker_info.banker_name` | - |
| `branch_id` | integer | FK -> `branch.branch_id` | `bank2.banker_info.branch_id` | - |

### Target Table: `customer_account`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `customer_id` | integer | PK, FK | `bank1.hold_by.custid`, `bank2.customer.customer_id` | - |
| `account_id` | integer | PK, FK | `bank1.hold_by.account_no`, `bank2.customer.account_id` | - |

### Target Table: `customer_loan`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `customer_id` | integer | PK, FK | `bank1.availed_by.custid`, `bank2.borrower.customer_id` | - |
| `loan_id` | integer | PK, FK | `bank1.availed_by.loan_id`, `bank2.borrower.loan_id` | - |

### Target Table: `branch_loan`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `branch_id` | integer | PK, FK | `bank1.offer.branch_id` | - |
| `loan_id` | integer | PK, FK | `bank1.offer.loan_id` | - |

### Target Table: `branch_account`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `branch_id` | integer | PK, FK | `bank1.maintain.branch_id` | - |
| `account_id` | integer | PK, FK | `bank1.maintain.account_no` | - |

## 3-Pillar Reference-Free Diagnostic Inspection

### Pillar 1: Information Preservation (Completeness)

- **Attribute Completeness ($Cov_{\text{attr}}$)**: `98.41%`

#### Dropped / Unmapped Source Attributes
- :x: `b:borrower.borrower_id`

### Pillar 2: Structural & Referential Constraints

- **Primary Key Validity**: `100.00%`
- **Foreign Key Validity**: `100.00%` (18 declared FKs)
- **Source FK Preservation**: `100.00%` (46/46 source relationships preserved)
- **Combined Structural Score ($S_{\text{rel}}$)**: `1.0000`
- **Total Target Tables**: `13`

:white_check_mark: All target foreign keys are valid and all source relational links are preserved.

### Pillar 3: Intrinsic Minimality & Non-Redundancy

- **Intra-Table Uniqueness ($M_{\text{unique}}$)**: `1.0000`

:white_check_mark: Zero semantic duplicate columns detected across target relations.

## Multi-Iteration Stability Analysis

| Iteration | Completeness | Integrity | Uniqueness | Clones Flagged | Latency (s) | Prompt Tokens | Completion Tokens | Total Tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.9841 | 0.9565 | 0.9963 | 1 | 43.98s | 7,424 | 13,856 | 21,280 |
| 2 | 0.9841 | 1.0000 | 1.0000 | 0 | 82.14s | 7,424 | 22,600 | 30,024 |
| 3 | 0.9841 | 1.0000 | 1.0000 | 0 | 44.34s | 7,424 | 13,307 | 20,731 |

### Cross-Iteration Attribute Mapping Consensus

- **Total Co-Aligned Attribute Pairs**: `17`
- **Invariant / Stable Alignments (100% Agreement)**: `14`
- **Volatile / Flaky Alignments (<100% Agreement)**: `3`
- **Overall Consensus Ratio**: `82.35%`

### Topological & Relational Drift

- **Mean Table Count**: `13.00 ± 0.00` (Range: 13 – 13)
- **Relational Graph Edge Stability (Mean Pairwise Jaccard)**: `0.5932`

#### Volatile Cross-Source Alignments (Flakiness Breakdown)

| Source A Attribute | Source B Attribute | Agreement Rate | Runs | Assigned Target Field(s) |
| --- | --- | --- | --- | --- |
| `hold_by.account_no` | `customer.account_id` | 66.7% | 2/3 | `customer_account.account_id` |
| `hold_by.custid` | `customer.customer_id` | 33.3% | 1/3 | `customer_account.customer_id` |
| `loan.amount` | `loan.issued_amount` | 66.7% | 2/3 | `loan.issued_amount` |

#### Confirmed Invariant Alignments (14 pairs)

| Source A Attribute | Source B Attribute | Unified Target Field |
| --- | --- | --- |
| `account.acc_type` | `account.account_type` | `account.account_type` |
| `account.account_no` | `account.account_id` | `account.account_id` |
| `account.balance` | `account.account_balance` | `account.balance` |
| `account.branch_id` | `account.branch_id` | `account.branch_id` |
| `availed_by.custid` | `borrower.customer_id` | `customer_loan.customer_id` |
| `availed_by.loan_id` | `borrower.loan_id` | `customer_loan.loan_id` |
| `branch.address` | `branch.branch_address` | `branch.address` |
| `branch.branch_id` | `branch.branch_id` | `branch.branch_id` |
| `branch.name` | `branch.branch_name` | `branch.branch_name`, `branch.name` |
| `customer.custid` | `customer.customer_id` | `customer.customer_id` |
| `customer.name` | `customer.customer_name` | `customer.customer_name`, `customer.name` |
| `customer.phone` | `customer.mobileno` | `customer.phone` |
| `loan.branch_id` | `loan.branch_id` | `loan.branch_id` |
| `loan.loan_id` | `loan.loan_id` | `loan.loan_id` |

### Intra-Table Clone Stability

- **Candidate Clones Stability Ratio**: `0.00%` (0/1 stable)

## Diagnostic & Observability Telemetry

- **Candidate Clones CSV**: [`detected_clones.csv`](./detected_clones.csv)
- **Mapping Consensus CSV**: [`mapping_consensus.csv`](./mapping_consensus.csv)
- **LLM Execution Trace**: [`execution_trace.jsonl`](./execution_trace.jsonl)
- **Per-Iteration Artifacts**: [`iterations/`](./iterations/)

