# Matching Benchmark: febrl1 — Dynamic Weighted

- **Domain**: synthetic
- **Strategy**: Dynamic Weighted
- **Model**: deepseek-v4.1-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 1.0000 | 0.0000 |
| Recall | 0.8787 | 0.1582 |
| F1 Score | 0.9301 | 0.0947 |
| Execution Time (s) | 0.3255 | 0.0686 |
| Peak Memory (MB) | 0.93 | 0.06 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 10,587 |
| Completion Tokens | 21,989 |
| Total Tokens | 32,576 |
| Estimated Cost (USD) | $0.0000 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9993 | 0.0012 |
| Potential F1 Ceiling | 0.9997 | 0.0006 |
| LLM Workload Ratio | 28.0% | - |
| Unrecoverable Loss | 0.0007 | - |
| Uncertain Purity | 35.0% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 71.17% |
| Consistent Matches | 348 |
| Flaky Matches | 141 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.9680 | 0.9837 | 1.0000 | 1.0000 | 38.2% | 2.6% | 484 | 0 | 16 | 0.3210 | 0.91 | 9379 | - |  |
| 2 | SUCCESS | 1.0000 | 0.6960 | 0.8208 | 0.9980 | 0.9990 | 9.4% | 100.0% | 348 | 0 | 152 | 0.2593 | 0.88 | 11802 | - |  |
| 3 | SUCCESS | 1.0000 | 0.9720 | 0.9858 | 1.0000 | 1.0000 | 36.5% | 2.4% | 486 | 0 | 14 | 0.3962 | 1.00 | 11395 | - |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.3955 | 0.7375 | [0.3442, 0.4469, 0.9313] |
| 2 | dynamic_skew | 0.5827 | 0.8977 | [0.3677, 0.7977, 0.9644] |
| 3 | dynamic_skew | 0.3381 | 0.7013 | [0.2876, 0.3886, 0.9097] |

## LLM Strategy Configuration & Prompts

