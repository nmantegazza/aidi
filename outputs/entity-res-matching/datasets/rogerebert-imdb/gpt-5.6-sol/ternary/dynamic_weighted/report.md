# Matching Benchmark: rogerebert-imdb — Dynamic Weighted

- **Domain**: movies
- **Strategy**: Dynamic Weighted
- **Model**: gpt-5.6-sol
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9828 | 0.0044 |
| Recall | 0.5546 | 0.0196 |
| F1 Score | 0.7090 | 0.0165 |
| Execution Time (s) | 0.4246 | 0.0112 |
| Peak Memory (MB) | 1.27 | 0.00 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 8,712 |
| Completion Tokens | 8,474 |
| Total Tokens | 17,186 |
| Estimated Cost (USD) | $0.1798 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9751 | 0.0000 |
| Potential F1 Ceiling | 0.9789 | 0.0022 |
| LLM Workload Ratio | 33.5% | - |
| Unrecoverable Loss | 0.0249 | - |
| Uncertain Purity | 81.1% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 89.66% |
| Consistent Matches | 130 |
| Flaky Matches | 15 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9848 | 0.5394 | 0.6971 | 0.9751 | 0.9800 | 34.9% | 80.8% | 130 | 2 | 111 | 0.4308 | 1.27 | 5983 | $0.0687 |  |
| 2 | SUCCESS | 0.9858 | 0.5768 | 0.7277 | 0.9751 | 0.9804 | 31.6% | 81.4% | 139 | 2 | 102 | 0.4314 | 1.27 | 5676 | $0.0570 |  |
| 3 | SUCCESS | 0.9778 | 0.5477 | 0.7021 | 0.9751 | 0.9764 | 34.0% | 81.1% | 132 | 3 | 109 | 0.4117 | 1.27 | 5527 | $0.0541 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.6262 | 0.7789 | [0.5317, 0.7208, 0.8176] |
| 2 | dynamic_skew | 0.6550 | 0.8059 | [0.5595, 0.7505, 0.8428] |
| 3 | dynamic_skew | 0.6167 | 0.7702 | [0.5221, 0.7114, 0.8094] |

## LLM Strategy Configuration & Prompts

