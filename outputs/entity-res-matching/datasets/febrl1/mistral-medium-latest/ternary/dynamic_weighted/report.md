# Matching Benchmark: febrl1 — Dynamic Weighted

- **Domain**: synthetic
- **Strategy**: Dynamic Weighted
- **Model**: mistral-medium-latest
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 1.0000 | 0.0000 |
| Recall | 0.7327 | 0.2265 |
| F1 Score | 0.8334 | 0.1419 |
| Execution Time (s) | 0.3336 | 0.1726 |
| Peak Memory (MB) | 0.80 | 0.13 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 10,680 |
| Completion Tokens | 48,104 |
| Total Tokens | 58,784 |
| Estimated Cost (USD) | $0.3768 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9960 | 0.0053 |
| Potential F1 Ceiling | 0.9980 | 0.0027 |
| LLM Workload Ratio | 16.4% | - |
| Unrecoverable Loss | 0.0040 | - |
| Uncertain Purity | 66.9% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 47.48% |
| Consistent Matches | 236 |
| Flaky Matches | 261 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.6100 | 0.7578 | 0.9980 | 0.9990 | 12.1% | 100.0% | 305 | 0 | 195 | 0.5045 | 0.89 | 20236 | $0.1304 |  |
| 2 | SUCCESS | 1.0000 | 0.9940 | 0.9970 | 1.0000 | 1.0000 | 24.8% | 0.8% | 497 | 0 | 3 | 0.3370 | 0.87 | 20653 | $0.1335 |  |
| 3 | SUCCESS | 1.0000 | 0.5940 | 0.7453 | 0.9900 | 0.9950 | 12.3% | 100.0% | 297 | 0 | 203 | 0.1594 | 0.65 | 17895 | $0.1129 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.5288 | 0.8716 | [0.2889, 0.7687, 0.9402] |
| 2 | dynamic_skew | 0.4218 | 0.7619 | [0.3654, 0.4781, 0.9511] |
| 3 | dynamic_skew | 0.5242 | 0.9041 | [0.2663, 0.7822, 0.9853] |

## LLM Strategy Configuration & Prompts

