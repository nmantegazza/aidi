# Matching Benchmark: febrl4 — Dynamic Weighted

- **Domain**: synthetic
- **Strategy**: Dynamic Weighted
- **Model**: gpt-5.6-sol
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 1.0000 | 0.0000 |
| Recall | 0.9764 | 0.0040 |
| F1 Score | 0.9881 | 0.0020 |
| Execution Time (s) | 8.4962 | 0.8744 |
| Peak Memory (MB) | 31.90 | 0.96 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 9,519 |
| Completion Tokens | 10,276 |
| Total Tokens | 19,795 |
| Estimated Cost (USD) | $0.2174 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 1.0000 | 0.0000 |
| Potential F1 Ceiling | 1.0000 | 0.0000 |
| LLM Workload Ratio | 41.6% | - |
| Unrecoverable Loss | 0.0000 | - |
| Uncertain Purity | 0.3% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 98.74% |
| Consistent Matches | 4857 |
| Flaky Matches | 62 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.9804 | 0.9901 | 1.0000 | 1.0000 | 43.3% | 0.2% | 4902 | 0 | 98 | 7.9739 | 32.45 | 6348 | $0.0720 |  |
| 2 | SUCCESS | 1.0000 | 0.9724 | 0.9860 | 1.0000 | 1.0000 | 40.2% | 0.3% | 4862 | 0 | 138 | 8.0091 | 32.45 | 6626 | $0.0708 |  |
| 3 | SUCCESS | 1.0000 | 0.9764 | 0.9881 | 1.0000 | 1.0000 | 41.4% | 0.3% | 4882 | 0 | 118 | 9.5057 | 30.79 | 6821 | $0.0747 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.3292 | 0.7163 | [0.2824, 0.3761, 0.9432] |
| 2 | dynamic_skew | 0.3251 | 0.7160 | [0.2782, 0.3721, 0.9453] |
| 3 | dynamic_skew | 0.3385 | 0.7282 | [0.2917, 0.3853, 0.9568] |

## LLM Strategy Configuration & Prompts

