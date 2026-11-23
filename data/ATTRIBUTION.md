# Benchmark Dataset Attribution

The `data/` directory bundles processed evaluation datasets used in Chapter 5 of the thesis. All third-party datasets remain the property of their respective authors and are included here solely for academic reproducibility.

- **Schema Alignment and Multi-Table Mapping (`data/schema_alignment/`, `data/schema_mapping/multi_table/`)**
  - **SchemaNet (`bank1-bank2`, `imdb-sakila`, `synthea-omop`):** Wang et al., *LLMATCH: a Unified Schema Matching Framework with Large Language Models*, APWeb-WAIM 2025 (`https://github.com/knowledge-fusion/LLMatch`).

- **Single-Table Schema Mapping (`data/schema_mapping/single_table/`)**
  - **Valentine (`Musicians_unionable`, `assays_both_0_70_ac3_av`, `miller2_both_50_50_ac5_av`, `prospect_both_50_50_ac5_av`):** Koutras et al., *Valentine: Evaluating Matching Techniques for Dataset Discovery*, ICDE 2021 (`https://delftdata.github.io/valentine/`).

- **Entity Resolution (`data/entity_resolution/datasets/`)**
  - **`DBLP-ACM`:** Köpcke, Thor, and Rahm, *Evaluation of entity resolution approaches on real-world match problems*, PVLDB 2010 (Database Group Leipzig Benchmark Repository).
  - **`amazon-walmart`, `fodors-zagats`, `itunes-apple`, `itunes-ebooks`, `rogerebert-imdb`:** Magellan Data Repository (Das et al., 2016; Konda et al., *Magellan: Toward Building Entity Matching Management Systems*, PVLDB 2016) and the DeepMatcher Benchmark Suite (Mudgal et al., *Deep Learning for Entity Matching: A Design Space Exploration*, SIGMOD 2018).
  - **`febrl1`, `febrl4`:** Christen, *Febrl: A Freely Available Record Linkage System with a Graphical User Interface*, HDKM 2008.

- **Data Fusion (`data/data_fusion/processed/`)**
  - Sourced from Xin Luna Dong's Truth Discovery repository (`http://lunadong.com/fusionDataSets.htm`):
    - **`books`:** Dong and Naumann, *Data Fusion: Resolving Data Conflicts for Integration*, VLDB 2009; Yin et al., *Truth Discovery with Multiple Conflicting Information Providers on the Web*, TKDE 2008.
    - **`flights`, `stocks`:** Li et al., *Truth Finding on the Deep Web: Is the Problem Solved?*, PVLDB 2012.

- **Running Example (`data/test_cases/running_example/`)**
  - Synthetic multi-table test case created for this thesis.
