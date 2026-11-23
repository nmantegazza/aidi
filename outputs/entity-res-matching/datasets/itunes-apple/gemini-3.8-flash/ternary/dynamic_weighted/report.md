# Matching Benchmark: itunes-apple — Dynamic Weighted

- **Domain**: music
- **Strategy**: Dynamic Weighted
- **Model**: gemini-3.8-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9907 | 0.0000 |
| Recall | 0.8030 | 0.0000 |
| F1 Score | 0.8870 | 0.0000 |
| Execution Time (s) | 1.0089 | 0.0289 |
| Peak Memory (MB) | 8.47 | 0.28 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 11,094 |
| Completion Tokens | 3,522 |
| Total Tokens | 14,616 |
| Estimated Cost (USD) | $0.0215 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9091 | 0.0000 |
| Potential F1 Ceiling | 0.9481 | 0.0000 |
| LLM Workload Ratio | 43.0% | - |
| Unrecoverable Loss | 0.0909 | - |
| Uncertain Purity | 6.0% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 100.00% |
| Consistent Matches | 107 |
| Flaky Matches | 0 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9907 | 0.8030 | 0.8870 | 0.9091 | 0.9481 | 42.5% | 6.1% | 106 | 1 | 26 | 1.0405 | 8.31 | 4811 | $0.0069 |  |
| 2 | SUCCESS | 0.9907 | 0.8030 | 0.8870 | 0.9091 | 0.9481 | 43.2% | 6.0% | 106 | 1 | 26 | 1.0024 | 8.79 | 4885 | $0.0072 |  |
| 3 | SUCCESS | 0.9907 | 0.8030 | 0.8870 | 0.9091 | 0.9481 | 43.2% | 6.0% | 106 | 1 | 26 | 0.9837 | 8.30 | 4920 | $0.0074 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.4772 | 0.8004 | [0.3359, 0.6184, 0.9217] |
| 2 | dynamic_skew | 0.4803 | 0.8010 | [0.3423, 0.6182, 0.9229] |
| 3 | dynamic_skew | 0.4731 | 0.7965 | [0.3369, 0.6092, 0.9213] |

## LLM Strategy Configuration & Prompts

- **Model**: `gemini-3.8-flash`
- **Provider**: `google-cloud`
- **Latency**: `8.42s`
- **Log File**: `outputs/logs/llm_calls/20260919_164852_780814_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "1. **Song_Name**:\n- *Exemplar Inspection*: Song titles can be identical ('diet mountain dew') or contain remix/version suffixes ('west coast mk remix' vs 'west coast zhu remix', 'how deep is your love disciples unorthodox remix').\n- *Statistical Profile*: High cardinality (3013 / 38273), 0% nulls, avg length ~22-23 chars. Primary identifying attribute of songs.\n- *Algorithm Trade-off*: Multi-word song titles benefit from `cosine` similarity to handle token additions/remixes/editions gracefully without being over-penalized by position or minor token shifts.\n- *Weight Justification*: Assigned 0.9 as it is the most critical core identity field distinguishing track records.\n\n2. **Artist_Name**:\n- *Exemplar Inspection*: Typically clean and consistent artist names ('lana del rey', 'calvin harris disciples').\n- *Statistical Profile*: 0% nulls, moderate cardinality (932 / 1770), avg length ~12-15 chars.\n- *Algorithm Trade-off*: Short string (< 20 chars). `jarowinkler` is ideal for handling small character variations, typos, or slight variations in artist names, while `cosine` fails on single-token or slightly misspelled names.\n- *Weight Justification*: Assigned 0.8 as the primary co-identifying attribute alongside the song title.\n\n3. **Album_Name**:\n- *Exemplar Inspection*: Album names often differ by appended qualifiers such as 'explicit' or 'ep' ('born to die the paradise edition' vs '... explicit', 'how deep is your love remixes ep' vs '... remixes').\n- *Statistical Profile*: 0% nulls in Source A, 0.03% in B, avg length ~24 chars.\n- *Algorithm Trade-off*: Multi-word descriptive text with token additions/omissions makes `cosine` the optimal choice, allowing partial token overlap without heavily penalizing extra words.\n- *Weight Justification*: Assigned 0.6 as a strong descriptive attribute confirming the track/release context.\n\n4. **Released**:\n- *Exemplar Inspection*: Formatted as timestamp/date strings ('2012-11-13 00:00:00'), matching exactly or closely across identical tracks.\n- *Statistical Profile*: Null % is 4.4% in A and 12.59% in B (both well below 50%). Good cardinality (668 / 1987).\n- *Algorithm Trade-off*: Calendar date field; `date` provides continuous similarity distance across release dates/years rather than binary rejection.\n- *Weight Justification*: Assigned 0.5 as a reliable temporal contextual attribute.\n\n5. **Time**:\n- *Exemplar Inspection*: Appears to represent song duration encoded as a time timestamp (e.g. '2026-09-19 03:42:00' representing 3m42s). In Match 1 and 3 they match exactly; in Match 2 they differ slightly ('05:26' vs '04:24').\n- *Statistical Profile*: Low nulls (2.22% / 0.19%), avg cardinality 397 / 819.\n- *Algorithm Trade-off*: `date` accounts for temporal difference/distance appropriately across formatted timestamps.\n- *Weight Justification*: Assigned 0.4 as supporting contextual attribute (track duration/time).\n\n6. **Price**:\n- *Exemplar Inspection*: Matches consistently (e.g., '129' / $1.29).\n- *Statistical Profile*: 0% nulls, low cardinality (6 / 10), avg length 3-4 chars.\n- *Algorithm Trade-off*: Numeric amount where `numeric_relative` accurately evaluates relative price differences.\n- *Weight Justification*: Assigned 0.2 as a weak supporting contextual feature.\n\n7. **Excluded Columns**:\n- `Sno`: Source-specific auto-increment row IDs.\n- `Album_Price`, `Customer_Rating`, `Label`: Present only in one source (100% missing in the other).\n- `CopyRight`: Lengthy, inconsistent publisher strings with disparate copyright phrasing ('c 2015 island records...' vs '2015 sony music...').\n- `Genre`: Highly disparate taxonomies ('alternativemusicrockadult alternative' vs 'alternative rock') with concatenated tokens in Source A.",
  "matching_columns": {
    "Artist_Name": {
      "algorithm": "jarowinkler",
      "weight": 0.8
    },
    "Album_Name": {
      "algorithm": "cosine",
      "weight": 0.6
    },
    "Price": {
      "algorithm": "numeric_relative",
      "weight": 0.2
    },
    "Time": {
      "algorithm": "date",
      "weight": 0.4
    },
    "Released": {
      "algorithm": "date",
      "weight": 0.5
    },
    "Song_Name": {
      "algorithm": "cosine",
      "weight": 0.9
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