- **Model**: `gpt-5.6-sol`
- **Provider**: `openai`
- **Latency**: `39.04s`
- **Log File**: `outputs/logs/llm_calls/20260919_163048_765669_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "rec_id\n1. Inspect Exemplar Candidate Matches: Values differ systematically by source-specific suffix, e.g. \"rec1409org\" versus \"rec1409dup0\", even though the rows represent the same entity.\n2. Inspect Statistical Profile: Nulls are 0% in both sources, cardinality is 5,000 in both, uniqueness is 100%, and average lengths are 9.78/10.78. Although statistically complete and unique, it is an internal source-specific record key.\n3. Algorithm Trade-off Evaluation: Exclude it. Exact would reject true matches, while character algorithms could spuriously exploit the shared embedded row number and source-generated naming convention. No comparison algorithm makes this a valid real-world identity feature.\n4. Weight Justification: No weight is assigned because system/internal identifiers must not participate in entity scoring.\n\ngiven_name\n1. Inspect Exemplar Candidate Matches: Candidate 1 has \"tylah\" versus \"kempe\" and Candidate 3 has \"emiily\" versus \"wilsonwheeler\" because given name and surname are transposed across fields; Candidate 2 is null on both sides. Thus same-column comparison fails for the observed true matches.\n2. Inspect Statistical Profile: Nulls are only 2.24%/4.68%, cardinalities are 769/1,702, and average lengths are 5.90/5.93, so neither formal null nor variance exclusions apply.\n3. Algorithm Trade-off Evaluation: Exclude it from this same-column configuration. Jaro-Winkler would normally be best for short typo-prone names and would accommodate a variant such as \"emiily\", but it cannot recover cross-column swaps. Cosine would be especially poor for these short single-token values, exact is too brittle, and Damerau-Levenshtein still compares the wrong attributes. A future derived canonical full-name field would be preferable.\n4. Weight Justification: No weight is assigned despite its identity semantics because the empirical field alignment is unreliable and would penalize high-confidence true matches.\n\nsurname\n1. Inspect Exemplar Candidate Matches: Candidate 1 has \"kempe\" versus \"tylah\" and Candidate 3 has \"wilsonwheeler\" versus \"emiily\", again showing systematic given-name/surname transposition; only Candidate 2 is aligned as \"stauntonsmith\" on both sides.\n2. Inspect Statistical Profile: Nulls are 0.96%/2.04%, cardinalities are 1,827/2,633, and average lengths are 6.54/6.52. It passes the null and variance rules and is potentially discriminative.\n3. Algorithm Trade-off Evaluation: Exclude it from same-column scoring. Jaro-Winkler would otherwise suit short surnames and spelling errors, but no string metric can make \"kempe\" similar to \"tylah\" when the matching value resides in given_name. Cosine is unsuitable for short single-token names, and exact or edit distance would strongly reject the observed swaps.\n4. Weight Justification: No weight is assigned because field transposition makes this otherwise strong descriptive identity attribute unsafe in the available column-wise configuration.\n\nstreet_number\n1. Inspect Exemplar Candidate Matches: All three exemplars have identical values (\"8.0\", \"68.0\", and \"1.0\") with the same decimal-like formatting and no observed unit or representation shift.\n2. Inspect Statistical Profile: Nulls are 3.16%/5.74%, cardinalities are 450/448, and cardinality is well above one. It is complete enough to use, though many entities naturally share a street number.\n3. Algorithm Trade-off Evaluation: Exact is selected because a different house number is materially meaningful and the exemplars show standardized equality. Numeric-linear could make neighboring house numbers seem similar even though they may identify different properties; numeric-relative is particularly inappropriate because relative closeness has no semantic meaning for house numbers. Character metrics add unnecessary fuzziness.\n4. Weight Justification: Weight 0.30 treats it as auxiliary address context: useful in combination with street and locality, but weak and non-unique by itself.\n\naddress_1\n1. Inspect Exemplar Candidate Matches: Candidates 1 and 3 are exact matches, while Candidate 2 shows an address-line swap: \"frome street\" is compared with \"kookaburra village\", with the matching values appearing in address_2 instead. No within-line typo is shown, but line placement is not fully reliable.\n2. Inspect Statistical Profile: Nulls are 1.96%/4.40%, cardinalities are 2,399/3,516, and average lengths are 14.65/14.50. It passes all exclusion rules and has substantial discrimination, but the strings are generally short.\n3. Algorithm Trade-off Evaluation: Jaro-Winkler is selected because these are short address phrases and it can tolerate minor character-level misspellings, abbreviations, or suffix changes. Word-level cosine is risky below 20 characters and would give no partial credit for typo-affected tokens; exact is too brittle. Jaro-Winkler cannot solve the observed line swap, so its influence is moderated and address_2 is also retained.\n4. Weight Justification: Weight 0.55 reflects a primary descriptive address attribute with good cardinality, reduced from a higher value because one exemplar demonstrates cross-line transposition.\n\naddress_2\n1. Inspect Exemplar Candidate Matches: Candidates 1 and 3 match exactly (\"tylden park\" and \"willandra\"), while Candidate 2 contains the reciprocal line swap: \"kookaburra village\" versus \"frome street\".\n2. Inspect Statistical Profile: Nulls are 8.40%/17.02%, below the 50% threshold; cardinalities are 2,575/3,305, and average lengths are 11.76/12.01. The field is variable and usable but less complete than address_1.\n3. Algorithm Trade-off Evaluation: Jaro-Winkler is selected for these short locality/address phrases and possible spelling variants. Cosine is poorly suited to the short values and typo-prone tokens; exact would reject small variations. As with address_1, no same-column string metric handles a full line swap, so the weight must limit that failure mode.\n4. Weight Justification: Weight 0.40 makes this supporting address context rather than a dominant signal because it has higher null rates and observed line-placement instability.\n\nsuburb\n1. Inspect Exemplar Candidate Matches: All exemplars agree exactly: \"adamstown heights\", \"broken hill\", and \"taree\". The values include both single-word and short multi-word place names, with no observed taxonomy divergence.\n2. Inspect Statistical Profile: Nulls are 1.10%/2.12%, cardinalities are 1,634/2,403, and average lengths are 9.31/9.32. It is complete, variable, and reasonably discriminative.\n3. Algorithm Trade-off Evaluation: Jaro-Winkler is selected because suburb names are short and may contain minor spelling variations; it remains effective on single words such as \"taree\". Cosine can collapse to zero for a typo in a short token, while exact would be unnecessarily brittle. Damerau-Levenshtein is possible but less suitable than prefix-weighted name/place matching for varying place-name lengths.\n4. Weight Justification: Weight 0.50 treats suburb as a strong descriptive location attribute, though not a unique entity identifier on its own.\n\npostcode\n1. Inspect Exemplar Candidate Matches: All three pairs match exactly (\"3133\", \"2870\", and \"2477\") and show a stable four-digit representation without punctuation or padding differences.\n2. Inspect Statistical Profile: Nulls are 0% in both sources, cardinalities are 1,419/1,691, and the field has substantial but non-unique variation.\n3. Algorithm Trade-off Evaluation: Exact is selected because this is a standardized discrete geographic code and the exemplars show consistent formatting. Damerau-Levenshtein could tolerate digit errors but risks granting similarity to different nearby-looking postcodes; numeric-linear and numeric-relative are semantically invalid because numerical distance between postal codes does not represent geographic similarity.\n4. Weight Justification: Weight 0.45 makes it strong supporting geographic context: complete and useful for confirmation, but shared by many people and therefore below core identity weight.\n\nstate\n1. Inspect Exemplar Candidate Matches: State matches exactly in every exemplar (\"sa\", \"vic\", and \"qld\") with a consistent abbreviated representation.\n2. Inspect Statistical Profile: Nulls are 1.00%/2.14%, cardinalities are 8/50, average lengths are 2.82/2.82, and neither source has cardinality one. Source B's larger taxonomy suggests possible nonstandard values beyond the exemplars, while overall discrimination remains low.\n3. Algorithm Trade-off Evaluation: Exact is selected because state is a discrete categorical jurisdiction and observed abbreviations are standardized. Jaro-Winkler could misleadingly score distinct short codes as similar, cosine is unsuitable for very short codes, and edit distance would inappropriately soften categorical disagreement.\n4. Weight Justification: Weight 0.15 reflects a weak contextual signal due to very low cardinality and the possibility of taxonomy inconsistency, despite good completeness.\n\ndate_of_birth\n1. Inspect Exemplar Candidate Matches: Every exemplar has an identical YYYYMMDD-like value with a trailing decimal marker, such as \"19721016.0\" in both sources; no day/month shifts are observed.\n2. Inspect Statistical Profile: Nulls are 1.88%/3.98%, cardinalities are 4,588/4,505, and uniqueness is 91.76%/90.10%. It is highly discriminative and passes all exclusion rules.\n3. Algorithm Trade-off Evaluation: Date is selected after normalizing the trailing \".0\" and parsing YYYYMMDD. It respects calendar structure and can provide controlled partial similarity for plausible date discrepancies. Numeric-relative is nonsensical for dates, numeric-linear on the raw integer encoding distorts calendar intervals, and exact would provide no tolerance for common birth-date transcription errors.\n4. Weight Justification: Weight 0.40 treats birth date as powerful contextual evidence but keeps it below direct identifiers, consistent with the prescribed contextual range.\n\nsoc_sec_id\n1. Inspect Exemplar Candidate Matches: The identifier is identical in all three pairs (\"1844518\", \"6922783\", and \"8119451\"), with no formatting, padding, or unit variation.\n2. Inspect Statistical Profile: Nulls are 0% in both sources, cardinalities are 5,000/5,000, and uniqueness is 100% in each source. Unlike rec_id, this is a real-world identity attribute rather than a source-generated record key.\n3. Algorithm Trade-off Evaluation: Damerau-Levenshtein is selected because social-security-style identifiers are digit strings for which a single transcription error or adjacent digit swap should receive limited partial credit. Exact would be safer against false positives and is supported by the exemplars, but it would entirely discard near-matches caused by one digit error; Jaro-Winkler's prefix boost is undesirable for identifiers, and numeric algorithms would wrongly interpret the code as a quantity.\n4. Weight Justification: Weight 1.00 reflects a complete, unique, core identity attribute and makes it the most decisive signal, while the aggregate should still require corroboration when it is only approximately similar.",
  "matching_columns": {
    "street_number": {
      "algorithm": "exact",
      "weight": 0.3
    },
    "address_1": {
      "algorithm": "jarowinkler",
      "weight": 0.55
    },
    "address_2": {
      "algorithm": "jarowinkler",
      "weight": 0.4
    },
    "suburb": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "postcode": {
      "algorithm": "exact",
      "weight": 0.45
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
      "weight": 1.0
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