- **Model**: `mistral-medium-latest`
- **Provider**: `mistral`
- **Latency**: `93.72s`
- **Log File**: `outputs/logs/llm_calls/20260919_162312_929578_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "**Column: soc_sec_id**\n1. **Inspect Exemplar Candidate Matches**: All three pairs show *exact* string equivalence (e.g., `\"4255165\" \u2194 \"4255165\"`). No typos, transpositions, or formatting variations are observed.\n2. **Inspect Statistical Profile**: Null% = 0.0% in both sources; cardinality = 500 (100% unique). Meets inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: As a standardized unique identifier, any discrepancy *must* indicate distinct entities. `exact` is the only correct choice\u2014string similarity algorithms (e.g., `jarowinkler`) risk false matches for numerically similar but distinct IDs (e.g., `4255165` vs `4255166`), and numeric algorithms are irrelevant for identity checks.\n4. **Weight Justification**: Core identity attribute (government-issued ID). Weight: **1.0**.\n\n---\n\n**Column: date_of_birth**\n1. **Inspect Exemplar Candidate Matches**: All pairs show *exact* numeric equivalence in `YYYYMMDD` format (e.g., `19080625.0 \u2194 19080625.0`).\n2. **Inspect Statistical Profile**: Null% = 2.6%|5.6% (<50%); cardinality = 483|469 (near-unique). Meets inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: Represents calendar dates. `date` is ideal as it models hierarchical similarity (year > month > day), so a 1-day difference yields high similarity, while a 1-year difference yields low similarity. `numeric_linear` would misinterpret `YYYYMMDD` as a raw number (e.g., `19080625` vs `19080626` = difference of 1, but semantically 1 day). `exact` is too strict for potential minor date entry errors.\n4. **Weight Justification**: Highly discriminative identity attribute. Weight: **0.8**.\n\n---\n\n**Column: surname**\n1. **Inspect Exemplar Candidate Matches**: Matches 1 and 3 show *swapped* values with `given_name` (e.g., `\"guthridge\" \u2194 \"thomas\"` when `given_name` has the inverse). Match 2 shows exact equivalence (`\"matthews\" \u2194 \"matthews\"`). No typos/abbreviations observed in non-swapped cases.\n2. **Inspect Statistical Profile**: Null% = 1.2%|2.4% (<50%); cardinality = 340|387; avg length = 6.57|6.57 (<20 chars). Meets inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: Short string (avg <20 chars) representing a person\u2019s last name. `jarowinkler` is optimal for short strings, providing robustness to minor typos/phonetic variants (e.g., `\"Smith\"` vs `\"Smyth\"`). `cosine` fails as it operates at the *word* level and would score 0.0 for single-word typos. `damerau_levenshtein` lacks phonetic awareness. Swapping is a *data alignment* issue (not solvable by string similarity), but `jarowinkler` correctly scores non-swapped cases.\n4. **Weight Justification**: Core identity attribute (last name). Weight: **0.7**.\n\n---\n\n**Column: given_name**\n1. **Inspect Exemplar Candidate Matches**: Same swapping pattern as `surname` (e.g., `\"thomas\" \u2194 \"guthridge\"` in Match 1). Match 2 shows exact equivalence (`\"lara\" \u2194 \"lara\"`).\n2. **Inspect Statistical Profile**: Null% = 3.0%|5.8% (<50%); cardinality = 259|320; avg length = 5.92|5.97 (<20 chars). Meets inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: Identical reasoning to `surname`: short string, best handled by `jarowinkler` for typo tolerance. Swapping is a data issue, not an algorithm limitation.\n4. **Weight Justification**: Core identity attribute (first name). Weight: **0.7**.\n\n---\n\n**Column: postcode**\n1. **Inspect Exemplar Candidate Matches**: All pairs show exact equivalence (e.g., `\"2073\" \u2194 \"2073\"`). Values are 4-digit Australian postal codes.\n2. **Inspect Statistical Profile**: Null% = 0.0%; cardinality = 389|409; avg length = N/A (numeric). Meets inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: Discrete numeric identifiers. `exact` is appropriate\u2014any difference indicates a different location. String algorithms (e.g., `damerau_levenshtein`) are inapplicable for numeric columns. Numeric difference algorithms (`numeric_linear`) are semantically incorrect (postcodes are categorical, not interval-scaled).\n4. **Weight Justification**: Strong descriptive attribute for geographic precision. Weight: **0.6**.\n\n---\n\n**Column: suburb**\n1. **Inspect Exemplar Candidate Matches**: All pairs show exact equivalence (e.g., `\"avondale heights\" \u2194 \"avondale heights\"`). Values include multi-word names.\n2. **Inspect Statistical Profile**: Null% = 1.2%|2.4% (<50%); cardinality = 390|427; avg length = 9.45|9.57 (<20 chars). Meets inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: Short proper nouns (avg <20 chars). `jarowinkler` is optimal for short strings, handling minor spelling variations (e.g., `\"avondale heights\"` vs `\"avondale hts\"`). `cosine` is less ideal for short strings with limited tokens. `jarowinkler`\u2019s prefix weighting also helps with common suffixes (e.g., `\"-ville\"`).\n4. **Weight Justification**: Important descriptive attribute for location. Weight: **0.5**.\n\n---\n\n**Column: address_1**\n1. **Inspect Exemplar Candidate Matches**: Matches 1 and 3 show exact equivalence (e.g., `\"brunswick circuit\" \u2194 \"brunswick circuit\"`). Match 2 shows *swapped* values with `address_2` (`\"beaumaris street\" \u2194 \"sunforest therapy centre\"`).\n2. **Inspect Statistical Profile**: Null% = 1.4%|3.6% (<50%); cardinality = 445|469; avg length = 14.45|14.47 (\u224814.5 chars). Meets inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: Multi-word free text (avg \u224814.5 chars). `cosine` (TF-IDF) is ideal as it is order-invariant and resilient to word permutations/additions (e.g., `\"brunswick circuit\"` vs `\"circuit brunswick\"`). `jarowinkler` is unsuitable for multi-word text. Swapping with `address_2` is a data alignment issue; `cosine` will still correctly score non-swapped cases.\n4. **Weight Justification**: Primary descriptive attribute for location. Weight: **0.5**.\n\n---\n\n**Column: address_2**\n1. **Inspect Exemplar Candidate Matches**: Matches 1 and 3 show exact equivalence (e.g., `\"tintagel\" \u2194 \"tintagel\"`). Match 2 shows swapped values with `address_1`.\n2. **Inspect Statistical Profile**: Null% = 7.4%|15.6% (<50%); cardinality = 411|401; avg length = 11.87|12.09 (\u224812 chars). Meets inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: Same reasoning as `address_1`: multi-word or single-word text, best handled by `cosine` for its word-level resilience.\n4. **Weight Justification**: Same as `address_1`. Weight: **0.5**.\n\n---\n\n**Column: street_number**\n1. **Inspect Exemplar Candidate Matches**: All pairs show exact equivalence (e.g., `6.0 \u2194 6.0`). Values are numeric with float representation.\n2. **Inspect Statistical Profile**: Null% = 2.8%|6.2% (<50%); cardinality = 146|141; avg length = N/A (numeric). Meets inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: Numeric address component. `numeric_linear` (absolute difference) is appropriate for small integer values where absolute gap matters (e.g., `6` vs `8` = difference of 2). `exact` is too strict if minor formatting variations exist (e.g., `6` vs `6.0`). `numeric_relative` is less suitable as street numbers don\u2019t span orders of magnitude.\n4. **Weight Justification**: Supporting contextual attribute for address precision. Weight: **0.4**.\n\n---\n\n**Column: state**\n1. **Inspect Exemplar Candidate Matches**: All pairs show exact equivalence (e.g., `\"vic\" \u2194 \"vic\"`). Values are 2\u20133 character abbreviations.\n2. **Inspect Statistical Profile**: Null% = 1.2%|1.8% (<50%); **cardinality = 8|17 (very low)**. Meets inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: Standardized low-cardinality codes. `exact` is ideal\u2014any discrepancy indicates a different state. String similarity algorithms risk false matches (e.g., `\"vic\"` vs `\"nsw\"` might score >0 with `jarowinkler`).\n4. **Weight Justification**: Low discriminative power due to few unique values, but still provides geographic context. Weight: **0.2**.\n\n---\n\n**Column: rec_id**\n- **Excluded**: Internal auto-generated key (e.g., `\"rec177org\"` vs `\"rec177dup0\"` are source-specific). Violates exclusion rule for system/internal attributes.",
  "matching_columns": {
    "soc_sec_id": {
      "algorithm": "exact",
      "weight": 1.0
    },
    "date_of_birth": {
      "algorithm": "date",
      "weight": 0.8
    },
    "surname": {
      "algorithm": "jarowinkler",
      "weight": 0.7
    },
    "given_name": {
      "algorithm": "jarowinkler",
      "weight": 0.7
    },
    "postcode": {
      "algorithm": "exact",
      "weight": 0.6
    },
    "suburb": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "address_1": {
      "algorithm": "cosine",
      "weight": 0.5
    },
    "address_2": {
      "algorithm": "cosine",
      "weight": 0.5
    },
    "street_number": {
      "algorithm": "numeric_linear",
      "weight": 0.4
    },
    "state": {
      "algorithm": "exact",
      "weight": 0.2
    }
  }
}
```

### LLM Input Prompts

<details>
<summary><b>System Prompt</b> (click to expand)</summary>

```text
You are an expert Data Steward configuring the Scoring and Classification stage of an Entity Resolution pipeline.

