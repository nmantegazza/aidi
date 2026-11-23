# Matching Benchmark: itunes-apple — Dynamic Weighted

- **Domain**: music
- **Strategy**: Dynamic Weighted
- **Model**: deepseek-v4.1-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.8610 | 0.0046 |
| Recall | 0.7980 | 0.0358 |
| F1 Score | 0.8280 | 0.0197 |
| Execution Time (s) | 1.2538 | 0.0859 |
| Peak Memory (MB) | 8.80 | 0.01 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 11,364 |
| Completion Tokens | 12,086 |
| Total Tokens | 23,450 |
| Estimated Cost (USD) | $0.0000 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9167 | 0.0000 |
| Potential F1 Ceiling | 0.8880 | 0.0025 |
| LLM Workload Ratio | 42.6% | - |
| Unrecoverable Loss | 0.0833 | - |
| Uncertain Purity | 6.8% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 72.34% |
| Consistent Matches | 102 |
| Flaky Matches | 39 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.8651 | 0.8258 | 0.8450 | 0.9167 | 0.8901 | 41.7% | 5.3% | 109 | 17 | 23 | 1.2846 | 8.80 | 7949 | - |  |
| 2 | SUCCESS | 0.8560 | 0.8106 | 0.8327 | 0.9167 | 0.8853 | 42.5% | 6.1% | 107 | 18 | 25 | 1.3200 | 8.79 | 8116 | - |  |
| 3 | SUCCESS | 0.8621 | 0.7576 | 0.8065 | 0.9167 | 0.8885 | 43.6% | 8.9% | 100 | 16 | 32 | 1.1567 | 8.80 | 7385 | - |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.5044 | 0.7795 | [0.3657, 0.6431, 0.8704] |
| 2 | dynamic_skew | 0.4837 | 0.7465 | [0.3515, 0.6160, 0.8335] |
| 3 | dynamic_skew | 0.5379 | 0.8121 | [0.3890, 0.6868, 0.8957] |

## LLM Strategy Configuration & Prompts

