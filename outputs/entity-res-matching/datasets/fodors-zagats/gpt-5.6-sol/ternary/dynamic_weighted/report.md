# Matching Benchmark: fodors-zagats — Dynamic Weighted

- **Domain**: restaurants
- **Strategy**: Dynamic Weighted
- **Model**: gpt-5.6-sol
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9474 | 0.0000 |
| Recall | 0.9643 | 0.0000 |
| F1 Score | 0.9558 | 0.0000 |
| Execution Time (s) | 0.5764 | 0.0089 |
| Peak Memory (MB) | 1.89 | 0.00 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 8,064 |
| Completion Tokens | 7,023 |
| Total Tokens | 15,087 |
| Estimated Cost (USD) | $0.1496 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 1.0000 | 0.0000 |
| Potential F1 Ceiling | 0.9730 | 0.0000 |
| LLM Workload Ratio | 51.1% | - |
| Unrecoverable Loss | 0.0000 | - |
| Uncertain Purity | 0.1% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 100.00% |
| Consistent Matches | 114 |
| Flaky Matches | 0 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9474 | 0.9643 | 0.9558 | 1.0000 | 0.9730 | 53.1% | 0.1% | 108 | 6 | 4 | 0.5808 | 1.89 | 5068 | $0.0537 |  |
| 2 | SUCCESS | 0.9474 | 0.9643 | 0.9558 | 1.0000 | 0.9730 | 50.0% | 0.1% | 108 | 6 | 4 | 0.5822 | 1.88 | 4963 | $0.0470 |  |
| 3 | SUCCESS | 0.9474 | 0.9643 | 0.9558 | 1.0000 | 0.9730 | 50.0% | 0.1% | 108 | 6 | 4 | 0.5661 | 1.89 | 5056 | $0.0489 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.3989 | 0.7278 | [0.3325, 0.4653, 0.9027] |
| 2 | dynamic_skew | 0.3941 | 0.7251 | [0.3284, 0.4598, 0.9020] |
| 3 | dynamic_skew | 0.3941 | 0.7251 | [0.3284, 0.4598, 0.9020] |

## LLM Strategy Configuration & Prompts