You will receive comparative metadata for two source datasets (null %, uniqueness %, cardinality, average field length) AND a set of **Exemplar Candidate Matching Pairs** discovered via holistic zero-configuration row-level textual overlap.

These exemplar pairs represent high-probability matches of the same real-world entity across Source A and Source B. You MUST carefully inspect these aligned pairs to observe how identical entities are represented across sources on each column (e.g., whether they exhibit minor typos, abbreviations, unit shifts, or divergent taxonomies), and use these direct empirical observations to select the most effective comparison algorithm and weight.

Your goal is to select the columns that best determine whether two records refer to the same real-world entity, assign appropriate comparison algorithms, and assign importance weights for aggregate similarity scoring.

## Task 1 — Select Matching Columns and Assign Comparison Algorithms

### Step 1a: Understand each column semantically
- **Identity attributes** (names, emails, tax IDs, phone numbers) → these directly identify an entity.
- **Descriptive attributes** (addresses, descriptions, categories) → these characterize the entity and can confirm or disambiguate matches.
- **Contextual attributes** (dates, amounts, coordinates) → these add supporting evidence.
- **System/internal attributes** (auto-increment IDs, UUIDs, row numbers) → exclude these.

### Step 1b: Apply exclusion rules
Exclude columns with:
- **Source-specific keys**: `id`, `uuid`, `row_id`, or internal auto-generated keys.
- **High nulls**: > 50% null in either source.
- **No variance**: cardinality = 1 in either source.

