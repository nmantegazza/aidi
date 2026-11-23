# Matching Benchmark: amazon-walmart — Dynamic Weighted

- **Domain**: e-commerce
- **Strategy**: Dynamic Weighted
- **Model**: deepseek-v4.1-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.7466 | 0.0271 |
| Recall | 0.2808 | 0.0596 |
| F1 Score | 0.4062 | 0.0683 |
| Execution Time (s) | 37.3198 | 1.3033 |
| Peak Memory (MB) | 290.08 | 2.87 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 16,476 |
| Completion Tokens | 14,216 |
| Total Tokens | 30,692 |
| Estimated Cost (USD) | $0.0000 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 0.8732 | 0.0213 |
| Potential F1 Ceiling | 0.8048 | 0.0226 |
| LLM Workload Ratio | 2.2% | - |
| Unrecoverable Loss | 0.1268 | - |
| Uncertain Purity | 8.2% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 60.41% |
| Consistent Matches | 322 |
| Flaky Matches | 211 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.7431 | 0.3033 | 0.4308 | 0.8899 | 0.8099 | 2.4% | 7.3% | 350 | 121 | 804 | 36.4194 | 287.26 | 10274 | - |  |
| 2 | SUCCESS | 0.7214 | 0.2132 | 0.3291 | 0.8492 | 0.7801 | 1.9% | 9.9% | 246 | 95 | 908 | 36.7257 | 292.99 | 9852 | - |  |
| 3 | SUCCESS | 0.7753 | 0.3258 | 0.4588 | 0.8804 | 0.8245 | 2.2% | 7.3% | 376 | 109 | 778 | 38.8143 | 289.98 | 10566 | - |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dispersion_boost | 0.4849 | 0.6623 | [0.2543, 0.3422, 0.4849] |
| 2 | dispersion_boost | 0.4761 | 0.6567 | [0.2454, 0.3288, 0.4761] |
| 3 | dispersion_boost | 0.4937 | 0.6758 | [0.2553, 0.3453, 0.4937] |

## LLM Strategy Configuration & Prompts