- **Model**: `deepseek-v4.1-flash`
- **Provider**: `deepseek`
- **Latency**: `24.87s`
- **Log File**: `outputs/logs/llm_calls/20260919_161729_467999_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "**Overview:** Two 500-row sources describing people (names, addresses, DOB, SSN). The three exemplar pairs show near-identical values on address/suburb/postcode/state/DOB/SSN, but with a notable data-quality quirk: for some records given_name and surname are *swapped* between sources (Cand. 1: \"thomas\"\u2194\"guthridge\"; Cand. 3: \"dante\"\u2194\"davilasanhdars\"), and address_1/address_2 lines are also permuted (Cand. 2). Fields are therefore noisy at the token/phrase level, favoring character-based comparators over pure token TF-IDF.\n\n**rec_id** \u2014 (1) Exemplars: \"rec177org\"\u2194\"rec177dup0\", \"rec447org\"\u2194\"rec447dup0\" \u2014 the numeric stem matches but the suffixes ('org'/'dup0') are source-specific and differ systematically. (2) Profile: 0% null, 100% unique in both. (3) This is an internal, auto-generated surrogate key; the divergent suffix is a source marker, so it carries no cross-source entity information. (4) EXCLUDED per system/internal-key rule (source-specific key).\n\n**given_name** \u2014 (1) Exemplars: \"lara\"\u2194\"lara\" (exact) but \"thomas\"\u2194\"guthridge\" and \"dante\"\u2194\"davilasanhdars\" reveal value-swapping with surname. (2) Profile: null 3.0%/5.8% (<50%), cardinality 259/320, avg len ~5.9 \u2192 very short single tokens. (3) Short single words are exactly where token-level cosine collapses (a 1-char typo \u2192 0.0), so cosine is unsafe; jarowinkler's prefix-weighted character alignment tolerates typos/truncations on short names and is the correct fit. (4) Core identity attribute but noisy/swappable \u2192 weight 0.6.\n\n**surname** \u2014 (1) Exemplars: \"matthews\"\u2194\"matthews\" (exact) with the same swap noise as given_name. (2) Profile: null 1.2%/2.4%, cardinality 340/387, avg len ~6.6 \u2192 short single tokens. (3) Same reasoning as given_name: cosine fails on short single-word tokens with typos; jarowinkler is robust. (4) Core identity, slightly more distinctive (higher cardinality) \u2192 weight 0.65.\n\n**street_number** \u2014 (1) Exemplars: \"6.0\"\u2194\"6.0\", \"303.0\"\u2194\"303.0\" (perfect). (2) Profile: null 2.8%/6.2%, cardinality 146/141 across both. (3) Numeric magnitude; low-cardinality and heavily repeated (many 6.0/303.0), so distinctive power is limited; numeric_linear reflects absolute house-number distance on a bounded scale better than relative distance (which would absurdly penalize 6 vs 303 as ~98% apart). (4) Weak, supporting address component \u2192 weight 0.15.\n\n**address_1** \u2014 (1) Exemplars: \"brunswick circuit\"\u2194\"brunswick circuit\" (exact) but permuted with address_2 in Cand. 2 (\"beaumaris street\"\u2194\"sunforest therapy centre\"). (2) Profile: null 1.4%/3.6%, cardinality 445/469 (highly unique), avg len ~14.5. (3) Multi-word but short (~2-3 tokens); cosine would score 0.5 whenever one street-name token has a spelling variant (e.g. \"brunswick\"\u2194\"brunkswick\"), so jarowinkler's character alignment is safer for these typo-prone short phrases. (4) Strong descriptive attribute \u2192 weight 0.5.\n\n**address_2** \u2014 (1) Exemplars: \"tintagel\"\u2194\"tintagel\" (exact), also swapped with address_1 and often a single building/locality token (\"surama\"). (2) Profile: null 7.4%/15.6% (higher but <50%), cardinality 411/401, avg len ~12. (3) Frequently single short tokens \u2192 cosine fails on typo; jarowinkler handles short single-word tokens. (4) Supporting descriptive attribute, noisier and less reliable than address_1 \u2192 weight 0.25.\n\n**suburb** \u2014 (1) Exemplars: \"avondale heights\"\u2194\"avondale heights\" (exact in all three). (2) Profile: null 1.2%/2.4%, cardinality 390/427, avg len ~9.5. (3) Short place names; jarowinkler is the recommended comparator for city/suburb names (typo and truncation tolerant), whereas cosine would break on single-token variants. (4) Supporting descriptive/geographic attribute \u2192 weight 0.4.\n\n**postcode** \u2014 (1) Exemplars: \"2073\"\u2194\"2073\", \"4179\"\u2194\"4179\", \"2029\"\u2194\"2029\" (exact). (2) Profile: null 0.0%/0.0%, cardinality 389/409, discrete 4-digit codes. (3) A standardized postal code is a discrete identifier: a differing digit denotes a genuinely different locality, so zero-tolerance `exact` is appropriate (damerau would over-credit 1-digit mismatches as 0.75). (4) Supporting geographic attribute, shared by many entities \u2192 weight 0.35.\n\n**state** \u2014 (1) Exemplars: \"vic\"\u2194\"vic\", \"nsw\"\u2194\"nsw\", \"wa\"\u2194\"wa\" (exact). (2) Profile: null 1.2%/1.8%, cardinality 8/17, avg len ~2.8 \u2192 2-3 char abbreviations. (3) Standardized categorical code \u2192 `exact`; jarowinkler/cosine give no benefit on 2-char codes and would add false partial credit. (4) Weak, coarse geographic context \u2192 weight 0.15.\n\n**date_of_birth** \u2014 (1) Exemplars: \"19080625.0\"\u2194\"19080625.0\", \"19911006.0\"\u2194\"19911006.0\" (identical). (2) Profile: null 2.6%/5.6%, cardinality 483/469. (3) Full calendar dates stored as YYYYMMDD; `date` gives graded credit for small parsing/format or minor day/month shifts, unlike exact. (4) Strong supporting identity attribute \u2192 weight 0.4.\n\n**soc_sec_id** \u2014 (1) Exemplars: \"4255165\"\u2194\"4255165\", \"2164704\"\u2194\"2164704\", \"2609420\"\u2194\"2609420\" (identical). (2) Profile: null 0.0%/0.0%, 100% unique in both \u2014 a true unique identifier. (3) It is a tax/SSN-style numeric code, so damerau_levenshtein preserves digit positions and tolerates single-digit transposition/typo, which is the recommended treatment for ID codes. (4) Core identity attribute (near-unique government ID) \u2192 highest weight 0.9.\n\nExcluded columns: rec_id (source-specific surrogate key). All retained columns pass the null (<50%) and cardinality (>1) filters.",
  "matching_columns": {
    "given_name": {
      "algorithm": "jarowinkler",
      "weight": 0.6
    },
    "surname": {
      "algorithm": "jarowinkler",
      "weight": 0.65
    },
    "street_number": {
      "algorithm": "numeric_linear",
      "weight": 0.15
    },
    "address_1": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "address_2": {
      "algorithm": "jarowinkler",
      "weight": 0.25
    },
    "suburb": {
      "algorithm": "jarowinkler",
      "weight": 0.4
    },
    "postcode": {
      "algorithm": "exact",
      "weight": 0.35
    },
    "state": {
      "algorithm": "exact",
      "weight": 0.15
    },
    "date_of_birth": {
      "algorithm": "date",
      "weight": 0.4
    },
    "soc_sec_id": {
      "algorithm": "damerau_levenshtein",
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
| **Total Rows** | 500 | 500 |
| **Column Count** | 11 | 11 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.97)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec177org" | "rec177dup0" |
| given_name | "thomas" | "guthridge" |
| surname | "guthridge" | "thomas" |
| street_number | "6.0" | "6.0" |
| address_1 | "brunswick circuit" | "brunswick circuit" |
| address_2 | "tintagel" | "tintagel" |
| suburb | "avondale heights" | "avondale heights" |
| postcode | "2073" | "2073" |
| state | "vic" | "vic" |
| date_of_birth | "19080625.0" | "19080625.0" |
| soc_sec_id | "4255165" | "4255165" |

#### Candidate Match 2 (Overall Text Match Score: 0.97)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec447org" | "rec447dup0" |
| given_name | "lara" | "lara" |
| surname | "matthews" | "matthews" |
| street_number | "6.0" | "6.0" |
| address_1 | "beaumaris street" | "sunforest therapy centre" |
| address_2 | "sunforest therapy centre" | "beaumaris street" |
| suburb | "the basin" | "the basin" |
| postcode | "4179" | "4179" |
| state | "nsw" | "nsw" |
| date_of_birth | "19911006.0" | "19911006.0" |
| soc_sec_id | "2164704" | "2164704" |

#### Candidate Match 3 (Overall Text Match Score: 0.96)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec57org" | "rec57dup0" |
| given_name | "dante" | "davilasanhdars" |
| surname | "davilasanhdars" | "dante" |
| street_number | "303.0" | "303.0" |
| address_1 | "wild street" | "wild street" |
| address_2 | "surama" | "surama" |
| suburb | "avondale heights" | "avondale heights" |
| postcode | "2029" | "2029" |
| state | "wa" | "wa" |
| date_of_birth | "19120206.0" | "19120206.0" |
| soc_sec_id | "2609420" | "2609420" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **rec_id** | 0.0% | 0.0% | 100.0% | 100.0% | 500 | 500 | 8.78 | 9.78 | "rec177org" ↔ "rec177dup0" |
| **given_name** | 3.0% | 5.8% | 51.8% | 64.0% | 259 | 320 | 5.92 | 5.97 | "thomas" ↔ "guthridge" |
| **surname** | 1.2% | 2.4% | 68.0% | 77.4% | 340 | 387 | 6.57 | 6.57 | "guthridge" ↔ "thomas" |
| **street_number** | 2.8% | 6.2% | 29.2% | 28.2% | 146 | 141 | N/A | N/A | "6.0" ↔ "6.0" |
| **address_1** | 1.4% | 3.6% | 89.0% | 93.8% | 445 | 469 | 14.45 | 14.47 | "brunswick circuit" ↔ "brunswick circuit" |
| **address_2** | 7.4% | 15.6% | 82.2% | 80.2% | 411 | 401 | 11.87 | 12.09 | "tintagel" ↔ "tintagel" |
| **suburb** | 1.2% | 2.4% | 78.0% | 85.4% | 390 | 427 | 9.45 | 9.57 | "avondale heights" ↔ "avondale heights" |
| **postcode** | 0.0% | 0.0% | 77.8% | 81.8% | 389 | 409 | N/A | N/A | "2073" ↔ "2073" |
| **state** | 1.2% | 1.8% | 1.6% | 3.4% | 8 | 17 | 2.84 | 2.84 | "vic" ↔ "vic" |
| **date_of_birth** | 2.6% | 5.6% | 96.6% | 93.8% | 483 | 469 | N/A | N/A | "19080625.0" ↔ "19080625.0" |
| **soc_sec_id** | 0.0% | 0.0% | 100.0% | 100.0% | 500 | 500 | N/A | N/A | "4255165" ↔ "4255165" |
```
</details>

