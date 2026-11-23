# Matching Benchmark: itunes-apple — Dynamic Weighted

- **Domain**: music
- **Strategy**: Dynamic Weighted
- **Model**: gpt-5.6-sol
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9357 | 0.0165 |
| Recall | 0.7727 | 0.0200 |
| F1 Score | 0.8464 | 0.0187 |
| Execution Time (s) | 1.2594 | 0.0070 |
| Peak Memory (MB) | 8.32 | 0.00 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 10,149 |
| Completion Tokens | 9,314 |
| Total Tokens | 19,463 |
| Estimated Cost (USD) | $0.1994 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9141 | 0.0044 |
| Potential F1 Ceiling | 0.9247 | 0.0073 |
| LLM Workload Ratio | 44.3% | - |
| Unrecoverable Loss | 0.0859 | - |
| Uncertain Purity | 7.8% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 79.51% |
| Consistent Matches | 97 |
| Flaky Matches | 25 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9455 | 0.7879 | 0.8595 | 0.9167 | 0.9308 | 44.7% | 7.1% | 104 | 6 | 28 | 1.2668 | 8.32 | 6287 | $0.0676 |  |
| 2 | SUCCESS | 0.9167 | 0.7500 | 0.8250 | 0.9167 | 0.9167 | 44.3% | 9.2% | 99 | 9 | 33 | 1.2585 | 8.32 | 6477 | $0.0637 |  |
| 3 | SUCCESS | 0.9450 | 0.7803 | 0.8548 | 0.9091 | 0.9267 | 43.8% | 7.2% | 103 | 6 | 29 | 1.2530 | 8.32 | 6699 | $0.0681 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.5087 | 0.7990 | [0.3595, 0.6578, 0.8932] |
| 2 | dynamic_skew | 0.5179 | 0.8128 | [0.3636, 0.6722, 0.9066] |
| 3 | dynamic_skew | 0.5054 | 0.8008 | [0.3553, 0.6555, 0.8976] |

## LLM Strategy Configuration & Prompts