- **Model**: `deepseek-v4.1-flash`
- **Provider**: `deepseek`
- **Latency**: `22.27s`
- **Log File**: `outputs/logs/llm_calls/20260919_160047_053003_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "**OVERVIEW.** The two sources are product catalogs (Source A \u2248 Amazon-style, Source B \u2248 Walmart-style) for rear-projection screens. The exemplar pairs reveal the KEY empirical facts: (a) brand is perfectly stable; (b) title and long_description are near-identical free text with only token deletions (the model number often appears in A's title but is absent in B); (c) modelno, price, shipweight, and category frequently DIVERGE between sources (e.g., modelno \"23050\"\u2194\"23046\", \"23181\"\u2194\"23096\"; price \"8968.99\"\u2194\"13997.99\"); (d) product_id/custom_id are mutually disjoint source-specific keys; (e) imageurl points to completely different CDNs. These observations drive algorithm choice and weighting.\n\n**custom_id** \u2014 EXCLUDED. Step 1: Exemplars \"18154\"\u2194\"1179\" are unrelated numeric keys. Step 2: 100% unique in both, cardinality = row count \u2192 it is an auto-generated surrogate key. Step 3: Any similarity algorithm would be meaningless (namespacing differs per source). Step 4: System/internal attribute \u2192 excluded.\n\n**product_id** \u2014 EXCLUDED. Step 1: A=\"b001fx1riu\" (10-char Amazon ASIN) vs B=\"15142373\" (Walmart 8-digit ID) \u2014 disjoint vocabularies. Step 2: 0% null, 100% unique, cardinality = row count. Step 3: This is a source-specific product key, not a shared identifier; no algorithm can align two different ID namespaces. Step 4: Excluded as source-specific key.\n\n**short_description** \u2014 EXCLUDED. Step 1: Empty in all exemplars (\"\"\u2194\"\"). Step 2: 80.13% null in A (> 50% threshold), 23.06% null in B. Step 3: Insufficient population makes any comparison unreliable. Step 4: Excluded per high-null rule.\n\n**imageurl** \u2014 EXCLUDED. Step 1: A=\"httpecximagesamazoncom...i412bgcln7arl...\" vs B=\"httpiwalmartimagescom...007170680...\" \u2014 entirely different hosts and path schemes. Step 2: ~0% null, 93\u2013100% unique. Step 3: Even cosine would yield ~0 similarity for genuinely matching entities because the CDN structure is unrelated; it injects pure noise. Step 4: Excluded as source-specific asset reference.\n\n**brand** \u2014 jarowinkler, weight 0.55. Step 1: \"dalite\"\u2194\"dalite\" identical across all three exemplars \u2014 a stable, high-signal identity token. Step 2: 0.01%/5.21% null, cardinality 1896/463, avg len ~7.3 \u2192 single short word, densely populated. Step 3: This is a short single-word brand, the textbook case where cosine/TF-IDF fails (a one-character typo \u2192 0.0); jarowinkler's prefix-weighted character alignment tolerates typos/phonetic variants while still discriminating. Step 4: Brand is a strong descriptive-identity attribute \u2192 0.55.\n\n**title** \u2014 cosine, weight 0.70. Step 1: \"dalite 27651 daglas deluxe rear projection screen 96 x 96 av format\" \u2194 \"dalite daglas deluxe rear projection screen 96 x 96 av format\" \u2014 identical except B omits the model-number token; other exemplars show the same token-level add/omission pattern. Step 2: 0%/0% null, ~99% unique, avg len 67.6/53.4 \u2192 multi-word free text. Step 3: Multi-word text with token insertions/deletions is exactly where word-level TF-IDF cosine is order-invariant and robust; jarowinkler would be thrown off by the extra token shifting character positions. Step 4: Title is the most discriminative descriptive attribute \u2192 0.70.\n\n**modelno** \u2014 damerau_levenshtein, weight 0.45. Step 1: Aligned values often diverge (\"23050\"\u2194\"23046\", \"23181\"\u2194\"23096\") and are sometimes null in A (\"\"\u2194\"27651\"). Step 2: 28.54%/6.42% null (< 50%), cardinality 15505/2389, avg len ~8 \u2192 short alphanumeric codes. Step 3: These are compact part codes; cosine fails on sub-token digit differences and numeric_relative wrongly treats them as quantities. damerau_levenshtein penalizes single-digit flips/transpositions that distinguish distinct models. Step 4: Product identifier, but empirically noisy across sources \u2192 moderate 0.45.\n\n**long_description** \u2014 cosine, weight 0.40. Step 1: Values are near-identical long boilerplate differing only in a leading code (\"dl8302...\" vs \"27651...\"). Step 2: 0.83%/1.33% null, 89\u201397% unique, avg len 995/398 \u2192 long free text. Step 3: Cosine is ideal for long multi-word text and is insensitive to the small prefix difference; jarowinkler/Levenshtein would over-penalize length mismatch (995 vs 398). Step 4: Strong descriptive evidence, but partly generic boilerplate shared across SKUs \u2192 0.40.\n\n**features** \u2014 cosine, weight 0.30. Step 1: Inconsistent alignment: A is often empty while B carries long text (\"\"\u2194\"dalite offers a wide range...\"), or A holds only a tiny label (\"model 23050\"). Step 2: 17.26%/4.7% null, 69\u201386% unique, avg len 259/228 \u2192 long free text. Step 3: Long-form content is correctly handled by word-level cosine; edit-distance algorithms would collapse under the length asymmetry. Step 4: Supporting descriptive text but noisily populated \u2192 0.30.\n\n**category** \u2014 cosine, weight 0.15. Step 1: Divergent taxonomies: \"projection screens office electronics accessories\" \u2194 \"electronics general\" \u2014 different vocabularies with only incidental shared tokens. Step 2: 5.57%/0% null, cardinality 1490/63, avg len 39.5/17.2. Step 3: Because the taxonomies are source-specific, only word-level overlap (cosine) can extract partial credit from shared tokens like \"electronics\"; this is a deliberately weak signal. Step 4: Weak contextual/taxonomic signal \u2192 0.15.\n\n**price** \u2014 numeric_relative, weight 0.20. Step 1: Prices diverge markedly (\"8968.99\"\u2194\"13997.99\", \"15985.81\"\u2194\"10048.99\"), and A may be null. Step 2: 12.96%/0% null, cardinality 7491/1398 \u2192 continuous monetary values. Step 3: Money spans orders of magnitude, so scale-invariant numeric_relative is appropriate (absolute numeric_linear would distort); exact/date are nonsensical here. Step 4: Supporting contextual attribute only \u2192 0.20.\n\n**shipweight** \u2014 numeric_relative, weight 0.15. Step 1: Only one exemplar aligns (\"1 065 pounds\"\u2194\"1065.0\"); others diverge (\"1 340 pounds\"\u2194\"809.0\", \"1 000 pounds\"\u2194\"1206.0\"). Step 2: 2.04%/7.28% null, cardinality 590/829 \u2192 physical weights. Step 3: Weights are continuous measures spanning orders of magnitude \u2192 numeric_relative absorbs unit/format noise better than string methods; cosine would break the \"1 065 pounds\" vs \"1065.0\" tokenization. Step 4: Weak supporting physical attribute \u2192 0.15.\n\n**dimensions** \u2014 cosine, weight 0.10. Step 1: Empty in all three exemplars (\"\"\u2194\"\"), so no discriminative evidence observed. Step 2: 38.58%/27.33% null (under 50%), cardinality 9115/1660, avg len ~20. Step 3: Dimension strings are short multi-token text; cosine tolerates token reordering, selected over edit distance. Step 4: Auxiliary attribute with no demonstrated alignment \u2192 0.10.",
  "matching_columns": {
    "brand": {
      "algorithm": "jarowinkler",
      "weight": 0.55
    },
    "title": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "modelno": {
      "algorithm": "damerau_levenshtein",
      "weight": 0.45
    },
    "long_description": {
      "algorithm": "cosine",
      "weight": 0.4
    },
    "features": {
      "algorithm": "cosine",
      "weight": 0.3
    },
    "price": {
      "algorithm": "numeric_relative",
      "weight": 0.2
    },
    "category": {
      "algorithm": "cosine",
      "weight": 0.15
    },
    "shipweight": {
      "algorithm": "numeric_relative",
      "weight": 0.15
    },
    "dimensions": {
      "algorithm": "cosine",
      "weight": 0.1
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

