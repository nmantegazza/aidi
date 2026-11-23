# Schema Alignment Diagnostic Report — bank1-bank2

## Summary Results



## Detailed Analysis

# Schema Alignment Diagnostic Report — bank1-bank2

- **Model**: `gemini-3.8-flash`
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
<summary><b>Iteration 1 Target Schema (11 tables, S_rel: 0.8261)</b></summary>

```mermaid
erDiagram
    bank {
        string code PK "Unique bank identifier code"
        string name "Legal name of the banking institution"
        string address "Headquarters address of the bank"
    }
    branch {
        integer branch_id PK "Unique identifier for each branch"
        string name "Branch name"
        string address "Physical address of the branch"
        number assets "Total assets held by the branch"
        string bank_code FK "Bank institution code the branch belo..."
    }
    banker {
        integer banker_id PK "Unique banker identifier"
        string name "Name of the banker"
        integer branch_id FK "Branch where the banker is assigned"
    }
    customer {
        integer customer_id PK "Unique customer identifier"
        string name "Full name of the customer"
        string phone "Primary telephone or mobile number"
        string address "Physical residential or mailing address"
        date dob "Customer date of birth"
    }
    account {
        integer account_id PK "Unique account identifier"
        string account_type "Type of account (e.g. savings, checking)"
        number balance "Current monetary balance in the account"
        integer branch_id FK "Branch holding the account"
    }
    customer_account {
        integer customer_id PK,FK "Customer holding the account"
        integer account_id PK,FK "Account held by the customer"
    }
    loan {
        integer loan_id PK "Unique loan identifier"
        string loan_type "Category or type of loan"
        number amount "Original principal or issued loan amount"
        number remaining_amount "Outstanding balance on the loan"
        integer branch_id FK "Branch issuing the loan"
        integer account_id FK "Account associated with loan disburse..."
    }
    loan_borrower {
        integer customer_id PK,FK "Borrowing customer identifier"
        integer loan_id PK,FK "Associated loan identifier"
    }
    loan_payment {
        integer loan_payment_id PK "Unique payment identifier"
        number amount "Payment amount made towards loan"
        integer loan_id FK "Associated loan being serviced"
    }
    credit_card {
        integer credit_card_id PK "Unique credit card identifier"
        date expiry_date "Expiration date of the credit card"
        number card_limit "Credit limit assigned to the card"
        integer customer_id FK "Customer owning the credit card"
        integer account_id FK "Account backing the credit card"
    }
    transaction {
        integer transaction_id PK "Unique transaction record identifier"
        number amount "Monetary transaction amount"
        integer customer_id FK "Customer initiating or involved in tr..."
        integer account_id FK "Account on which transaction occurred"
    }
    branch }o--|| bank : "bank_code"
    banker }o--|| branch : "branch_id"
    account }o--|| branch : "branch_id"
    customer_account }o--|| customer : "customer_id"
    customer_account }o--|| account : "account_id"
    loan }o--|| branch : "branch_id"
    loan }o--|| account : "account_id"
    loan_borrower }o--|| customer : "customer_id"
    loan_borrower }o--|| loan : "loan_id"
    loan_payment }o--|| loan : "loan_id"
    credit_card }o--|| customer : "customer_id"
    credit_card }o--|| account : "account_id"
    transaction }o--|| customer : "customer_id"
    transaction }o--|| account : "account_id"
```
</details>

<details>
<summary><b>Iteration 2 Target Schema (11 tables, S_rel: 0.8261)</b></summary>

