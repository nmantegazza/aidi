# Matching Benchmark: itunes-ebooks — Dynamic Weighted

- **Domain**: ebooks
- **Strategy**: Dynamic Weighted
- **Model**: gemini-3.8-flash
- **Classification Mode**: ClassificationMode.TERNARY
- **Successful Iterations**: 3 / 3

## Aggregated Metrics

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Precision | 0.9888 | 0.0097 |
| Recall | 0.8931 | 0.0000 |
| F1 Score | 0.9385 | 0.0044 |
| Execution Time (s) | 0.5998 | 0.0555 |
| Peak Memory (MB) | 6.75 | 0.04 |

## Telemetry

| Metric | Value |
| :--- | :--- |
| Prompt Tokens | 20,271 |
| Completion Tokens | 3,376 |
| Total Tokens | 23,647 |
| Estimated Cost (USD) | $0.0252 |

## Triage Perspective Metrics (Cascaded Tier 1)

| Metric | Mean | Std Dev |
| :--- | :--- | :--- |
| Potential Recall Ceiling | 1.0000 | 0.0000 |
| Potential F1 Ceiling | 0.9943 | 0.0049 |
| LLM Workload Ratio | 18.2% | - |
| Unrecoverable Loss | 0.0000 | - |
| Uncertain Purity | 19.3% | - |

## Iterations

| Iter | Status | Precision | Recall | F1 | Pot-R | Pot-F1 | Workload | Purity | TP | FP | FN | Time (s) | Mem (MB) | Tokens | Cost (USD) | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SUCCESS | 0.9832 | 0.8931 | 0.9360 | 1.0000 | 0.9915 | 18.5% | 18.9% | 117 | 2 | 14 | 0.6158 | 6.74 | 7917 | $0.0094 |  |
| 2 | SUCCESS | 1.0000 | 0.8931 | 0.9435 | 1.0000 | 1.0000 | 17.5% | 20.0% | 117 | 0 | 14 | 0.6456 | 6.71 | 7813 | $0.0063 |  |
| 3 | SUCCESS | 0.9832 | 0.8931 | 0.9360 | 1.0000 | 0.9915 | 18.5% | 18.9% | 117 | 2 | 14 | 0.5381 | 6.80 | 7917 | $0.0094 |  |

## Dynamic Thresholds

| Iter | Mode | Lower Threshold | Upper Threshold | Centroids (Low, Mid, High) |
| :--- | :--- | :--- | :--- | :--- |
| 3 | dynamic_skew | 0.4990 | 0.8168 | [0.3689, 0.6291, 0.9419] |

## LLM Strategy Configuration & Prompts

- **Model**: `gemini-3.8-flash`
- **Provider**: `google-cloud`
- **Latency**: `8.95s`
- **Log File**: `outputs/logs/llm_calls/20260919_165623_917501_IndexingConfigWeightedScoreMatchingConfig.json`

### LLM Output (Generated Strategy Configuration)

```json
{
  "reasoning": "Step 1: Column Selection and Exclusion\n- record_id: Excluded as it is a source-specific internal identifier.\n- rating_value: Excluded due to excessive missingness (>90% null in Source A, >99% null in Source B).\n- language, url, rating_star, seller, genre, page_id: Excluded as they exist only in Source A.\n- ISBN, review_count: Excluded as they exist only in Source B.\n- short_description: Contains over 42.8% nulls in Source A and 33.2% in Source B; also largely redundant with title and full description. Excluded in favor of full description.\n- date: While present in both, candidate pairs show varying granularity and inconsistent dates (e.g., '2008-06-30' vs '2008-06-01', '2014-12-16' vs '2014-12-01') which represent edition/release dates that fluctuate across platforms; omitted to avoid penalizing true matches when other stable attributes exist.\n\nStep 2: Selected Matching Columns Analysis\n1. title:\n- Exemplar Candidate Matches: Inspecting the exemplars shows consistent multi-word book titles across both datasets (e.g., 'blasted heaths and blessed green', 'les andes guide dalpinisme guide complet').\n- Statistical Profile: Null % is 0.0% in A and 0.02% in B; high uniqueness (~96-99%), avg length ~25-28 chars.\n- Algorithm Trade-off: Titles are multi-word phrases. 'cosine' provides robust token-level similarity resilient to minor word re-ordering or subtitle inclusions/omissions.\n- Weight Justification: Assigned a high descriptive weight of 0.75, being the primary distinguishing identifier for books.\n\n2. author:\n- Exemplar Candidate Matches: Demonstrates exact or near-exact person names (e.g., 'james w finegan', 'john biggar').\n- Statistical Profile: Low nulls (<0.2%), high cardinality (~74-76%), avg length ~15-19 chars.\n- Algorithm Trade-off: Author names are short person names where character-level alignment and prefix weighting are ideal; 'jarowinkler' handles small spelling variations, typos, or middle initial differences effectively, whereas cosine is brittle on short names.\n- Weight Justification: Assigned 0.60 as a strong primary descriptive identity attribute.\n\n3. description:\n- Exemplar Candidate Matches: Long narrative summaries; Source B frequently includes trailing UI tokens such as 'less'.\n- Statistical Profile: Extremely high uniqueness (>97%), avg length ~940-1030 characters, nulls <0.3%.\n- Algorithm Trade-off: 'cosine' TF-IDF similarity is the optimal choice for long multi-sentence texts, gracefully absorbing word additions or truncation artifacts (e.g., trailing 'less'). Edit distance algorithms fail on long strings.\n- Weight Justification: Assigned 0.65 as a decisive descriptive feature given its rich information content.\n\n4. publisher:\n- Exemplar Candidate Matches: Shows exact matches ('simon schuster') as well as occasional imprint/distribution differences ('nevicata' vs 'primento digital publishing').\n- Statistical Profile: 0% nulls in A, 0.02% in B, moderate cardinality (1667 in A, 662 in B), avg length 16-17 chars.\n- Algorithm Trade-off: Short brand/organization names suit 'jarowinkler' to handle minor punctuation, abbreviations, and suffix differences.\n- Weight Justification: Contextual/supporting attribute assigned 0.35.\n\n5. length (Page count):\n- Exemplar Candidate Matches: Matches exactly across exemplars ('288' \u2194 '288', '306' \u2194 '306').\n- Statistical Profile: 0% nulls, cardinality 537 / 617. Represents book page count.\n- Algorithm Trade-off: Page count is an integer count on a uniform interval scale; 'numeric_linear' computes standard absolute difference.\n- Weight Justification: Supporting contextual attribute assigned 0.30.\n\n6. price:\n- Exemplar Candidate Matches: Shows aligned monetary figures ('14.99' \u2194 '14.99', '5.99' \u2194 '5.99').\n- Statistical Profile: 0% nulls, numerical value spanning typical book pricing ranges.\n- Algorithm Trade-off: 'numeric_relative' measures percentage divergence, which is appropriate for prices across different price tiers.\n- Weight Justification: Supporting contextual attribute assigned 0.30.",
  "matching_columns": {
    "publisher": {
      "algorithm": "jarowinkler",
      "weight": 0.35
    },
    "length": {
      "algorithm": "numeric_linear",
      "weight": 0.3
    },
    "title": {
      "algorithm": "cosine",
      "weight": 0.75
    },
    "author": {
      "algorithm": "jarowinkler",
      "weight": 0.6
    },
    "price": {
      "algorithm": "numeric_relative",
      "weight": 0.3
    },
    "description": {
      "algorithm": "cosine",
      "weight": 0.65
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

