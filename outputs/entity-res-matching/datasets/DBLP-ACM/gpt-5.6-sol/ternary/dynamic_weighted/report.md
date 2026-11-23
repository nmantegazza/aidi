# Matching Benchmark: DBLP-ACM — Dynamic Weighted

- **Domain**: citations
- **Strategy**: Dynamic Weighted
- **Model**: gpt-5.6-sol
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9934 | 0.0010 |
| Recall | 0.9769 | 0.0036 |
| F1 Score | 0.9851 | 0.0021 |
| Execution Time (s) | 6.7660 | 0.1134 |
| Peak Memory (MB) | 45.50 | 0.05 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 8,865 |
| Completion Tokens | 6,029 |
| Total Tokens | 14,894 |
| Estimated Cost (USD) | $0.1385 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9951 | 0.0009 |
| Potential F1 Ceiling | 0.9942 | 0.0009 |
| LLM Workload Ratio | 1.6% | - |
| Unrecoverable Loss | 0.0049 | - |
| Uncertain Purity | 1.0% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 98.05% |
| Consistent Matches | 2167 |
| Flaky Matches | 43 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9945 | 0.9775 | 0.9859 | 0.9960 | 0.9952 | 1.5% | 1.1% | 2174 | 12 | 50 | 6.6361 | 45.56 | 4971 | $0.0550 |  |
| 2 | SUCCESS | 0.9927 | 0.9730 | 0.9827 | 0.9942 | 0.9934 | 1.4% | 1.3% | 2164 | 16 | 60 | 6.8169 | 45.48 | 4952 | $0.0416 |  |
| 3 | SUCCESS | 0.9932 | 0.9802 | 0.9866 | 0.9951 | 0.9941 | 1.9% | 0.7% | 2180 | 15 | 44 | 6.8451 | 45.48 | 4971 | $0.0419 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.3323 | 0.7073 | [0.2441, 0.4206, 0.8984] |
| 2 | dynamic_skew | 0.3389 | 0.7127 | [0.2454, 0.4323, 0.8996] |
| 3 | dynamic_skew | 0.3240 | 0.7014 | [0.2441, 0.4038, 0.8998] |

## LLM Strategy Configuration & Prompts

