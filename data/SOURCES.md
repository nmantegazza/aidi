# Dataset Sources

The evaluation datasets in `data/` were downloaded from the following public repositories and packages:

- **Schema alignment and multi-table mapping (`data/schema_alignment/`, `data/schema_mapping/multi_table/`)**
  - `bank1-bank2`, `imdb-sakila`, `synthea-omop` (SchemaNet): downloaded from the LLMatch repository (`https://github.com/knowledge-fusion/LLMatch`).

- **Single-table schema mapping (`data/schema_mapping/single_table/`)**
  - `Musicians_unionable`, `assays_both_0_70_ac3_av`, `miller2_both_50_50_ac5_av`, `prospect_both_50_50_ac5_av`: downloaded from the Valentine benchmark suite (`https://delftdata.github.io/valentine/`).

- **Entity resolution (`data/entity_resolution/datasets/`)**
  - `DBLP-ACM`: downloaded from the University of Leipzig Database Group benchmark portal (`https://dbs.uni-leipzig.de/research/projects/benchmark-datasets-for-entity-resolution`).
  - `amazon-walmart`, `fodors-zagats`, `itunes-apple`, `itunes-ebooks`, `rogerebert-imdb`: downloaded from the Magellan Data Repository (`https://sites.google.com/site/anhaidgroup/useful-stuff/the-magellan-data-repository`) and DeepMatcher (`https://github.com/anhaidgroup/deepmatcher/blob/master/Datasets.md`).
  - `febrl1`, `febrl4`: exported from the `recordlinkage.datasets` Python package (`https://recordlinkage.readthedocs.io/`).

- **Data fusion (`data/data_fusion/processed/`)**
  - `books`, `flights`, `stocks`: downloaded from Xin Luna Dong's Truth Discovery datasets (`http://lunadong.com/fusionDataSets.htm`).

- **Running example (`data/test_cases/running_example/`)**
  - Synthetic multi-table dataset created for this thesis.