### Comparison Algorithms & Explicit Trade-Offs

Select the algorithm that best fits each column's semantic type and empirical variation:

- **`cosine` (Token / Word-Level TF-IDF Cosine Similarity)**:
  - **Strengths**: Multi-word free text (avg length >= 20), long descriptions, multi-word titles, article abstracts. Completely order-invariant, resilient to token permutations, additions, or omissions of other words.
  - **Weaknesses / Critical Limitations**:
    - **Zero tolerance for sub-word typos or spelling variants**: Operates strictly at the word/token level. If a word has a typo, abbreviation, or hyphenation variation (e.g. "MDR-7506" vs "MDR7506", "Smith" vs "Smyth", "ProBook" vs "Pro Book"), word-level TF-IDF treats them as completely distinct orthogonal tokens with 0 similarity.
    - **Fails on short strings, codes, and single words (< 20 chars)**: If a single-word name or brand has even a 1-character typo, the entire token match fails (score drops to 0.0). Always use `jarowinkler` or `damerau_levenshtein` instead!
    - **Fails on divergent taxonomies**: Different vocabularies (e.g. "electronics" vs "consumer audio") yield 0.0 similarity.
  - **When to use**: Multi-word descriptions, article abstracts, long titles, full addresses where individual words are standard dictionary words or consistently spelled tokens.

- **`jarowinkler` (Prefix-Weighted Character Alignment)**:
  - **Strengths**: Short strings (avg length < 20-30), single words, names, brands, cities. Extremely robust to typos, phonetic variants, or suffix truncations on short words.
  - **Weaknesses**: Word order shifts, long multi-word text.
  - **When to use**: Person/author names, brand names, cities, single-phrase titles, short labels.

- **`damerau_levenshtein` (Edit Distance with Transpositions)**:
  - **Strengths**: Preserves exact character positions and lengths; detects single digit/char flips or swaps.
  - **Weaknesses**: Heavy penalty on length mismatches; useless on multi-word reordering.
  - **When to use**: Alphanumeric codes, serial numbers, part codes, phone numbers, tax IDs, SKUs.

- **`numeric_relative` (Percentage Difference)**:
  - **Strengths**: Scale-invariant; measures relative gap (|x1 - x2| / (max(|x1|, |x2|) + eps)). A $10 difference on a $20 item is penalized heavily (50%), while a $10 difference on a $1,500 item is penalized minimally (0.7%).
  - **Weaknesses**: Nonsensical on interval scales like calendar years.
  - **When to use**: Prices, monetary amounts, weights, physical dimensions, measurements spanning multiple orders of magnitude.

- **`numeric_linear` (Absolute Uniform Distance)**:
  - **Strengths**: Measures uniform absolute distance |x1 - x2| regardless of baseline.
  - **Weaknesses**: Distorts scale when values span orders of magnitude.
  - **When to use**: Uniform interval scales where absolute difference is constant: calendar years, ages, page counts.

- **`exact` (Strict Binary Identity)**:
  - **Strengths**: Zero tolerance for false positives.
  - **Weaknesses**: Zero tolerance for typos or format quirks.
  - **When to use**: Standardized codes, status booleans, or discrete identifier/temporal keys where any discrepancy indicates distinct entities.

- **`date` (Calendar Hierarchy Matcher)**:
  - **When to use**: Full calendar dates, birth dates, timestamps where small day/month/year shifts should yield continuous similarity.

### Step 1d: Assign importance weights (0.0 to 1.0)
- **0.8-1.0**: Core identity attributes (emails, tax IDs, phone numbers).
- **0.5-0.7**: Strong descriptive attributes (names, titles).
- **0.2-0.4**: Supporting contextual attributes (dates, amounts).
- **0.05-0.19**: Weak signals.

## Task 2 — Structured Reasoning

In your `reasoning` field, follow this exact protocol:
### Mandatory 4-Step Column Reasoning Protocol

