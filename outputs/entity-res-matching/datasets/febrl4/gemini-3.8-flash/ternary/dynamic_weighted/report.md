# Matching Benchmark: febrl4 — Dynamic Weighted

- **Domain**: synthetic
- **Strategy**: Dynamic Weighted
- **Model**: gemini-3.8-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 1.0000 | 0.0000 |
| Recall | 0.9836 | 0.0018 |
| F1 Score | 0.9917 | 0.0009 |
| Execution Time (s) | 8.7841 | 0.4242 |
| Peak Memory (MB) | 37.34 | 1.12 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 10,362 |
| Completion Tokens | 4,116 |
| Total Tokens | 14,478 |
| Estimated Cost (USD) | $0.0232 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 1.0000 | 0.0000 |
| Potential F1 Ceiling | 1.0000 | 0.0000 |
| LLM Workload Ratio | 31.3% | - |
| Unrecoverable Loss | 0.0000 | - |
| Uncertain Purity | 0.3% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 97.79% |
| Consistent Matches | 4859 |
| Flaky Matches | 110 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.9854 | 0.9926 | 1.0000 | 1.0000 | 16.1% | 0.5% | 4927 | 0 | 73 | 8.7002 | 36.08 | 4880 | $0.0079 |  |
| 2 | SUCCESS | 1.0000 | 0.9836 | 0.9917 | 1.0000 | 1.0000 | 40.5% | 0.2% | 4918 | 0 | 82 | 8.4081 | 38.24 | 4864 | $0.0079 |  |
| 3 | SUCCESS | 1.0000 | 0.9818 | 0.9908 | 1.0000 | 1.0000 | 37.1% | 0.2% | 4909 | 0 | 91 | 9.2439 | 37.70 | 4734 | $0.0074 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.2601 | 0.6498 | [0.2267, 0.2935, 0.8874] |
| 2 | dynamic_skew | 0.2773 | 0.6762 | [0.2454, 0.3092, 0.9209] |
| 3 | dynamic_skew | 0.2984 | 0.6710 | [0.2567, 0.3400, 0.8917] |

## LLM Strategy Configuration & Prompts

