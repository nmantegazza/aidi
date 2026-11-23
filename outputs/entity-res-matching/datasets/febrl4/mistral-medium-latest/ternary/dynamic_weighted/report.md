# Matching Benchmark: febrl4 — Dynamic Weighted

- **Domain**: synthetic
- **Strategy**: Dynamic Weighted
- **Model**: mistral-medium-latest
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 1.0000 | 0.0000 |
| Recall | 0.9862 | 0.0080 |
| F1 Score | 0.9930 | 0.0040 |
| Execution Time (s) | 10.5589 | 1.7688 |
| Peak Memory (MB) | 37.14 | 0.95 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 10,791 |
| Completion Tokens | 50,019 |
| Total Tokens | 60,810 |
| Estimated Cost (USD) | $0.3913 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 1.0000 | 0.0000 |
| Potential F1 Ceiling | 1.0000 | 0.0000 |
| LLM Workload Ratio | 49.4% | - |
| Unrecoverable Loss | 0.0000 | - |
| Uncertain Purity | 0.1% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 97.57% |
| Consistent Matches | 4860 |
| Flaky Matches | 121 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.9910 | 0.9955 | 1.0000 | 1.0000 | 48.6% | 0.1% | 4955 | 0 | 45 | 11.2352 | 36.60 | 23389 | $0.1538 |  |
| 2 | SUCCESS | 1.0000 | 0.9770 | 0.9884 | 1.0000 | 1.0000 | 54.9% | 0.2% | 4885 | 0 | 115 | 8.5517 | 38.24 | 14217 | $0.0850 |  |
| 3 | SUCCESS | 1.0000 | 0.9906 | 0.9953 | 1.0000 | 1.0000 | 44.6% | 0.1% | 4953 | 0 | 47 | 11.8898 | 36.58 | 23204 | $0.1524 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.4051 | 0.7490 | [0.3605, 0.4496, 0.9487] |
| 2 | dynamic_skew | 0.3595 | 0.7168 | [0.3151, 0.4038, 0.9256] |
| 3 | dynamic_skew | 0.3934 | 0.7470 | [0.3491, 0.4377, 0.9533] |

## LLM Strategy Configuration & Prompts

