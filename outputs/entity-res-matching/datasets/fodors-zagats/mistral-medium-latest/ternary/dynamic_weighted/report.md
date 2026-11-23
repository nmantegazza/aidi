# Matching Benchmark: fodors-zagats — Dynamic Weighted

- **Domain**: restaurants
- **Strategy**: Dynamic Weighted
- **Model**: mistral-medium-latest
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9881 | 0.0206 |
| Recall | 0.9792 | 0.0186 |
| F1 Score | 0.9836 | 0.0180 |
| Execution Time (s) | 0.6221 | 0.0644 |
| Peak Memory (MB) | 1.97 | 0.00 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 9,111 |
| Completion Tokens | 30,302 |
| Total Tokens | 39,413 |
| Estimated Cost (USD) | $0.2409 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 1.0000 | 0.0000 |
| Potential F1 Ceiling | 0.9939 | 0.0105 |
| LLM Workload Ratio | 44.4% | - |
| Unrecoverable Loss | 0.0000 | - |
| Uncertain Purity | 0.1% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 93.10% |
| Consistent Matches | 108 |
| Flaky Matches | 8 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9643 | 0.9643 | 0.9643 | 1.0000 | 0.9818 | 50.8% | 0.1% | 108 | 4 | 4 | 0.5883 | 1.97 | 12363 | $0.0745 |  |
| 2 | SUCCESS | 1.0000 | 0.9732 | 0.9864 | 1.0000 | 1.0000 | 28.5% | 0.2% | 109 | 0 | 3 | 0.6964 | 1.97 | 15090 | $0.0950 |  |
| 3 | SUCCESS | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 53.8% | 0.0% | 112 | 0 | 0 | 0.5816 | 1.97 | 11960 | $0.0715 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.3848 | 0.7169 | [0.3253, 0.4444, 0.8986] |
| 2 | dynamic_skew | 0.2987 | 0.6571 | [0.2500, 0.3475, 0.8635] |
| 3 | dynamic_skew | 0.3465 | 0.7123 | [0.2961, 0.3970, 0.9225] |

## LLM Strategy Configuration & Prompts

