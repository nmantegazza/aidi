# Matching Benchmark: febrl4 — Dynamic Weighted

- **Domain**: synthetic
- **Strategy**: Dynamic Weighted
- **Model**: deepseek-v4.1-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 1.0000 | 0.0000 |
| Recall | 0.9734 | 0.0051 |
| F1 Score | 0.9865 | 0.0026 |
| Execution Time (s) | 11.7472 | 0.2527 |
| Peak Memory (MB) | 36.44 | 0.45 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 10,626 |
| Completion Tokens | 33,195 |
| Total Tokens | 43,821 |
| Estimated Cost (USD) | $0.0000 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 1.0000 | 0.0000 |
| Potential F1 Ceiling | 1.0000 | 0.0000 |
| LLM Workload Ratio | 48.2% | - |
| Unrecoverable Loss | 0.0000 | - |
| Uncertain Purity | 0.3% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 97.53% |
| Consistent Matches | 4812 |
| Flaky Matches | 122 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.9728 | 0.9862 | 1.0000 | 1.0000 | 51.6% | 0.3% | 4864 | 0 | 136 | 12.0101 | 36.80 | 12349 | - |  |
| 2 | SUCCESS | 1.0000 | 0.9686 | 0.9840 | 1.0000 | 1.0000 | 51.1% | 0.3% | 4843 | 0 | 157 | 11.7253 | 36.58 | 19327 | - |  |
| 3 | SUCCESS | 1.0000 | 0.9788 | 0.9893 | 1.0000 | 1.0000 | 41.9% | 0.3% | 4894 | 0 | 106 | 11.5063 | 35.94 | 12145 | - |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.3773 | 0.7382 | [0.3255, 0.4291, 0.9444] |
| 2 | dynamic_skew | 0.3912 | 0.7454 | [0.3374, 0.4450, 0.9457] |
| 3 | dynamic_skew | 0.3285 | 0.6957 | [0.2799, 0.3771, 0.9081] |

## LLM Strategy Configuration & Prompts

