# Matching Benchmark: amazon-walmart — Dynamic Weighted

- **Domain**: e-commerce
- **Strategy**: Dynamic Weighted
- **Model**: mistral-medium-latest
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.7225 | 0.0145 |
| Recall | 0.4027 | 0.0966 |
| F1 Score | 0.5117 | 0.0769 |
| Execution Time (s) | 31.1840 | 5.5195 |
| Peak Memory (MB) | 284.17 | 8.10 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 17,232 |
| Completion Tokens | 26,775 |
| Total Tokens | 44,007 |
| Estimated Cost (USD) | $0.2174 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.8790 | 0.0135 |
| Potential F1 Ceiling | 0.7929 | 0.0033 |
| LLM Workload Ratio | 3.4% | - |
| Unrecoverable Loss | 0.1210 | - |
| Uncertain Purity | 4.9% | - |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.7385 | 0.3059 | 0.4326 | 0.8648 | 0.7967 | 2.0% | 8.1% | 353 | 125 | 801 | 25.0561 | 275.04 | 6969 | $0.0093 |  |
| 2 | SUCCESS | 0.7187 | 0.4029 | 0.5164 | 0.8804 | 0.7914 | 3.6% | 3.9% | 465 | 182 | 689 | 35.7651 | 290.50 | 20222 | $0.1168 |  |
| 3 | SUCCESS | 0.7102 | 0.4991 | 0.5863 | 0.8917 | 0.7907 | 4.5% | 2.5% | 576 | 235 | 578 | 32.7307 | 286.97 | 16816 | $0.0913 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dispersion_boost | 0.5331 | 0.7546 | [0.2601, 0.3582, 0.5331] |

## LLM Strategy Configuration & Prompts

