# Matching Benchmark: DBLP-ACM — Dynamic Weighted

- **Domain**: citations
- **Strategy**: Dynamic Weighted
- **Model**: deepseek-v4.1-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9914 | 0.0012 |
| Recall | 0.9793 | 0.0055 |
| F1 Score | 0.9853 | 0.0022 |
| Execution Time (s) | 8.1244 | 1.2756 |
| Peak Memory (MB) | 65.50 | 17.32 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 9,969 |
| Completion Tokens | 7,721 |
| Total Tokens | 17,690 |
| Estimated Cost (USD) | $0.0000 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9939 | 0.0011 |
| Potential F1 Ceiling | 0.9926 | 0.0011 |
| LLM Workload Ratio | 6.9% | - |
| Unrecoverable Loss | 0.0061 | - |
| Uncertain Purity | 0.3% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 97.30% |
| Consistent Matches | 2165 |
| Flaky Matches | 60 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9905 | 0.9825 | 0.9865 | 0.9928 | 0.9916 | 9.7% | 0.1% | 2185 | 21 | 39 | 9.1288 | 75.51 | 5729 | - |  |
| 2 | SUCCESS | 0.9909 | 0.9825 | 0.9867 | 0.9937 | 0.9923 | 8.5% | 0.1% | 2185 | 20 | 39 | 8.5553 | 75.49 | 5539 | - |  |
| 3 | SUCCESS | 0.9927 | 0.9730 | 0.9827 | 0.9951 | 0.9939 | 2.5% | 0.7% | 2164 | 16 | 60 | 6.6892 | 45.51 | 6422 | - |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.2960 | 0.6790 | [0.2366, 0.3554, 0.8947] |
| 2 | dynamic_skew | 0.3028 | 0.6815 | [0.2374, 0.3683, 0.8903] |
| 3 | dynamic_skew | 0.3355 | 0.6999 | [0.2417, 0.4294, 0.8803] |

## LLM Strategy Configuration & Prompts

- **Model**: `deepseek-v4.1-flash`
- **Provider**: `deepseek`
- **Latency**: `11.96s`
- **Log File**: `outputs/logs/llm_calls/20260919_155410_061211_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "**Task 1 \u2014 Column Selection & Algorithm Assignment**\n\nThis is a bibliographic (academic publication) dataset. Matching entities are the same paper published across two sources.\n\n---\n\n**COLUMN: id \u2014 EXCLUDED**\n1. *Exemplar inspection*: Source A holds semantic string keys (\"journalssigmodchongftsykdjj03\", \"confsigmodarpacidusseauachp97\") while Source B holds plain integers (\"777000\", \"253322\"). These are completely disjoint key namespaces with zero correspondence.\n2. *Statistical profile*: 100% unique, cardinality = row count (2616 / 2294). This is a surrogate/auto-generated primary key.\n3. *Algorithm trade-off*: No string or numeric algorithm can bridge two unrelated key formats; matching on them would create systematic false negatives.\n4. *Conclusion*: Excluded \u2014 source-specific internal identifier with no cross-source semantics.\n\n---\n\n**COLUMN: title \u2014 cosine, weight 0.7**\n1. *Exemplar inspection*: Titles align near-verbatim across all three candidates (\"highperformance sorting on networks of workstations\" \u2194 identical). Text is long, multi-word, and composed of standard dictionary tokens.\n2. *Statistical profile*: 0% null, ~96% unique, cardinality 2507/2216, avg length \u2248 55 chars (well above the 20-char multi-word threshold).\n3. *Algorithm trade-off*: With avg length 55 and many standard-word tokens, cosine (token-level TF-IDF) is the natural fit \u2014 it is order-invariant and resilient to token additions/omissions and punctuation/hyphenation noise. Jaro-Winkler would over-weight the prefix and degrade on long strings; damerau_levenshtein would over-penalize length differences.\n4. *Weight justification*: Titles are the single most discriminating descriptive attribute for a paper (high cardinality, near-unique), so they earn a primary descriptive weight of 0.7.\n\n---\n\n**COLUMN: authors \u2014 cosine, weight 0.55**\n1. *Exemplar inspection*: The author *set* is essentially identical but the *ordering is heavily permuted* across sources (exemplar 1: \"mahesh jagannath\u2026richard jiang ramkumar krishnan\" vs a reshuffled B ordering; exemplar 3 fully reordered). Minor variants also appear (\"alon y levy\" vs \"alon levy\", dropped middle initials).\n2. *Statistical profile*: 0%/0.61% null, ~88% unique, avg length \u2248 44 chars \u2014 a multi-token free-text field.\n3. *Algorithm trade-off*: Because the token ORDER is scrambled, cosine's order-invariance is essential \u2014 Jaro-Winkler and damerau_levenshtein both penalize reordering severely and would collapse to low scores. Cosine tolerates the drop of middle initials (token omission) gracefully. Chosen: **cosine**.\n4. *Weight justification*: Authorship is a strong corroborating identity signal for a publication, so weight 0.55.\n\n---\n\n**COLUMN: venue \u2014 jarowinkler, weight 0.15**\n1. *Exemplar inspection*: Divergent taxonomy/abbreviation: \"sigmod record\" \u2194 \"acm sigmod record\" (prefix expansion) and \"sigmod conference\" \u2194 \"international conference on management of data\" (abbreviation vs full name \u2014 almost no surface overlap).\n2. *Statistical profile*: 0% null, cardinality = 5 in both (very low variance, but not 1), avg length 11.2 (A) / 34.6 (B) \u2014 short labels.\n3. *Algorithm trade-off*: Values are short labels, so cosine would fail on the abbreviation\u2194full-name pairs (0 token overlap for \"sigmod conference\" vs \"international conference on management of data\"). Jaro-Winkler at least captures the shared \"sigmod\" prefix in the \"acm sigmod record\" cases and is best suited to short strings. No algorithm fully bridges the abbreviated\u2194expanded taxonomy, so this remains an inherently weak signal.\n4. *Weight justification*: Low cardinality plus divergent taxonomies make venue only a weak supporting signal \u2192 weight 0.15.\n\n---\n\n**COLUMN: year \u2014 numeric_linear, weight 0.25**\n1. *Exemplar inspection*: Year matches exactly across all three pairs (\"2003\"\u2194\"2003\", \"1997\"\u2194\"1997\", \"2000\"\u2194\"2000\").\n2. *Statistical profile*: 0% null, cardinality 10, no nulls; discrete calendar interval scale.\n3. *Algorithm trade-off*: Year is a uniform interval scale where absolute distance is meaningful (a +1yr gap should give partial credit). numeric_relative is explicitly inappropriate for calendar years (it would treat 1999 vs 2000 as a tiny gap but 2000 vs 2001 differently at scale boundaries); exact would be too brittle for a confirming attribute. Chosen: **numeric_linear**.\n4. *Weight justification*: A supporting contextual attribute that corroborates a match but cannot uniquely identify a paper \u2192 weight 0.25.",
  "matching_columns": {
    "title": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "authors": {
      "algorithm": "cosine",
      "weight": 0.55
    },
    "venue": {
      "algorithm": "jarowinkler",
      "weight": 0.15
    },
    "year": {
      "algorithm": "numeric_linear",
      "weight": 0.25
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

