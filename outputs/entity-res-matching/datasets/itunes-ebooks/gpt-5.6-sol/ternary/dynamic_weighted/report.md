# Matching Benchmark: itunes-ebooks — Dynamic Weighted

- **Domain**: ebooks
- **Strategy**: Dynamic Weighted
- **Model**: gpt-5.6-sol
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9839 | 0.0137 |
| Recall | 0.9237 | 0.0000 |
| F1 Score | 0.9528 | 0.0065 |
| Execution Time (s) | 0.7432 | 0.0586 |
| Peak Memory (MB) | 6.73 | 0.01 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 19,278 |
| Completion Tokens | 10,514 |
| Total Tokens | 29,792 |
| Estimated Cost (USD) | $0.2411 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 1.0000 | 0.0000 |
| Potential F1 Ceiling | 0.9918 | 0.0070 |
| LLM Workload Ratio | 19.9% | - |
| Unrecoverable Loss | 0.0000 | - |
| Uncertain Purity | 12.7% | - |

## Deterministic Flakiness Analysis

| Metric | Value |
| :--- | :--- |
| Stability Ratio | 96.03% |
| Consistent Matches | 121 |
| Flaky Matches | 5 |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9918 | 0.9237 | 0.9565 | 1.0000 | 0.9959 | 18.2% | 13.7% | 121 | 1 | 10 | 0.7882 | 6.74 | 9435 | $0.0849 |  |
| 2 | SUCCESS | 0.9918 | 0.9237 | 0.9565 | 1.0000 | 0.9959 | 19.0% | 13.2% | 121 | 1 | 10 | 0.7643 | 6.74 | 10110 | $0.0767 |  |
| 3 | SUCCESS | 0.9680 | 0.9237 | 0.9453 | 1.0000 | 0.9837 | 22.5% | 11.1% | 121 | 4 | 10 | 0.6770 | 6.72 | 10247 | $0.0794 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | dynamic_skew | 0.4302 | 0.7464 | [0.3190, 0.5414, 0.8831] |
| 2 | dynamic_skew | 0.4534 | 0.7568 | [0.3438, 0.5630, 0.8860] |
| 3 | dynamic_skew | 0.5114 | 0.7727 | [0.4200, 0.6027, 0.8860] |

## LLM Strategy Configuration & Prompts

