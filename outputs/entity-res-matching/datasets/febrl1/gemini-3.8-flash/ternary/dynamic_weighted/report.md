# Matching Benchmark: febrl1 — Dynamic Weighted

- **Domain**: synthetic
- **Strategy**: Dynamic Weighted
- **Model**: gemini-3.8-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 1.0000 | 0.0000 |
| Recall | 0.6260 | 0.0053 |
| F1 Score | 0.7700 | 0.0040 |
| Execution Time (s) | 0.3864 | 0.0515 |
| Peak Memory (MB) | 0.94 | 0.08 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 10,239 |
| Completion Tokens | 4,520 |
| Total Tokens | 14,759 |
| Estimated Cost (USD) | $0.0246 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9987 | 0.0012 |
| Potential F1 Ceiling | 0.9993 | 0.0006 |
| LLM Workload Ratio | 11.6% | - |
| Unrecoverable Loss | 0.0013 | - |
| Uncertain Purity | 100.0% | - |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.6280 | 0.7715 | 0.9980 | 0.9990 | 11.5% | 100.0% | 314 | 0 | 186 | 0.3294 | 0.90 | 4715 | $0.0074 |  |
| 2 | SUCCESS | 1.0000 | 0.6200 | 0.7654 | 1.0000 | 1.0000 | 11.8% | 100.0% | 310 | 0 | 190 | 0.4296 | 1.03 | 5279 | $0.0096 |  |
| 3 | SUCCESS | 1.0000 | 0.6300 | 0.7730 | 0.9980 | 0.9990 | 11.4% | 100.0% | 315 | 0 | 185 | 0.4000 | 0.88 | 4765 | $0.0076 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 2 | dynamic_skew | 0.5158 | 0.8719 | [0.2568, 0.7748, 0.9366] |

## LLM Strategy Configuration & Prompts

- **Model**: `gemini-3.8-flash`
- **Provider**: `google-cloud`
- **Latency**: `9.13s`
- **Log File**: `outputs/logs/llm_calls/20260919_161850_338234_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "1. rec_id: Internal record identifier (exclusion rule: source-specific key/UUID/internal ID). Excluded.\n2. soc_sec_id:\n- Step 1 (Exemplar): Values match exactly as multi-digit numeric identifiers (e.g., '4255165' vs '4255165').\n- Step 2 (Profile): 0.0% nulls in both sources, 100% uniqueness/cardinality (500/500). High discriminatory power.\n- Step 3 (Algorithm): Code/numeric string identifier. 'damerau_levenshtein' is optimal as it evaluates character/digit sequence edit distance while catching single-digit transposition/typo errors without the distortion of numeric arithmetic.\n- Step 4 (Weight): Core identity attribute; assigned 0.9.\n3. date_of_birth:\n- Step 1 (Exemplar): Values are formatted as compact numeric YYYYMMDD.0 floats (e.g. '19080625.0').\n- Step 2 (Profile): Low nulls (2.6% / 5.6%), very high cardinality (483 / 469).\n- Step 3 (Algorithm): Because of the float-formatted YYYYMMDD representation, standard calendar date parser might misinterpret the float without preprocessing, whereas 'exact' binary matching ensures strict alignment of birth dates across matches.\n- Step 4 (Weight): Strong identifying attribute; assigned 0.7.\n4. address_1:\n- Step 1 (Exemplar): Street names such as 'brunswick circuit', 'beaumaris street', 'wild street'. Notice Candidate 2 shows address line swapping ('address_1' vs 'address_2').\n- Step 2 (Profile): Low nulls (1.4% / 3.6%), high cardinality (445 / 469), avg length ~14.5.\n- Step 3 (Algorithm): Street addresses are multi-word phrases. 'cosine' is chosen for multi-word token overlap, providing invariance to word ordering and token shifts.\n- Step 4 (Weight): Primary descriptive attribute; assigned 0.6.\n5. given_name & surname:\n- Step 1 (Exemplar): Person names show potential inversions (Candidate 1 & 3 show given_name and surname swapped) and minor variations/typos.\n- Step 2 (Profile): Low nulls (<6%), moderate-to-high cardinality (259-387), short string length (~6 chars).\n- Step 3 (Algorithm): Short person names. 'jarowinkler' is the gold standard for personal names with prefix weighting and character-level typo tolerance.\n- Step 4 (Weight): Primary descriptive attributes; assigned 0.5 each.\n6. suburb:\n- Step 1 (Exemplar): Australian suburbs such as 'avondale heights', 'the basin'.\n- Step 2 (Profile): Low nulls (1.2% / 2.4%), high cardinality (390 / 427), avg length ~9.5.\n- Step 3 (Algorithm): Short place names / suburbs. 'jarowinkler' handles small misspellings and prefix consistency well on short strings.\n- Step 4 (Weight): Descriptive geographical attribute; assigned 0.5.\n7. postcode:\n- Step 1 (Exemplar): 4-digit postal codes (e.g., '2073', '4179', '2029') matching exactly.\n- Step 2 (Profile): 0.0% nulls, cardinality ~400.\n- Step 3 (Algorithm): Standardized discrete numeric postal code where exact correspondence is expected. 'exact' is best.\n- Step 4 (Weight): Supporting geographic attribute; assigned 0.5.\n8. street_number:\n- Step 1 (Exemplar): Street numbers formatted with decimal floats (e.g. '6.0', '303.0').\n- Step 2 (Profile): Low nulls (2.8% / 6.2%), cardinality ~145.\n- Step 3 (Algorithm): Discrete building number; 'exact' avoids false similarity between different house numbers (e.g. 6 vs 60).\n- Step 4 (Weight): Contextual attribute; assigned 0.4.\n9. state:\n- Step 1 (Exemplar): Standard Australian state codes (e.g. 'vic', 'nsw', 'wa').\n- Step 2 (Profile): Low nulls (<2%), low cardinality (8/17), length ~2.8.\n- Step 3 (Algorithm): Short categorical abbreviations; 'exact' is optimal.\n- Step 4 (Weight): Low-cardinality supporting attribute; assigned 0.3.\n10. address_2:\n- Excluded or omitted due to frequent swaps with address_1 and higher null rates, allowing address_1, suburb, state, and postcode to reliably capture the spatial address profile.",
  "matching_columns": {
    "street_number": {
      "algorithm": "exact",
      "weight": 0.4
    },
    "suburb": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "address_1": {
      "algorithm": "cosine",
      "weight": 0.6
    },
    "state": {
      "algorithm": "exact",
      "weight": 0.3
    },
    "soc_sec_id": {
      "algorithm": "damerau_levenshtein",
      "weight": 0.9
    },
    "date_of_birth": {
      "algorithm": "exact",
      "weight": 0.7
    },
    "surname": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "postcode": {
      "algorithm": "exact",
      "weight": 0.5
    },
    "given_name": {
      "algorithm": "jarowinkler",
      "weight": 0.5
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

