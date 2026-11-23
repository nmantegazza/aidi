# Matching Benchmark: DBLP-ACM — Dynamic Weighted

- **Domain**: citations
- **Strategy**: Dynamic Weighted
- **Model**: gemini-3.8-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9909 | 0.0012 |
| Recall | 0.9814 | 0.0014 |
| F1 Score | 0.9861 | 0.0012 |
| Execution Time (s) | 6.9748 | 0.1689 |
| Peak Memory (MB) | 43.17 | 2.03 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 9,081 |
| Completion Tokens | 2,850 |
| Total Tokens | 11,931 |
| Estimated Cost (USD) | $0.0175 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9936 | 0.0013 |
| Potential F1 Ceiling | 0.9922 | 0.0012 |
| LLM Workload Ratio | 5.6% | - |
| Unrecoverable Loss | 0.0064 | - |
| Uncertain Purity | 0.2% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 98.74% |
| Consistent Matches | 2189 |
| Flaky Matches | 28 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9905 | 0.9802 | 0.9853 | 0.9928 | 0.9916 | 4.7% | 0.2% | 2180 | 21 | 44 | 6.8274 | 45.51 | 3972 | $0.0058 |  |
| 2 | SUCCESS | 0.9923 | 0.9829 | 0.9876 | 0.9951 | 0.9937 | 5.8% | 0.2% | 2186 | 17 | 38 | 6.9380 | 41.87 | 3922 | $0.0056 |  |
| 3 | SUCCESS | 0.9900 | 0.9811 | 0.9855 | 0.9928 | 0.9914 | 6.2% | 0.2% | 2182 | 22 | 42 | 7.1591 | 42.13 | 4037 | $0.0061 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.3052 | 0.6710 | [0.2358, 0.3745, 0.8688] |
| 2 | dynamic_skew | 0.3070 | 0.6776 | [0.2371, 0.3770, 0.8780] |
| 3 | dynamic_skew | 0.3040 | 0.6638 | [0.2367, 0.3712, 0.8589] |

## LLM Strategy Configuration & Prompts

