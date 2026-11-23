# Matching Benchmark: DBLP-ACM — Dynamic Weighted

- **Domain**: citations
- **Strategy**: Dynamic Weighted
- **Model**: mistral-medium-latest
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9903 | 0.0030 |
| Recall | 0.9729 | 0.0072 |
| F1 Score | 0.9815 | 0.0022 |
| Execution Time (s) | 7.0220 | 0.0557 |
| Peak Memory (MB) | 45.49 | 0.01 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 9,783 |
| Completion Tokens | 20,285 |
| Total Tokens | 30,068 |
| Estimated Cost (USD) | $0.1668 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9936 | 0.0003 |
| Potential F1 Ceiling | 0.9919 | 0.0016 |
| LLM Workload Ratio | 2.8% | - |
| Unrecoverable Loss | 0.0064 | - |
| Uncertain Purity | 1.1% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 96.68% |
| Consistent Matches | 2152 |
| Flaky Matches | 74 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9913 | 0.9699 | 0.9805 | 0.9937 | 0.9925 | 1.9% | 1.0% | 2157 | 19 | 67 | 7.0847 | 45.50 | 9397 | $0.0509 |  |
| 2 | SUCCESS | 0.9869 | 0.9811 | 0.9840 | 0.9933 | 0.9901 | 5.4% | 0.2% | 2182 | 29 | 42 | 7.0034 | 45.50 | 9783 | $0.0538 |  |
| 3 | SUCCESS | 0.9926 | 0.9676 | 0.9800 | 0.9937 | 0.9932 | 1.1% | 2.0% | 2152 | 16 | 72 | 6.9781 | 45.48 | 10888 | $0.0621 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.3372 | 0.6872 | [0.2431, 0.4312, 0.8579] |
| 2 | dynamic_skew | 0.2996 | 0.6129 | [0.2392, 0.3601, 0.7815] |
| 3 | dynamic_skew | 0.3484 | 0.7250 | [0.2463, 0.4504, 0.9081] |

## LLM Strategy Configuration & Prompts

- **Model**: `mistral-medium-latest`
- **Provider**: `mistral`
- **Latency**: `35.30s`
- **Log File**: `outputs/logs/llm_calls/20260919_155829_038270_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "## Column: title\n1. **Inspect Exemplar Candidate Matches**: In all three candidate pairs, title values are *identical character-for-character* across Source A and Source B (e.g., \"a mapping mechanism to support bitmap index...\" matches exactly). This confirms title as a near-perfect identity anchor for academic publications.\n2. **Inspect Statistical Profile**: Null % = 0.0% in both sources, uniqueness > 95%, cardinality = 2507/2216, avg length = 55.39/55.93 (\u226b20 characters). No exclusion criteria violated.\n3. **Algorithm Trade-off Evaluation**: Column contains *multi-word free text* with avg length > 20. **`cosine`** (token-level TF-IDF) is optimal: it is fully order-invariant and excels at multi-word similarity. Alternatives fail: `jarowinkler` is designed for short strings (<20) and struggles with word reordering; `damerau_levenshtein` is for short codes; `exact` would break on any textual variation.\n4. **Weight Justification**: Title is the *core identity attribute* for academic papers. Assigned **weight = 0.9**.\n\n## Column: authors\n1. **Inspect Exemplar Candidate Matches**: Author lists contain the *exact same names* but in *completely different orders* (e.g., Source A: \"mahesh jagannath eugene inseok chong...\" vs Source B: \"eugene inseok chong jagannathan srinivasan...\"). No typos or abbreviations in the names themselves\u2014only permutation.\n2. **Inspect Statistical Profile**: Null % \u2248 0%, uniqueness > 87%, cardinality = 2316/2008, avg length = 43.84/43.34 (>20 characters). No exclusion criteria violated.\n3. **Algorithm Trade-off Evaluation**: Column is a *space-separated list of names* with avg length > 20. **`cosine`** is ideal: it is *order-invariant* (perfectly handles reordering) and operates at the token level. Alternatives fail: `jarowinkler` is for short strings and cannot handle word permutation; `damerau_levenshtein` is for short codes; no sub-word typos observed, so `cosine`'s token-level approach suffices.\n4. **Weight Justification**: Authors are a *primary descriptive attribute* that strongly confirms entity identity. Assigned **weight = 0.8**.\n\n## Column: venue\n1. **Inspect Exemplar Candidate Matches**: Venue names show *systematic textual variations*: \"sigmod record\" \u2194 \"acm sigmod record\" (prefix addition), and \"sigmod conference\" \u2194 \"international conference on management of data\" (different phrasing for the same venue). These are semantic equivalents with word-level differences.\n2. **Inspect Statistical Profile**: Null % = 0%, but cardinality is extremely low (5 unique values in each source). Avg length = 11.17 (Source A) and 34.57 (Source B). Despite low cardinality, the textual variations are informative for matching.\n3. **Algorithm Trade-off Evaluation**: Strings are relatively short (Source A avg < 20), but variations are *word-based* (additions, different phrasings) rather than character-level typos. **`cosine`** is chosen because it matches on shared words (e.g., \"sigmod\", \"record\", \"conference\") even when other words differ, providing meaningful partial similarity. Alternatives fail: `jarowinkler` would give near-zero similarity for \"sigmod conference\" vs \"international conference on management of data\" due to character-level divergence; `exact` fails due to observed variations; `damerau_levenshtein` is for short codes.\n4. **Weight Justification**: Venue is a *contextual attribute* with low cardinality. Assigned **weight = 0.3**.\n\n## Column: year\n1. **Inspect Exemplar Candidate Matches**: Year values are *identical* in all candidate pairs (e.g., \"2003\" \u2194 \"2003\").\n2. **Inspect Statistical Profile**: Null % = 0%, cardinality = 10/10 (only 10 unique years). Numeric column.\n3. **Algorithm Trade-off Evaluation**: Year is a *calendar year* (uniform interval scale). **`numeric_linear`** (absolute difference |x1 - x2|) is appropriate: it penalizes year gaps uniformly (e.g., 1-year difference always costs the same). Alternatives fail: `numeric_relative` would distort (e.g., |2000-2001|/2001 \u2248 0.05% vs |1997-1998|/1998 \u2248 0.05%\u2014actually similar in this case, but conceptually `numeric_linear` is the standard for calendar years); `exact` is too rigid; `date` requires full date components.\n4. **Weight Justification**: Year is a *supporting contextual attribute*. Assigned **weight = 0.2**.\n\n## Column: id\n**Excluded**: This is a *system/internal auto-generated key* with completely divergent formats across sources (e.g., \"journalssigmodchongftsykdjj03\" \u2194 \"777000\"). Such columns violate the exclusion rule for source-specific keys and cannot contribute to entity resolution.",
  "matching_columns": {
    "title": {
      "algorithm": "cosine",
      "weight": 0.9
    },
    "authors": {
      "algorithm": "cosine",
      "weight": 0.8
    },
    "venue": {
      "algorithm": "cosine",
      "weight": 0.3
    },
    "year": {
      "algorithm": "numeric_linear",
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