- **Model**: `gpt-5.6-sol`
- **Provider**: `openai`
- **Latency**: `42.25s`
- **Log File**: `outputs/logs/llm_calls/20260919_170611_194945_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "### id\n1. **Inspect Exemplar Candidate Matches**: The values differ for known matches (`1410` vs `640`, `543` vs `221`, and `1497` vs `622`), showing that these are source-local record keys rather than cross-source entity identifiers.\n2. **Inspect Statistical Profile**: The field is fully populated and effectively unique in both sources (3,556 vs 6,913 distinct values), a classic internal-key profile.\n3. **Algorithm Trade-off Evaluation**: Exclude it under the source-specific-key rule. `exact` would reject true matches, while fuzzy or numeric comparisons could create meaningless similarity between unrelated internal IDs.\n4. **Weight Justification**: No weight is assigned because the column is not valid matching evidence.\n\n### movie_name\n1. **Inspect Exemplar Candidate Matches**: All three known pairs have identical titles. Titles are short phrases, and production data may still contain minor spelling, punctuation, spacing, or suffix differences.\n2. **Inspect Statistical Profile**: Null rates are 0% in both sources, cardinality is high (3,417 and 6,492), uniqueness is about 96.09% and 93.91%, and average length is only about 15 characters. It is highly discriminative and passes all exclusion checks.\n3. **Algorithm Trade-off Evaluation**: Choose `jarowinkler` because the strings are short and title variants may involve small character-level edits. Word-level `cosine` is unsafe below 20 characters and can collapse when a short title contains one misspelled or differently joined token. `exact` is unnecessarily brittle, while Damerau-Levenshtein is less suitable than Jaro-Winkler for general short names and truncations.\n4. **Weight Justification**: Weight 0.70. The movie title is the strongest primary descriptive attribute, but it is not a globally unique identifier and remakes or identically titled films require corroboration.\n\n### year\n1. **Inspect Exemplar Candidate Matches**: Equivalent years have formatting variation (`2013.0` vs `2013`), and one high-confidence pair differs by one year (`2015.0` vs `2014`), indicating that exact equality is too strict.\n2. **Inspect Statistical Profile**: Null rates are negligible (0.14% in A and 0% in B), and both sources contain 96 distinct year values. The low uniqueness is expected for a contextual calendar-year field, but it passes the null and variance rules.\n3. **Algorithm Trade-off Evaluation**: Choose `numeric_linear` after numeric coercion because calendar years are interval-scale values and a one-year difference should incur the same penalty regardless of decade. `numeric_relative` is inappropriate because relative percentage differences make recent-year discrepancies artificially tiny. `exact` would fail the observed one-year mismatch and may also fail on textual formatting, while `date` is unnecessary for year-only values.\n4. **Weight Justification**: Weight 0.30. Release year is useful contextual evidence for distinguishing remakes and same-title films, but the observed one-year discrepancy proves it cannot dominate.\n\n### directors\n1. **Inspect Exemplar Candidate Matches**: Two pairs are exact, while `milan lutheria` vs `milan luthria` exhibits a small character-level spelling variation in a person name.\n2. **Inspect Statistical Profile**: Source A has 25.31% nulls and Source B 0%, both below the exclusion threshold. Cardinality is 1,929 and 3,889, uniqueness is roughly 54.25% and 56.26%, and average lengths are 14.62 and 12.93 characters.\n3. **Algorithm Trade-off Evaluation**: Choose `jarowinkler` because these are short person-name strings and the exemplar directly demonstrates a minor typo. `cosine` could treat the misspelled surname as an unrelated token and is unsuitable at this length. `exact` would reject the observed true match, while Damerau-Levenshtein is better reserved for structured codes and would be less forgiving of ordinary name variation.\n4. **Weight Justification**: Weight 0.60. Director is a strong primary descriptive attribute that substantially disambiguates movies, though it is less decisive than the title and is missing in a quarter of Source A.\n\n### actors\n1. **Inspect Exemplar Candidate Matches**: One pair is exactly aligned, but the others contain reordered and partial cast lists. Source A also concatenates adjacent names without delimiters (`perlmantony`, `jaadolph`, `kumarsonakshi`), while Source B contains shorter, space-delimited subsets.\n2. **Inspect Statistical Profile**: Null rates are 16.54% and 2.33%, below the exclusion threshold. Cardinality is high (2,907 and 6,492), uniqueness is about 81.75% and 93.91%, and average lengths are long (85.24 and 40.05), making cast information potentially discriminative.\n3. **Algorithm Trade-off Evaluation**: Choose `cosine` because it is the available algorithm best able to tolerate cast ordering changes, extra actors, and subset lists in long multi-word fields. Jaro-Winkler and Damerau-Levenshtein would heavily penalize reordered and unequal-length lists, and `exact` would reject the observed variants. Word-level cosine will still lose evidence where Source A merges name boundaries, so this field should ideally be preprocessed to restore separators; that empirical limitation prevents a higher weight.\n4. **Weight Justification**: Weight 0.50. Cast is a primary descriptive signal and often highly identifying in combination, but incomplete lists and severe token-boundary corruption make it less reliable than title or director.\n\n### critic_rating\n1. **Inspect Exemplar Candidate Matches**: No aligned cross-source values are available because the field exists only in Source A.\n2. **Inspect Statistical Profile**: Source B has no corresponding column, so the attribute is unavailable for cross-source comparison; Source A also has only nine distinct values and 0.25% uniqueness.\n3. **Algorithm Trade-off Evaluation**: Exclude it. No comparison algorithm can generate pairwise evidence without a Source B counterpart; treating absence as a value would produce systematic false disagreement.\n4. **Weight Justification**: No weight is assigned because it cannot contribute cross-source matching evidence.\n\n### genre\n1. **Inspect Exemplar Candidate Matches**: Two pairs are exact, while `action adventure` vs `action adventure drama` shows an added category token with the shared taxonomy otherwise preserved.\n2. **Inspect Statistical Profile**: Null rates are 5.85% and 0%, cardinalities are 704 and 285, and average lengths are 18.58 and 17.74. The field has variance and acceptable completeness, although categories are reused across many movies.\n3. **Algorithm Trade-off Evaluation**: Choose `cosine` because genre is a multi-token label where order and added or omitted categories should not cause failure; it directly accommodates the observed extra `drama` token. `exact` would reject that true pair. Jaro-Winkler and Damerau-Levenshtein are order-sensitive and can over-penalize token additions or permutations. Although the average length is near the usual cosine threshold, the exemplars show stable shared vocabulary rather than divergent taxonomies, supporting token comparison here.\n4. **Weight Justification**: Weight 0.30. Genre is auxiliary contextual evidence: it can confirm compatibility but is too broad and non-unique to identify a movie by itself.\n\n### pg_rating\n1. **Inspect Exemplar Candidate Matches**: No aligned values are present because this field exists only in Source A.\n2. **Inspect Statistical Profile**: Source B has no counterpart; Source A has 13.19% nulls, only 12 values, and 0.34% uniqueness.\n3. **Algorithm Trade-off Evaluation**: Exclude it despite its standardized categorical nature. `exact` would ordinarily fit normalized certification codes, but no cross-source comparison is possible.\n4. **Weight Justification**: No weight is assigned because the attribute is unavailable in Source B.\n\n### duration\n1. **Inspect Exemplar Candidate Matches**: Numeric durations agree where both are present, but units are expressed as `minutes` versus `min`; one pair is missing duration in Source A (`\"\"` vs `160 min`).\n2. **Inspect Statistical Profile**: Null rates are 7.51% and 0%, cardinalities are 138 and 186, and average textual lengths are 10.58 and 6.43. The field passes exclusion checks and varies enough to provide supporting evidence.\n3. **Algorithm Trade-off Evaluation**: Choose `numeric_relative` after extracting the numeric minute value and normalizing units. Runtime is a physical measurement, and proportional difference is more meaningful than character similarity or strict text equality. `exact` would fail on `106 minutes` vs `106 min`; Jaro-Winkler could over-reward shared unit text even when numbers differ; `numeric_linear` is plausible but less scale-aware across short and very long runtimes. Missing values must remain missing rather than being converted to zero.\n4. **Weight Justification**: Weight 0.30. Duration is useful auxiliary evidence but can differ across cuts, releases, or metadata providers and therefore should not dominate identity scoring.\n\n### movie_rating\n1. **Inspect Exemplar Candidate Matches**: No aligned values are available because this field exists only in Source B.\n2. **Inspect Statistical Profile**: Source A has no corresponding column; Source B has 78 distinct values and 1.13% uniqueness.\n3. **Algorithm Trade-off Evaluation**: Exclude it. A numeric comparison could be meaningful only if both sources supplied comparable ratings on the same scale; neither prerequisite is established here.\n4. **Weight Justification**: No weight is assigned because there is no cross-source evidence.",
  "matching_columns": {
    "movie_name": {
      "algorithm": "jarowinkler",
      "weight": 0.7
    },
    "year": {
      "algorithm": "numeric_linear",
      "weight": 0.3
    },
    "directors": {
      "algorithm": "jarowinkler",
      "weight": 0.6
    },
    "actors": {
      "algorithm": "cosine",
      "weight": 0.5
    },
    "genre": {
      "algorithm": "cosine",
      "weight": 0.3
    },
    "duration": {
      "algorithm": "numeric_relative",
      "weight": 0.3
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
| **Total Rows** | 3556 | 6913 |
| **Column Count** | 9 | 8 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.82)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "1410" | "640" |
| movie_name | "all is lost" | "all is lost" |
| year | "2013.0" | "2013" |
| directors | "jc chandor" | "jc chandor" |
| actors | "robert redford" | "robert redford" |
| genre | "action adventure" | "action adventure drama" |
| duration | "106 minutes" | "106 min" |

#### Candidate Match 2 (Overall Text Match Score: 0.75)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "543" | "221" |
| movie_name | "skin trade" | "skin trade" |
| year | "2015.0" | "2014" |
| directors | "ekachai uekrongtham" | "ekachai uekrongtham" |
| actors | "ron perlmantony jaadolph lundgrencelina jademichael jai whitepeter weller" | "dolph lundgren tony jaa ron perlman" |
| genre | "action crime thriller" | "action crime thriller" |
| duration | "96 minutes" | "96 min" |

#### Candidate Match 3 (Overall Text Match Score: 0.75)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "1497" | "622" |
| movie_name | "once upon a time in mumbai dobaara" | "once upon a time in mumbai dobaara" |
| year | "2013.0" | "2013" |
| directors | "milan lutheria" | "milan luthria" |
| actors | "akshay kumarsonakshi sinhaimran khansonali bendrepitobash tripathy" | "akshay kumar imran khan sonakshi sinha" |
| genre | "action crime drama" | "action crime drama" |
| duration | "" | "160 min" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **id** | 0.0% | 0.0% | 100.0% | 100.0% | 3556 | 6913 | N/A | N/A | "1410" ↔ "640" |
| **movie_name** | 0.0% | 0.0% | 96.09% | 93.91% | 3417 | 6492 | 14.99 | 14.83 | "all is lost" ↔ "all is lost" |
| **year** | 0.14% | 0.0% | 2.7% | 1.39% | 96 | 96 | N/A | N/A | "2013.0" ↔ "2013" |
| **directors** | 25.31% | 0.0% | 54.25% | 56.26% | 1929 | 3889 | 14.62 | 12.93 | "jc chandor" ↔ "jc chandor" |
| **actors** | 16.54% | 2.33% | 81.75% | 93.91% | 2907 | 6492 | 85.24 | 40.05 | "robert redford" ↔ "robert redford" |
| **critic_rating** | 0.0% | N/A | 0.25% | N/A | 9 | N/A | N/A | N/A | N/A |
| **genre** | 5.85% | 0.0% | 19.8% | 4.12% | 704 | 285 | 18.58 | 17.74 | "action adventure" ↔ "action adventure drama" |
| **pg_rating** | 13.19% | N/A | 0.34% | N/A | 12 | N/A | 8.19 | N/A | N/A |
| **duration** | 7.51% | 0.0% | 3.88% | 2.69% | 138 | 186 | 10.58 | 6.43 | "106 minutes" ↔ "106 min" |
| **movie_rating** | N/A | 0.0% | N/A | 1.13% | N/A | 78 | N/A | N/A | N/A |
```
</details>