- **Model**: `deepseek-v4.1-flash`
- **Provider**: `deepseek`
- **Latency**: `38.77s`
- **Log File**: `outputs/logs/llm_calls/20260919_162646_906692_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "**Dataset:** FEBRL-style person records (5000\u00d72). Exemplars reveal swapped name fields, swapped address lines, and single-character typos, but rock-solid agreement on soc_sec_id, DOB, postcode, suburb, state.\n\n**rec_id \u2014 EXCLUDED.** (1) Exemplars: \"rec1409org\" \u2194 \"rec1409dup0\" \u2014 identical stem with different source-specific suffixes. (2) Profile: 100% unique, 0% null, but this is an internally generated row key. (3) It is a System/internal attribute per exclusion rules (source-specific key with org/dup markers); no comparison algorithm is meaningful. (4) Weight 0.\n\n**given_name \u2014 jarowinkler, weight 0.5.** (1) Exemplars show single-word tokens with typos (\"emiily\") and, importantly, field-order swaps across sources (A given_name = B surname). (2) Profile: 2.24%/4.68% null (well under 50%), avg len 5.9, cardinality 769/1702 \u2192 keep. (3) Values are short single tokens (< 6 chars), where cosine collapses to 0 on any 1-char typo (\"emiily\" vs \"emily\" \u2192 orthogonal tokens); damerau over-penalizes length; jarowinkler is prefix-weighted and typo/phonetic tolerant on short names \u2014 the correct fit. (4) Identity attribute but degraded by cross-source swapping, so moderate 0.5 rather than 0.8+.\n\n**surname \u2014 jarowinkler, weight 0.6.** (1) Exemplars: multi-part surnames (\"stauntonsmith\", \"wilsonwheeler\") also subject to swapping. (2) Profile: 0.96%/2.04% null, avg len 6.54, cardinality 1827/2633 \u2192 keep. (3) Short single-token strings; cosine fails on any sub-word typo while jarowinkler absorbs character-level variation and prefix truncation. damerau would penalize the longer fused surnames heavily. (4) Surnames are more discriminating than given names (higher cardinality), so 0.6.\n\n**street_number \u2014 exact, weight 0.2.** (1) Exemplars: \"8.0\" \u2194 \"8.0\", \"68.0\" \u2194 \"68.0\", \"1.0\" \u2194 \"1.0\" \u2014 identical, with a trailing \".0\" representation. (2) Profile: 3.16%/5.74% null, cardinality 450/448 \u2192 keep. (3) A house number is a discrete locator where any digit change denotes a *different* address; numeric_linear/numeric_relative would misleadingly reward \"8\" vs \"9\" (adjacent houses) as near-identical, so strict `exact` is correct after the shared \".0\" format is normalized. (4) Supporting locator detail, low weight 0.2 (address_1 carries most of the street signal).\n\n**address_1 \u2014 jarowinkler, weight 0.3.** (1) Exemplars: \"arthur circle\" \u2194 \"arthur circle\" (matches 1,3) but swapped with address_2 in match 2 \u2014 short two-word street names. (2) Profile: 1.96%/4.4% null, avg len 14.65, cardinality 2399/3516 \u2192 keep. (3) Avg length < 20 disqualifies cosine (a single-token typo, e.g. \"circle\"\u2192\"circuit\", drops cosine to ~0.5); word reordering/abbreviation is better handled by jarowinkler's prefix-weighted character alignment for these short phrases. (4) Confirming descriptive/contextual address evidence, weight 0.3.\n\n**address_2 \u2014 jarowinkler, weight 0.25.** (1) Exemplars: \"tylden park\" \u2194 \"tylden park\", \"kookaburra village\" \u2194 \"frome street\" (swapped with address_1 in match 2). (2) Profile: 8.4%/17.02% null (still < 50%), avg len 11.76 \u2192 keep. (3) Same short-phrase regime as address_1; jarowinkler for typo/abbreviation tolerance over cosine. (4) Secondary/non-mandatory address line \u2192 slightly lower weight 0.25.\n\n**suburb \u2014 jarowinkler, weight 0.35.** (1) Exemplars: \"adamstown heights\" \u2194 \"adamstown heights\", \"broken hill\" \u2194 \"broken hill\", \"taree\" \u2194 \"taree\" \u2014 stable short locality phrases. (2) Profile: 1.1%/2.12% null, avg len 9.31 \u2192 keep. (3) Short locality label (< 20 chars); jarowinkler tolerates typos and truncations while cosine would zero out on any single misspelled token. (4) Strong geographic corroboration \u2192 0.35.\n\n**postcode \u2014 damerau_levenshtein, weight 0.4.** (1) Exemplars: \"3133\", \"2870\", \"2477\" all identical across sources. (2) Profile: 0%/0% null, cardinality 1419/1691 \u2192 keep. (3) A numeric postal code is a position-sensitive code; damerau_levenshtein detects single-digit flips/transpositions (\"3133\" vs \"3313\") which exact would over-punish to 0 and which cosine/jarowinkler handle poorly on digits. (4) Strong geographic identifier \u2192 0.4.\n\n**state \u2014 jarowinkler, weight 0.1.** (1) Exemplars: \"sa\", \"vic\", \"qld\" \u2014 identical 2-char codes. (2) Profile: 1.0%/2.14% null, cardinality 8/50 (B shows more values, possibly abbreviations/corruptions) \u2192 keep (not cardinality 1). (3) Very short standardized label; jarowinkler gives 1.0 on exact codes and graceful partial credit for abbreviation vs full-name variants, where cosine would return 0. (4) Weak, low-cardinality signal shared by many records \u2192 weight 0.1.\n\n**date_of_birth \u2014 date, weight 0.4.** (1) Exemplars: \"19721016.0\" identical across all three matches. (2) Profile: 1.88%/3.98% null, 91.76%/90.1% unique \u2192 keep. (3) Calendar dates should use the calendar-hierarchy matcher so small day/month/year shifts yield continuous similarity rather than the 0/1 cliff of exact; numeric_linear would be nonsensical on an encoded YYYYMMDD float. (4) Near-unique, highly identifying, but conventionally contextual \u2192 0.4.\n\n**soc_sec_id \u2014 damerau_levenshtein, weight 0.9.** (1) Exemplars: \"1844518\", \"6922783\", \"8119451\" \u2014 perfectly identical across sources. (2) Profile: 0%/0% null, 100% unique in both \u2192 keep (the gold discriminator). (3) An alphanumeric government/tax identifier is best matched by damerau_levenshtein, which preserves digit positions yet tolerates a single typo/transposition; cosine is meaningless on a token-free digit code. (4) Core identity attribute \u2192 highest weight 0.9.\n\n**Excluded:** rec_id (source-specific key). All other columns retain weights as above; the aggregate is dominated by soc_sec_id, names, postcode and DOB, which is consistent with the observed exemplar stability.",
  "matching_columns": {
    "given_name": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "surname": {
      "algorithm": "jarowinkler",
      "weight": 0.6
    },
    "street_number": {
      "algorithm": "exact",
      "weight": 0.2
    },
    "address_1": {
      "algorithm": "jarowinkler",
      "weight": 0.3
    },
    "address_2": {
      "algorithm": "jarowinkler",
      "weight": 0.25
    },
    "suburb": {
      "algorithm": "jarowinkler",
      "weight": 0.35
    },
    "postcode": {
      "algorithm": "damerau_levenshtein",
      "weight": 0.4
    },
    "state": {
      "algorithm": "jarowinkler",
      "weight": 0.1
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
| **Total Rows** | 5000 | 5000 |
| **Column Count** | 11 | 11 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.97)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec1409org" | "rec1409dup0" |
| given_name | "tylah" | "kempe" |
| surname | "kempe" | "tylah" |
| street_number | "8.0" | "8.0" |
| address_1 | "arthur circle" | "arthur circle" |
| address_2 | "tylden park" | "tylden park" |
| suburb | "adamstown heights" | "adamstown heights" |
| postcode | "3133" | "3133" |
| state | "sa" | "sa" |
| date_of_birth | "19721016.0" | "19721016.0" |
| soc_sec_id | "1844518" | "1844518" |

#### Candidate Match 2 (Overall Text Match Score: 0.96)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec4917org" | "rec4917dup0" |
| given_name | "" | "" |
| surname | "stauntonsmith" | "stauntonsmith" |
| street_number | "68.0" | "68.0" |
| address_1 | "frome street" | "kookaburra village" |
| address_2 | "kookaburra village" | "frome street" |
| suburb | "broken hill" | "broken hill" |
| postcode | "2870" | "2870" |
| state | "vic" | "vic" |
| date_of_birth | "19820117.0" | "19820117.0" |
| soc_sec_id | "6922783" | "6922783" |

#### Candidate Match 3 (Overall Text Match Score: 0.96)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| rec_id | "rec3571org" | "rec3571dup0" |
| given_name | "emiily" | "wilsonwheeler" |
| surname | "wilsonwheeler" | "emiily" |
| street_number | "1.0" | "1.0" |
| address_1 | "woolcock street" | "woolcock street" |
| address_2 | "willandra" | "willandra" |
| suburb | "taree" | "taree" |
| postcode | "2477" | "2477" |
| state | "qld" | "qld" |
| date_of_birth | "19610625.0" | "19610625.0" |
| soc_sec_id | "8119451" | "8119451" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **rec_id** | 0.0% | 0.0% | 100.0% | 100.0% | 5000 | 5000 | 9.78 | 10.78 | "rec1409org" ↔ "rec1409dup0" |
| **given_name** | 2.24% | 4.68% | 15.38% | 34.04% | 769 | 1702 | 5.9 | 5.93 | "tylah" ↔ "kempe" |
| **surname** | 0.96% | 2.04% | 36.54% | 52.66% | 1827 | 2633 | 6.54 | 6.52 | "kempe" ↔ "tylah" |
| **street_number** | 3.16% | 5.74% | 9.0% | 8.96% | 450 | 448 | N/A | N/A | "8.0" ↔ "8.0" |
| **address_1** | 1.96% | 4.4% | 47.98% | 70.32% | 2399 | 3516 | 14.65 | 14.5 | "arthur circle" ↔ "arthur circle" |
| **address_2** | 8.4% | 17.02% | 51.5% | 66.1% | 2575 | 3305 | 11.76 | 12.01 | "tylden park" ↔ "tylden park" |
| **suburb** | 1.1% | 2.12% | 32.68% | 48.06% | 1634 | 2403 | 9.31 | 9.32 | "adamstown heights" ↔ "adamstown heights" |
| **postcode** | 0.0% | 0.0% | 28.38% | 33.82% | 1419 | 1691 | N/A | N/A | "3133" ↔ "3133" |
| **state** | 1.0% | 2.14% | 0.16% | 1.0% | 8 | 50 | 2.82 | 2.82 | "sa" ↔ "sa" |
| **date_of_birth** | 1.88% | 3.98% | 91.76% | 90.1% | 4588 | 4505 | N/A | N/A | "19721016.0" ↔ "19721016.0" |
| **soc_sec_id** | 0.0% | 0.0% | 100.0% | 100.0% | 5000 | 5000 | N/A | N/A | "1844518" ↔ "1844518" |
```
</details>