- **Model**: `gpt-5.6-sol`
- **Provider**: `openai`
- **Latency**: `45.26s`
- **Log File**: `outputs/logs/llm_calls/20260919_165742_408098_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "1. record_id\n   1. Inspect Exemplar Candidate Matches: The same books have different values across sources (for example, 3871 \u2194 10662, 1011 \u2194 2020, and 3194 \u2194 3425), showing that this is a source-local identifier rather than a shared entity attribute.\n   2. Inspect Statistical Profile: It is complete and unique in both sources, with cardinalities equal to the row counts (6,500 and 14,110), which is characteristic of an internal key. The explicit source-specific-key exclusion rule applies.\n   3. Algorithm Trade-off Evaluation: No comparison algorithm is appropriate. exact would reject true matches because the IDs differ, while fuzzy or numeric comparisons could create meaningless proximity between unrelated internal IDs.\n   4. Weight Justification: Excluded; no weight is assigned because it contains no cross-source identity evidence.\n\n2. publisher\n   1. Inspect Exemplar Candidate Matches: Two pairs agree exactly (simon schuster and john blake), but one true match differs substantially (nevicata \u2194 primento digital publishing), likely reflecting imprint/distributor or edition metadata rather than a typo.\n   2. Inspect Statistical Profile: Null rates are 0.0% and 0.02%, cardinalities are 1,667 and 662, and average lengths are 16.18 and 17.0. It passes the null and variance rules but is substantially less distinctive than title or description.\n   3. Algorithm Trade-off Evaluation: jarowinkler is best for these short publisher names and can tolerate minor spelling, punctuation, or suffix variation. cosine is risky at this length because a one-token typo or abbreviation can lose all token overlap; exact is too brittle. No available algorithm can reconcile genuinely divergent imprint taxonomies such as nevicata versus primento digital publishing, so this field must remain weak.\n   4. Weight Justification: Weight 0.20. Publisher is auxiliary descriptive context, not core identity, and observed publisher divergence makes stronger weighting unsafe.\n\n3. date\n   1. Inspect Exemplar Candidate Matches: One pair agrees exactly, while the other two preserve year and month but differ in day (June 30 \u2194 June 1 and December 16 \u2194 December 1). This suggests source-specific day precision or month-level normalization.\n   2. Inspect Statistical Profile: Null rates are 0.0% and 1.32%, with cardinalities 2,292 and 333. The field passes exclusions, but Source B's much lower cardinality supports reduced date precision.\n   3. Algorithm Trade-off Evaluation: date is appropriate because it recognizes calendar hierarchy and gives partial credit to dates sharing a year and month. exact would wrongly reject observed true matches; numeric_linear is inappropriate for encoded timestamps and does not model month/year structure; numeric_relative is nonsensical for calendar dates.\n   4. Weight Justification: Weight 0.30. Publication date is useful contextual evidence, but edition differences and day-normalization prevent it from being a primary identity signal.\n\n4. description\n   1. Inspect Exemplar Candidate Matches: Descriptions are nearly identical long passages, with small spacing/concatenation changes and a Source B trailing token, \u201cless.\u201d The semantic content and almost all word tokens remain shared.\n   2. Inspect Statistical Profile: Null rates are 0.02% and 0.3%, uniqueness is 97.14% and 98.77%, cardinalities are 6,314 and 13,937, and average lengths are 942.72 and 1,028.85. This is highly available, highly discriminative long text.\n   3. Algorithm Trade-off Evaluation: cosine is ideal for very long multi-word text and tolerates the observed extra token, omissions, and local spacing differences without requiring positional alignment. jarowinkler and damerau_levenshtein would be overly sensitive to length and cumulative character shifts across roughly 1,000 characters; exact would fail on the appended \u201cless\u201d and spacing differences.\n   4. Weight Justification: Weight 0.65. Description is a strong, highly distinctive primary descriptive attribute, though it is not given core-identifier weight because descriptions may be reused across editions or copied between related products.\n\n5. title\n   1. Inspect Exemplar Candidate Matches: All three titles agree exactly, including a short title (39 days of gazza) and longer multi-word titles. This is strong direct evidence that title is central to book identity.\n   2. Inspect Statistical Profile: Null rates are 0.0% and 0.02%, uniqueness is 99.15% and 96.35%, cardinalities are 6,445 and 13,595, and average lengths are 28.0 and 24.87. It is complete and exceptionally discriminative.\n   3. Algorithm Trade-off Evaluation: cosine is selected because the typical title is multi-word and around 25\u201328 characters, and token comparison is robust to token ordering, subtitles, or omitted words. exact would be unnecessarily brittle. jarowinkler would better handle a typo in a very short title, but it is weaker for word-order shifts and additions; the exemplars show stable title tokens rather than spelling errors. damerau_levenshtein would over-penalize subtitle or length differences.\n   4. Weight Justification: Weight 0.70. Title is the strongest primary descriptive attribute and nearly unique, warranting the top of the 0.5\u20130.7 range.\n\n6. rating_value\n   1. Inspect Exemplar Candidate Matches: The value is blank on both sides in every exemplar, so it contributes no positive evidence for these matches.\n   2. Inspect Statistical Profile: Null rates are 90.57% in Source A and 99.67% in Source B, both far above the 50% exclusion threshold; Source B also has cardinality 4.\n   3. Algorithm Trade-off Evaluation: Although a numeric comparison could theoretically compare ratings, the extreme missingness makes any algorithm operationally ineffective. exact would also confuse shared missingness with meaningful agreement if null handling were imperfect.\n   4. Weight Justification: Excluded; no weight is assigned because it fails the mandatory high-null rule.\n\n7. price\n   1. Inspect Exemplar Candidate Matches: Each exemplar has an identical price across sources (14.99, 5.99, and 22.99). This supports price as corroborating evidence, although many different books can share a price.\n   2. Inspect Statistical Profile: Null rates are 0.0% in both sources, but uniqueness is only 1.05% and 5.2%, with cardinalities 68 and 734. It passes exclusion rules but has low distinctiveness and may vary by market or edition.\n   3. Algorithm Trade-off Evaluation: numeric_relative is appropriate for monetary values because it evaluates differences proportionally to the price baseline. numeric_linear would treat the same absolute gap uniformly even when economically very different; exact would reject legitimate discounts or price updates; string-edit algorithms are semantically inappropriate.\n   4. Weight Justification: Weight 0.20. Price is auxiliary context with low cardinality and possible temporal variation, despite exact agreement in the exemplars.\n\n8. author\n   1. Inspect Exemplar Candidate Matches: All exemplar author values agree exactly (james w finegan, steve pitts, and john biggar), demonstrating stable author attribution across sources.\n   2. Inspect Statistical Profile: Null rates are 0.05% and 0.12%, uniqueness is 73.86% and 76.0%, cardinalities are 4,801 and 10,724, and average lengths are 15.54 and 18.74. It is highly available and discriminative.\n   3. Algorithm Trade-off Evaluation: jarowinkler is best for short personal-name strings and can tolerate initials, minor misspellings, or suffix truncation. cosine is unsafe for names below roughly 20 characters because one misspelled single-token surname may lose token overlap entirely; exact is too brittle; damerau_levenshtein is less suitable when initials or honorifics create length differences.\n   4. Weight Justification: Weight 0.65. Author is a strong identity-bearing descriptive attribute, but it is below core-identifier weight because authors can have many books and collaborations may be represented differently.\n\n9. short_description\n   1. Inspect Exemplar Candidate Matches: The first pair agrees exactly on a multi-word subtitle-like phrase, while the second and third pairs are blank in both sources. Thus, when present it can be highly confirming, but availability is inconsistent.\n   2. Inspect Statistical Profile: Null rates are 42.82% and 33.2%, below but close to the 50% exclusion threshold; uniqueness is 52.45% and 61.16%, cardinalities are 3,409 and 8,630, and average lengths are 46.25 and 43.78. It passes exclusions and has moderate-to-high distinctiveness among populated values.\n   3. Algorithm Trade-off Evaluation: cosine fits the roughly 44\u201346 character multi-word text and tolerates word additions, omissions, and reordering. exact would be brittle; jarowinkler is weaker on reordered multi-word phrases; damerau_levenshtein would penalize length differences. Cosine's typo weakness is accepted because the exemplar variation shows phrase-level equality rather than sub-word spelling noise.\n   4. Weight Justification: Weight 0.40. This is useful supporting descriptive evidence, but its substantial missingness and overlap with title/description cap it at the high end of auxiliary context.\n\n10. length\n   1. Inspect Exemplar Candidate Matches: Page length agrees exactly in all exemplars (288, 288, and 306), making it useful for confirming the same edition or format.\n   2. Inspect Statistical Profile: Null rates are 0.0% in both sources, uniqueness is 8.26% and 4.37%, and cardinalities are 537 and 617. It is complete but not individually distinctive.\n   3. Algorithm Trade-off Evaluation: numeric_linear is appropriate for page counts because a fixed absolute discrepancy has a consistent interpretation. numeric_relative could under-penalize a large absolute page difference for long books; exact would be too strict for minor edition or metadata differences; textual algorithms are inappropriate.\n   4. Weight Justification: Weight 0.25. Page count is supporting edition context, not entity identity, and its low uniqueness limits its influence.\n\n11. Source-only columns: language, url, rating_star, seller, genre, page_id, ISBN, and review_count\n   1. Inspect Exemplar Candidate Matches: No aligned A \u2194 B values are available because each appears in only one source, so empirical cross-source agreement cannot be assessed.\n   2. Inspect Statistical Profile: Some are otherwise potentially useful\u2014especially ISBN\u2014but no counterpart exists in the other source. page_id and url also appear system/source-specific; review_count is 99.67% null in Source B.\n   3. Algorithm Trade-off Evaluation: No pairwise comparison algorithm can operate when the corresponding column is absent from one source. In particular, exact on ISBN would be excellent only if ISBN were mapped from both sources; page_id/url comparisons would risk matching source-local identifiers.\n   4. Weight Justification: Excluded from this cross-source scoring configuration; no weights are assigned.",
  "matching_columns": {
    "publisher": {
      "algorithm": "jarowinkler",
      "weight": 0.2
    },
    "date": {
      "algorithm": "date",
      "weight": 0.3
    },
    "description": {
      "algorithm": "cosine",
      "weight": 0.65
    },
    "title": {
      "algorithm": "cosine",
      "weight": 0.7
    },
    "price": {
      "algorithm": "numeric_relative",
      "weight": 0.2
    },
    "author": {
      "algorithm": "jarowinkler",
      "weight": 0.65
    },
    "short_description": {
      "algorithm": "cosine",
      "weight": 0.4
    },
    "length": {
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
| **Total Rows** | 6500 | 14110 |
| **Column Count** | 16 | 12 |

### 2. Exemplar Candidate Matches (High-Confidence Entity Pairs)
The following candidate pairs were discovered via holistic zero-configuration row-level textual overlap.
Inspect how field values, units, abbreviations, typos, and taxonomies vary across matching records:

#### Candidate Match 1 (Overall Text Match Score: 0.99)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| record_id | "3871" | "10662" |
| publisher | "simon schuster" | "simon schuster" |
| date | "2008-06-30 00:00:00" | "2008-06-01 00:00:00" |
| description | "every golfer alive knows that he or she has two ancestral homes ones own and scotland on her rolling shores the game of golf had its origins and to walk the links of st andrews is to feel at one with the shepherd who decided one day to see how far he could whack a stone with his crook most serious golfers will make the pilgrimage to scotland to try to hit the postage stamp green at troon to trace the footsteps of ben hogan at carnoustie and to brave the challenge of the road hole at st andrews all golfers dream of taking such a tripfor the tourist or the dreamer there can be no better guide than james w finegan a passionate advocate of the game thats played on the links between land and sea finegan combines a writers eye a historians knowledge and a golfers sense of wonder and apprehension to provide an impossibly ambitious grand tour of golfs native landin a loop of a thousand miles that begins in edinburgh and ends across the firth of forth in st andrews finegan covers some sixty courses visiting the true shrines of the game the courses that are well known and respected and the littleknown gems you might otherwise pass right by he shares the history of the courses both of their creation and of the most famous matches played there he also writes marvelously about the scenic and strategic charms to be found as you play them yourself and he provides all the information you need to make your arrangements to do just that because unlike most championship courses in the united states the great courses of scotland are available to the publicin addition to his delightful descriptions of the golf to be found there finegan gives us his recommendations for places to stay ranging from the most modest bedandbreakfast to the most magnificent castle hotel he describes the pleasures to be found off the beaten track the spectacular views from a country road or the ancient cathedral thats worth a stop on the way to the first tee and because all the travel within the country is done by car he spells out the actual routes from town to town and course to courseblasted heaths and blessed greens is a book to be read to be savored and to be tucked away in your suitcase when you finally undertake the journey of your dreams" | "every golfer alive knows that he or she has two ancestral homes ones own and scotland on her rolling shores the game of golf had its origins and to walk the links of st andrews is to feel at one with the shepherd who decided one day to see how far he could whack a stone with his crook most serious golfers will make the pilgrimage to scotland to try to hit the postage stamp green at troon to trace the footsteps of ben hogan at carnoustie and to brave the challenge of the road hole at st andrews all golfers dream of taking such a tripfor the tourist or the dreamer there can be no better guide than james w finegan a passionate advocate of the game thats played on the links between land and sea finegan combines a writers eye a historians knowledge and a golfers sense of wonder and apprehension to provide an impossibly ambitious grand tour of golfs native landin a loop of a thousand miles that begins in edinburgh and ends across the firth of forth in st andrews finegan covers some sixty courses visiting the true shrines of the game the courses that are well known and respected and the littleknown gems you might otherwise pass right by he shares the history of the courses both of their creation and of the most famous matches played there he also writes marvelously about the scenic and strategic charms to be found as you play them yourself and he provides all the information you need to make your arrangements to do just that because unlike most championship courses in the united states the great courses of scotland are available to the publicin addition to his delightful descriptions of the golf to be found there finegan gives us his recommendations for places to stay ranging from the most modest bedandbreakfast to the most magnificent castle hotel he describes the pleasures to be found off the beaten track the spectacular views from a country road or the ancient cathedral thats worth a stop on the way to the first tee and because all the travel within the country is done by car he spells out the actual routes from town to town and course to courseblasted heaths and blessed greens is a book to be read to be savored and to be tucked away in your suitcase when you finally undertake the journey of your dreams less" |
| title | "blasted heaths and blessed green" | "blasted heaths and blessed green" |
| rating_value | "" | "" |
| price | "14.99" | "14.99" |
| author | "james w finegan" | "james w finegan" |
| short_description | "a golfers pilgrimage to the courses of scotland" | "a golfers pilgrimage to the courses of scotland" |
| length | "288" | "288" |

#### Candidate Match 2 (Overall Text Match Score: 0.99)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| record_id | "1011" | "2020" |
| publisher | "john blake" | "john blake" |
| date | "2013-03-01 00:00:00" | "2013-03-01 00:00:00" |
| description | "the tragicomic story of how the disintegration of paul gascoignes managerial role impacted many peoples lives not least his own as the firsttime manager of a provincial nonleague football team former england star paul gascoigne promised to fulfill their dreams but then in the space of just 39 days both manager and team saw a dramatic reversal of fortune gazza was the english football icon on the 1990s his magnificent midfield play provided some of englands most memorable moments and he enjoyed a headlinegrabbing career with newcastle united tottenham lazio glasgow rangers middlesbrough and everton then it all went terribly wrong he still made the headlines but for all the wrong reasonsalcoholism drugs wifebeating personality disorder runins with the law and nervous breakdown gascoigne seemed to have passed a personal point of no return then in the autumn of 2005 he was given a chance to rebuild his career with his first job as a football manager as part of a consortium which bought kettering town gazza reinvented himself appearing to have his personal problems under control he took charge full of big ideas about steering the club into the football league and towards the big time the people of kettering were starstruck by the celebrity among them and yet within just a few short weeks after gascoigne was appointed manager he would be sacked amid an increasingly bizarre series of allegations leaving a once hopeful club on its knees" | "the tragicomic story of how the disintegration of paul gascoignes managerial role impacted many peoples lives not least his ownas the firsttime manager of a provincial nonleague football team former england star paul gascoigne promised to fulfill their dreams but then in the space of just 39 days both manager and team saw a dramatic reversal of fortune gazza was the english football icon on the 1990s his magnificent midfield play provided some of englands most memorable moments and he enjoyed a headlinegrabbing career with newcastle united tottenham lazio glasgow rangers middlesbrough and everton then it all went terribly wrong he still made the headlines but for all the wrong reasonsalcoholism drugs wifebeating personality disorder runins with the law and nervous breakdown gascoigne seemed to have passed a personal point of no return then in the autumn of 2005 he was given a chance to rebuild his career with his first job as a football manager as part of a consortium which bought kettering town gazza reinvented himself appearing to have his personal problems under control he took charge full of big ideas about steering the club into the football league and towards the big time the people of kettering were starstruck by the celebrity among them and yet within just a few short weeks after gascoigne was appointed manager he would be sacked amid an increasingly bizarre series of allegations leaving a once hopeful club on its knees less" |
| title | "39 days of gazza" | "39 days of gazza" |
| rating_value | "" | "" |
| price | "5.99" | "5.99" |
| author | "steve pitts" | "steve pitts" |
| short_description | "" | "" |
| length | "288" | "288" |

#### Candidate Match 3 (Overall Text Match Score: 0.99)
| Column | Value in Source A | Value in Source B |
| :--- | :--- | :--- |
| record_id | "3194" | "3425" |
| publisher | "nevicata" | "primento digital publishing" |
| date | "2014-12-16 00:00:00" | "2014-12-01 00:00:00" |
| description | "le premier topo dalpinisme couvrant lensemble de la cordillere des andes du venezuela a la patagonie et la terre de feu quel amateur de montagne na reve de decouvrir un jour lamerique du sud par ses plus belles montagnesdestine aux alpinistes et aux randonneurs ce guide complet reprend tous les sommets de plus de 6000 metres daltitude les 5000 les plus importants et les principales montagnes de patagonie et de terre de feu sans oublier les principaux sites descalade et de bloc au total plus de 400 sommets decrits en detail avec des milliers dinformations uniques ainsi que de nombreuses cartes et photos de locean pacifique aux confins de laltiplano des grandes parois aux volcans les plus faciles de la montagne la plus proche a la cordillere la plus reculee vous trouverez dans ce guide le sommet de vos reves pour preparer et realiser un voyage inoubliable ce quen pense la critiquele premier ouvrage publie par cette nouvelle maison dedition comble un vide dans les livres consacres a la montagne voyages voyages un ouvrage incontournable a destination des alpinistesbaroudeurs francophones montagnes magazine les amateurs de montagnes lointaines trouveront leur compte de reves et de projets dans ce guide les alpes a propos de lauteurinstructeur de montagne professionnel john biggar grimpe regulierement dans les andes depuis une quinzaine dannees lorsquil nest pas en amerique du sud il vit a castle douglas en ecosse ou il dirige andes une agence de voyages specialisee en trekking alpinisme et ski dans les andes" | "le premier topo dalpinisme couvrant lensemble de la cordillere des andes du venezuela a la patagonie et la terre de feu quel amateur de montagne na reve de decouvrir un jour lamerique du sud par ses plus belles montagnesdestine aux alpinistes et aux randonneurs ce guide complet reprend tous les sommets de plus de 6000 metres daltitude les 5000 les plus importants et les principales montagnes de patagonie et de terre de feu sans oublier les principaux sites descalade et de bloc au total plus de 400 sommets decrits en detail avec des milliers dinformations uniques ainsi que de nombreuses cartes et photos de locean pacifique aux confins de laltiplano des grandes parois aux volcans les plus faciles de la montagne la plus proche a la cordillere la plus reculee vous trouverez dans ce guide le sommet de vos reves pour preparer et realiser un voyage inoubliable ce quen pense la critiquele premier ouvrage publie par cette nouvelle maison dedition comble un vide dans les livres consacres a la montagne voyages voyages un ouvrage incontournable a destination des alpinistesbaroudeurs francophones montagnes magazine les amateurs de montagnes lointaines trouveront leur compte de reves et de projets dans ce guide les alpes a propos de lauteurinstructeur de montagne professionnel john biggar grimpe regulierement dans les andes depuis une quinzaine dannees lorsquil nest pas en amerique du sud il vit a castle douglas en ecosse ou il dirige andes une agence de voyages specialisee en trekking alpinisme et ski dans les andes less" |
| title | "les andes guide dalpinisme guide complet" | "les andes guide dalpinisme guide complet" |
| rating_value | "" | "" |
| price | "22.99" | "22.99" |
| author | "john biggar" | "john biggar" |
| short_description | "" | "" |
| length | "306" | "306" |

### 3. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **record_id** | 0.0% | 0.0% | 100.0% | 100.0% | 6500 | 14110 | N/A | N/A | "3871" ↔ "10662" |
| **publisher** | 0.0% | 0.02% | 25.65% | 4.69% | 1667 | 662 | 16.18 | 17.0 | "simon schuster" ↔ "simon schuster" |
| **date** | 0.0% | 1.32% | 35.26% | 2.36% | 2292 | 333 | N/A | N/A | "2008-06-30 00:00:00" ↔ "2008-06-01 00:00:00" |
| **description** | 0.02% | 0.3% | 97.14% | 98.77% | 6314 | 13937 | 942.72 | 1028.85 | "every golfer alive knows that he or she has two ancestral homes ones own and scotland on her rolling shores the game of golf had its origins and to walk the links of st andrews is to feel at one with the shepherd who decided one day to see how far he could whack a stone with his crook most serious golfers will make the pilgrimage to scotland to try to hit the postage stamp green at troon to trace the footsteps of ben hogan at carnoustie and to brave the challenge of the road hole at st andrews all golfers dream of taking such a tripfor the tourist or the dreamer there can be no better guide than james w finegan a passionate advocate of the game thats played on the links between land and sea finegan combines a writers eye a historians knowledge and a golfers sense of wonder and apprehension to provide an impossibly ambitious grand tour of golfs native landin a loop of a thousand miles that begins in edinburgh and ends across the firth of forth in st andrews finegan covers some sixty courses visiting the true shrines of the game the courses that are well known and respected and the littleknown gems you might otherwise pass right by he shares the history of the courses both of their creation and of the most famous matches played there he also writes marvelously about the scenic and strategic charms to be found as you play them yourself and he provides all the information you need to make your arrangements to do just that because unlike most championship courses in the united states the great courses of scotland are available to the publicin addition to his delightful descriptions of the golf to be found there finegan gives us his recommendations for places to stay ranging from the most modest bedandbreakfast to the most magnificent castle hotel he describes the pleasures to be found off the beaten track the spectacular views from a country road or the ancient cathedral thats worth a stop on the way to the first tee and because all the travel within the country is done by car he spells out the actual routes from town to town and course to courseblasted heaths and blessed greens is a book to be read to be savored and to be tucked away in your suitcase when you finally undertake the journey of your dreams" ↔ "every golfer alive knows that he or she has two ancestral homes ones own and scotland on her rolling shores the game of golf had its origins and to walk the links of st andrews is to feel at one with the shepherd who decided one day to see how far he could whack a stone with his crook most serious golfers will make the pilgrimage to scotland to try to hit the postage stamp green at troon to trace the footsteps of ben hogan at carnoustie and to brave the challenge of the road hole at st andrews all golfers dream of taking such a tripfor the tourist or the dreamer there can be no better guide than james w finegan a passionate advocate of the game thats played on the links between land and sea finegan combines a writers eye a historians knowledge and a golfers sense of wonder and apprehension to provide an impossibly ambitious grand tour of golfs native landin a loop of a thousand miles that begins in edinburgh and ends across the firth of forth in st andrews finegan covers some sixty courses visiting the true shrines of the game the courses that are well known and respected and the littleknown gems you might otherwise pass right by he shares the history of the courses both of their creation and of the most famous matches played there he also writes marvelously about the scenic and strategic charms to be found as you play them yourself and he provides all the information you need to make your arrangements to do just that because unlike most championship courses in the united states the great courses of scotland are available to the publicin addition to his delightful descriptions of the golf to be found there finegan gives us his recommendations for places to stay ranging from the most modest bedandbreakfast to the most magnificent castle hotel he describes the pleasures to be found off the beaten track the spectacular views from a country road or the ancient cathedral thats worth a stop on the way to the first tee and because all the travel within the country is done by car he spells out the actual routes from town to town and course to courseblasted heaths and blessed greens is a book to be read to be savored and to be tucked away in your suitcase when you finally undertake the journey of your dreams less" |
| **language** | 0.0% | N/A | 0.34% | N/A | 22 | N/A | 6.98 | N/A | N/A |
| **title** | 0.0% | 0.02% | 99.15% | 96.35% | 6445 | 13595 | 28.0 | 24.87 | "blasted heaths and blessed green" ↔ "blasted heaths and blessed green" |
| **url** | 0.0% | N/A | 100.0% | N/A | 6500 | N/A | 59.12 | N/A | N/A |
| **rating_value** | 90.57% | 99.67% | 4.97% | 0.03% | 323 | 4 | N/A | N/A | "" ↔ "" |
| **price** | 0.0% | 0.0% | 1.05% | 5.2% | 68 | 734 | N/A | N/A | "14.99" ↔ "14.99" |
| **author** | 0.05% | 0.12% | 73.86% | 76.0% | 4801 | 10724 | 15.54 | 18.74 | "james w finegan" ↔ "james w finegan" |
| **rating_star** | 0.0% | N/A | 0.14% | N/A | 9 | N/A | N/A | N/A | N/A |
| **seller** | 0.69% | N/A | 11.69% | N/A | 760 | N/A | 23.09 | N/A | N/A |
| **short_description** | 42.82% | 33.2% | 52.45% | 61.16% | 3409 | 8630 | 46.25 | 43.78 | "a golfers pilgrimage to the courses of scotland" ↔ "a golfers pilgrimage to the courses of scotland" |
| **length** | 0.0% | 0.0% | 8.26% | 4.37% | 537 | 617 | N/A | N/A | "288" ↔ "288" |
| **genre** | 0.0% | N/A | 1.51% | N/A | 98 | N/A | 9.7 | N/A | N/A |
| **page_id** | 0.06% | N/A | 99.94% | N/A | 6496 | N/A | N/A | N/A | N/A |
| **ISBN** | N/A | 1.32% | N/A | 98.36% | N/A | 13878 | N/A | N/A | N/A |
| **review_count** | N/A | 99.67% | N/A | 0.02% | N/A | 3 | N/A | N/A | N/A |
```
</details>