- **Model**: `gpt-5.6-sol`
- **Provider**: `openai`
- **Latency**: `33.03s`
- **Log File**: `outputs/logs/llm_calls/20260919_155626_149411_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "Column: id\n1. Inspect Exemplar Candidate Matches: The same publications have completely different ID schemes: descriptive DBLP-like strings in Source A versus unrelated numeric identifiers in Source B (for example, \"journalssigmodchongftsykdjj03\" \u2194 \"777000\"). Thus, cross-source ID similarity does not represent entity similarity.\n2. Inspect Statistical Profile: The column is fully populated and effectively unique in each source, with cardinalities equal to the row counts (2616 and 2294). Despite excellent completeness and variance, it is a source-specific system key and must be excluded.\n3. Algorithm Trade-off Evaluation: Exact comparison would reject true matches because the key domains differ. Damerau-Levenshtein or Jaro-Winkler could produce accidental character overlap without semantic meaning, while cosine is unsuitable for these identifiers. No comparison algorithm can make the two source-specific key systems reliably comparable without an external crosswalk.\n4. Weight Justification: Excluded and assigned no scoring weight because it is an internal/source-specific identifier rather than a shared identity attribute.\n\nColumn: title\n1. Inspect Exemplar Candidate Matches: Titles are identical across all three exemplars, including long multi-word strings such as \"a mapping mechanism to support bitmap index and other auxiliary structures on tables stored as primary btrees.\" The data also uses concatenated forms such as \"highperformance\" and \"selforganizing,\" but these forms are consistent across the aligned examples.\n2. Inspect Statistical Profile: Null rates are 0% in both sources; cardinality is high (2507/2616 and 2216/2294), uniqueness is approximately 95.83% and 96.6%, and average lengths are 55.39 and 55.93. The column is highly discriminative and passes all exclusion rules.\n3. Algorithm Trade-off Evaluation: Cosine is appropriate for long, multi-word publication titles and is resilient to possible token additions, omissions, or word-order variation. Jaro-Winkler is less appropriate for strings averaging about 56 characters and can degrade with long-text changes; Damerau-Levenshtein over-penalizes insertions and length differences; exact matching would be unnecessarily brittle to minor title metadata variation. Cosine cannot repair sub-word typos or spacing differences, but the exemplars show consistent title tokenization, making that limitation less concerning here.\n4. Weight Justification: Weight 0.70. A publication title is the strongest primary descriptive attribute in this dataset and is highly distinctive, but it is not given core-identifier weight because duplicate or generic titles can occur.\n\nColumn: authors\n1. Inspect Exemplar Candidate Matches: The exemplars contain substantially the same author names but in radically different order. For example, Candidate 1 begins with \"mahesh jagannath\" in Source A and \"eugene inseok chong\" in Source B, while Candidate 3 reverses and rearranges nearly the entire author list. Minor representation differences also appear, such as \"zachary g ives\" versus \"zachary ives\" and \"alon y levy\" versus \"alon levy.\"\n2. Inspect Statistical Profile: Null rates are 0% in Source A and 0.61% in Source B, well below the 50% threshold. Cardinalities are high (2316 and 2008), uniqueness is about 88.53% and 87.53%, and average lengths are 43.84 and 43.34. The field is complete, variable, and strongly discriminative.\n3. Algorithm Trade-off Evaluation: Cosine is the best fit because these are long, multi-token author lists whose dominant empirical variation is token/order permutation and occasional omitted initials. Jaro-Winkler and Damerau-Levenshtein are order-sensitive and would heavily penalize the observed rearrangements; exact matching would reject all reordered lists. Cosine's weakness is that it does not recognize misspelled name tokens, but the exemplars mainly show reordering and initial omission rather than spelling errors, so token-level overlap is the more important behavior.\n4. Weight Justification: Weight 0.65. The author set is a strong primary descriptive signal that substantially confirms title identity, though common authors and incomplete author lists make it slightly less decisive than title.\n\nColumn: venue\n1. Inspect Exemplar Candidate Matches: Venue representation is inconsistent. Candidate 1 differs only by an added token (\"sigmod record\" \u2194 \"acm sigmod record\"), while Candidates 2 and 3 use divergent taxonomies (\"sigmod conference\" \u2194 \"international conference on management of data\") with little or no lexical overlap despite denoting the same venue.\n2. Inspect Statistical Profile: Null rates are 0% in both sources and cardinality is 5 in each, so the field passes formal exclusion rules but has very low uniqueness (about 0.19% and 0.22%). Average length differs considerably between sources (11.17 versus 34.57), supporting the observation that Source B uses more expanded labels.\n3. Algorithm Trade-off Evaluation: Cosine is selected because it handles multi-word venue labels and token additions such as the extra \"acm\" without imposing word-order sensitivity. Exact would reject even the simple expanded form; Jaro-Winkler and Damerau-Levenshtein would be distorted by large length differences and cannot resolve taxonomy synonyms. Cosine also cannot recognize \"sigmod conference\" as equivalent to \"international conference on management of data,\" so this column remains unreliable without a venue crosswalk and must have very low influence.\n4. Weight Justification: Weight 0.15. Venue is only a weak corroborating signal because it has five values and empirically divergent taxonomies; it should help where lexical overlap exists but never override title and author evidence.\n\nColumn: year\n1. Inspect Exemplar Candidate Matches: Publication years agree exactly in every exemplar: 2003 \u2194 2003, 1997 \u2194 1997, and 2000 \u2194 2000. No formatting differences, offsets, or date granularity issues are observed.\n2. Inspect Statistical Profile: Null rates are 0% in both sources, cardinality is 10 in each, and uniqueness is low (about 0.38% and 0.44%). The field passes exclusion rules but has limited standalone discrimination.\n3. Algorithm Trade-off Evaluation: Exact is appropriate because the values are standardized four-digit publication years and all known matches agree. Numeric-linear would give partial credit to adjacent years, which could increase false positives among similar papers, and numeric-relative is inappropriate for calendar years because relative percentage difference has no useful temporal meaning. The date matcher is unnecessary because these are years rather than full dates.\n4. Weight Justification: Weight 0.30. Year is useful auxiliary context that can reject otherwise similar records, but its low cardinality prevents it from serving as a primary identity signal.",
  "matching_columns": {
    "title": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "authors": {
      "algorithm": "cosine",
      "weight": 0.65
    },
    "venue": {
      "algorithm": "cosine",
      "weight": 0.15
    },
    "year": {
      "algorithm": "exact",
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

