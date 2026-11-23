# Benchmark Dataset Attribution

The `data/` directory bundles processed evaluation datasets used in the AIDI thesis experiments. All third-party datasets remain the property of their respective authors and are included here solely for academic reproducibility.

- **Entity Resolution (`data/entity_resolution/datasets/`)**
  - **DBLP-ACM, DBLP-GoogleScholar, Abt-Buy, Amazon-Google:** Kopcke et al., *Evaluation of Entity Resolution Approaches on Real-World Match Problems*, VLDB 2010 (University of Leipzig Benchmark Datasets).
  - **Amazon-Walmart, iTunes-Amazon (Music), iTunes-eBooks:** Mudgal et al., *Deep Learning for Entity Matching: A Design Space Exploration*, SIGMOD 2018 (Magellan Data Repository).
  - **FEBRL:** Christen, *A Comparison of Personal Name Matching: Techniques and Practical Issues*, ICDM Workshops 2006 (Freely Extensible Biomedical Record Linkage).

- **Data Fusion (`data/data_fusion/processed/`)**
  - **Books, Flights, Stocks:** Dong et al., *Truth Discovery and Data Fusion* benchmark datasets (Luna Dong / AT&T Labs & University of Waterloo).

- **Schema Alignment & Mapping (`data/schema_alignment/`, `data/schema_mapping/`)**
  - **SchemaNet:** Schema alignment benchmark pairs.
  - **Valentine / Miller2 Benchmarks:** Koutras et al., *Valentine: Evaluating Matching Techniques for Dataset Discovery*, ICDE 2021.

- **End-to-End Running Example (`data/test_cases/running_example/`)**
  - Custom multi-table synthetic test case created for this thesis.
