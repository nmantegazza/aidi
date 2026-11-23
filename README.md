# AIDI — Agentic AI for Data Integration

**Master of Science in Computer Science and Engineering — Ingegneria Informatica**  
**Politecnico di Milano — Academic Year 2025–2026**

- **Candidate**: Niccolò Mantegazza
- **Supervisor**: Prof.ssa Cinzia Cappiello

---

## 1. Thesis Documents

The complete thesis deliverables are available in [`docs/`](docs/):

- **Full Thesis**: [`docs/thesis.pdf`](docs/thesis.pdf)
- **Executive Summary**: [`docs/executive-summary.pdf`](docs/executive-summary.pdf)
- **Defense Presentation**: [`docs/presentation.pdf`](docs/presentation.pdf)

---

## 2. Overview

**AIDI** (*Agentic AI for Data Integration*) is an end-to-end, LLM-powered data integration pipeline that couples specialized LLM meta-reasoners with deterministic relational execution engines. The architecture comprises three decoupled, modular subsystems and an end-to-end orchestrator:

1. **Schema Integration** (`src/schema_integration`): 3-stage schema alignment, mapping synthesis, and relational execution.
2. **Entity Resolution** (`src/entity_resolution`): Two-tier record linkage combining deterministic indexing (TF-IDF, Q-Gram, Sorted Neighborhood, MinHash LSH) and missing-aware weighted similarity scoring with selective LLM boundary disambiguation.
3. **Data Fusion** (`src/data_fusion`): Two-phase conflict resolution using offline LLM policy synthesis and vectorized execution.
4. **End-to-End Orchestrator** (`src/pipeline`): Unified CLI and interactive Gradio wizard interface.

---

## 3. Repository Layout

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
├── data/                              # Curated benchmark evaluation datasets (see data/ATTRIBUTION.md)
│   ├── entity_resolution/datasets/    # 8 ER benchmark datasets (DBLP-ACM, Amazon-Walmart, FEBRL, etc.)
│   ├── data_fusion/processed/         # 3 bipartite fusion benchmarks (Books, Flights, Stocks)
│   ├── schema_alignment/              # SchemaNet alignment benchmarks
│   ├── schema_mapping/                # Single-table and multi-table mapping benchmarks
│   └── test_cases/running_example/    # Multi-table end-to-end running example
│
├── outputs/                           # Pre-computed thesis evaluation results and logs
│   ├── data-fusion/                   # Final metrics, summaries, and traces
│   ├── entity-res-indexing/           # Indexing reduction ratios, pair completeness, runtime
│   ├── entity-res-matching/           # Matching F1, precision, recall, and cost traces
│   ├── schema-alignment/              # Alignment accuracy and token expenditure
│   └── schema-mapping/                # Mapping correctness, operator aggregates, and summaries
│
├── tests/                             # pytest unit and integration test suite
├── pyproject.toml                     # Package metadata, dependencies, and CLI entrypoints
├── uv.lock                            # Exact lockfile for deterministic reproducibility
├── .env.example                       # Template for LLM provider API keys
├── CITATION.cff                       # Academic citation metadata
└── LICENSE                            # MIT License
```

---

## 4. Installation & Setup

The project uses [`uv`](https://docs.astral.sh/uv/) for deterministic dependency management. Python **>= 3.10** is required.

### 4.1 Install `uv` (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 4.2 Install Dependencies
Clone the repository and run:
```bash
uv sync
```
This creates a virtual environment and installs all dependencies pinned in `uv.lock`.

### 4.3 Configure Environment Variables (Optional for Inspection)
To execute live LLM calls, copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Populate `.env` with the API keys for the providers you want to use (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `MISTRAL_API_KEY`, `DEEPSEEK_API_KEY`, and optionally `HF_TOKEN`).  
*Note: Live API keys are only needed to generate new runs; all thesis evaluation runs are pre-computed in [`outputs/`](outputs/).*

---

## 5. Thesis Evaluation Results (`outputs/`)

The benchmark outputs and metrics reported in **Chapter 5 (Evaluation)** of [`docs/thesis.pdf`](docs/thesis.pdf) are preserved in `outputs/`:

| Subsystem | Location | Available Files |
| :--- | :--- | :--- |
| **Data Fusion** | [`outputs/data-fusion/`](outputs/data-fusion/) | `summary.csv`, `summary.json`, `summary.md`, per-dataset traces |
| **ER Indexing** | [`outputs/entity-res-indexing/`](outputs/entity-res-indexing/) | `summary.csv`, `summary.json`, `summary.md` |
| **ER Matching** | [`outputs/entity-res-matching/`](outputs/entity-res-matching/) | `summary.csv`, `summary.json`, `summary.md`, `figure_5_8_data.json` |
| **Schema Alignment** | [`outputs/schema-alignment/`](outputs/schema-alignment/) | `summary.csv`, `summary.json`, `summary.md` |
| **Schema Mapping** | [`outputs/schema-mapping/`](outputs/schema-mapping/) | `summary.csv`, `summary.json`, `summary.md`, `ops_aggregates.json` |

You can inspect the summary markdown tables directly:
```bash
cat outputs/entity-res-matching/summary.md
cat outputs/data-fusion/summary.md
```

---

## 6. Reproducing Benchmarks

All evaluation harnesses are exposed as standalone CLI commands via `pyproject.toml`:

### 6.1 Entity Resolution Benchmarks
```bash
# Run ER Indexing / Blocking benchmark
uv run er-index-benchmark --datasets febrl1 DBLP-ACM

# Run ER Matching benchmark
uv run er-matching-benchmark --datasets febrl1 --strategies weighted ecm

# Run complete ER benchmark harness
uv run er-benchmark --datasets febrl1
```

### 6.2 Data Fusion Benchmarks
```bash
# Run Data Fusion benchmark across baseline strategies and LLM models
uv run df-benchmark --datasets books flights stocks
```

### 6.3 Schema Integration Benchmarks
```bash
# Run Schema Alignment benchmark (SchemaNet pairs)
uv run si-alignment-benchmark

# Run Schema Mapping benchmark (Single & Multi-table)
uv run si-mapping-benchmark
```

---

## 7. Running Tests

```bash
# Run the entire test suite
uv run pytest

# Run a specific module test suite
uv run pytest tests/test_data_fusion_execution_engine.py
uv run pytest tests/test_entity_resolution.py
```

---

## 8. Interactive Pipeline & GUI

Run the complete end-to-end integration pipeline:

```bash
# Run CLI mode on the running example
uv run integration data/test_cases/running_example

# Launch the interactive Gradio Web GUI
uv run integration --gui
```

---

## 9. Dataset Attribution

> **Attribution:** The benchmark datasets in [`data/`](data/) are curated from established academic benchmarks (University of Leipzig, Magellan, FEBRL, Dong et al., SchemaNet, and Valentine). All third-party datasets remain the property of their respective authors — see [`data/ATTRIBUTION.md`](data/ATTRIBUTION.md) for full references and credits.
