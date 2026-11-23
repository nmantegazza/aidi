# Matching Benchmark: fodors-zagats — Dynamic Weighted

- **Domain**: restaurants
- **Strategy**: Dynamic Weighted
- **Model**: gemini-3.8-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9730 | 0.0000 |
| Recall | 0.9643 | 0.0000 |
| F1 Score | 0.9686 | 0.0000 |
| Execution Time (s) | 0.6252 | 0.0407 |
| Peak Memory (MB) | 2.04 | 0.13 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 8,583 |
| Completion Tokens | 3,545 |
| Total Tokens | 12,128 |
| Estimated Cost (USD) | $0.0197 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9911 | 0.0000 |
| Potential F1 Ceiling | 0.9819 | 0.0000 |
| LLM Workload Ratio | 29.8% | - |
| Unrecoverable Loss | 0.0089 | - |
| Uncertain Purity | 0.2% | - |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9730 | 0.9643 | 0.9686 | 0.9911 | 0.9819 | 29.8% | 0.2% | 108 | 3 | 4 | 0.6701 | 2.12 | 4105 | $0.0068 |  |
| 2 | SUCCESS | 0.9730 | 0.9643 | 0.9686 | 0.9911 | 0.9819 | 29.8% | 0.2% | 108 | 3 | 4 | 0.5909 | 2.12 | 4105 | $0.0068 |  |
| 3 | SUCCESS | 0.9730 | 0.9643 | 0.9686 | 0.9911 | 0.9819 | 29.8% | 0.2% | 108 | 3 | 4 | 0.6145 | 1.89 | 3918 | $0.0061 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 2 | dynamic_skew | 0.3321 | 0.6992 | [0.2782, 0.3861, 0.9080] |

## LLM Strategy Configuration & Prompts

- **Model**: `gemini-3.8-flash`
- **Provider**: `google-cloud`
- **Latency**: `8.93s`
- **Log File**: `outputs/logs/llm_calls/20260919_164230_415519_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "1. id:\n- Step 1 (Exemplar Inspection): Candidate 1 shows '536' vs '221'. These are internal dataset-specific auto-increment row IDs.\n- Step 2 (Statistical Profile): 0% nulls, 100% uniqueness in both datasets.\n- Step 3 (Algorithm Trade-off): Excluded per rule Task 1b as a source-specific key.\n- Step 4 (Weight Justification): Excluded.\n\n2. class:\n- Step 1 (Exemplar Inspection): Values align as '2' \u2194 '2', '8' \u2194 '8', '98' \u2194 '98'. However, in benchmark restaurant datasets, 'class' is often a ground-truth cluster ID or partition label (unique % is 100%, cardinality matches row counts 533 and 331). Using it would leak ground-truth evaluation labels.\n- Step 2 (Statistical Profile): 100% unique in both sources, exactly matching row counts.\n- Step 3 (Algorithm Trade-off): Excluded as it functions as an internal ground-truth clustering ID / key.\n- Step 4 (Weight Justification): Excluded.\n\n3. phone:\n- Step 1 (Exemplar Inspection): Exemplars show exact 10-digit strings without formatting, e.g., '3104721211' \u2194 '3104721211' and '4159555555' \u2194 '4159555555'.\n- Step 2 (Statistical Profile): 0.0% nulls, ~99% uniqueness in both datasets, average length is ~10.0 chars.\n- Step 3 (Algorithm Trade-off): Phone numbers are structured alphanumeric sequences where character positions and single digit typos/transpositions are critical. `damerau_levenshtein` is the optimal algorithm for digit codes/phone numbers. `cosine` would fail as it's a single token.\n- Step 4 (Weight Justification): Core identity attribute; phone number uniquely identifies restaurant locations. Weight assigned: 0.9.\n\n4. name:\n- Step 1 (Exemplar Inspection): Exemplar 1 shows token inversion: 'hotel belair' \u2194 'belair hotel'. Exemplars 2 & 3 show exact matches ('granita', 'campton place').\n- Step 2 (Statistical Profile): 0.0% nulls, ~99-100% uniqueness, avg length 12-14 chars.\n- Step 3 (Algorithm Trade-off): 'hotel belair' vs 'belair hotel' demonstrates word permutation/inversion across sources. `jarowinkler` is heavily order/prefix dependent and penalizes word inversions severely. `cosine` (TF-IDF token similarity) handles token permutations like 'hotel belair' vs 'belair hotel' with a perfect score (1.0).\n- Step 4 (Weight Justification): Primary descriptive attribute that strongly identifies the establishment. Weight assigned: 0.7.\n\n5. addr:\n- Step 1 (Exemplar Inspection): Exemplars show full street addresses, e.g., '701 stone canyon rd', '23725 w malibu rd', '340 stockton st'.\n- Step 2 (Statistical Profile): 0.0% nulls, ~97% uniqueness, avg length 16-22 chars (multi-word text).\n- Step 3 (Algorithm Trade-off): Addresses are multi-token strings where tokens can occasionally vary in position or include abbreviations. `cosine` is ideal for multi-word addresses with standard spelling.\n- Step 4 (Weight Justification): Strong descriptive/locational attribute confirming identity. Weight assigned: 0.6.\n\n6. city:\n- Step 1 (Exemplar Inspection): Exemplars show exact city names like 'bel air', 'malibu', 'san francisco'.\n- Step 2 (Statistical Profile): 0.0% nulls, low uniqueness (3% - 14%), cardinality 16-46, avg length 9-10 chars.\n- Step 3 (Algorithm Trade-off): Short geographic names where typos or small prefix variations may occur. `jarowinkler` is the standard and most resilient algorithm for short city names.\n- Step 4 (Weight Justification): Auxiliary contextual attribute; shared by many restaurants. Weight assigned: 0.3.\n\n7. type:\n- Step 1 (Exemplar Inspection): Exemplars show cuisine categories, e.g., 'californian' \u2194 'californian', 'american' \u2194 'american new'.\n- Step 2 (Statistical Profile): 0.0% nulls, cardinality 40-58, avg length 8.5-9.2 chars.\n- Step 3 (Algorithm Trade-off): Short category strings with slight prefix/suffix variations ('american' vs 'american new'). `jarowinkler` provides partial credit for shared prefixes on short categorical labels.\n- Step 4 (Weight Justification): Weak supporting contextual attribute. Weight assigned: 0.2.",
  "matching_columns": {
    "phone": {
      "algorithm": "damerau_levenshtein",
      "weight": 0.9
    },
    "name": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "city": {
      "algorithm": "jarowinkler",
      "weight": 0.3
    },
    "type": {
      "algorithm": "jarowinkler",
      "weight": 0.2
    },
    "addr": {
      "algorithm": "cosine",
      "weight": 0.6
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

