# Matching Benchmark: rogerebert-imdb — Dynamic Weighted

- **Domain**: movies
- **Strategy**: Dynamic Weighted
- **Model**: deepseek-v4.1-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9885 | 0.0079 |
| Recall | 0.5947 | 0.0024 |
| F1 Score | 0.7427 | 0.0036 |
| Execution Time (s) | 0.4108 | 0.0231 |
| Peak Memory (MB) | 1.24 | 0.05 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 9,798 |
| Completion Tokens | 13,187 |
| Total Tokens | 22,985 |
| Estimated Cost (USD) | $0.0000 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9751 | 0.0000 |
| Potential F1 Ceiling | 0.9818 | 0.0039 |
| LLM Workload Ratio | 32.2% | - |
| Unrecoverable Loss | 0.0249 | - |
| Uncertain Purity | 76.4% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 88.96% |
| Consistent Matches | 137 |
| Flaky Matches | 17 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9931 | 0.5975 | 0.7461 | 0.9751 | 0.9840 | 31.1% | 78.4% | 144 | 1 | 97 | 0.4300 | 1.26 | 7958 | - |  |
| 2 | SUCCESS | 0.9931 | 0.5934 | 0.7429 | 0.9751 | 0.9840 | 32.7% | 75.4% | 143 | 1 | 98 | 0.3852 | 1.19 | 7105 | - |  |
| 3 | SUCCESS | 0.9795 | 0.5934 | 0.7390 | 0.9751 | 0.9773 | 32.7% | 75.4% | 143 | 3 | 98 | 0.4170 | 1.27 | 7922 | - |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.6548 | 0.8043 | [0.5638, 0.7459, 0.8433] |
| 2 | dynamic_skew | 0.6315 | 0.7852 | [0.5370, 0.7260, 0.8248] |
| 3 | dynamic_skew | 0.6033 | 0.7598 | [0.5156, 0.6909, 0.8057] |

## LLM Strategy Configuration & Prompts

- **Model**: `deepseek-v4.1-flash`
- **Provider**: `deepseek`
- **Latency**: `22.35s`
- **Log File**: `outputs/logs/llm_calls/20260919_170423_455560_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "Evaluated every column against the exemplar pairs and statistical profiles.\n\n**movie_name** \u2014 (1) Exemplars show exact string equality across sources (\"all is lost\"\u2194\"all is lost\", \"skin trade\"\u2194\"skin trade\"), so titles are stable but may still contain minor typos/abbreviation risk at the character level. (2) 0% null in both, near-unique (96% A / 94% B), cardinality 3417/6492, avg length ~15 (<20 chars). (3) Avg length below 20 means word-level cosine is risky: a single-word title with a 1-char typo would collapse a whole token to 0.0 similarity. jarowinkler's prefix-weighted character alignment tolerates typos, truncations and article/format variants on short phrases while still scoring multi-word titles like \"once upon a time in mumbai dobaara\" reliably; damerau_levenshtein over-penalizes length mismatches. (4) This is the single strongest identity attribute for a movie (near-unique), so weight 0.8.\n\n**directors** \u2014 (1) Exemplar 3 shows a genuine name typo: \"milan lutheria\"\u2194\"milan luthria\"; exemplar 1 is exact (\"jc chandor\"). (2) 25.3% null A / 0% B (under 50% threshold), cardinality 1929/3889, avg length ~13-15 (short single-name field). (3) Because it is a short personal/brand name field, jarowinkler is the correct fit \u2014 it absorbs the \"lutheria/luthria\" spelling divergence and phonetic variants that word-level cosine would score as an orthogonal token (0.0) and that edit distance would over-penalize. (4) Directors are a strong identity/descriptive discriminator, so weight 0.6 (tempered slightly by the 25% nulls in A).\n\n**actors** \u2014 (1) Exemplars show heavy divergence: Source A concatenates names without spaces (\"ron perlmantony jaadolph lundgrencelina jademichael jai whitepeter weller\") and orders them differently, while Source B uses clean space-separated subsets (\"dolph lundgren tony jaa ron perlman\"). (2) 16.5% null A / 2.3% B, near-unique, avg length 85/40 \u2014 well above 20, genuine multi-token free text. (3) cosine (token TF-IDF) is the only suitable choice: it is order-invariant and resilient to additions/omissions, matching the majority of actor names that do appear as clean tokens in both sources. jarowinkler/edit distance would fail catastrophically on reordering and huge length gaps. (4) Supporting descriptive attribute that is noisy and partially concatenated, so weight 0.4.\n\n**genre** \u2014 (1) Exemplars show taxonomy subset drift: \"action adventure\"\u2194\"action adventure drama\" (extra token), otherwise identical tags. (2) 5.85% null A / 0% B, cardinality 704/285, avg length ~18, multi-word categorical tags. (3) cosine handles token additions/omissions gracefully (shared \"action adventure\" tokens dominate), which is exactly the observed drift; character algorithms would be distorted by word-count differences and divergent taxonomy vocabularies. (4) Supporting descriptive/contextual attribute, weight 0.35.\n\n**year** \u2014 (1) Format differs (\"2013.0\" vs \"2013\", same value) and exemplar 2 shows a 1-year off-by-one (\"2015.0\" vs \"2014\"). (2) 0.14%/0% null, cardinality 96 both, fully numeric. (3) Calendar years are a uniform interval scale, so numeric_linear (absolute distance) is correct \u2014 numeric_relative is nonsensical on interval scales (a 1-year gap is 1 year regardless of era). (4) Useful but secondary disambiguator (remakes exist), weight 0.3.\n\n**duration** \u2014 (1) Exemplar 1 shows a perfect value match with unit drift (\"106 minutes\"\u2194\"106 min\"); values are physical time measurements. (2) 7.5% null A / 0% B, cardinality 138/186, low avg length. (3) Duration is a physical measurement spanning from short films (~5 min) to epics (~240 min)\u2014nearly two orders of magnitude\u2014so numeric_relative (scale-invariant percentage gap) is preferable to absolute linear distance, correctly penalizing small absolute gaps on short films without over-penalizing on long ones; the numeric parser normalizes the \"minutes\"/\"min\" suffix. (4) Auxiliary contextual attribute, weight 0.3.\n\n**Excluded columns** \u2014 `id`: source-specific auto-increment key with no cross-source agreement (\"1410\"\u2194\"640\"). `critic_rating`, `pg_rating` (Source A only) and `movie_rating` (Source B only): present in a single source, so no pairwise cross-source comparison is possible.",
  "matching_columns": {
    "movie_name": {
      "algorithm": "jarowinkler",
      "weight": 0.8
    },
    "directors": {
      "algorithm": "jarowinkler",
      "weight": 0.6
    },
    "actors": {
      "algorithm": "cosine",
      "weight": 0.4
    },
    "genre": {
      "algorithm": "cosine",
      "weight": 0.35
    },
    "year": {
      "algorithm": "numeric_linear",
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