- **Model**: `gemini-3.8-flash`
- **Provider**: `google-cloud`
- **Latency**: `7.11s`
- **Log File**: `outputs/logs/llm_calls/20260919_155510_464565_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "1. Column 'id':\n- Exemplar Candidate Matches: In Source A, 'id' is a bibliographic key (e.g., 'journalssigmodchongftsykdjj03'), whereas in Source B, it is an arbitrary numeric internal record identifier (e.g., '777000').\n- Statistical Profile: 0% nulls, 100% unique in both datasets.\n- Algorithm Trade-off: These are completely distinct source-specific surrogate keys with zero semantic overlap.\n- Weight Justification: Excluded per Step 1b exclusion rules for source-specific keys.\n\n2. Column 'title':\n- Exemplar Candidate Matches: Highly descriptive, long publication titles (e.g., 'a mapping mechanism to support bitmap index...', 'highperformance sorting on networks of workstations'). The titles match very closely across datasets.\n- Statistical Profile: 0% null in both sources, uniqueness >95%, high cardinality (~2,500), average length ~55 characters.\n- Algorithm Trade-off: 'cosine' is optimal for multi-word titles with avg length > 20 characters because it is robust against slight word reordering or dropped stop words. 'jarowinkler' fails on longer multi-word text with potential word-level movements, while 'exact' would fail if any whitespace/punctuation variation exists.\n- Weight Justification: High weight of 0.85 as publication title is the primary descriptive identifier for academic paper deduplication.\n\n3. Column 'authors':\n- Exemplar Candidate Matches: Author lists exhibit frequent reordering of co-authors across Source A and Source B (e.g., Candidate 1 and Candidate 2 show identical sets of authors listed in different order: 'mahesh jagannath ...' vs 'eugene inseok chong ... mahesh jagannath').\n- Statistical Profile: 0% null in A, 0.61% in B, high cardinality (>2000), avg length ~43-44 chars.\n- Algorithm Trade-off: 'cosine' (TF-IDF token-based) is crucial here due to its token order-invariance, successfully matching author lists regardless of author sequence permutation. Edit-distance and prefix algorithms ('jarowinkler', 'damerau_levenshtein') severely fail when name orders are scrambled.\n- Weight Justification: Assigned a strong weight of 0.65 as author composition is a crucial discriminating attribute alongside title.\n\n4. Column 'venue':\n- Exemplar Candidate Matches: Systematic variations in conference/journal publication venue naming (e.g., 'sigmod record' vs 'acm sigmod record', 'sigmod conference' vs 'international conference on management of data').\n- Statistical Profile: 0% nulls, very low cardinality (cardinality 5 in both sources), average length 11.17 in A vs 34.57 in B.\n- Algorithm Trade-off: 'cosine' captures shared tokens like 'sigmod record' vs 'acm sigmod record' or 'conference', providing partial credit for related terms.\n- Weight Justification: Weight of 0.20 as an auxiliary contextual signal, kept low due to low cardinality (only 5 distinct venues) and significant taxonomy differences ('sigmod conference' vs 'international conference on management of data').\n\n5. Column 'year':\n- Exemplar Candidate Matches: Exact integer years matching across candidate pairs (e.g., '2003' \u2194 '2003', '1997' \u2194 '1997').\n- Statistical Profile: 0% nulls, 10 distinct values representing publication years.\n- Algorithm Trade-off: 'numeric_linear' is ideal for calendar years, measuring absolute distance (1 year difference is slightly penalized rather than dropping to zero as with 'exact'). 'numeric_relative' is inappropriate for interval calendar years.\n- Weight Justification: Supporting contextual attribute assigned a weight of 0.30 to validate or penalize temporal publication discrepancies.",
  "matching_columns": {
    "title": {
      "algorithm": "cosine",
      "weight": 0.85
    },
    "authors": {
      "algorithm": "cosine",
      "weight": 0.65
    },
    "venue": {
      "algorithm": "cosine",
      "weight": 0.2
    },
    "year": {
      "algorithm": "numeric_linear",
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
| **Total Rows** | 2616 | 2294 |
| **Column Count** | 5 | 5 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.90)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "journalssigmodchongftsykdjj03" | "777000" |
| title | "a mapping mechanism to support bitmap index and other auxiliary structures on tables stored as primary btrees" | "a mapping mechanism to support bitmap index and other auxiliary structures on tables stored as primary btrees" |
| authors | "mahesh jagannath eugene inseok chong aravind yalamanchi chuck freiwald souripriya das anhtuan tran jagannathan srinivasan richard jiang ramkumar krishnan" | "eugene inseok chong jagannathan srinivasan souripriya das chuck freiwald aravind yalamanchi mahesh jagannath anhtuan tran ramkumar krishnan richard jiang" |
| venue | "sigmod record" | "acm sigmod record" |
| year | "2003" | "2003" |

#### Candidate Match 2 (Overall Text Match Score: 0.90)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "confsigmodarpacidusseauachp97" | "253322" |
| title | "highperformance sorting on networks of workstations" | "highperformance sorting on networks of workstations" |
| authors | "david e culler joseph m hellerstein david a patterson andrea c arpacidusseau remzi h arpacidusseau" | "andrea c arpacidusseau remzi h arpacidusseau david e culler joseph m hellerstein david a patterson" |
| venue | "sigmod conference" | "international conference on management of data" |
| year | "1997" | "1997" |

#### Candidate Match 3 (Overall Text Match Score: 0.90)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "confsigmodiveslpst00" | "335492" |
| title | "selforganizing data sharing communities with sagres" | "selforganizing data sharing communities with sagres" |
| authors | "igor tatarinov wai tak theodora yeung shiori betzler jing su jayant madhavan rachel pottinger alon y levy ewa jaslikowska stefan saroiu qiong chen zachary g ives" | "zachary ives alon levy jayant madhavan rachel pottinger stefan saroiu igor tatarinov shiori betzler qiong chen ewa jaslikowska jing su wai tak theodora yeung" |
| venue | "sigmod conference" | "international conference on management of data" |
| year | "2000" | "2000" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **id** | 0.0% | 0.0% | 100.0% | 100.0% | 2616 | 2294 | 21.0 | N/A | "journalssigmodchongftsykdjj03" ↔ "777000" |
| **title** | 0.0% | 0.0% | 95.83% | 96.6% | 2507 | 2216 | 55.39 | 55.93 | "a mapping mechanism to support bitmap index and other auxiliary structures on tables stored as primary btrees" ↔ "a mapping mechanism to support bitmap index and other auxiliary structures on tables stored as primary btrees" |
| **authors** | 0.0% | 0.61% | 88.53% | 87.53% | 2316 | 2008 | 43.84 | 43.34 | "mahesh jagannath eugene inseok chong aravind yalamanchi chuck freiwald souripriya das anhtuan tran jagannathan srinivasan richard jiang ramkumar krishnan" ↔ "eugene inseok chong jagannathan srinivasan souripriya das chuck freiwald aravind yalamanchi mahesh jagannath anhtuan tran ramkumar krishnan richard jiang" |
| **venue** | 0.0% | 0.0% | 0.19% | 0.22% | 5 | 5 | 11.17 | 34.57 | "sigmod record" ↔ "acm sigmod record" |
| **year** | 0.0% | 0.0% | 0.38% | 0.44% | 10 | 10 | N/A | N/A | "2003" ↔ "2003" |
```
</details>

