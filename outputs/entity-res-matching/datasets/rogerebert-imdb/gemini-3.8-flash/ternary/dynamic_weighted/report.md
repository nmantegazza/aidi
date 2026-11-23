# Matching Benchmark: rogerebert-imdb — Dynamic Weighted

- **Domain**: movies
- **Strategy**: Dynamic Weighted
- **Model**: gemini-3.8-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9860 | 0.0005 |
| Recall | 0.5864 | 0.0192 |
| F1 Score | 0.7353 | 0.0153 |
| Execution Time (s) | 0.3188 | 0.0394 |
| Peak Memory (MB) | 1.17 | 0.02 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 9,231 |
| Completion Tokens | 3,329 |
| Total Tokens | 12,560 |
| Estimated Cost (USD) | $0.0194 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9779 | 0.0024 |
| Potential F1 Ceiling | 0.9819 | 0.0014 |
| LLM Workload Ratio | 33.2% | - |
| Unrecoverable Loss | 0.0221 | - |
| Uncertain Purity | 76.1% | - |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9863 | 0.5975 | 0.7442 | 0.9793 | 0.9828 | 32.7% | 75.4% | 144 | 2 | 97 | 0.3134 | 1.16 | 4199 | $0.0065 |  |
| 2 | SUCCESS | 0.9855 | 0.5643 | 0.7177 | 0.9751 | 0.9803 | 34.3% | 77.3% | 136 | 2 | 105 | 0.3607 | 1.15 | 4162 | $0.0064 |  |
| 3 | SUCCESS | 0.9863 | 0.5975 | 0.7442 | 0.9793 | 0.9828 | 32.7% | 75.4% | 144 | 2 | 97 | 0.2824 | 1.19 | 4199 | $0.0065 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 3 | dynamic_skew | 0.5828 | 0.7551 | [0.4761, 0.6896, 0.7988] |

## LLM Strategy Configuration & Prompts

- **Model**: `gemini-3.8-flash`
- **Provider**: `google-cloud`
- **Latency**: `8.17s`
- **Log File**: `outputs/logs/llm_calls/20260919_170515_041915_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "Step 1: Inspect Columns and Exclusions\n- 'id': Internal source-specific identifier (different numeric IDs in A and B). Excluded.\n- 'critic_rating', 'pg_rating', 'movie_rating': Missing entirely in one of the sources (N/A in Source B or Source A). Excluded.\n- 'duration': Shows unit discrepancies ('106 minutes' vs '106 min') and empty strings. However, duration can vary widely between releases/edits or be missing/empty. Given the strong primary identifiers available (movie_name, year, directors, actors, genre), duration is weak and formatting differs, but could be evaluated; however, movie_name, year, directors, actors, and genre provide full, robust coverage.\n\nStep 2: Mandatory 4-Step Column Reasoning Protocol\n\n1. movie_name:\n- Inspect Exemplar Candidate Matches: Exactly aligned or minor title differences ('all is lost' \u2194 'all is lost', 'skin trade' \u2194 'skin trade', 'once upon a time in mumbai dobaara' \u2194 'once upon a time in mumbai dobaara').\n- Inspect Statistical Profile: 0.0% null in both sources, ~94-96% uniqueness, high cardinality (3417 / 6492), average length ~15 characters.\n- Algorithm Trade-off Evaluation: Average length is ~15 characters (short string). 'jarowinkler' is ideal for handling small character variations, minor typos, and prefix matches in short movie titles. 'cosine' would fail on single-word titles or minor typos within tokens.\n- Weight Justification: Core primary descriptive entity identifier (0.85).\n\n2. year:\n- Inspect Exemplar Candidate Matches: Represented as float string in A ('2013.0') and integer string in B ('2013'). Small variations like 2015.0 vs 2014 occur due to release date differences.\n- Inspect Statistical Profile: <0.2% null in both sources, cardinality 96.\n- Algorithm Trade-off Evaluation: 'numeric_linear' handles absolute calendar differences directly and tolerates 1-year discrepancy between release/festival/international dates. 'numeric_relative' is inappropriate for calendar years; 'exact' would fail on format ('2013.0' vs '2013') and release year skews (2014 vs 2015).\n- Weight Justification: Disambiguating temporal attribute (0.50).\n\n3. directors:\n- Inspect Exemplar Candidate Matches: Shows matching names with potential typos ('milan lutheria' vs 'milan luthria') or exact matches ('jc chandor' vs 'jc chandor').\n- Inspect Statistical Profile: 25.3% null in A, 0.0% null in B. High uniqueness and cardinality (1929 / 3889), average length ~13-15 characters.\n- Algorithm Trade-off Evaluation: Average length is short (~14 chars), typically a single person's name. 'jarowinkler' handles small spelling differences ('lutheria' vs 'luthria') effectively. 'cosine' would penalize short single-token or two-token names severely if misspelled.\n- Weight Justification: Strong descriptive disambiguating attribute (0.65).\n\n4. actors:\n- Inspect Exemplar Candidate Matches: Exemplars show concatenated or multi-actor lists ('robert redford' \u2194 'robert redford', concatenated 'ron perlmantony jaadolph...' vs 'dolph lundgren tony jaa ron perlman').\n- Inspect Statistical Profile: 16.5% null in A, 2.3% null in B, high cardinality, average length up to 85 chars in A and 40 in B.\n- Algorithm Trade-off Evaluation: Multi-word text with varied actor order and subset overlap. 'cosine' (TF-IDF/token-level overlap) is designed for token permutations and partial overlap across cast lists. Edit distance / 'jarowinkler' fails on reordered or subset lists.\n- Weight Justification: Strong descriptive attribute (0.60).\n\n5. genre:\n- Inspect Exemplar Candidate Matches: Multi-token genre lists with subset overlaps ('action adventure' \u2194 'action adventure drama').\n- Inspect Statistical Profile: 5.85% null in A, 0.0% in B, average length ~18 chars.\n- Algorithm Trade-off Evaluation: Multi-token categorical bag of words. 'cosine' naturally measures token overlap between multi-genre tags.\n- Weight Justification: Contextual supporting attribute (0.35).",
  "matching_columns": {
    "actors": {
      "algorithm": "cosine",
      "weight": 0.6
    },
    "movie_name": {
      "algorithm": "jarowinkler",
      "weight": 0.85
    },
    "year": {
      "algorithm": "numeric_linear",
      "weight": 0.5
    },
    "directors": {
      "algorithm": "jarowinkler",
      "weight": 0.65
    },
    "genre": {
      "algorithm": "cosine",
      "weight": 0.35
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