- **Model**: `mistral-medium-latest`
- **Provider**: `mistral`
- **Latency**: `99.72s`
- **Log File**: `outputs/logs/llm_calls/20260919_163450_868191_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "### Column Selection and Algorithm Assignment Reasoning\n\n#### Excluded Columns\n- **rec_id**: Source-specific internal key (auto-generated identifier with prefix patterns like \"rec1409org\" vs \"rec1409dup0\"). Excluded per Step 1b exclusion rules.\n\n#### Included Columns\n\n**soc_sec_id**\n1. **Inspect Exemplar Candidate Matches**: In all three candidate matches, soc_sec_id values are identical between Source A and Source B (\"1844518\", \"6922783\", \"8119451\"). No typos, abbreviations, or format variations observed.\n2. **Inspect Statistical Profile**: 0.0% null in both sources, 100.0% unique (cardinality = 5000 in both), numeric field.\n3. **Algorithm Trade-off Evaluation**: As a 7-digit numeric social security identifier, `damerau_levenshtein` is optimal because it detects single-digit transpositions or substitutions (e.g., \"1844518\" vs \"1844581\") which are common in manually entered IDs. `exact` would be too strict for real-world data, while `jarowinkler` and `cosine` are designed for textual strings, not numeric codes. `numeric_relative`/`numeric_linear` are inappropriate as these are identifiers, not measurements.\n4. **Weight Justification**: Government-issued unique identifier representing core entity identity. Weight = 1.0.\n\n**date_of_birth**\n1. **Inspect Exemplar Candidate Matches**: All three matches show identical date_of_birth values across sources (\"19721016.0\", \"19820117.0\", \"19610625.0\") in YYYYMMDD format.\n2. **Inspect Statistical Profile**: Low null percentage (1.88% | 3.98%), high cardinality (91.76% | 90.1%).\n3. **Algorithm Trade-off Evaluation**: The `date` algorithm is specifically designed for calendar dates, handling minor variations (e.g., off-by-one day) continuously. `exact` would be too brittle, while string-based algorithms (`jarowinkler`, `damerau_levenshtein`) would not respect date semantics (e.g., \"19721016\" vs \"19721017\" are adjacent dates but string algorithms would treat them as very different).\n4. **Weight Justification**: Highly distinctive personal identifier. Weight = 0.9.\n\n**suburb**\n1. **Inspect Exemplar Candidate Matches**: All three matches show identical suburb values (\"adamstown heights\", \"broken hill\", \"taree\").\n2. **Inspect Statistical Profile**: Low null percentage (1.1% | 2.12%), moderate cardinality (32.68% | 48.06%), average length ~9.3 characters.\n3. **Algorithm Trade-off Evaluation**: Suburb names are short multi-word strings. `jarowinkler` is ideal as it handles typos and minor spelling variations in short strings (e.g., \"adamstown heights\" vs \"adamstown hts\"). `cosine` requires longer text (avg >= 20 chars) and would fail on these short strings. `exact` would be too strict for potential abbreviations.\n4. **Weight Justification**: Strong descriptive location attribute. Weight = 0.7.\n\n**postcode**\n1. **Inspect Exemplar Candidate Matches**: All three matches show identical 4-digit postcode values (\"3133\", \"2870\", \"2477\").\n2. **Inspect Statistical Profile**: 0.0% null, moderate cardinality (28.38% | 33.82%).\n3. **Algorithm Trade-off Evaluation**: As short numeric codes, `damerau_levenshtein` handles single-digit errors (e.g., \"2477\" vs \"2476\") that are common in manually entered postcodes. `exact` would be too strict, while `jarowinkler` is less optimal for pure numeric codes.\n4. **Weight Justification**: Strong location identifier. Weight = 0.6.\n\n**state**\n1. **Inspect Exemplar Candidate Matches**: All three matches show identical 2-3 letter state codes (\"sa\", \"vic\", \"qld\").\n2. **Inspect Statistical Profile**: Low null percentage (1.0% | 2.14%), very low cardinality (8 | 50 unique values).\n3. **Algorithm Trade-off Evaluation**: State codes are standardized abbreviations. `exact` is appropriate because any discrepancy (e.g., \"sa\" vs \"wa\") indicates a different state, and fuzzy matching would risk false positives. String similarity algorithms are unnecessary for such highly standardized values.\n4. **Weight Justification**: Low-cardinality supporting geographic context. Weight = 0.2.\n\n**street_number**\n1. **Inspect Exemplar Candidate Matches**: All three matches show identical street_number values (\"8.0\", \"68.0\", \"1.0\").\n2. **Inspect Statistical Profile**: Moderate null percentage (3.16% | 5.74%), low cardinality (9.0% | 8.96%).\n3. **Algorithm Trade-off Evaluation**: Street numbers are numeric values where absolute difference matters. `numeric_linear` (absolute distance) is appropriate because a difference of 1 between street numbers is significant regardless of magnitude (e.g., 8 vs 9 is as different as 100 vs 101). `numeric_relative` would incorrectly treat the latter as a small difference (1%).\n4. **Weight Justification**: Supporting address attribute. Weight = 0.3.\n\n**surname**\n1. **Inspect Exemplar Candidate Matches**: In Match 2, surname is identical (\"stauntonsmith\"). In Matches 1 and 3, surname values are swapped with given_name across sources (\"kempe\" in A appears as surname in A but given_name in B is \"kempe\", while surname in B is \"tylah\" which is given_name in A; similarly for \"wilsonwheeler\" and \"emiily\"). This indicates a field swapping pattern in the data.\n2. **Inspect Statistical Profile**: Low null percentage (0.96% | 2.04%), high cardinality (36.54% | 52.66%), average length ~6.5 characters.\n3. **Algorithm Trade-off Evaluation**: Surname is a short string. `jarowinkler` is optimal for names as it handles typos, phonetic variants, and minor spelling differences (e.g., \"Smith\" vs \"Smyth\"). The field swapping is a data alignment issue that cannot be resolved by the comparison algorithm itself; `jarowinkler` will still match when the values align correctly.\n4. **Weight Justification**: Core identity attribute, but reliability is reduced due to observed field swapping. Weight = 0.5.\n\n**given_name**\n1. **Inspect Exemplar Candidate Matches**: In Match 2, given_name is empty in both sources. In Matches 1 and 3, given_name values are swapped with surname across sources (\"tylah\" in A appears as given_name in A but surname in B is \"tylah\", while given_name in B is \"kempe\" which is surname in A; similarly for \"emiily\" and \"wilsonwheeler\").\n2. **Inspect Statistical Profile**: Moderate null percentage (2.24% | 4.68%), moderate cardinality (15.38% | 34.04%), average length ~5.9 characters.\n3. **Algorithm Trade-off Evaluation**: Given name is a short string. `jarowinkler` is optimal for the same reasons as surname, handling typos and minor variations in short names.\n4. **Weight Justification**: Core identity attribute, but reliability is reduced due to observed field swapping. Weight = 0.5.\n\n**address_1**\n1. **Inspect Exemplar Candidate Matches**: In Matches 1 and 3, address_1 is identical across sources (\"arthur circle\", \"woolcock street\"). In Match 2, address_1 values are swapped with address_2 (\"frome street\" in A appears as address_1 in A but address_2 in B is \"frome street\", while address_1 in B is \"kookaburra village\" which is address_2 in A).\n2. **Inspect Statistical Profile**: Low null percentage (1.96% | 4.4%), high cardinality (47.98% | 70.32%), average length ~14.6 characters.\n3. **Algorithm Trade-off Evaluation**: Address_1 values are short to medium-length strings. `jarowinkler` handles potential typos or minor variations in street names (e.g., \"woolcock street\" vs \"woolcock st\"). Despite field swapping in one exemplar, the algorithm will match when values align.\n4. **Weight Justification**: Strong descriptive attribute, but reliability is reduced due to observed field swapping. Weight = 0.5.\n\n**address_2**\n1. **Inspect Exemplar Candidate Matches**: In Matches 1 and 3, address_2 is identical across sources (\"tylden park\", \"willandra\"). In Match 2, address_2 values are swapped with address_1 (\"kookaburra village\" in A appears as address_2 in A but address_1 in B is \"kookaburra village\", while address_2 in B is \"frome street\" which is address_1 in A).\n2. **Inspect Statistical Profile**: Moderate null percentage (8.4% | 17.02%), high cardinality (51.5% | 66.1%), average length ~12 characters.\n3. **Algorithm Trade-off Evaluation**: Similar to address_1, these are short to medium-length strings. `jarowinkler` handles potential typos well.\n4. **Weight Justification**: Strong descriptive attribute, but reliability is reduced due to observed field swapping. Weight = 0.5.",
  "matching_columns": {
    "soc_sec_id": {
      "algorithm": "damerau_levenshtein",
      "weight": 1.0
    },
    "date_of_birth": {
      "algorithm": "date",
      "weight": 0.9
    },
    "suburb": {
      "algorithm": "jarowinkler",
      "weight": 0.7
    },
    "postcode": {
      "algorithm": "damerau_levenshtein",
      "weight": 0.6
    },
    "state": {
      "algorithm": "exact",
      "weight": 0.2
    },
    "street_number": {
      "algorithm": "numeric_linear",
      "weight": 0.3
    },
    "surname": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "given_name": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "address_1": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "address_2": {
      "algorithm": "jarowinkler",
      "weight": 0.5
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