```mermaid
erDiagram
    bank {
        string bank_code PK "Unique code identifying the bank inst..."
        string bank_name "Name of the bank institution."
        string address "Headquarters or primary address of th..."
    }
    branch {
        integer branch_id PK "Unique identifier for the bank branch."
        string branch_name "Name of the branch."
        string address "Physical address of the branch."
        number assets "Total asset value held by the branch."
        string bank_code FK "Foreign key identifying the owning bank."
    }
    banker {
        integer banker_id PK "Unique identifier for the banker/empl..."
        string banker_name "Full name of the banker."
        integer branch_id FK "Branch where the banker is assigned."
    }
    customer {
        integer customer_id PK "Unique identifier for the customer."
        string customer_name "Full name of the customer."
        string phone_number "Primary contact telephone or mobile n..."
        string address "Residential address of the customer."
        date dob "Customer date of birth."
    }
    account {
        integer account_id PK "Unique identifier for the account."
        string account_type "Category or type of account (e.g., ch..."
        number balance "Current account monetary balance."
        integer branch_id FK "Identifier of branch managing the acc..."
    }
    customer_account {
        integer customer_id PK,FK "Identifier of the participating custo..."
        integer account_id PK,FK "Identifier of the linked account."
    }
    loan {
        integer loan_id PK "Unique identifier for the loan."
        string loan_type "Classification/type of loan product."
        number amount "Total amount of the loan granted/issued."
        number remaining_amount "Outstanding principal or balance rema..."
        integer branch_id FK "Branch originating or maintaining the..."
        integer account_id FK "Linked account associated with loan d..."
    }
    customer_loan {
        integer customer_id PK,FK "Identifier of the borrower/customer."
        integer loan_id PK,FK "Identifier of the availed loan."
    }
    loan_payment {
        integer loan_payment_id PK "Unique identifier for the loan repaym..."
        number amount "Monetary amount paid towards the loan."
        integer loan_id FK "Identifier of the loan being repaid."
    }
    transaction {
        integer transaction_id PK "Unique identifier for the account tra..."
        number amount "Transaction monetary amount."
        integer customer_id FK "Customer performing the transaction."
        integer account_id FK "Account affected by the transaction."
    }
    customer_credit_card {
        integer credit_card_id PK "Unique identifier for the credit card."
        date expiry_date "Card expiration date."
        number card_limit "Credit limit approved on the card."
        integer customer_id FK "Customer owning the credit card."
        integer account_id FK "Linked billing/settlement account."
    }
    branch }o--|| bank : "bank_code"
    banker }o--|| branch : "branch_id"
    account }o--|| branch : "branch_id"
    customer_account }o--|| customer : "customer_id"
    customer_account }o--|| account : "account_id"
    loan }o--|| branch : "branch_id"
    loan }o--|| account : "account_id"
    customer_loan }o--|| customer : "customer_id"
    customer_loan }o--|| loan : "loan_id"
    loan_payment }o--|| loan : "loan_id"
    transaction }o--|| customer : "customer_id"
    transaction }o--|| account : "account_id"
    customer_credit_card }o--|| customer : "customer_id"
    customer_credit_card }o--|| account : "account_id"
```
</details>

<details open>
<summary><b>Iteration 3 Target Schema (11 tables, S_rel: 0.8261) [Representative / Final Run]</b></summary>

```mermaid
erDiagram
    bank {
        string bank_code PK "Unique code identifying the bank inst..."
        string name "Name of the bank institution."
        string address "Address of the bank institution headq..."
    }
    branch {
        integer branch_id PK "Unique identifier for the bank branch."
        string branch_name "Name of the bank branch."
        string branch_address "Physical address of the bank branch."
        string bank_code FK "Reference to the parent bank institut..."
        number assets "Total asset valuation of the branch."
    }
    banker {
        integer banker_id PK "Unique identifier for the banker."
        string banker_name "Full name of the banker."
        integer branch_id FK "Branch where the banker is stationed."
    }
    customer {
        integer customer_id PK "Unique identifier for the customer."
        string customer_name "Full name of the customer."
        string phone_number "Primary phone or mobile number of the..."
        string address "Address of the customer."
        date birth_date "Date of birth of the customer."
    }
    account {
        integer account_id PK "Unique identifier or account number f..."
        string account_type "Classification or category of the acc..."
        number balance "Current balance of funds in the account."
        integer branch_id FK "Identifier of the branch maintaining ..."
    }
    customer_account {
        integer customer_id PK,FK "Identifier of the customer holding th..."
        integer account_id PK,FK "Identifier of the account held by the..."
    }
    loan {
        integer loan_id PK "Unique identifier for the loan."
        string loan_type "Type or category of the loan."
        number amount "Total initial principal or issued amo..."
        number remaining_amount "Outstanding or remaining loan balance..."
        integer branch_id FK "Branch that granted or manages the loan."
        integer account_id FK "Associated bank account for loan disb..."
    }
    loan_borrower {
        integer customer_id PK,FK "Customer who availed or borrowed the ..."
        integer loan_id PK,FK "Loan associated with the customer."
    }
    loan_payment {
        integer loan_payment_id PK "Unique identifier of the loan payment..."
        number amount "Amount paid towards the loan."
        integer loan_id FK "Identifier of the loan receiving the ..."
    }
    transaction {
        integer transaction_id PK "Unique identifier for the transaction..."
        number amount "Monetary amount transacted."
        integer customer_id FK "Customer initiating or associated wit..."
        integer account_id FK "Account affected by the transaction."
    }
    customer_credit_card {
        integer credit_card_id PK "Unique identifier for the credit card."
        date expiry_date "Credit card expiration date."
        number card_limit "Credit limit allocated to the card."
        integer customer_id FK "Cardholder customer identifier."
        integer account_id FK "Account linked to the credit card."
    }
    branch }o--|| bank : "bank_code"
    banker }o--|| branch : "branch_id"
    account }o--|| branch : "branch_id"
    customer_account }o--|| customer : "customer_id"
    customer_account }o--|| account : "account_id"
    loan }o--|| branch : "branch_id"
    loan }o--|| account : "account_id"
    loan_borrower }o--|| customer : "customer_id"
    loan_borrower }o--|| loan : "loan_id"
    loan_payment }o--|| loan : "loan_id"
    transaction }o--|| customer : "customer_id"
    transaction }o--|| account : "account_id"
    customer_credit_card }o--|| customer : "customer_id"
    customer_credit_card }o--|| account : "account_id"
```
</details>