- **Model**: `mistral-medium-latest`
- **Provider**: `mistral`
- **Latency**: `79.87s`
- **Log File**: `outputs/logs/llm_calls/20260919_161431_777416_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "\n## Column-by-Column Reasoning (Mandatory 4-Step Protocol)\n\n### 1. brand\n1. **Inspect Exemplar Candidate Matches**: All three high-confidence matches show \"dalite\" \u2194 \"dalite\" \u2014 exact character-for-character identity with no typos, abbreviations, or formatting variations.\n2. **Inspect Statistical Profile**: Null % (0.01%|5.21%) < 50%, cardinality (1896|463) > 1, avg length (7.29|7.34) \u2014 short, low-null, high-cardinality identity field.\n3. **Algorithm Trade-off Evaluation**: As a short, single-word brand name, `jarowinkler` is optimal because it excels at short strings and handles minor typos robustly (though none are observed here). `exact` would be brittle to any future typo, `cosine` fails on sub-20-char strings, and `damerau_levenshtein` is overkill for non-code identifiers. `jarowinkler` best balances precision and resilience.\n4. **Weight Justification**: Core identity attribute (manufacturer name directly identifies the entity) \u2192 **0.9**.\n\n---\n\n### 2. modelno\n1. **Inspect Exemplar Candidate Matches**: \n   - Match 1: `\"\"` \u2194 `\"27651\"` (null in A)\n   - Match 2: `\"23050\"` \u2194 `\"23046\"` (single-digit suffix difference)\n   - Match 3: `\"23181\"` \u2194 `\"23096\"` (multi-digit internal variance)\n   Shows alphanumeric codes with minor character-level edits (likely model variants or transcription errors).\n2. **Inspect Statistical Profile**: Null % (28.54%|6.42%) < 50%, cardinality (15505|2389) > 1, avg length (8.52|7.55) \u2014 short, sparse, high-cardinality code field.\n3. **Algorithm Trade-off Evaluation**: As a short alphanumeric code, `damerau_levenshtein` is ideal because it explicitly accounts for transpositions (e.g., \"23050\" vs \"23046\") and single-character edits, which are empirically observed. `jarowinkler` is less precise for codes; `exact` fails on all observed matches; `cosine` fails on short, non-dictionary tokens.\n4. **Weight Justification**: Strong identity attribute (model number is a primary product identifier) \u2192 **0.8**.\n\n---\n\n### 3. title\n1. **Inspect Exemplar Candidate Matches**:\n   - Match 1: `\"dalite 27651 daglas deluxe rear projection screen 96 x 96 av format\"` \u2194 `\"dalite daglas deluxe rear projection screen 96 x 96 av format\"` (extra model code prefix in A)\n   - Match 2: `\"dalite daglas thruthewall rear projection screen 72 x 96 video format\"` \u2194 `\"dalite daview thruthewall rear projection screen 60 x 80 video format\"` (brand variant \"daglas\" vs \"daview\", dimension variance)\n   - Match 3: Similar pattern with model descriptor variance (\"data pro\" vs \"daplex\")\n   Shows **multi-word free text** with token additions/omissions (e.g., model codes) and minor word-level substitutions (e.g., \"daglas\" vs \"daview\").\n2. **Inspect Statistical Profile**: Null % (0.0%|0.0%), cardinality (21888|2539) > 1, avg length (67.6|53.38) \u2014 long, non-null, high-cardinality descriptive field.\n3. **Algorithm Trade-off Evaluation**: Long, multi-word text where **word order may shift slightly** and **individual tokens may be added/omitted**. `cosine` (TF-IDF) is order-invariant and resilient to these exact variations. `jarowinkler` fails on long strings; `damerau_levenshtein` fails on multi-word reordering; `exact` fails on all observed matches. The shared dictionary words (e.g., \"dalite\", \"rear\", \"projection\") ensure `cosine` captures semantic similarity despite minor variations.\n4. **Weight Justification**: Primary descriptive attribute (title is the human-readable product identifier) \u2192 **0.7**.\n\n---\n\n### 4. long_description\n1. **Inspect Exemplar Candidate Matches**: All three matches show **near-identical long-form text** (avg ~400\u20131000 chars) with only minor prefix variations (e.g., model codes like \"27651\" or \"dl8302\") and consistent core content. The textual overlap is extensive despite these small differences.\n2. **Inspect Statistical Profile**: Null % (0.83%|1.33%) < 50%, cardinality (19751|2474) > 1, avg length (995.47|397.85) \u2014 very long, low-null, high-cardinality free text.\n3. **Algorithm Trade-off Evaluation**: Extremely long multi-word text where minor token differences (prefixes) should not dominate. `cosine` is the only algorithm designed for this: it treats text as a bag-of-words, making it invariant to word order and resilient to minor additions/omissions. All other algorithms fail on this length/scale.\n4. **Weight Justification**: Strong descriptive attribute (detailed product description) \u2192 **0.6**.\n\n---\n\n### 5. features\n1. **Inspect Exemplar Candidate Matches**: \n   - Match 1: `\"\"` \u2194 full description (null in A)\n   - Match 2: `\"model 23050\"` \u2194 full description starting with \"the dalite thruthewall...\"\n   - Match 3: `\"model 23181\"` \u2194 similar full description\n   Shows **asymmetric content**: Source A often has a brief model reference, while Source B has a full descriptive paragraph. However, the *semantic content* is aligned (both describe the same product features).\n2. **Inspect Statistical Profile**: Null % (17.26%|4.7%) < 50%, cardinality (15247|2206) > 1, avg length (259.25|228.08) \u2014 long, moderately sparse, high-cardinality text.\n3. **Algorithm Trade-off Evaluation**: Long multi-word text (avg >200 chars) where the *presence of shared dictionary terms* (e.g., \"dalite\", \"rear projection\", \"module\") indicates semantic similarity despite length/asymmetry. `cosine` captures this word-level overlap. String-based algorithms (`jarowinkler`, `damerau_levenshtein`) fail on long text; `exact` fails on all observed matches.\n4. **Weight Justification**: Auxiliary descriptive attribute (supplemental to title/long_description) \u2192 **0.4**.\n\n---\n\n### 6. category\n1. **Inspect Exemplar Candidate Matches**:\n   - Match 1: `\"projection screens office electronics accessories\"` \u2194 `\"electronics general\"`\n   - Match 2: `\"projection screens televisions video\"` \u2194 `\"electronics general\"`\n   - Match 3: `\"projection screens televisions video\"` \u2194 `\"electronics general\"`\n   Shows **divergent taxonomies**: Source A uses fine-grained, multi-word categories; Source B uses a coarse \"electronics general\" label. However, **shared dictionary word \"electronics\"** exists in all pairs.\n2. **Inspect Statistical Profile**: Null % (5.57%|0.0%) < 50%, cardinality (1490|63) > 1, avg length (39.53|17.15) \u2014 multi-word, low-null, moderate-cardinality.\n3. **Algorithm Trade-off Evaluation**: Multi-word text where **partial word overlap** (e.g., \"electronics\") provides signal. `cosine` can detect this shared vocabulary despite taxonomy divergence. `exact` fails on all matches; `jarowinkler` is suboptimal for multi-word; `damerau_levenshtein` fails on length. The limitation of `cosine` (\"fails on divergent taxonomies\") is *mitigated here* because the vocabularies still share critical terms.\n4. **Weight Justification**: Weak descriptive attribute (noisy, taxonomy-dependent) \u2192 **0.3**.\n\n---\n\n### 7. price\n1. **Inspect Exemplar Candidate Matches**:\n   - Match 1: `\"\"` \u2194 `\"6128.99\"` (null in A)\n   - Match 2: `\"8968.99\"` \u2194 `\"13997.99\"` (66% relative difference)\n   - Match 3: `\"15985.81\"` \u2194 `\"10048.99\"` (37% relative difference)\n   Shows **monetary amounts** that can vary significantly across retailers, but the *relative gap* is meaningful for comparison.\n2. **Inspect Statistical Profile**: Null % (12.96%|0.0%) < 50%, cardinality (7491|1398) > 1 \u2014 numeric field spanning orders of magnitude (tens to tens of thousands).\n3. **Algorithm Trade-off Evaluation**: Monetary values where **absolute difference is misleading** (e.g., $10 is trivial for $10,000 but huge for $10). `numeric_relative` (percentage difference) is scale-invariant and aligns with how price variance affects entity resolution. `numeric_linear` would distort comparisons across magnitude ranges.\n4. **Weight Justification**: Contextual attribute (supporting evidence, not identity) \u2192 **0.3**.\n\n---\n\n### 8. shipweight\n1. **Inspect Exemplar Candidate Matches**:\n   - Match 1: `\"1 065 pounds\"` \u2194 `\"1065.0\"` (same value, **format divergence**: space as thousands separator + \"pounds\" suffix in A vs. decimal in B)\n   - Match 2: `\"1 340 pounds\"` \u2194 `\"809.0\"` (value difference, but format issue persists)\n   - Match 3: `\"1 000 pounds\"` \u2194 `\"1206.0\"` (value difference)\n   Shows **physical measurements** with **unit/syntax inconsistency** between sources.\n2. **Inspect Statistical Profile**: Null % (2.04%|7.28%) < 50%, cardinality (590|829) > 1, avg length (8.47) \u2014 short numeric strings representing weights.\n3. **Algorithm Trade-off Evaluation**: Represents a **physical dimension** (weight) where the *underlying numeric value* is the signal, but raw strings differ in formatting. `numeric_relative` is appropriate because it compares the parsed numeric values (ignoring \"pounds\" suffix and space formatting), which is the semantically correct approach for measurements. String-based algorithms would fail due to format divergence.\n4. **Weight Justification**: Contextual attribute (secondary physical trait) \u2192 **0.25**.\n\n---\n\n## Excluded Columns\n- **custom_id**: Internal auto-generated key (Step 1b exclusion).\n- **product_id**: Internal auto-generated key (Step 1b exclusion).\n- **short_description**: Null % = 80.13% in Source A > 50% (Step 1b exclusion).\n- **dimensions**: All exemplar matches have null values in *both* sources, providing **zero empirical evidence** of matching behavior. Cannot satisfy Step 1 of the protocol.\n- **imageurl**: Source-specific URLs (Amazon vs. Walmart domains) are **guaranteed to differ** for the same entity. Acts as a system/internal attribute in practice.",
  "matching_columns": {
    "brand": {
      "algorithm": "jarowinkler",
      "weight": 0.9
    },
    "modelno": {
      "algorithm": "damerau_levenshtein",
      "weight": 0.8
    },
    "title": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "long_description": {
      "algorithm": "cosine",
      "weight": 0.6
    },
    "features": {
      "algorithm": "cosine",
      "weight": 0.4
    },
    "category": {
      "algorithm": "cosine",
      "weight": 0.3
    },
    "price": {
      "algorithm": "numeric_relative",
      "weight": 0.3
    },
    "shipweight": {
      "algorithm": "numeric_relative",
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
| **Total Rows** | 22074 | 2554 |
| **Column Count** | 13 | 13 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.91)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| custom_id | "18154" | "1179" |
| product_id | "b001fx1riu" | "15142373" |
| brand | "dalite" | "dalite" |
| modelno | "" | "27651" |
| category | "projection screens office electronics accessories" | "electronics general" |
| title | "dalite 27651 daglas deluxe rear projection screen 96 x 96 av format" | "dalite daglas deluxe rear projection screen 96 x 96 av format" |
| price | "" | "6128.99" |
| features | "" | "dalite offers a wide range of rigid rear projection screen systems for any need ranging from corporate boardrooms to home theaters designed to provide the highest resolution and most accurate color fidelity with dalite rear projection screens viewers can enjoy bright high resolution images without turning the lights off this coating is deposited on a transparent glass daglas or acrylic daplex substrate dalite utilizes a special coating process which chemically bonds the optical layer to the substrate creating a very high degree of adhesion guaranteed not to peel or strip off deluxe frame features impressive architectural design adds sophistication to any installation 13 4 x 3 rectangular base tube dovetail frame eliminates light leakage black anodized finish frame size equals screen viewing area plus 51 2" |
| short_description | "" | "" |
| long_description | "dalite 27651 dalite offers a wide range of rigid rear projection screen systems for any need ranging from corporate boardrooms to home theaters designed to provide the highest resolution and most accurate color fidelity with dalite rear projection screens viewers can enjoy bright high resolution images without turning the lights off this coating is deposited on a transparent glass daglas or acrylic daplex substrate dalite utilizes a special coating process which chemically bonds the optical layer to the substrate creating a very high degree of adhesion guaranteed not to peel or strip off deluxe frame features impressive architectural design adds sophistication to any installation 13 4 x 3 rectangular base tube dovetail frame eliminates light leakage black anodized finish frame size equals screen viewing area plus 51 2" | "dl8302dalite offers a wide range of rigid rear projection screen systems for any need ranging from corporate boardrooms to home theaters designed to provide the highest resolution and most accurate color fidelity with dalite rear projection screens viewers can enjoy bright high resolution images without turning the lights off this coating is deposited on a transparent glass daglas or acrylic daplex substrate dalite utilizes a special coating process which chemically bonds the optical layer to the substrate creating a very high degree of adhesion guaranteed not to peel or strip off deluxe frame features impressive architectural design adds sophistication to any installation 13 4 x 3 rectangular base tube dovetail frame eliminates light leakage black anodized finish frame size equals screen viewing area plus 51 2" |
| dimensions | "" | "" |
| imageurl | "httpecximagesamazoncomimagesi412bgcln7arl_sl500_aa300_jpg" | "httpiwalmartimagescomimp00717068020071706802825_p255045_300x300jpg" |
| shipweight | "1 065 pounds" | "1065.0" |

#### Candidate Match 2 (Overall Text Match Score: 0.90)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| custom_id | "19012" | "853" |
| product_id | "b001rijw2g" | "15142352" |
| brand | "dalite" | "dalite" |
| modelno | "23050" | "23046" |
| category | "projection screens televisions video" | "electronics general" |
| title | "dalite daglas thruthewall rear projection screen 72 x 96 video format" | "dalite daview thruthewall rear projection screen 60 x 80 video format" |
| price | "8968.99" | "13997.99" |
| features | "model 23050" | "the dalite thruthewall rear projection screen is a rear projection package that comes complete with a factory framed rear projection screen of your choice and a rear projection module the rpm is a precision made aluminum extrusion based rear projection system custom engineered to meet the exacting requirements of today s digital projectors the rpm is standard with a finetuning projector mount cradle which provides a host of alignment adjustments and features a mirror mounted by a threepoint suspension system to ensure superior stability and flatness the perfect mirror adjustment systems is a standard feature on all mirror systems for 42 x 60 and smaller mirrors" |
| short_description | "" | "" |
| long_description | "23050 the dalite thruthewall rear projection screen is a rear projection package that comes complete with a factory framed rear projection screen of your choice and a rear projection module the rpm is a precision made aluminum extrusion based rear projection system custom engineered to meet the exacting requirements of today s digital projectors the rpm is standard with a finetuning projector mount cradle which provides a host of alignment adjustments and features a mirror mounted by a threepoint suspension system to ensure superior stability and flatness the perfect mirror adjustment systems is a standard feature on all mirror systems for 42 x 60 and smaller mirrors" | "dl8440the dalite thruthewall rear projection screen is a rear projection package that comes complete with a factory framed rear projection screen of your choice and a rear projection module the rpm is a precision made aluminum extrusion based rear projection system custom engineered to meet the exacting requirements of today s digital projectors the rpm is standard with a finetuning projector mount cradle which provides a host of alignment adjustments and features a mirror mounted by a threepoint suspension system to ensure superior stability and flatness the perfect mirror adjustment systems is a standard feature on all mirror systems for 42 x 60 and smaller mirrors" |
| dimensions | "" | "" |
| imageurl | "httpecximagesamazoncomimagesi41rfyasotnl_sl500_aa300_jpg" | "httpiwalmartimagescomimp00717068050071706805248_p255045_300x300jpg" |
| shipweight | "1 340 pounds" | "809.0" |

#### Candidate Match 3 (Overall Text Match Score: 0.89)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| custom_id | "6741" | "2431" |
| product_id | "b003001i8k" | "15142480" |
| brand | "dalite" | "dalite" |
| modelno | "23181" | "23096" |
| category | "projection screens televisions video" | "electronics general" |
| title | "dalite data pro thruthewall rear projection screen 52 x 92 hdtv format" | "dalite daplex thruthewall rear projection screen 81 x 108 video format" |
| price | "15985.81" | "10048.99" |
| features | "model 23181" | "the dalite thruthewall rear projection screen is a rear projection package that comes complete with a factory framed rear projection screen of your choice and a rear projection module the rpm is a precision made aluminum extrusion based rear projection system custom engineered to meet the exacting requirements of today s digital projectors the rpm is standard with a finetuning projector mount cradle which provides a host of alignment adjustments and features a mirror mounted by a threepoint suspension system to ensure superior stability and flatness the perfect mirror adjustment systems is a standard feature on all mirror systems for 42 x 60 and smaller mirrors" |
| short_description | "" | "" |
| long_description | "23181 the dalite thruthewall rear projection screen is a rear projection package that comes complete with a factory framed rear projection screen of your choice and a rear projection module the rpm is a precision made aluminum extrusion based rear projection system custom engineered to meet the exacting requirements of today s digital projectors the rpm is standard with a finetuning projector mount cradle which provides a host of alignment adjustments and features a mirror mounted by a threepoint suspension system to ensure superior stability and flatness the perfect mirror adjustment systems is a standard feature on all mirror systems for 42 x 60 and smaller mirrors" | "dl8426the dalite thruthewall rear projection screen is a rear projection package that comes complete with a factory framed rear projection screen of your choice and a rear projection module the rpm is a precision made aluminum extrusion based rear projection system custom engineered to meet the exacting requirements of today s digital projectors the rpm is standard with a finetuning projector mount cradle which provides a host of alignment adjustments and features a mirror mounted by a threepoint suspension system to ensure superior stability and flatness the perfect mirror adjustment systems is a standard feature on all mirror systems for 42 x 60 and smaller mirrors" |
| dimensions | "" | "" |
| imageurl | "httpecximagesamazoncomimagesi41rfyasotnl_sl500_aa300_jpg" | "httpiwalmartimagescomimp00717068080071706808278_p255045_300x300jpg" |
| shipweight | "1 000 pounds" | "1206.0" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **custom_id** | 0.0% | 0.0% | 100.0% | 100.0% | 22074 | 2554 | N/A | N/A | "18154" ↔ "1179" |
| **product_id** | 0.0% | 0.0% | 100.0% | 100.0% | 22074 | 2554 | 10.0 | N/A | "b001fx1riu" ↔ "15142373" |
| **brand** | 0.01% | 5.21% | 8.59% | 18.13% | 1896 | 463 | 7.29 | 7.34 | "dalite" ↔ "dalite" |
| **modelno** | 28.54% | 6.42% | 70.24% | 93.54% | 15505 | 2389 | 8.52 | 7.55 | "" ↔ "27651" |
| **category** | 5.57% | 0.0% | 6.75% | 2.47% | 1490 | 63 | 39.53 | 17.15 | "projection screens office electronics accessories" ↔ "electronics general" |
| **title** | 0.0% | 0.0% | 99.16% | 99.41% | 21888 | 2539 | 67.6 | 53.38 | "dalite 27651 daglas deluxe rear projection screen 96 x 96 av format" ↔ "dalite daglas deluxe rear projection screen 96 x 96 av format" |
| **price** | 12.96% | 0.0% | 33.94% | 54.74% | 7491 | 1398 | N/A | N/A | "" ↔ "6128.99" |
| **features** | 17.26% | 4.7% | 69.07% | 86.37% | 15247 | 2206 | 259.25 | 228.08 | "" ↔ "dalite offers a wide range of rigid rear projection screen systems for any need ranging from corporate boardrooms to home theaters designed to provide the highest resolution and most accurate color fidelity with dalite rear projection screens viewers can enjoy bright high resolution images without turning the lights off this coating is deposited on a transparent glass daglas or acrylic daplex substrate dalite utilizes a special coating process which chemically bonds the optical layer to the substrate creating a very high degree of adhesion guaranteed not to peel or strip off deluxe frame features impressive architectural design adds sophistication to any installation 13 4 x 3 rectangular base tube dovetail frame eliminates light leakage black anodized finish frame size equals screen viewing area plus 51 2" |
| **short_description** | 80.13% | 23.06% | 18.28% | 72.98% | 4036 | 1864 | 516.38 | 284.68 | "" ↔ "" |
| **long_description** | 0.83% | 1.33% | 89.48% | 96.87% | 19751 | 2474 | 995.47 | 397.85 | "dalite 27651 dalite offers a wide range of rigid rear projection screen systems for any need ranging from corporate boardrooms to home theaters designed to provide the highest resolution and most accurate color fidelity with dalite rear projection screens viewers can enjoy bright high resolution images without turning the lights off this coating is deposited on a transparent glass daglas or acrylic daplex substrate dalite utilizes a special coating process which chemically bonds the optical layer to the substrate creating a very high degree of adhesion guaranteed not to peel or strip off deluxe frame features impressive architectural design adds sophistication to any installation 13 4 x 3 rectangular base tube dovetail frame eliminates light leakage black anodized finish frame size equals screen viewing area plus 51 2" ↔ "dl8302dalite offers a wide range of rigid rear projection screen systems for any need ranging from corporate boardrooms to home theaters designed to provide the highest resolution and most accurate color fidelity with dalite rear projection screens viewers can enjoy bright high resolution images without turning the lights off this coating is deposited on a transparent glass daglas or acrylic daplex substrate dalite utilizes a special coating process which chemically bonds the optical layer to the substrate creating a very high degree of adhesion guaranteed not to peel or strip off deluxe frame features impressive architectural design adds sophistication to any installation 13 4 x 3 rectangular base tube dovetail frame eliminates light leakage black anodized finish frame size equals screen viewing area plus 51 2" |
| **dimensions** | 38.58% | 27.33% | 41.29% | 65.0% | 9115 | 1660 | 19.61 | 20.79 | "" ↔ "" |
| **imageurl** | 0.08% | 0.0% | 93.84% | 100.0% | 20714 | 2554 | 55.87 | 58.68 | "httpecximagesamazoncomimagesi412bgcln7arl_sl500_aa300_jpg" ↔ "httpiwalmartimagescomimp00717068020071706802825_p255045_300x300jpg" |
| **shipweight** | 2.04% | 7.28% | 2.67% | 32.46% | 590 | 829 | 8.47 | N/A | "1 065 pounds" ↔ "1065.0" |
```
</details>

