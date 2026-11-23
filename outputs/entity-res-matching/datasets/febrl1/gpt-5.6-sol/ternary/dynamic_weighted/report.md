# Matching Benchmark: febrl1 — Dynamic Weighted

- **Domain**: synthetic
- **Strategy**: Dynamic Weighted
- **Model**: gpt-5.6-sol
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 1.0000 | 0.0000 |
| Recall | 0.8073 | 0.0410 |
| F1 Score | 0.8930 | 0.0254 |
| Execution Time (s) | 0.2142 | 0.0341 |
| Peak Memory (MB) | 0.82 | 0.07 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 9,468 |
| Completion Tokens | 10,467 |
| Total Tokens | 19,935 |
| Estimated Cost (USD) | $0.2212 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.9987 | 0.0012 |
| Potential F1 Ceiling | 0.9993 | 0.0006 |
| LLM Workload Ratio | 5.9% | - |
| Unrecoverable Loss | 0.0013 | - |
| Uncertain Purity | 100.0% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 88.65% |
| Consistent Matches | 375 |
| Flaky Matches | 48 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 1.0000 | 0.7600 | 0.8636 | 0.9980 | 0.9990 | 7.4% | 100.0% | 380 | 0 | 120 | 0.2534 | 0.90 | 6608 | $0.0775 |  |
| 2 | SUCCESS | 1.0000 | 0.8320 | 0.9083 | 0.9980 | 0.9990 | 5.2% | 100.0% | 416 | 0 | 84 | 0.1920 | 0.79 | 6860 | $0.0758 |  |
| 3 | SUCCESS | 1.0000 | 0.8300 | 0.9071 | 1.0000 | 1.0000 | 5.3% | 100.0% | 415 | 0 | 85 | 0.1971 | 0.76 | 6467 | $0.0679 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.5646 | 0.8870 | [0.3489, 0.7803, 0.9582] |
| 2 | dynamic_skew | 0.4783 | 0.8506 | [0.2703, 0.6863, 0.9601] |
| 3 | dynamic_skew | 0.4713 | 0.8491 | [0.2568, 0.6857, 0.9580] |

## LLM Strategy Configuration & Prompts

