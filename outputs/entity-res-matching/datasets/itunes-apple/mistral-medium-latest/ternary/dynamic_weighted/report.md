# Matching Benchmark: itunes-apple — Dynamic Weighted

- **Domain**: music
- **Strategy**: Dynamic Weighted
- **Model**: mistral-medium-latest
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.8090 | 0.0144 |
| Recall | 0.7601 | 0.0244 |
| F1 Score | 0.7838 | 0.0195 |
| Execution Time (s) | 1.0978 | 0.3069 |
| Peak Memory (MB) | 7.34 | 1.70 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 11,595 |
| Completion Tokens | 32,654 |
| Total Tokens | 44,249 |
| Estimated Cost (USD) | $0.2623 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9192 | 0.0044 |
| Potential F1 Ceiling | 0.8605 | 0.0076 |
| LLM Workload Ratio | 41.7% | - |
| Unrecoverable Loss | 0.0808 | - |
| Uncertain Purity | 9.3% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 75.35% |
| Consistent Matches | 107 |
| Flaky Matches | 35 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.7984 | 0.7500 | 0.7734 | 0.9167 | 0.8534 | 41.9% | 9.7% | 99 | 25 | 33 | 1.3447 | 8.32 | 11539 | $0.0634 |  |
| 2 | SUCCESS | 0.8033 | 0.7424 | 0.7717 | 0.9242 | 0.8595 | 41.7% | 10.7% | 98 | 24 | 34 | 1.1945 | 8.32 | 15200 | $0.0908 |  |
| 3 | SUCCESS | 0.8254 | 0.7879 | 0.8062 | 0.9167 | 0.8686 | 41.6% | 7.6% | 104 | 22 | 28 | 0.7541 | 5.38 | 17510 | $0.1081 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.4912 | 0.7647 | [0.3437, 0.6387, 0.8487] |
| 2 | dynamic_skew | 0.5323 | 0.8017 | [0.3815, 0.6830, 0.8808] |
| 3 | dynamic_skew | 0.5076 | 0.7808 | [0.3676, 0.6475, 0.8697] |

## LLM Strategy Configuration & Prompts