## Performance & Efficiency Summary

| Completeness (Cov_attr) | Structural Integrity (S_rel) | Intra-Table Uniqueness (M_unique) | Latency (s) | Total Tokens |
| --- | --- | --- | --- | --- |
| 0.9206 | 0.8261 | 0.9919 | 22.36s | 35,349 |

## Target Schema Detailed Specifications

### Target Table: `bank`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `bank_code` | string | PK | `bank1.bank.code` | Unique code identifying the bank institution. |
| `name` | string | - | `bank1.bank.name` | Name of the bank institution. |
| `address` | string | - | `bank1.bank.address` | Address of the bank institution headquarters. |

### Target Table: `branch`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `branch_id` | integer | PK | `bank1.branch.branch_id`, `bank2.branch.branch_id` | Unique identifier for the bank branch. |
| `branch_name` | string | - | `bank1.branch.name`, `bank2.branch.branch_name` | Name of the bank branch. |
| `branch_address` | string | - | `bank1.branch.address`, `bank2.branch.branch_address` | Physical address of the bank branch. |
| `bank_code` | string | FK -> `bank.bank_code` | `bank1.branch.bank_code` | Reference to the parent bank institution. |
| `assets` | number | - | `bank2.branch.assets` | Total asset valuation of the branch. |

### Target Table: `banker`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `banker_id` | integer | PK | `bank2.banker_info.banker_id` | Unique identifier for the banker. |
| `banker_name` | string | - | `bank2.banker_info.banker_name` | Full name of the banker. |
| `branch_id` | integer | FK -> `branch.branch_id` | `bank2.banker_info.branch_id` | Branch where the banker is stationed. |

### Target Table: `customer`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `customer_id` | integer | PK | `bank1.customer.custid`, `bank2.customer.customer_id` | Unique identifier for the customer. |
| `customer_name` | string | - | `bank1.customer.name`, `bank2.customer.customer_name` | Full name of the customer. |
| `phone_number` | string | - | `bank1.customer.phone`, `bank2.customer.mobileno` | Primary phone or mobile number of the customer. |
| `address` | string | - | `bank1.customer.address` | Address of the customer. |
| `birth_date` | date | - | `bank2.customer.dob` | Date of birth of the customer. |

### Target Table: `account`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `account_id` | integer | PK | `bank1.account.account_no`, `bank2.account.account_id` | Unique identifier or account number for the bank account. |
| `account_type` | string | - | `bank1.account.acc_type`, `bank2.account.account_type` | Classification or category of the account (e.g. savings, checking). |
| `balance` | number | - | `bank1.account.balance`, `bank2.account.account_balance` | Current balance of funds in the account. |
| `branch_id` | integer | FK -> `branch.branch_id` | `bank1.account.branch_id`, `bank2.account.branch_id` | Identifier of the branch maintaining this account. |

### Target Table: `customer_account`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `customer_id` | integer | PK, FK | `bank1.hold_by.custid`, `bank2.customer.customer_id` | Identifier of the customer holding the account. |
| `account_id` | integer | PK, FK | `bank1.hold_by.account_no`, `bank2.customer.account_id` | Identifier of the account held by the customer. |