- **Model**: `deepseek-v4.1-flash`
- **Provider**: `deepseek`
- **Latency**: `19.16s`
- **Log File**: `outputs/logs/llm_calls/20260919_164755_913979_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "MANDATORY 4-STEP PROTOCOL PER COLUMN\n\n--- Song_Name (SELECTED: cosine, w=0.70) ---\n1. Exemplar: \"diet mountain dew\"=\"diet mountain dew\" (identical), \"how deep is your love disciples unorthodox remix\"=identical, \"west coast mk remix\" vs \"west coast zhu remix\" (only one token differs). Multi-word free-text track titles.\n2. Profile: 0% null, cardinality 3013/38273, avg len 22.95/21.97. High variance, well populated.\n3. Algorithm: avg length ~23 (>=20) and multi-word, so token-level TF-IDF `cosine` is correct \u2014 it is order-invariant and tolerant of the added/omitted/remixed tokens seen in exemplars (score stays high despite the \"mk\"/\"zhu\" substitution). `jarowinkler` would over-penalize word order and length; `damerau_levenshtein` would collapse on multi-word reordering. Single-word name failures that plague cosine do not apply because titles are long multi-token strings.\n4. Weight: Track title is the single most decisive identity attribute for a music entity \u2192 0.70.\n\n--- Artist_Name (SELECTED: jarowinkler, w=0.65) ---\n1. Exemplar: identical in all three pairs (\"lana del rey\", \"calvin harris disciples\").\n2. Profile: 0% null, cardinality 932/1770, avg len 12.47/14.67 (short).\n3. Algorithm: short single-phrase names (< 20 chars). `jarowinkler` is prefix-weighted and robust to typos/phonetic/suffix variation on short strings, handling the space/punctuation variants and truncations likely across sources. `cosine` fails on short strings (a 1-char typo drops to 0.0); `damerau_levenshtein` over-penalizes length gaps. Jaro-Winkler is the best fit.\n4. Weight: Core identifying attribute (artist) that co-determines the track entity \u2192 0.65.\n\n--- Album_Name (SELECTED: cosine, w=0.55) ---\n1. Exemplar: \"born to die the paradise edition\" vs \"born to die the paradise edition explicit\" (trailing token added); \"how deep is your love remixes ep\" vs \"how deep is your love remixes\" (token dropped); \"west coast remix ep\" identical. Only token additions/omissions.\n2. Profile: 0% null (A) / 0.03% null (B), cardinality 1116/5050, avg len 24.17/24.26.\n3. Algorithm: long (>=20) multi-word title \u2192 `cosine` tolerates the extra/missing tokens (\"explicit\", \"ep\") while retaining high similarity. `jarowinkler` and `damerau_levenshtein` would be distorted by token additions and word-order changes.\n4. Weight: Strong descriptive attribute that groups releases; slightly below Song_Name in specificity \u2192 0.55.\n\n--- Released (SELECTED: date, w=0.30) ---\n1. Exemplar: identical full timestamps across all three pairs (\"2012-11-13 00:00:00\", etc.).\n2. Profile: null 4.4%/12.59% (<50%, acceptable), cardinality 668/1987.\n3. Algorithm: full calendar date/time value \u2192 `date` hierarchy matcher yields continuous similarity for small day/month shifts; `numeric_linear`/`numeric_relative` are nonsensical on dates and `exact` would be brittle to formatting.\n4. Weight: Supporting contextual attribute that corroborates but does not uniquely identify \u2192 0.30.\n\n--- Price (SELECTED: numeric_relative, w=0.20) ---\n1. Exemplar: \"129\"=\"129\" identical in all pairs.\n2. Profile: 0% null, cardinality 6/10 (low variance but >1, so retained), avg len 4.05/3.0.\n3. Algorithm: monetary amount spanning orders of magnitude \u2192 `numeric_relative` (scale-invariant percentage gap) is appropriate since a fixed absolute gap should be penalized differently on cheap vs expensive items. `exact` would be brittle to currency/rounding, `numeric_linear` distorts scale.\n4. Weight: Auxiliary supporting signal, low cardinality makes it non-discriminative alone \u2192 0.20.\n\n--- CopyRight (SELECTED: cosine, w=0.15) ---\n1. Exemplar: prefix shift \"2012 lana\u2026\" vs \"c 2012 lana\u2026\" (high overlap), BUT Candidate 3 diverges completely (\"2015 sony music entertainment uk limited\" vs \"c 2015 island records\u2026\"). Noisy/divergent when licensing differs.\n2. Profile: 0% null, cardinality 603/2553, avg len 61.2/34.17 (long, multi-word).\n3. Algorithm: long multi-word legal text \u2192 `cosine` captures the shared standard phrasing/artist tokens despite the \"c \" prefix, and correctly yields low similarity on genuinely divergent labels. `jarowinkler`/`damerau_levenshtein` would fail on long text and word-order shifts.\n4. Weight: Weak, noisy secondary signal (can legitimately differ for the same track) \u2192 0.15.\n\n--- Genre (SELECTED: cosine, w=0.10) ---\n1. Exemplar: divergent concatenated taxonomy \u2014 \"alternativemusicrockadult alternative\" vs \"alternative rock\"; \"dancemusicrock\" vs \"dance electronic\". Shares some stem tokens but vocabularies differ.\n2. Profile: 0% null, cardinality 383/430, avg len 31.47/16.04.\n3. Algorithm: multi-word strings; `cosine` at least credits the shared \"alternative\" token, whereas `exact` would be 0 and `jarowinkler` is unreliable on concatenated multi-word blobs. Known weakness on divergent taxonomies justifies the very low weight rather than exclusion.\n4. Weight: Weak supporting signal given the divergent taxonomy \u2192 0.10.\n\n--- EXCLUDED COLUMNS ---\n* Sno: auto-increment serial/source key (cardinality = row count, e.g. \"6088\" vs \"7967\"); no cross-source entity semantics \u2192 excluded per source-specific-key rule.\n* Album_Price (A only) and Customer_Rating (A only): no counterpart in Source B; cannot compute cross-source similarity \u2192 excluded.\n* Label (B only): no counterpart in Source A \u2192 excluded.\n* Time: despite 0.19\u20132.22% nulls, exemplar Candidate 2 (a confirmed match at 0.87) shows 05:26 vs 04:24 and 03:42 elsewhere \u2014 it is a non-semantic ingestion/processing timestamp that is noisy for the same entity \u2192 excluded rather than down-weighted.",
  "matching_columns": {
    "Song_Name": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "Artist_Name": {
      "algorithm": "jarowinkler",
      "weight": 0.65
    },
    "Album_Name": {
      "algorithm": "cosine",
      "weight": 0.55
    },
    "Released": {
      "algorithm": "date",
      "weight": 0.3
    },
    "Price": {
      "algorithm": "numeric_relative",
      "weight": 0.2
    },
    "CopyRight": {
      "algorithm": "cosine",
      "weight": 0.15
    },
    "Genre": {
      "algorithm": "cosine",
      "weight": 0.1
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