- **Model**: `mistral-medium-latest`
- **Provider**: `mistral`
- **Latency**: `52.21s`
- **Log File**: `outputs/logs/llm_calls/20260919_164524_083072_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "### Mandatory 4-Step Column Reasoning Protocol\n\n#### Column: **name**\n1. **Inspect Exemplar Candidate Matches**: Matching entities exhibit word-order permutation (\"hotel belair\" \u2194 \"belair hotel\") and exact matches (\"granita\", \"campton place\"). No sub-word typos observed.\n2. **Inspect Statistical Profile**: Null % = 0.0%, cardinality = 528/331 (high), avg length = 12.05/13.67 characters (**< 20**).\n3. **Algorithm Trade-off Evaluation**: \n   - `cosine` is **excluded** because avg length < 20 chars (guideline explicitly warns it fails on short strings).\n   - `jarowinkler` is **selected** because it excels on short strings and names, handling minor permutations robustly.\n   - `damerau_levenshtein` is **rejected** as it targets codes/serials, not natural language names.\n4. **Weight Justification**: Name is a **primary descriptive attribute** for hotels (critical for identification). Assigned **0.7** (within 0.5\u20130.7 range for strong descriptors).\n\n---\n\n#### Column: **addr**\n1. **Inspect Exemplar Candidate Matches**: All matches show **exact string equality** (\"701 stone canyon rd\", \"23725 w malibu rd\", \"340 stockton st\").\n2. **Inspect Statistical Profile**: Null % = 0.0%, cardinality = 519/322 (high), avg length = 21.57/15.79 (**Source A \u2265 20**).\n3. **Algorithm Trade-off Evaluation**:\n   - `cosine` is **selected** because addresses are multi-word free text with avg length \u2265 20 in Source A, and token-level matching (order-invariant) is ideal for street addresses.\n   - `jarowinkler` is **rejected** as it underperforms on longer multi-word text.\n   - `damerau_levenshtein` is **rejected** (not for free text).\n4. **Weight Justification**: Address is a **strong descriptive attribute** that uniquely locates entities. Assigned **0.7** (0.5\u20130.7 range).\n\n---\n\n#### Column: **city**\n1. **Inspect Exemplar Candidate Matches**: All matches are **exact** (\"bel air\", \"malibu\", \"san francisco\").\n2. **Inspect Statistical Profile**: Null % = 0.0%, cardinality = 16/46 (**low**), avg length = 9.34/10.2 (**< 20**).\n3. **Algorithm Trade-off Evaluation**:\n   - `jarowinkler` is **selected** for short city names; handles potential minor typos (e.g., \"san francisco\" vs \"san francisco\").\n   - `exact` is **rejected** due to zero tolerance for typos.\n   - `cosine` is **rejected** (avg length < 20).\n4. **Weight Justification**: City is a **supporting contextual attribute** with low cardinality (weak discriminator). Assigned **0.3** (0.2\u20130.4 range).\n\n---\n\n#### Column: **phone**\n1. **Inspect Exemplar Candidate Matches**: All matches are **exact** (\"3104721211\", \"3104560488\", \"4159555555\").\n2. **Inspect Statistical Profile**: Null % = 0.0%, cardinality = 528/329 (high), avg length = 10.02/10.0 (fixed 10-digit format).\n3. **Algorithm Trade-off Evaluation**:\n   - `damerau_levenshtein` is **selected** because phone numbers are alphanumeric codes where digit transpositions (e.g., \"1234567890\" vs \"1234567809\") or single-digit errors are plausible.\n   - `jarowinkler` is **rejected** (less optimal for pure numeric codes).\n   - `exact` is **rejected** (too strict for real-world phone number variations).\n4. **Weight Justification**: Phone numbers are **core identity attributes** (like tax IDs/emails). Assigned **0.9** (0.8\u20131.0 range).\n\n---\n\n#### Column: **type**\n1. **Inspect Exemplar Candidate Matches**: Mostly exact (\"californian\"), but **divergent taxonomy** observed (\"american\" \u2194 \"american new\").\n2. **Inspect Statistical Profile**: Null % = 0.0%, cardinality = 40/58 (medium), avg length = 8.46/9.21 (**< 20**).\n3. **Algorithm Trade-off Evaluation**:\n   - `jarowinkler` is **selected** for short descriptive strings; resilient to minor additions/abbreviations.\n   - `cosine` is **rejected** (avg length < 20).\n   - `damerau_levenshtein` is **rejected** (not for descriptive text).\n4. **Weight Justification**: Type is a **supporting contextual attribute** (category). Assigned **0.3** (0.2\u20130.4 range).\n\n---\n\n#### Column: **class**\n1. **Inspect Exemplar Candidate Matches**: All matches are **exact numeric equality** (\"2\" \u2194 \"2\", \"8\" \u2194 \"8\", \"98\" \u2194 \"98\").\n2. **Inspect Statistical Profile**: Null % = 0.0%, cardinality = 533/331 (**100% unique**), avg length = N/A (numeric).\n3. **Algorithm Trade-off Evaluation**:\n   - `exact` is **selected** because class appears to be a discrete numeric code (e.g., rating/classification ID) where any discrepancy = distinct entities.\n   - Numeric algorithms (`numeric_linear`, `numeric_relative`) are **rejected** as class is not a measurement (e.g., no partial matches like \"2\" vs \"2.1\" observed).\n4. **Weight Justification**: Class is a **supporting contextual attribute** with high cardinality. Assigned **0.2** (0.05\u20130.19 range).\n\n---\n\n#### Excluded Column: **id**\n- **Reason**: Source-specific auto-increment key (explicit exclusion rule).",
  "matching_columns": {
    "name": {
      "algorithm": "jarowinkler",
      "weight": 0.7
    },
    "addr": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "city": {
      "algorithm": "jarowinkler",
      "weight": 0.3
    },
    "phone": {
      "algorithm": "damerau_levenshtein",
      "weight": 0.9
    },
    "type": {
      "algorithm": "jarowinkler",
      "weight": 0.3
    },
    "class": {
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
| **Total Rows** | 533 | 331 |
| **Column Count** | 7 | 7 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.96)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "536" | "221" |
| name | "hotel belair" | "belair hotel" |
| addr | "701 stone canyon rd" | "701 stone canyon rd" |
| city | "bel air" | "bel air" |
| phone | "3104721211" | "3104721211" |
| type | "californian" | "californian" |
| class | "2" | "2" |

#### Candidate Match 2 (Overall Text Match Score: 0.95)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "542" | "227" |
| name | "granita" | "granita" |
| addr | "23725 w malibu rd" | "23725 w malibu rd" |
| city | "malibu" | "malibu" |
| phone | "3104560488" | "3104560488" |
| type | "californian" | "californian" |
| class | "8" | "8" |

#### Candidate Match 3 (Overall Text Match Score: 0.95)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "632" | "317" |
| name | "campton place" | "campton place" |
| addr | "340 stockton st" | "340 stockton st" |
| city | "san francisco" | "san francisco" |
| phone | "4159555555" | "4159555555" |
| type | "american" | "american new" |
| class | "98" | "98" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **id** | 0.0% | 0.0% | 100.0% | 100.0% | 533 | 331 | N/A | N/A | "536" ↔ "221" |
| **name** | 0.0% | 0.0% | 99.06% | 100.0% | 528 | 331 | 12.05 | 13.67 | "hotel belair" ↔ "belair hotel" |
| **addr** | 0.0% | 0.0% | 97.37% | 97.28% | 519 | 322 | 21.57 | 15.79 | "701 stone canyon rd" ↔ "701 stone canyon rd" |
| **city** | 0.0% | 0.0% | 3.0% | 13.9% | 16 | 46 | 9.34 | 10.2 | "bel air" ↔ "bel air" |
| **phone** | 0.0% | 0.0% | 99.06% | 99.4% | 528 | 329 | 10.02 | 10.0 | "3104721211" ↔ "3104721211" |
| **type** | 0.0% | 0.0% | 7.5% | 17.52% | 40 | 58 | 8.46 | 9.21 | "californian" ↔ "californian" |
| **class** | 0.0% | 0.0% | 100.0% | 100.0% | 533 | 331 | N/A | N/A | "2" ↔ "2" |
```
</details>