### Target Table: `loan`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `loan_id` | integer | PK | `bank1.loan.loan_id`, `bank2.loan.loan_id` | Unique identifier for the loan. |
| `loan_type` | string | - | `bank1.loan.loan_type` | Type or category of the loan. |
| `amount` | number | - | `bank1.loan.amount`, `bank2.loan.issued_amount` | Total initial principal or issued amount of the loan. |
| `remaining_amount` | number | - | `bank2.loan.remaining_amount` | Outstanding or remaining loan balance amount. |
| `branch_id` | integer | FK -> `branch.branch_id` | `bank1.loan.branch_id`, `bank2.loan.branch_id` | Branch that granted or manages the loan. |
| `account_id` | integer | FK -> `account.account_id` | `bank2.loan.account_id` | Associated bank account for loan disbursement or payments. |

### Target Table: `loan_borrower`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `customer_id` | integer | PK, FK | `bank1.availed_by.custid`, `bank2.borrower.customer_id` | Customer who availed or borrowed the loan. |
| `loan_id` | integer | PK, FK | `bank1.availed_by.loan_id`, `bank2.borrower.loan_id` | Loan associated with the customer. |

### Target Table: `loan_payment`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `loan_payment_id` | integer | PK | `bank2.loan_payment.loan_payment_id` | Unique identifier of the loan payment record. |
| `amount` | number | - | `bank2.loan_payment.amount` | Amount paid towards the loan. |
| `loan_id` | integer | FK -> `loan.loan_id` | `bank2.loan_payment.loan_id` | Identifier of the loan receiving the payment. |

### Target Table: `transaction`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `transaction_id` | integer | PK | `bank2.transaction.transaction_id` | Unique identifier for the transaction record. |
| `amount` | number | - | `bank2.transaction.amount` | Monetary amount transacted. |
| `customer_id` | integer | FK -> `customer.customer_id` | `bank2.transaction.customer_id` | Customer initiating or associated with the transaction. |
| `account_id` | integer | FK -> `account.account_id` | `bank2.transaction.account_id` | Account affected by the transaction. |

### Target Table: `customer_credit_card`

| Column Name | Type | Key | Source Provenance | Description |
| --- | --- | --- | --- | --- |
| `credit_card_id` | integer | PK | `bank2.customer_credit_card.credit_card_id` | Unique identifier for the credit card. |
| `expiry_date` | date | - | `bank2.customer_credit_card.expiry_date` | Credit card expiration date. |
| `card_limit` | number | - | `bank2.customer_credit_card.card_limit` | Credit limit allocated to the card. |
| `customer_id` | integer | FK -> `customer.customer_id` | `bank2.customer_credit_card.customer_id` | Cardholder customer identifier. |
| `account_id` | integer | FK -> `account.account_id` | `bank2.customer_credit_card.account_id` | Account linked to the credit card. |

## 3-Pillar Reference-Free Diagnostic Inspection

### Pillar 1: Information Preservation (Completeness)

- **Attribute Completeness ($Cov_{\text{attr}}$)**: `92.06%`

#### Dropped / Unmapped Source Attributes
- :x: `a:maintain.account_no`
- :x: `a:maintain.branch_id`
- :x: `a:offer.branch_id`
- :x: `a:offer.loan_id`
- :x: `b:borrower.borrower_id`

### Pillar 2: Structural & Referential Constraints

- **Primary Key Validity**: `100.00%`
- **Foreign Key Validity**: `100.00%` (14 declared FKs)
- **Source FK Preservation**: `82.61%` (38/46 source relationships preserved)
- **Combined Structural Score ($S_{\text{rel}}$)**: `0.8261`
- **Total Target Tables**: `11`

#### Unpreserved Source Foreign Keys
- :warning: Source bank1 FK 'offer' -> 'branch' has unmapped columns in target
- :warning: Source bank1 FK 'offer' -> 'loan' has unmapped columns in target
- :warning: Source bank1 FK 'offer' -> 'branch' has unmapped columns in target
- :warning: Source bank1 FK 'offer' -> 'loan' has unmapped columns in target
- :warning: Source bank1 FK 'maintain' -> 'branch' has unmapped columns in target
- :warning: Source bank1 FK 'maintain' -> 'account' has unmapped columns in target
- :warning: Source bank1 FK 'maintain' -> 'branch' has unmapped columns in target
- :warning: Source bank1 FK 'maintain' -> 'account' has unmapped columns in target