- **Model**: `mistral-medium-latest`
- **Provider**: `mistral`
- **Latency**: `42.55s`
- **Log File**: `outputs/logs/llm_calls/20260919_165232_888898_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "### Column-by-Column Reasoning (Mandatory 4-Step Protocol)\n\n**Album_Name**\n1. **Inspect Exemplar Candidate Matches**: Matching entities show minor word-level variations: \"born to die the paradise edition\" \u2194 \"born to die the paradise edition explicit\" (suffix addition), \"how deep is your love remixes ep\" \u2194 \"how deep is your love remixes\" (suffix truncation). Core words remain identical with small permutations.\n2. **Inspect Statistical Profile**: Null % (0.0%|0.03%) < 50%, cardinality (1116|5050) > 1, avg length (24.17|24.26) \u2265 20 characters. Passes all inclusion criteria.\n3. **Algorithm Trade-off Evaluation**: Multi-word text with average length >20 characters. `cosine` (TF-IDF) excels at word-level additions/omissions in longer text. `jarowinkler` is suboptimal for multi-word strings of this length. `damerau_levenshtein` fails on word reordering. `exact` fails on any variation. Thus `cosine` is optimal.\n4. **Weight Justification**: Primary identity attribute for music entities (0.7).\n\n**Artist_Name**\n1. **Inspect Exemplar Candidate Matches**: Perfect string matches in all exemplars: \"lana del rey\" \u2194 \"lana del rey\", \"calvin harris disciples\" \u2194 \"calvin harris disciples\". Expect minor typos in broader data (e.g., \"Smyth\" vs \"Smith\").\n2. **Inspect Statistical Profile**: Null % (0.0%|0.0%) < 50%, cardinality (932|1770) > 1, avg length (12.47|14.67) < 20 characters. Passes inclusion.\n3. **Algorithm Trade-off Evaluation**: Short strings (12-15 chars) representing names. `jarowinkler` handles typos/phonetic variants in short labels. `cosine` fails on strings <20 chars. `damerau_levenshtein` over-penalizes length mismatches. `exact` fails on any typo. Thus `jarowinkler` is optimal.\n4. **Weight Justification**: Core identity attribute (0.9).\n\n**CopyRight**\n1. **Inspect Exemplar Candidate Matches**: Minor character prefixes (\"2012...\" \u2194 \"c 2012...\" in Matches 1-2) and larger taxonomy shifts (\"sony music entertainment\" \u2194 \"island records...universal music\" in Match 3).\n2. **Inspect Statistical Profile**: Null % (0.0%|0.0%) < 50%, cardinality (603|2553) > 1, avg length (61.2|34.17) > 20 characters. Passes inclusion.\n3. **Algorithm Trade-off Evaluation**: Long multi-word text. `cosine` handles word additions/omissions and prefix variations robustly. `jarowinkler` fails on long text. `damerau_levenshtein` fails on length differences. `exact` fails on any variation. Thus `cosine` is optimal despite taxonomy shifts.\n4. **Weight Justification**: Supporting descriptive attribute (0.3).\n\n**Genre**\n1. **Inspect Exemplar Candidate Matches**: Significant taxonomy variations: \"alternativemusicrockadult alternative\" \u2194 \"alternative rock\" (concatenation + extra words), \"dancemusicrock\" \u2194 \"dance electronic\" (divergent vocabularies).\n2. **Inspect Statistical Profile**: Null % (0.0%|0.0%) < 50%, cardinality (383|430) > 1, avg length (31.47|16.04). Source A avg length >20. Passes inclusion.\n3. **Algorithm Trade-off Evaluation**: Multi-word text in Source A (avg 31.47 chars). `cosine` is the only viable option for multi-word text; taxonomy divergence is a known limitation but unavoidable. `jarowinkler` fails on multi-word. `damerau_levenshtein` fails on word reordering. Thus `cosine` is best available.\n4. **Weight Justification**: Weak signal due to taxonomy inconsistency (0.2).\n\n**Price**\n1. **Inspect Exemplar Candidate Matches**: Exact matches in all exemplars (\"129\" \u2194 \"129\"). Expect minor numeric discrepancies in broader data.\n2. **Inspect Statistical Profile**: Null % (0.0%|0.0%) < 50%, cardinality (6|10) > 1, avg length (4.05|3.0). Passes inclusion.\n3. **Algorithm Trade-off Evaluation**: Numeric monetary value. `numeric_linear` measures absolute uniform distance, appropriate for prices on consistent scales. `numeric_relative` would distort small absolute differences. String-based algorithms fail on numeric semantics. Thus `numeric_linear` is optimal.\n4. **Weight Justification**: Auxiliary contextual attribute (0.2).\n\n**Released**\n1. **Inspect Exemplar Candidate Matches**: Exact timestamp matches in all exemplars (\"2012-11-13 00:00:00\" \u2194 identical). Expect minor date shifts in broader data.\n2. **Inspect Statistical Profile**: Null % (4.4%|12.59%) < 50%, cardinality (668|1987) > 1. Passes inclusion.\n3. **Algorithm Trade-off Evaluation**: Calendar date field. `date` algorithm handles hierarchical date matching (year > month > day), providing continuous similarity for small shifts. String-based algorithms fail on date semantics. Thus `date` is optimal.\n4. **Weight Justification**: Strong contextual attribute (0.5).\n\n**Song_Name**\n1. **Inspect Exemplar Candidate Matches**: Mostly exact matches (\"diet mountain dew\", \"how deep is your love disciples unorthodox remix\"). One case shows remix variant difference (\"west coast mk remix\" \u2194 \"west coast zhu remix\"), but overall entity match remains high due to other fields.\n2. **Inspect Statistical Profile**: Null % (0.0%|0.0%) < 50%, cardinality (3013|38273) > 1, avg length (22.95|21.97) \u2265 20 characters. Passes inclusion.\n3. **Algorithm Trade-off Evaluation**: Multi-word text with avg length >20. `cosine` handles word-level variations and minor permutations in longer strings. `jarowinkler` fails on multi-word. `damerau_levenshtein` fails on word reordering. `exact` fails on any variation. Thus `cosine` is optimal.\n4. **Weight Justification**: Primary identity attribute (0.8).\n\n### Excluded Columns\n- **Sno**: Internal auto-increment ID (system attribute).\n- **Album_Price**: Only present in Source A (no cross-source comparison possible).\n- **Customer_Rating**: Only present in Source A.\n- **Time**: System timestamp (internal attribute).\n- **Label**: Only present in Source B.",
  "matching_columns": {
    "Album_Name": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "Artist_Name": {
      "algorithm": "jarowinkler",
      "weight": 0.9
    },
    "CopyRight": {
      "algorithm": "cosine",
      "weight": 0.3
    },
    "Genre": {
      "algorithm": "cosine",
      "weight": 0.2
    },
    "Price": {
      "algorithm": "numeric_linear",
      "weight": 0.2
    },
    "Released": {
      "algorithm": "date",
      "weight": 0.5
    },
    "Song_Name": {
      "algorithm": "cosine",
      "weight": 0.8
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
| **Total Rows** | 6907 | 55923 |
| **Column Count** | 11 | 10 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.89)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| Sno | "6088" | "7967" |
| Album_Name | "born to die the paradise edition" | "born to die the paradise edition explicit" |
| Artist_Name | "lana del rey" | "lana del rey" |
| CopyRight | "2012 lana del rey under exclusive licence to polydor ltd uk under exclusive licence to interscope records in the usa" | "c 2012 lana del rey under exclusive licence to polydor ltd uk under exclusive licence to interscope records in the usa" |
| Genre | "alternativemusicrockadult alternative" | "alternative rock" |
| Price | "129" | "129" |
| Released | "2012-11-13 00:00:00" | "2012-11-13 00:00:00" |
| Song_Name | "diet mountain dew" | "diet mountain dew" |
| Time | "2026-09-19 03:42:00" | "2026-09-19 03:42:00" |

#### Candidate Match 2 (Overall Text Match Score: 0.87)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| Sno | "18" | "54025" |
| Album_Name | "west coast remix ep" | "west coast remix ep" |
| Artist_Name | "lana del rey" | "lana del rey" |
| CopyRight | "2014 lana del rey under exclusive licence to polydor ltd uk under exclusive licence to interscope records in the usa" | "c 2014 lana del rey under exclusive licence to polydor ltd uk under exclusive licence to interscope records in the usa" |
| Genre | "alternativemusicrock" | "alternative rock" |
| Price | "129" | "129" |
| Released | "2014-07-13 00:00:00" | "2014-07-13 00:00:00" |
| Song_Name | "west coast mk remix" | "west coast zhu remix" |
| Time | "2026-09-19 05:26:00" | "2026-09-19 04:24:00" |

#### Candidate Match 3 (Overall Text Match Score: 0.86)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| Sno | "3144" | "22527" |
| Album_Name | "how deep is your love remixes ep" | "how deep is your love remixes" |
| Artist_Name | "calvin harris disciples" | "calvin harris disciples" |
| CopyRight | "2015 sony music entertainment uk limited" | "c 2015 island records a division of universal music operations limited" |
| Genre | "dancemusicrock" | "dance electronic" |
| Price | "129" | "129" |
| Released | "2015-08-07 00:00:00" | "2015-08-07 00:00:00" |
| Song_Name | "how deep is your love disciples unorthodox remix" | "how deep is your love disciples unorthodox remix" |
| Time | "2026-09-19 06:04:00" | "2026-09-19 06:04:00" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sno** | 0.0% | 0.0% | 100.0% | 100.0% | 6907 | 55923 | N/A | N/A | "6088" ↔ "7967" |
| **Album_Name** | 0.0% | 0.03% | 16.16% | 9.03% | 1116 | 5050 | 24.17 | 24.26 | "born to die the paradise edition" ↔ "born to die the paradise edition explicit" |
| **Album_Price** | 0.0% | N/A | 0.68% | N/A | 47 | N/A | 3.36 | N/A | N/A |
| **Artist_Name** | 0.0% | 0.0% | 13.49% | 3.17% | 932 | 1770 | 12.47 | 14.67 | "lana del rey" ↔ "lana del rey" |
| **CopyRight** | 0.0% | 0.0% | 8.73% | 4.57% | 603 | 2553 | 61.2 | 34.17 | "2012 lana del rey under exclusive licence to polydor ltd uk under exclusive licence to interscope records in the usa" ↔ "c 2012 lana del rey under exclusive licence to polydor ltd uk under exclusive licence to interscope records in the usa" |
| **Customer_Rating** | 0.91% | N/A | 13.81% | N/A | 954 | N/A | N/A | N/A | N/A |
| **Genre** | 0.0% | 0.0% | 5.55% | 0.77% | 383 | 430 | 31.47 | 16.04 | "alternativemusicrockadult alternative" ↔ "alternative rock" |
| **Price** | 0.0% | 0.0% | 0.09% | 0.02% | 6 | 10 | 4.05 | 3.0 | "129" ↔ "129" |
| **Released** | 4.4% | 12.59% | 9.67% | 3.55% | 668 | 1987 | N/A | N/A | "2012-11-13 00:00:00" ↔ "2012-11-13 00:00:00" |
| **Song_Name** | 0.0% | 0.0% | 43.62% | 68.44% | 3013 | 38273 | 22.95 | 21.97 | "diet mountain dew" ↔ "diet mountain dew" |
| **Time** | 2.22% | 0.19% | 5.75% | 1.46% | 397 | 819 | N/A | N/A | "2026-09-19 03:42:00" ↔ "2026-09-19 03:42:00" |
| **Label** | N/A | 0.0% | N/A | 3.1% | N/A | 1732 | N/A | 15.25 | N/A |
```
</details>