- **Model**: `gpt-5.6-sol`
- **Provider**: `openai`
- **Latency**: `49.30s`
- **Log File**: `outputs/logs/llm_calls/20260919_161952_130864_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "1. rec_id\n1. Inspect Exemplar Candidate Matches: The values encode source/record provenance rather than shared entity identity: for example, \"rec177org\" maps to \"rec177dup0\", with the suffix changing systematically across sources.\n2. Inspect Statistical Profile: It has 0% nulls, 500/500 cardinality, 100% uniqueness, and average lengths 8.78/9.78. Although statistically complete and discriminative, it is explicitly a source-specific internal key.\n3. Algorithm Trade-off Evaluation: No comparison algorithm is appropriate. Exact would reject true matches because the source-specific suffix differs; character similarity would merely exploit record-generation conventions and create leakage rather than measure real-world identity.\n4. Weight Justification: Excluded and assigned no weight because internal IDs must not participate in entity matching.\n\n2. given_name\n1. Inspect Exemplar Candidate Matches: One pair agrees (\"lara\" \u2194 \"lara\"), but two pairs show given name and surname transposed (\"thomas\" \u2194 \"guthridge\" and \"dante\" \u2194 \"davilasanhdars\"). Thus the field contains useful name evidence but has substantial cross-field placement instability.\n2. Inspect Statistical Profile: Nulls are low at 3.0%/5.8%; cardinalities are 259/320, both greater than 1; average lengths are short at 5.92/5.97. It passes the formal inclusion rules.\n3. Algorithm Trade-off Evaluation: Jaro-Winkler is best for short personal names and can tolerate minor spelling errors, truncations, and phonetic variants. Word-level cosine is unsuitable for these sub-20-character, usually single-token values and would collapse to zero for one-character typos. Damerau-Levenshtein could handle edits but penalizes length variation more strongly; exact is too brittle. No same-column algorithm can solve the observed given-name/surname swaps, so this signal must be moderated and supported by stronger identifiers.\n4. Weight Justification: Weight 0.50, at the low end for a primary descriptive name attribute, because names are identifying but the exemplars reveal frequent column transposition.\n\n3. surname\n1. Inspect Exemplar Candidate Matches: One pair agrees (\"matthews\" \u2194 \"matthews\"), while two pairs contain reciprocal surname/given-name swaps (\"guthridge\" \u2194 \"thomas\" and \"davilasanhdars\" \u2194 \"dante\").\n2. Inspect Statistical Profile: Nulls are only 1.2%/2.4%; cardinalities are 340/387; average lengths are 6.57/6.57. It has good coverage and useful variance.\n3. Algorithm Trade-off Evaluation: Jaro-Winkler fits short surnames and is robust to minor character errors and suffix differences. Cosine is inappropriate for short single-token names and has no sub-word typo tolerance. Exact would miss spelling variants, while Damerau-Levenshtein is less forgiving of unequal-length variants. The algorithm cannot recover cross-column swaps, so surname cannot dominate scoring.\n4. Weight Justification: Weight 0.50 as a primary descriptive identity signal, reduced to the bottom of the normal name range because two of three exemplars are transposed.\n\n4. street_number\n1. Inspect Exemplar Candidate Matches: All three pairs agree exactly, including the decimal-style representation: \"6.0\" \u2194 \"6.0\" and \"303.0\" \u2194 \"303.0\".\n2. Inspect Statistical Profile: Nulls are low at 2.8%/6.2%; cardinalities are 146/141, so the column has variance but considerable reuse. Average length is unavailable. It passes the exclusion rules.\n3. Algorithm Trade-off Evaluation: Exact is preferred because a house number is a discrete address component and the exemplars show consistent formatting. Numeric-relative would incorrectly make nearby but different house numbers appear similar; numeric-linear would likewise reward an absolute difference of one even though neighboring properties may be different entities. Damerau-Levenshtein is unnecessary given the numeric normalization observed.\n4. Weight Justification: Weight 0.25 as auxiliary address context: useful with street and postcode, but weak and non-unique by itself.\n\n5. address_1\n1. Inspect Exemplar Candidate Matches: Two pairs agree exactly (for example, \"brunswick circuit\" \u2194 \"brunswick circuit\"), but Candidate 2 shows address-line transposition: Source A address_1 \"beaumaris street\" appears in Source B address_2, while Source B address_1 contains the organization/location text from Source A address_2.\n2. Inspect Statistical Profile: Nulls are low at 1.4%/3.6%; cardinalities are high at 445/469; average lengths are 14.45/14.47, below the recommended range for cosine. It is highly discriminative and passes inclusion rules.\n3. Algorithm Trade-off Evaluation: Jaro-Winkler is selected because these are short address phrases and it can tolerate minor character-level spelling, spacing, or suffix variation. Cosine is not preferred because the average is under 20 characters and token-level comparison has no tolerance for sub-word typos or hyphenation. Damerau-Levenshtein is less suitable for phrase-length variation, while exact is too brittle. Jaro-Winkler cannot fix address_1/address_2 swaps, so the paired address-line signals must not overpower core identifiers.\n4. Weight Justification: Weight 0.50 as a strong descriptive address attribute, held at the low end because address-line placement is inconsistent in the exemplars.\n\n6. address_2\n1. Inspect Exemplar Candidate Matches: Candidates 1 and 3 agree exactly (\"tintagel\" and \"surama\" respectively), while Candidate 2 swaps \"sunforest therapy centre\" and \"beaumaris street\" between address_1 and address_2.\n2. Inspect Statistical Profile: Nulls are 7.4%/15.6%, safely below 50%; cardinalities are 411/401; average lengths are 11.87/12.09. It has good coverage and high variance.\n3. Algorithm Trade-off Evaluation: Jaro-Winkler is appropriate for short labels and address phrases and tolerates minor typos better than exact. Cosine is risky at these short average lengths and would fail on altered single tokens; Damerau-Levenshtein can over-penalize additions and length differences. As with address_1, no same-column comparator handles line swaps, so its influence is limited.\n4. Weight Justification: Weight 0.50 as descriptive address evidence. It is useful and high-cardinality, but line swapping and somewhat higher null rates prevent a stronger weight.\n\n7. suburb\n1. Inspect Exemplar Candidate Matches: Every exemplar agrees exactly, including repeated multi-word values such as \"avondale heights\" \u2194 \"avondale heights\" and \"the basin\" \u2194 \"the basin\".\n2. Inspect Statistical Profile: Nulls are low at 1.2%/2.4%; cardinalities are 390/427; average lengths are short at 9.45/9.57. It passes all exclusion criteria and is fairly discriminative.\n3. Algorithm Trade-off Evaluation: Jaro-Winkler is selected for short city/suburb names and can absorb spelling variants or small typographical errors. Cosine is unsuitable at this length and can score a typo-altered single token as unrelated. Exact would be unnecessarily brittle, and Damerau-Levenshtein is less suitable for variable-length locality names.\n4. Weight Justification: Weight 0.40 as supporting geographic context. It is strong corroboration but not a core identifier and may be shared by many people.\n\n8. postcode\n1. Inspect Exemplar Candidate Matches: All three pairs have exact four-digit agreement: \"2073\", \"4179\", and \"2029\" respectively.\n2. Inspect Statistical Profile: It has 0% nulls in both sources, cardinalities of 389/409, and substantial but not unique discrimination. Average length is unavailable, but the exemplars show standardized codes.\n3. Algorithm Trade-off Evaluation: Exact is preferred because postcode is a standardized discrete geographic code and observed formatting is consistent. Damerau-Levenshtein would grant partial credit to a mistyped code that may denote a different area; numeric-relative and numeric-linear are semantically invalid because numerical proximity does not imply geographic proximity.\n4. Weight Justification: Weight 0.40 as supporting geographic context: highly complete and useful in combination with address fields, but not a person-level identifier.\n\n9. state\n1. Inspect Exemplar Candidate Matches: State agrees exactly in all exemplars (\"vic\", \"nsw\", and \"wa\"). No abbreviation mismatch is observed.\n2. Inspect Statistical Profile: Nulls are low at 1.2%/1.8%; cardinalities are only 8/17 but exceed 1; average lengths are 2.84/2.84. The low cardinality makes it weakly discriminative, although it is not formally excluded.\n3. Algorithm Trade-off Evaluation: Exact is appropriate for standardized short state codes because the exemplars show consistent representation. Jaro-Winkler or Damerau-Levenshtein would undesirably award similarity to distinct short codes, while cosine is especially unsuitable for very short tokens.\n4. Weight Justification: Weight 0.10 as a weak contextual signal due to very low cardinality; it can confirm an address but should contribute little by itself.\n\n10. date_of_birth\n1. Inspect Exemplar Candidate Matches: All exemplars agree exactly on full birth dates, represented as YYYYMMDD with a trailing decimal marker, such as \"19080625.0\" \u2194 \"19080625.0\".\n2. Inspect Statistical Profile: Nulls are low at 2.6%/5.6%; cardinalities are very high at 483/469; the field has excellent discriminatory power and passes all exclusion rules.\n3. Algorithm Trade-off Evaluation: The date comparator is selected because this is a full calendar date and date-aware hierarchical similarity is appropriate if small day/month/year discrepancies occur outside the exemplars. Numeric-relative is nonsensical for calendar values; numeric-linear treats the encoded YYYYMMDD number as a uniform quantity and produces invalid distances across month/year boundaries. Exact is defensible for the displayed samples but would be overly brittle to common date-entry shifts.\n4. Weight Justification: Weight 0.80 because date of birth is a strong identity attribute with high cardinality and coverage, though it is not globally unique on its own.\n\n11. soc_sec_id\n1. Inspect Exemplar Candidate Matches: Every exemplar has exact agreement, including \"4255165\", \"2164704\", and \"2609420\". No punctuation, spacing, or formatting variation is observed.\n2. Inspect Statistical Profile: It has 0% nulls, 500/500 cardinality, and 100% uniqueness in both sources, making it the strongest available real-world identifier.\n3. Algorithm Trade-off Evaluation: Exact is chosen because the field is a standardized social-security identifier and the empirical evidence shows exact cross-source preservation. Damerau-Levenshtein could tolerate a digit edit or transposition, but that would risk treating two genuinely different identifiers as similar. Numeric algorithms are semantically inappropriate because numeric distance between identifiers has no meaning, and cosine is inappropriate for a short code.\n4. Weight Justification: Weight 1.00 as the highest-confidence core identity attribute: complete, unique, and exactly aligned in all exemplars.",
  "matching_columns": {
    "given_name": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "surname": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "street_number": {
      "algorithm": "exact",
      "weight": 0.25
    },
    "address_1": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "address_2": {
      "algorithm": "jarowinkler",
      "weight": 0.5
    },
    "suburb": {
      "algorithm": "jarowinkler",
      "weight": 0.4
    },
    "postcode": {
      "algorithm": "exact",
      "weight": 0.4
    },
    "state": {
      "algorithm": "exact",
      "weight": 0.1
    },
    "date_of_birth": {
      "algorithm": "date",
      "weight": 0.8
    },
    "soc_sec_id": {
      "algorithm": "exact",
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

