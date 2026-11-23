# AIDI: Agentic AI for Data Integration

Master of Science in Computer Science and Engineering (Ingegneria Informatica), Politecnico di Milano, Academic Year 2025/2026.

Candidate: Niccolò Mantegazza  
Supervisor: Prof.ssa Cinzia Cappiello

## 1. Thesis documents

The thesis deliverables are in [`docs/`](docs/):

- Full thesis: [`docs/thesis.pdf`](docs/thesis.pdf)
- Executive summary: [`docs/executive-summary.pdf`](docs/executive-summary.pdf)
- Defense presentation: [`docs/presentation.pdf`](docs/presentation.pdf)

## 2. Overview

AIDI (Agentic AI for Data Integration) is an LLM-driven data integration pipeline that pairs LLM meta-reasoners with deterministic relational execution engines. It consists of three decoupled subsystems and a pipeline orchestrator:

1. Schema Integration (`src/schema_integration`): three-stage schema alignment, mapping synthesis, and relational execution.
2. Entity Resolution (`src/entity_resolution`): two-tier record linkage combining deterministic indexing (TF-IDF, Q-Gram, Sorted Neighborhood, MinHash LSH) and missing-aware weighted similarity scoring with selective LLM disambiguation on uncertain pairs.
3. Data Fusion (`src/data_fusion`): two-phase conflict resolution using offline LLM policy synthesis and vectorized execution.
4. Orchestrator (`src/pipeline`): unified CLI and Gradio wizard interface.

## 3. Repository layout

```text
.
├── docs/                              # Thesis PDF, executive summary, and defense slides
│   ├── thesis.pdf
│   ├── executive-summary.pdf
│   └── presentation.pdf
│
├── src/                               # Core Python source packages
│   ├── schema_integration/            # Schema alignment, mapping, and execution
│   ├── entity_resolution/             # Indexing, blocking, similarity, and matching
│   │   └── benchmarking/              # ER benchmark runners and metrics evaluator
│   ├── data_fusion/                   # Conflict resolution engine and policy synthesizer
│   │   └── benchmarking/              # Data fusion benchmark runners and loaders
│   ├── pipeline/                      # End-to-end pipeline orchestrator & Gradio GUI
│   └── shared/                        # Cross-cutting utilities (LLM agents, models, config)
│
├── data/                              # Benchmark evaluation datasets (see data/ATTRIBUTION.md)
│   ├── entity_resolution/datasets/    # 8 ER datasets (DBLP-ACM, amazon-walmart, febrl1/4, etc.)
│   ├── data_fusion/processed/         # 3 bipartite fusion datasets (books, flights, stocks)
│   ├── schema_alignment/              # SchemaNet alignment benchmarks
│   ├── schema_mapping/                # Single-table and multi-table mapping benchmarks
│   └── test_cases/running_example/    # Multi-table running example
│
├── outputs/                           # Saved thesis evaluation results and logs
│   ├── data-fusion/                   # Final metrics, summaries, and traces
│   ├── entity-res-indexing/           # Indexing reduction ratios, pair completeness, runtime
│   ├── entity-res-matching/           # Matching F1, precision, recall, and cost traces
│   ├── schema-alignment/              # Alignment accuracy and token expenditure
│   └── schema-mapping/                # Mapping correctness, operator aggregates, and summaries
│
├── tests/                             # pytest unit and integration test suite
├── pyproject.toml                     # Package metadata, dependencies, and CLI entrypoints
├── uv.lock                            # Exact lockfile for dependency reproducibility
├── .env.example                       # Template for LLM provider API keys
├── CITATION.cff                       # Academic citation metadata
└── LICENSE                            # MIT License
```

## 4. Installation and setup

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management and requires Python >= 3.10.

### 4.1 Install `uv`
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 4.2 Install dependencies
Clone the repository and run:
```bash
uv sync
```
This creates a virtual environment and installs the dependencies pinned in `uv.lock`.

### 4.3 Configure environment variables (optional)
To run live LLM calls, copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add API keys for the providers you want to run (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `MISTRAL_API_KEY`, `DEEPSEEK_API_KEY`, and optionally `HF_TOKEN`). Live API keys are only needed to generate new runs; all thesis evaluation outputs are already saved in [`outputs/`](outputs/).

## 5. Thesis evaluation results (`outputs/`)

The benchmark outputs and metrics reported in Chapter 5 (Evaluation) of [`docs/thesis.pdf`](docs/thesis.pdf) are stored in `outputs/`:

| Subsystem | Location | Available Files |
| :--- | :--- | :--- |
| Data Fusion | [`outputs/data-fusion/`](outputs/data-fusion/) | `summary.csv`, `summary.json`, `summary.md`, per-dataset traces |
| ER Indexing | [`outputs/entity-res-indexing/`](outputs/entity-res-indexing/) | `summary.csv`, `summary.json`, `summary.md` |
| ER Matching | [`outputs/entity-res-matching/`](outputs/entity-res-matching/) | `summary.csv`, `summary.json`, `summary.md`, `figure_5_8_data.json` |
| Schema Alignment | [`outputs/schema-alignment/`](outputs/schema-alignment/) | `summary.csv`, `summary.json`, `summary.md` |
| Schema Mapping | [`outputs/schema-mapping/`](outputs/schema-mapping/) | `summary.csv`, `summary.json`, `summary.md`, `ops_aggregates.json` |

To inspect the summary tables directly:
```bash
cat outputs/entity-res-matching/summary.md
cat outputs/data-fusion/summary.md
```

## 6. Reproducing benchmarks

All evaluation harnesses are registered as CLI commands in `pyproject.toml`:

### 6.1 Entity resolution benchmarks
```bash
# Run ER Indexing / Blocking benchmark
uv run er-index-benchmark --datasets febrl1 DBLP-ACM

# Run ER Matching benchmark
uv run er-matching-benchmark --datasets febrl1 --strategies weighted ecm

# Run complete ER benchmark harness
uv run er-benchmark --datasets febrl1
```

### 6.2 Data fusion benchmarks
```bash
# Run Data Fusion benchmark across baseline strategies and LLM models
uv run df-benchmark --datasets books flights stocks
```

### 6.3 Schema integration benchmarks
```bash
# Run Schema Alignment benchmark (SchemaNet pairs)
uv run si-alignment-benchmark

# Run Schema Mapping benchmark (Single & Multi-table)
uv run si-mapping-benchmark
```

## 7. Running tests

```bash
# Run the entire test suite
uv run pytest

# Run a specific module test suite
uv run pytest tests/test_data_fusion_execution_engine.py
uv run pytest tests/test_entity_resolution.py
```

## 8. Interactive pipeline and GUI

Run the full integration pipeline on the running example:

```bash
# Run CLI mode on the running example
uv run integration data/test_cases/running_example

# Launch the interactive Gradio Web GUI
uv run integration --gui
```

## 9. Dataset attribution

> **Attribution:** The benchmark datasets in [`data/`](data/) come from established academic benchmarks: SchemaNet (Wang et al., 2025), Valentine (Koutras et al., 2021), the Leipzig ER benchmarks (Köpcke et al., 2010), the Magellan and DeepMatcher repositories (Konda et al., 2016; Mudgal et al., 2018), FEBRL (Christen, 2008), and Xin Luna Dong's Truth Discovery repository (Dong and Naumann, 2009; Li et al., 2012). All third-party datasets remain the property of their respective authors. Full references are listed in [`data/ATTRIBUTION.md`](data/ATTRIBUTION.md).