- **Model**: `gpt-5.6-sol`
- **Provider**: `openai`
- **Latency**: `35.65s`
- **Log File**: `outputs/logs/llm_calls/20260919_164956_009094_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "Sno\n1. Inspect Exemplar Candidate Matches: The aligned records have unrelated values (6088 vs 7967, with similarly source-specific row numbers in the other exemplars), so this field does not transfer across sources.\n2. Inspect Statistical Profile: It is non-null and effectively unique in both sources (6,907/6,907 and 55,923/55,923), which is the signature of a row key rather than a shared entity attribute.\n3. Algorithm Trade-off Evaluation: Exclude it under the source-specific/internal-key rule. Exact or edit-distance matching would incorrectly reward coincidental row-number proximity or equality and would not identify songs.\n4. Weight Justification: Excluded; no weight is assigned because it is a system identifier, not entity evidence.\n\nAlbum_Name\n1. Inspect Exemplar Candidate Matches: Matching albums show optional qualifier tokens and suffixes: \u201cborn to die the paradise edition\u201d vs \u201c\u2026 explicit,\u201d exact agreement for \u201cwest coast remix ep,\u201d and \u201chow deep is your love remixes ep\u201d vs \u201c\u2026 remixes.\u201d\n2. Inspect Statistical Profile: Null rates are 0.0% and 0.03%, cardinalities are 1,116 and 5,050 (both greater than 1), and average lengths are 24.17 and 24.26, so the field is eligible, well populated, and moderately discriminative.\n3. Algorithm Trade-off Evaluation: Choose cosine because these are multi-word strings around 24 characters and observed differences are whole-token additions/omissions, for which token-level order-invariant comparison is effective. Jaro-Winkler would be less stable on long titles and suffix additions; Damerau-Levenshtein would over-penalize length differences; exact would reject the demonstrated \u201cexplicit\u201d and \u201cep\u201d variants.\n4. Weight Justification: Weight 0.62 as a strong primary descriptive attribute. Album titles strongly support identity but are not unique enough to outweigh the song title and artist.\n\nAlbum_Price\n1. Inspect Exemplar Candidate Matches: No aligned A-to-B values are available because this field exists only in Source A.\n2. Inspect Statistical Profile: Source A is non-null with cardinality 47 and average length 3.36, but Source B has no corresponding column or statistics.\n3. Algorithm Trade-off Evaluation: Exclude it because pairwise similarity cannot be computed across both sources. Numeric-relative would otherwise suit a monetary amount, but no B-side operand exists.\n4. Weight Justification: Excluded; no aggregate weight is assigned.\n\nArtist_Name\n1. Inspect Exemplar Candidate Matches: Artist strings agree exactly in all three exemplars, including the short name \u201clana del rey\u201d and the multi-artist string \u201ccalvin harris disciples.\u201d No token reordering is observed.\n2. Inspect Statistical Profile: Null rates are 0.0% in both sources, cardinalities are 932 and 1,770, and average lengths are short at 12.47 and 14.67. The field is eligible and meaningfully discriminative.\n3. Algorithm Trade-off Evaluation: Choose Jaro-Winkler because artist names are short identity-like names where minor spelling, punctuation, or suffix variation should remain similar. Cosine is unsafe for these sub-20-character names because one misspelled token can become orthogonal; exact is too brittle; Damerau-Levenshtein is less suitable for natural names and multi-token punctuation variation.\n4. Weight Justification: Weight 0.68 as a strong primary descriptive/identity attribute. It is highly useful but not unique enough to establish a track by itself.\n\nCopyRight\n1. Inspect Exemplar Candidate Matches: Two pairs differ only by Source B\u2019s leading \u201cc,\u201d but the third has materially different rights-holder text (\u201csony music entertainment uk limited\u201d vs \u201cisland records \u2026 universal music operations limited\u201d) despite the candidate otherwise appearing aligned.\n2. Inspect Statistical Profile: Null rates are 0.0%, cardinalities are 603 and 2,553, and average lengths are 61.2 and 34.17. It is eligible and is long multi-word text, though repeated across many records.\n3. Algorithm Trade-off Evaluation: Choose cosine because it can preserve evidence from shared year, artist, label, and licensing tokens while tolerating a leading token and differing phrase lengths. Jaro-Winkler and Damerau-Levenshtein would over-penalize long-text insertions and replacements; exact would fail on the routine leading \u201cc.\u201d Cosine will still score the genuinely divergent third pair lower, appropriately limiting its confirmation value.\n4. Weight Justification: Weight 0.20 as auxiliary context. Copyright text can corroborate a release but may differ legitimately by territory, distributor, or edition.\n\nCustomer_Rating\n1. Inspect Exemplar Candidate Matches: No cross-source aligned values are available because the field is present only in Source A.\n2. Inspect Statistical Profile: Source A has 0.91% nulls and cardinality 954, but Source B has no corresponding field.\n3. Algorithm Trade-off Evaluation: Exclude it because no pairwise comparison can be made. Even if present in both sources, ratings are mutable contextual measures rather than stable identity attributes; a numeric algorithm would not solve the missing counterpart.\n4. Weight Justification: Excluded; no weight is assigned.\n\nGenre\n1. Inspect Exemplar Candidate Matches: Taxonomies and formatting diverge substantially: concatenated \u201calternativemusicrockadult alternative\u201d maps to \u201calternative rock,\u201d \u201calternativemusicrock\u201d maps to \u201calternative rock,\u201d and \u201cdancemusicrock\u201d maps to \u201cdance electronic.\u201d\n2. Inspect Statistical Profile: Null rates are 0.0%, cardinalities are 383 and 430, and average lengths differ notably at 31.47 and 16.04. The field passes formal exclusions but is low-cardinality and source-taxonomy dependent.\n3. Algorithm Trade-off Evaluation: Choose Jaro-Winkler as a weak comparison because character alignment can retain partial evidence across spacing/concatenation differences such as \u201calternativemusic\u201d versus \u201calternative.\u201d Cosine would lose concatenated-token overlap and fails on divergent labels such as \u201crock\u201d versus \u201celectronic\u201d; exact is far too strict; edit distance would heavily penalize taxonomy additions and length differences. No available algorithm fully resolves divergent taxonomies, hence the deliberately low influence.\n4. Weight Justification: Weight 0.10 as a weak auxiliary signal. Genre can corroborate broad compatibility but should not veto otherwise strong title/artist/date evidence.\n\nPrice\n1. Inspect Exemplar Candidate Matches: All three exemplar pairs agree at 129, showing consistent formatting in the observed matches.\n2. Inspect Statistical Profile: Null rates are 0.0%, but cardinality is only 6 in A and 10 in B, with average lengths 4.05 and 3.0. It passes the no-variance rule but has very low discriminative power.\n3. Algorithm Trade-off Evaluation: Choose numeric-relative because price is monetary and percentage difference is more meaningful than a uniform absolute gap if the available price points vary in scale. Numeric-linear can distort comparisons across price levels; exact would reject legitimate pricing changes or formatting/conversion effects; string algorithms are semantically inappropriate.\n4. Weight Justification: Weight 0.15 as weak supporting context. Exact exemplar agreement helps, but many unrelated tracks share the same small set of prices.\n\nReleased\n1. Inspect Exemplar Candidate Matches: All three pairs have exactly matching full release dates, making this a consistent corroborating feature in the exemplars.\n2. Inspect Statistical Profile: Null rates are 4.4% and 12.59%, both below 50%; cardinalities are 668 and 1,987, both above 1. The field is eligible and moderately discriminative.\n3. Algorithm Trade-off Evaluation: Choose date because values are calendar timestamps and the matcher can preserve partial similarity for plausible day/month/year shifts or edition-date differences. Exact would be unnecessarily brittle; numeric-linear is inappropriate for encoded calendar values; textual algorithms ignore calendar hierarchy.\n4. Weight Justification: Weight 0.35 as supporting contextual evidence. A shared release date is valuable but editions or regional releases can legitimately differ.\n\nSong_Name\n1. Inspect Exemplar Candidate Matches: Two pairs agree exactly, while one shares the base title but changes the remix designation from \u201cmk remix\u201d to \u201czhu remix.\u201d This shows both stable multi-word title cores and potentially divergent version tokens.\n2. Inspect Statistical Profile: Null rates are 0.0%, cardinalities are high at 3,013 and 38,273, uniqueness is 43.62% and 68.44%, and average lengths are 22.95 and 21.97. It is eligible and the most discriminative shared descriptive field.\n3. Algorithm Trade-off Evaluation: Choose cosine because song names are multi-word strings above 20 characters and the observed remix discrepancy is a token replacement while the remaining title tokens are identical. Cosine preserves that shared core and tolerates token additions/order changes. Exact would reject version variation; Damerau-Levenshtein would penalize inserted or replaced words; Jaro-Winkler is less reliable for multi-word title rearrangements. Its typo limitation is acknowledged, but the exemplars primarily show whole-token version variation rather than sub-word misspellings.\n4. Weight Justification: Weight 0.70 as the strongest primary descriptive attribute. It is highly discriminative, though it should be combined with artist and album because remixes and repeated song titles exist.\n\nTime\n1. Inspect Exemplar Candidate Matches: Two pairs match exactly, while the second differs by 62 minutes (05:26 vs 04:24) on the same displayed date. This suggests a timestamp or time-like contextual field that may vary even for otherwise aligned candidates.\n2. Inspect Statistical Profile: Null rates are 2.22% and 0.19%, cardinalities are 397 and 819, and both cardinalities exceed 1. It is eligible but relatively low-cardinality, and the supplied average length is unavailable.\n3. Algorithm Trade-off Evaluation: Choose date because the values are full datetime strings and calendar/time hierarchy is preferable to raw string distance. Exact would fail the observed one-hour shift; numeric algorithms would require explicit conversion and an understood unit; cosine or character matching would give misleading similarity to timestamps sharing boilerplate date digits.\n4. Weight Justification: Weight 0.10 as weak auxiliary context. The unexplained 2026 date and the exemplar discrepancy make it unsafe as a decisive identity feature.\n\nLabel\n1. Inspect Exemplar Candidate Matches: No A-to-B aligned values are available because Label exists only in Source B.\n2. Inspect Statistical Profile: Source B is non-null with cardinality 1,732 and average length 15.25, but Source A has no corresponding field.\n3. Algorithm Trade-off Evaluation: Exclude it because cross-source comparison is impossible. Jaro-Winkler could compare short label names if a Source A counterpart existed, but it cannot operate on a missing column.\n4. Weight Justification: Excluded; no weight is assigned.",
  "matching_columns": {
    "Album_Name": {
      "algorithm": "cosine",
      "weight": 0.62
    },
    "Artist_Name": {
      "algorithm": "jarowinkler",
      "weight": 0.68
    },
    "CopyRight": {
      "algorithm": "cosine",
      "weight": 0.2
    },
    "Genre": {
      "algorithm": "jarowinkler",
      "weight": 0.1
    },
    "Price": {
      "algorithm": "numeric_relative",
      "weight": 0.15
    },
    "Released": {
      "algorithm": "date",
      "weight": 0.35
    },
    "Song_Name": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "Time": {
      "algorithm": "date",
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