- **Model**: `gpt-5.6-sol`
- **Provider**: `openai`
- **Latency**: `36.26s`
- **Log File**: `outputs/logs/llm_calls/20260919_164317_606003_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "Mandatory 4-Step Column Reasoning Protocol\n\nid\n1. Inspect Exemplar Candidate Matches: The values differ for known matches (for example, \"536\" \u2194 \"221\", \"542\" \u2194 \"227\", and \"632\" \u2194 \"317\"), showing that this is a source-local key rather than a shared entity attribute.\n2. Inspect Statistical Profile: Nulls are 0% in both sources, and cardinality/uniqueness is effectively one value per row (533/533 and 331/331). Although it passes the null and variance checks, its source-specific uniqueness triggers the explicit internal-key exclusion rule.\n3. Algorithm Trade-off Evaluation: No comparison algorithm is appropriate. Exact or edit-distance comparison would incorrectly reject true matches because corresponding entities deliberately have different IDs; fuzzy similarity between unrelated sequential numbers would also create spurious evidence.\n4. Weight Justification: Excluded and assigned no weight because it is a source-specific system identifier, not entity evidence.\n\nname\n1. Inspect Exemplar Candidate Matches: Names are usually identical (\"granita\" \u2194 \"granita\" and \"campton place\" \u2194 \"campton place\"), but one match reverses token order (\"hotel belair\" \u2194 \"belair hotel\"). Thus, names are strong identity-bearing descriptions with occasional ordering variation.\n2. Inspect Statistical Profile: Nulls are 0% in both sources, cardinality is high (528 and 331), uniqueness is 99.06% and 100%, and average lengths are short at 12.05 and 13.67 characters. The column passes all exclusion rules and is highly discriminative.\n3. Algorithm Trade-off Evaluation: jarowinkler is selected because these are short restaurant names, including a single-word example, and character-level tolerance is needed for likely spelling variants, truncations, or minor typos. Word-level cosine would handle the observed token reversal better, but average strings are below 20 characters and a one-character typo in a single-word name such as \"granita\" could collapse token similarity to zero. Damerau-Levenshtein is less suitable because token reordering causes a large positional edit penalty. Jarowinkler's weakness on the observed word-order reversal is offset by stronger address and phone evidence.\n4. Weight Justification: Weight 0.70 because the name is a primary descriptive identity attribute with near-total uniqueness, but it is not as format-stable as phone and can vary in word order.\n\naddr\n1. Inspect Exemplar Candidate Matches: All three exemplar addresses are exactly aligned, including house number and street abbreviation: \"701 stone canyon rd\", \"23725 w malibu rd\", and \"340 stockton st\". The samples indicate stable tokenized postal text, while real address data can still differ by token ordering, omitted directional terms, or added components.\n2. Inspect Statistical Profile: Nulls are 0% in both sources, cardinalities are 519 and 322, uniqueness is 97.37% and 97.28%, and average lengths are 21.57 and 15.79. It passes all exclusions and is highly discriminative.\n3. Algorithm Trade-off Evaluation: cosine is selected because addresses are multi-token text and token overlap should remain useful if components are reordered, added, or omitted. Exact matching would be too brittle to formatting differences. Jarowinkler and Damerau-Levenshtein preserve character order and can over-penalize reordered address components. Cosine's weakness is that sub-word differences such as \"road\" versus \"rd\" or a typo in a street name receive no partial token credit; however, the exemplars show consistent abbreviations and exact street tokens, making token similarity empirically appropriate here.\n4. Weight Justification: Weight 0.70 because a nearly unique street address is a strong descriptive locator and can disambiguate names, though it is somewhat less direct than a phone number and may be shared or reformatted.\n\ncity\n1. Inspect Exemplar Candidate Matches: City values are exactly equal in every exemplar: \"bel air\", \"malibu\", and \"san francisco\". No taxonomy or spelling divergence is observed.\n2. Inspect Statistical Profile: Nulls are 0% in both sources, cardinality is only 16 and 46, uniqueness is 3.0% and 13.9%, and average lengths are 9.34 and 10.2. It passes exclusion rules but has low discriminative power because many restaurants share a city.\n3. Algorithm Trade-off Evaluation: jarowinkler is selected because city names are short strings and character-level matching can tolerate minor misspellings or suffix variation. Cosine is unsuitable for these sub-20-character values and would fail completely on a typo in a single-token city. Exact would be unnecessarily brittle, while Damerau-Levenshtein is possible but less naturally suited than prefix-aware Jaro-Winkler for short place names.\n4. Weight Justification: Weight 0.30 because city is auxiliary geographic context: useful for confirming or rejecting a candidate but far too non-unique to establish identity.\n\nphone\n1. Inspect Exemplar Candidate Matches: Phone numbers are exactly identical for all exemplars, such as \"3104721211\" \u2194 \"3104721211\". The representation is consistently a compact 10-digit string without punctuation in the shown pairs.\n2. Inspect Statistical Profile: Nulls are 0% in both sources, cardinalities are 528 and 329, uniqueness is 99.06% and 99.4%, and average lengths are approximately 10 characters. It passes all exclusions and is the strongest observed core identifier.\n3. Algorithm Trade-off Evaluation: damerau_levenshtein is selected because phone numbers are short positional digit sequences, and edit distance can retain partial similarity for a single mistyped or transposed digit while strongly penalizing larger discrepancies. Cosine is invalid for a short digit code, and Jaro-Winkler's prefix boost could over-reward different phones sharing an area code. Exact would fit the exemplars but would discard all evidence after a single transcription or formatting error, so edit distance is safer.\n4. Weight Justification: Weight 0.95 because phone is a core identity attribute, is almost fully unique, and is perfectly aligned in the exemplars.\n\ntype\n1. Inspect Exemplar Candidate Matches: Two examples match exactly as \"californian\" \u2194 \"californian\", while one exhibits a taxonomy refinement: \"american\" \u2194 \"american new\". This indicates that one source may use broader labels and the other more specific labels.\n2. Inspect Statistical Profile: Nulls are 0% in both sources, cardinalities are 40 and 58, uniqueness is 7.5% and 17.52%, and average lengths are short at 8.46 and 9.21. It passes exclusions but is neither unique nor fully taxonomy-consistent.\n3. Algorithm Trade-off Evaluation: jarowinkler is selected because values are short labels and it provides useful partial similarity when one label extends another, as in \"american\" versus \"american new\", while tolerating spelling variants. Exact would wrongly score that observed match as completely different. Cosine is unreliable for such short labels and divergent taxonomies, although it could recognize the shared token in this one example. Damerau-Levenshtein would penalize the appended subtype more heavily because of the length mismatch.\n4. Weight Justification: Weight 0.20 because cuisine type is weak auxiliary context shared by many entities and can diverge across taxonomies; it should confirm stronger evidence rather than drive a match.\n\nclass\n1. Inspect Exemplar Candidate Matches: Values align exactly for known matches (\"2\" \u2194 \"2\", \"8\" \u2194 \"8\", and \"98\" \u2194 \"98\"). Combined with one unique value per row, this pattern strongly suggests a cross-source class, cluster, or gold-standard entity label rather than an observable restaurant characteristic.\n2. Inspect Statistical Profile: Nulls are 0% in both sources and cardinality/uniqueness is effectively 100% (533 and 331 distinct values). It passes the mechanical null and variance checks, but its system-label semantics and row-level uniqueness make it identifier leakage.\n3. Algorithm Trade-off Evaluation: Exact would trivially identify the exemplars, but using it would leak a preassigned class/entity key into scoring rather than compare business attributes. Numeric algorithms would also be semantically invalid because numerical distance between class labels has no meaning. Therefore, no algorithm is selected.\n4. Weight Justification: Excluded and assigned no weight because it is an internal/classification identifier, not legitimate matching evidence.",
  "matching_columns": {
    "name": {
      "algorithm": "jarowinkler",
      "weight": 0.7
    },
    "addr": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "city": {
      "algorithm": "jarowinkler",
      "weight": 0.3
    },
    "phone": {
      "algorithm": "damerau_levenshtein",
      "weight": 0.95
    },
    "type": {
      "algorithm": "jarowinkler",
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
| **Total Rows** | 533 | 331 |
| **Column Count** | 7 | 7 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.96)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "536" | "221" |
| name | "hotel belair" | "belair hotel" |
| addr | "701 stone canyon rd" | "701 stone canyon rd" |
| city | "bel air" | "bel air" |
| phone | "3104721211" | "3104721211" |
| type | "californian" | "californian" |
| class | "2" | "2" |

#### Candidate Match 2 (Overall Text Match Score: 0.95)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "542" | "227" |
| name | "granita" | "granita" |
| addr | "23725 w malibu rd" | "23725 w malibu rd" |
| city | "malibu" | "malibu" |
| phone | "3104560488" | "3104560488" |
| type | "californian" | "californian" |
| class | "8" | "8" |

#### Candidate Match 3 (Overall Text Match Score: 0.95)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| id | "632" | "317" |
| name | "campton place" | "campton place" |
| addr | "340 stockton st" | "340 stockton st" |
| city | "san francisco" | "san francisco" |
| phone | "4159555555" | "4159555555" |
| type | "american" | "american new" |
| class | "98" | "98" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **id** | 0.0% | 0.0% | 100.0% | 100.0% | 533 | 331 | N/A | N/A | "536" ↔ "221" |
| **name** | 0.0% | 0.0% | 99.06% | 100.0% | 528 | 331 | 12.05 | 13.67 | "hotel belair" ↔ "belair hotel" |
| **addr** | 0.0% | 0.0% | 97.37% | 97.28% | 519 | 322 | 21.57 | 15.79 | "701 stone canyon rd" ↔ "701 stone canyon rd" |
| **city** | 0.0% | 0.0% | 3.0% | 13.9% | 16 | 46 | 9.34 | 10.2 | "bel air" ↔ "bel air" |
| **phone** | 0.0% | 0.0% | 99.06% | 99.4% | 528 | 329 | 10.02 | 10.0 | "3104721211" ↔ "3104721211" |
| **type** | 0.0% | 0.0% | 7.5% | 17.52% | 40 | 58 | 8.46 | 9.21 | "californian" ↔ "californian" |
| **class** | 0.0% | 0.0% | 100.0% | 100.0% | 533 | 331 | N/A | N/A | "2" ↔ "2" |
```
</details>