For EACH evaluated column, your reasoning MUST follow this exact 4-step sequence:
1. **Inspect Exemplar Candidate Matches**: Observe how matching entities actually differ on this column (typos, abbreviations, units, taxonomy).
2. **Inspect Statistical Profile**: Check null percentage, cardinality, and avg length. Exclude if >50% null or cardinality = 1.
3. **Algorithm Trade-off Evaluation**: Explicitly justify why the chosen algorithm fits the sample data and why competing alternatives would fail on this column.
4. **Weight Justification**: Assign importance weight based on whether the attribute is core identity (0.8-1.0), primary descriptive (0.5-0.7), or auxiliary context (0.2-0.4).
```
</details>

<details>
<summary><b>User Prompt (Comparative Profile & Exemplars)</b> (click to expand)</summary>

```markdown
### 1. Dataset Comparison Summary
| Metric | Source A | Source B |
| :--- | :--- | :--- |
| **Total Rows** | 500 | 500 |
| **Column Count** | 11 | 11 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.97)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec177org" | "rec177dup0" |
| given_name | "thomas" | "guthridge" |
| surname | "guthridge" | "thomas" |
| street_number | "6.0" | "6.0" |
| address_1 | "brunswick circuit" | "brunswick circuit" |
| address_2 | "tintagel" | "tintagel" |
| suburb | "avondale heights" | "avondale heights" |
| postcode | "2073" | "2073" |
| state | "vic" | "vic" |
| date_of_birth | "19080625.0" | "19080625.0" |
| soc_sec_id | "4255165" | "4255165" |

#### Candidate Match 2 (Overall Text Match Score: 0.97)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec447org" | "rec447dup0" |
| given_name | "lara" | "lara" |
| surname | "matthews" | "matthews" |
| street_number | "6.0" | "6.0" |
| address_1 | "beaumaris street" | "sunforest therapy centre" |
| address_2 | "sunforest therapy centre" | "beaumaris street" |
| suburb | "the basin" | "the basin" |
| postcode | "4179" | "4179" |
| state | "nsw" | "nsw" |
| date_of_birth | "19911006.0" | "19911006.0" |
| soc_sec_id | "2164704" | "2164704" |

#### Candidate Match 3 (Overall Text Match Score: 0.96)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec57org" | "rec57dup0" |
| given_name | "dante" | "davilasanhdars" |
| surname | "davilasanhdars" | "dante" |
| street_number | "303.0" | "303.0" |
| address_1 | "wild street" | "wild street" |
| address_2 | "surama" | "surama" |
| suburb | "avondale heights" | "avondale heights" |
| postcode | "2029" | "2029" |
| state | "wa" | "wa" |
| date_of_birth | "19120206.0" | "19120206.0" |
| soc_sec_id | "2609420" | "2609420" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **rec_id** | 0.0% | 0.0% | 100.0% | 100.0% | 500 | 500 | 8.78 | 9.78 | "rec177org" ↔ "rec177dup0" |
| **given_name** | 3.0% | 5.8% | 51.8% | 64.0% | 259 | 320 | 5.92 | 5.97 | "thomas" ↔ "guthridge" |
| **surname** | 1.2% | 2.4% | 68.0% | 77.4% | 340 | 387 | 6.57 | 6.57 | "guthridge" ↔ "thomas" |
| **street_number** | 2.8% | 6.2% | 29.2% | 28.2% | 146 | 141 | N/A | N/A | "6.0" ↔ "6.0" |
| **address_1** | 1.4% | 3.6% | 89.0% | 93.8% | 445 | 469 | 14.45 | 14.47 | "brunswick circuit" ↔ "brunswick circuit" |
| **address_2** | 7.4% | 15.6% | 82.2% | 80.2% | 411 | 401 | 11.87 | 12.09 | "tintagel" ↔ "tintagel" |
| **suburb** | 1.2% | 2.4% | 78.0% | 85.4% | 390 | 427 | 9.45 | 9.57 | "avondale heights" ↔ "avondale heights" |
| **postcode** | 0.0% | 0.0% | 77.8% | 81.8% | 389 | 409 | N/A | N/A | "2073" ↔ "2073" |
| **state** | 1.2% | 1.8% | 1.6% | 3.4% | 8 | 17 | 2.84 | 2.84 | "vic" ↔ "vic" |
| **date_of_birth** | 2.6% | 5.6% | 96.6% | 93.8% | 483 | 469 | N/A | N/A | "19080625.0" ↔ "19080625.0" |
| **soc_sec_id** | 0.0% | 0.0% | 100.0% | 100.0% | 500 | 500 | N/A | N/A | "4255165" ↔ "4255165" |
```
</details>