- **Model**: `gemini-3.8-flash`
- **Provider**: `google-cloud`
- **Latency**: `10.22s`
- **Log File**: `outputs/logs/llm_calls/20260919_162921_332898_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "1. Column: rec_id\n- Inspect Exemplar Candidate Matches: Exemplars show 'rec1409org' vs 'rec1409dup0'. These are dataset record identifiers containing synthetic/internal tracking indicators.\n- Inspect Statistical Profile: 100% unique in both datasets.\n- Algorithm Trade-off Evaluation: Internal record IDs should never be matched across datasets as they represent system-specific metadata.\n- Weight Justification: Excluded.\n\n2. Column: soc_sec_id\n- Inspect Exemplar Candidate Matches: Perfectly matches across exemplar pairs (e.g., '1844518' vs '1844518', '6922783' vs '6922783').\n- Inspect Statistical Profile: 0% nulls, 100% unique in both datasets (cardinality 5000/5000).\n- Algorithm Trade-off Evaluation: Social security / national ID is an alphanumeric/numeric code identifier. 'damerau_levenshtein' is ideal as it measures exact character position changes, detecting single-digit typos or digit swaps while heavily penalizing dissimilar codes. 'numeric_relative' or 'numeric_linear' are unsuitable for non-scalar identifiers.\n- Weight Justification: 0.95. This is a primary, uniquely identifying identity attribute.\n\n3. Column: date_of_birth\n- Inspect Exemplar Candidate Matches: Exemplars show dates formatted as floats/strings like '19721016.0' matching identically.\n- Inspect Statistical Profile: Nulls < 4%, very high cardinality (4588/4505).\n- Algorithm Trade-off Evaluation: The format is represented numerically with floating-point suffix (.0). 'exact' matching works reliably for standardized YYYYMMDD dates where any difference strongly suggests a different individual or dirty record.\n- Weight Justification: 0.8. Birth date is a critical identity verification attribute.\n\n4. Column: given_name & surname\n- Inspect Exemplar Candidate Matches: In exemplar matches, names show occasional swaps (given_name 'tylah' / surname 'kempe' vs given_name 'kempe' / surname 'tylah') and occasional minor typos/truncations ('emiily').\n- Inspect Statistical Profile: Low nulls (< 5%), moderate cardinality, average length ~5.9 - 6.5 characters.\n- Algorithm Trade-off Evaluation: 'jarowinkler' is the industry gold standard for person names due to prefix weighting and resilience to minor character insertions/deletions. 'cosine' fails on short strings and single-token typos.\n- Weight Justification: 0.5 each. High descriptive power, though name field transposition occurs in synthetic corruption datasets, so keeping both at moderate weight ensures balanced scoring.\n\n5. Column: street_number\n- Inspect Exemplar Candidate Matches: Exemplar pairs match identical numbers ('8.0' \u2194 '8.0', '68.0' \u2194 '68.0').\n- Inspect Statistical Profile: Low nulls (~3-6%), cardinality ~450.\n- Algorithm Trade-off Evaluation: Street numbers are discrete categorical identifiers; 'exact' is best because street number '8' vs '18' is a completely different location, making continuous metrics hazardous.\n- Weight Justification: 0.5. Essential address component for disambiguating street-level co-residents.\n\n6. Column: address_1 & address_2\n- Inspect Exemplar Candidate Matches: Exemplar 2 shows address field swapping ('frome street' in address_1 vs address_2) and multi-word street addresses ('arthur circle', 'kookaburra village').\n- Inspect Statistical Profile: Average length 11.7 - 14.65, low nulls for address_1 (~2-4%), address_2 nulls (~8-17%), high uniqueness.\n- Algorithm Trade-off Evaluation: Multi-word addresses benefit from 'cosine' similarity because street type words ('street', 'circle', 'village') and token order shifts or slight word recombinations are handled smoothly by token-level TF-IDF.\n- Weight Justification: address_1 at 0.6 (primary descriptive address field), address_2 at 0.4 (secondary address line).\n\n7. Column: suburb\n- Inspect Exemplar Candidate Matches: Suburbs are multi-word or single-word town names like 'adamstown heights', 'broken hill', 'taree' matching cleanly.\n- Inspect Statistical Profile: Low nulls (~1-2%), avg length ~9.3.\n- Algorithm Trade-off Evaluation: 'jarowinkler' handles short to medium town names and typographical errors effectively.\n- Weight Justification: 0.5. Geographic disambiguation.\n\n8. Column: postcode\n- Inspect Exemplar Candidate Matches: Exemplars match identically ('3133', '2870', '2477').\n- Inspect Statistical Profile: 0% nulls, cardinality ~1400-1700.\n- Algorithm Trade-off Evaluation: Postal codes are discrete postal zone identifiers where character difference denotes distinct regions. 'exact' is optimal.\n- Weight Justification: 0.5. Strong geographic anchor.\n\n9. Column: state\n- Inspect Exemplar Candidate Matches: Clean 2-letter codes ('sa', 'vic', 'qld').\n- Inspect Statistical Profile: Very low cardinality (8 to 50), low nulls (~1-2%).\n- Algorithm Trade-off Evaluation: 'exact' binary match is ideal for standardized short state abbreviations.\n- Weight Justification: 0.3. Coarse geographic attribute with low entropy.",
  "matching_columns": {
    "given_name": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "suburb": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "state": {
      "algorithm": "exact",
      "weight": 0.3
    },
    "postcode": {
      "algorithm": "exact",
      "weight": 0.5
    },
    "soc_sec_id": {
      "algorithm": "damerau_levenshtein",
      "weight": 0.95
    },
    "date_of_birth": {
      "algorithm": "exact",
      "weight": 0.8
    },
    "address_2": {
      "algorithm": "cosine",
      "weight": 0.4
    },
    "address_1": {
      "algorithm": "cosine",
      "weight": 0.6
    },
    "street_number": {
      "algorithm": "exact",
      "weight": 0.5
    },
    "surname": {
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
| **Total Rows** | 5000 | 5000 |
| **Column Count** | 11 | 11 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.97)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec1409org" | "rec1409dup0" |
| given_name | "tylah" | "kempe" |
| surname | "kempe" | "tylah" |
| street_number | "8.0" | "8.0" |
| address_1 | "arthur circle" | "arthur circle" |
| address_2 | "tylden park" | "tylden park" |
| suburb | "adamstown heights" | "adamstown heights" |
| postcode | "3133" | "3133" |
| state | "sa" | "sa" |
| date_of_birth | "19721016.0" | "19721016.0" |
| soc_sec_id | "1844518" | "1844518" |

#### Candidate Match 2 (Overall Text Match Score: 0.96)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec4917org" | "rec4917dup0" |
| given_name | "" | "" |
| surname | "stauntonsmith" | "stauntonsmith" |
| street_number | "68.0" | "68.0" |
| address_1 | "frome street" | "kookaburra village" |
| address_2 | "kookaburra village" | "frome street" |
| suburb | "broken hill" | "broken hill" |
| postcode | "2870" | "2870" |
| state | "vic" | "vic" |
| date_of_birth | "19820117.0" | "19820117.0" |
| soc_sec_id | "6922783" | "6922783" |

#### Candidate Match 3 (Overall Text Match Score: 0.96)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec3571org" | "rec3571dup0" |
| given_name | "emiily" | "wilsonwheeler" |
| surname | "wilsonwheeler" | "emiily" |
| street_number | "1.0" | "1.0" |
| address_1 | "woolcock street" | "woolcock street" |
| address_2 | "willandra" | "willandra" |
| suburb | "taree" | "taree" |
| postcode | "2477" | "2477" |
| state | "qld" | "qld" |
| date_of_birth | "19610625.0" | "19610625.0" |
| soc_sec_id | "8119451" | "8119451" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **rec_id** | 0.0% | 0.0% | 100.0% | 100.0% | 5000 | 5000 | 9.78 | 10.78 | "rec1409org" ↔ "rec1409dup0" |
| **given_name** | 2.24% | 4.68% | 15.38% | 34.04% | 769 | 1702 | 5.9 | 5.93 | "tylah" ↔ "kempe" |
| **surname** | 0.96% | 2.04% | 36.54% | 52.66% | 1827 | 2633 | 6.54 | 6.52 | "kempe" ↔ "tylah" |
| **street_number** | 3.16% | 5.74% | 9.0% | 8.96% | 450 | 448 | N/A | N/A | "8.0" ↔ "8.0" |
| **address_1** | 1.96% | 4.4% | 47.98% | 70.32% | 2399 | 3516 | 14.65 | 14.5 | "arthur circle" ↔ "arthur circle" |
| **address_2** | 8.4% | 17.02% | 51.5% | 66.1% | 2575 | 3305 | 11.76 | 12.01 | "tylden park" ↔ "tylden park" |
| **suburb** | 1.1% | 2.12% | 32.68% | 48.06% | 1634 | 2403 | 9.31 | 9.32 | "adamstown heights" ↔ "adamstown heights" |
| **postcode** | 0.0% | 0.0% | 28.38% | 33.82% | 1419 | 1691 | N/A | N/A | "3133" ↔ "3133" |
| **state** | 1.0% | 2.14% | 0.16% | 1.0% | 8 | 50 | 2.82 | 2.82 | "sa" ↔ "sa" |
| **date_of_birth** | 1.88% | 3.98% | 91.76% | 90.1% | 4588 | 4505 | N/A | N/A | "19721016.0" ↔ "19721016.0" |
| **soc_sec_id** | 0.0% | 0.0% | 100.0% | 100.0% | 5000 | 5000 | N/A | N/A | "1844518" ↔ "1844518" |
```
</details>