### Pillar 3: Intrinsic Minimality & Non-Redundancy

- **Intra-Table Uniqueness ($M_{\text{unique}}$)**: `0.9835`

#### Flagged Intra-Table Candidate Clones
| Target Table | Column A | Column B | Data Type | Cosine Sim | Source Prov A | Source Prov B |
| --- | --- | --- | --- | --- | --- | --- |
| `customer_account` | `customer_id` | `account_id` | integer | 0.9546 | bank1.hold_by.custid, bank2.customer.customer_id | bank1.hold_by.account_no, bank2.customer.account_id |
| `loan_borrower` | `customer_id` | `loan_id` | integer | 0.9264 | bank1.availed_by.custid, bank2.borrower.customer_id | bank1.availed_by.loan_id, bank2.borrower.loan_id |

## Multi-Iteration Stability Analysis

| Iteration | Completeness | Integrity | Uniqueness | Clones Flagged | Latency (s) | Prompt Tokens | Completion Tokens | Total Tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.9206 | 0.8261 | 0.9923 | 1 | 22.61s | 7,559 | 4,193 | 11,752 |
| 2 | 0.9206 | 0.8261 | 1.0000 | 0 | 22.38s | 7,559 | 4,303 | 11,862 |
| 3 | 0.9206 | 0.8261 | 0.9835 | 2 | 22.08s | 7,559 | 4,176 | 11,735 |

### Cross-Iteration Attribute Mapping Consensus

- **Total Co-Aligned Attribute Pairs**: `17`
- **Invariant / Stable Alignments (100% Agreement)**: `17`
- **Volatile / Flaky Alignments (<100% Agreement)**: `0`
- **Overall Consensus Ratio**: `100.00%`

### Topological & Relational Drift

- **Mean Table Count**: `11.00 ± 0.00` (Range: 11 – 11)
- **Relational Graph Edge Stability (Mean Pairwise Jaccard)**: `0.6236`

:white_check_mark: Zero volatile attribute alignments; 100% agreement across all runs.

#### Confirmed Invariant Alignments (17 pairs)

| Source A Attribute | Source B Attribute | Unified Target Field |
| --- | --- | --- |
| `account.acc_type` | `account.account_type` | `account.account_type` |
| `account.account_no` | `account.account_id` | `account.account_id` |
| `account.balance` | `account.account_balance` | `account.balance` |
| `account.branch_id` | `account.branch_id` | `account.branch_id` |
| `availed_by.custid` | `borrower.customer_id` | `customer_loan.customer_id`, `loan_borrower.customer_id` |
| `availed_by.loan_id` | `borrower.loan_id` | `customer_loan.loan_id`, `loan_borrower.loan_id` |
| `branch.address` | `branch.branch_address` | `branch.address`, `branch.branch_address` |
| `branch.branch_id` | `branch.branch_id` | `branch.branch_id` |
| `branch.name` | `branch.branch_name` | `branch.branch_name`, `branch.name` |
| `customer.custid` | `customer.customer_id` | `customer.customer_id` |
| `customer.name` | `customer.customer_name` | `customer.customer_name`, `customer.name` |
| `customer.phone` | `customer.mobileno` | `customer.phone`, `customer.phone_number` |
| `hold_by.account_no` | `customer.account_id` | `customer_account.account_id` |
| `hold_by.custid` | `customer.customer_id` | `customer_account.customer_id` |
| `loan.amount` | `loan.issued_amount` | `loan.amount` |
| `loan.branch_id` | `loan.branch_id` | `loan.branch_id` |
| `loan.loan_id` | `loan.loan_id` | `loan.loan_id` |

### Intra-Table Clone Stability

- **Candidate Clones Stability Ratio**: `0.00%` (0/2 stable)

## Diagnostic & Observability Telemetry

- **Candidate Clones CSV**: [`detected_clones.csv`](./detected_clones.csv)
- **Mapping Consensus CSV**: [`mapping_consensus.csv`](./mapping_consensus.csv)
- **LLM Execution Trace**: [`execution_trace.jsonl`](./execution_trace.jsonl)
- **Per-Iteration Artifacts**: [`iterations/`](./iterations/)

