"""
Synthetic data generator for controlled Entity Resolution evaluation.

Generates two DataFrames (Source A and Source B) from a shared universe of
entities, with configurable overlap, noise, and null injection. The ground-truth
match pairs are returned alongside the DataFrames, enabling exact P/R/F1 evaluation.

## Named Schema Registry

Instead of accepting an arbitrary TableSchema, the generator uses a built-in
registry of domain-specific schemas, each with dedicated Faker providers:

    - "persons"   : Individual people — name, email, phone, city, address, birth_date
    - "companies" : Business entities — company_name, industry, city, country, revenue, founded_date
    - "products"  : Product catalog — product_name, brand, category, sku, unit_price, description

Extend the registry by adding a new entry to SYNTHETIC_SCHEMAS (see bottom of file).
"""

from __future__ import annotations

import random
import string
from typing import Callable, Dict, Any, Set, Tuple, List, Optional

import numpy as np
import pandas as pd
from faker import Faker
from pydantic import BaseModel, Field

from shared.schema_models import TableSchema, TableField
from .models import ColumnMatchConfig, SimilarityAlgorithm


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------

class _ColumnSpec:
    """
    Internal descriptor tying a column to its Faker generator and similarity algorithm.
    """
    __slots__ = ("field", "algorithm", "generator")

    def __init__(
        self,
        name: str,
        description: str,
        algorithm: SimilarityAlgorithm,
        generator: Callable[[Faker], Any],
        logical_type: str = "string"
    ):
        self.field = TableField(name=name, type=logical_type, description=description)
        self.algorithm = algorithm
        self.generator = generator


class SyntheticSchemaSpec:
    """
    A named, domain-specific schema spec: column definitions + Faker generators.
    Produces a TableSchema and a default ERPipelineConfiguration skeleton.
    """

    def __init__(self, name: str, description: str, columns: List[_ColumnSpec]):
        self.name = name
        self.description = description
        self._columns = columns

    def table_schema_fields(self) -> List[TableField]:
        """Return the TableField list for this spec."""
        return [c.field for c in self._columns]

    def table_schema(self) -> TableSchema:
        """Return the TableSchema for this spec (used by the ER pipeline)."""
        return TableSchema(fields=self.table_schema_fields())

    def default_matching_columns(self) -> Dict[str, ColumnMatchConfig]:
        """Return a sensible default matching_columns mapping for ERPipelineConfiguration."""
        return {
            c.field.name: ColumnMatchConfig(algorithm=c.algorithm, weight=1.0)
            for c in self._columns
        }

    def column_names(self) -> List[str]:
        return [c.field.name for c in self._columns]

    def generate_row(self, fake: Faker) -> Dict[str, Any]:
        return {c.field.name: c.generator(fake) for c in self._columns}


# ------------------------------------------------------------------
# Built-in named schemas
# --------------------------------------------------
_PERSONS_SCHEMA = SyntheticSchemaSpec(
    name="persons",
    description="Individual people — useful for customer deduplication across CRM systems.",
    columns=[
        _ColumnSpec("name",       "Full name of the person",           SimilarityAlgorithm.JAROWINKLER, lambda f: f.name()),
        _ColumnSpec("email",      "Email address",                     SimilarityAlgorithm.DAMERAU_LEVENSHTEIN,   lambda f: f.email()),
        _ColumnSpec("phone",      "Phone number",                      SimilarityAlgorithm.DAMERAU_LEVENSHTEIN,   lambda f: f.phone_number()),
        _ColumnSpec("city",       "City of residence",                 SimilarityAlgorithm.JAROWINKLER, lambda f: f.city()),
        _ColumnSpec("address",    "Full street address",               SimilarityAlgorithm.COSINE,  lambda f: f.street_address()),
        _ColumnSpec("birth_date", "Date of birth (ISO format)",        SimilarityAlgorithm.DATE,         lambda f: f.date_of_birth(minimum_age=18, maximum_age=85), "datetime"),
    ],
)

_COMPANIES_SCHEMA = SyntheticSchemaSpec(
    name="companies",
    description="Business entities — useful for supplier/vendor deduplication across procurement systems.",
    columns=[
        _ColumnSpec("company_name",  "Legal company name",                 SimilarityAlgorithm.JAROWINKLER, lambda f: f.company()),
        _ColumnSpec("industry",      "Industry sector",                    SimilarityAlgorithm.JAROWINKLER, lambda f: f.bs().split()[0].capitalize()),
        _ColumnSpec("city",          "City of headquarters",               SimilarityAlgorithm.JAROWINKLER, lambda f: f.city()),
        _ColumnSpec("country",       "Country of registration",            SimilarityAlgorithm.JAROWINKLER, lambda f: f.country()),
        _ColumnSpec("revenue",       "Annual revenue in USD",              SimilarityAlgorithm.NUMERIC_LINEAR,      lambda f: round(random.uniform(50_000, 50_000_000), 2), "number"),
        _ColumnSpec("founded_date",  "Year or date the company was founded", SimilarityAlgorithm.DATE,       lambda f: f.date_between(start_date="-60y", end_date="-1y"), "datetime"),
        _ColumnSpec("ein",           "Employer Identification Number",     SimilarityAlgorithm.DAMERAU_LEVENSHTEIN,   lambda f: f.ein() if hasattr(f, "ein") else f.bothify("##-#######")),
    ],
)

_PRODUCTS_SCHEMA = SyntheticSchemaSpec(
    name="products",
    description="Product catalog entries — useful for catalog deduplication across e-commerce or ERP systems.",
    columns=[
        _ColumnSpec("product_name", "Product name",                       SimilarityAlgorithm.JAROWINKLER, lambda f: f.catch_phrase()),
        _ColumnSpec("brand",        "Brand or manufacturer name",          SimilarityAlgorithm.JAROWINKLER, lambda f: f.company().split()[0]),
        _ColumnSpec("category",     "Product category",                   SimilarityAlgorithm.JAROWINKLER, lambda f: random.choice([
            "Electronics", "Clothing", "Food", "Furniture", "Books",
            "Sports", "Toys", "Beauty", "Automotive", "Garden",
        ])),
        _ColumnSpec("sku",          "Stock-Keeping Unit — unique product code", SimilarityAlgorithm.DAMERAU_LEVENSHTEIN, lambda f: f.bothify("??-####-??").upper()),
        _ColumnSpec("unit_price",   "Unit price in USD",                  SimilarityAlgorithm.NUMERIC_LINEAR,      lambda f: round(random.uniform(0.99, 4999.99), 2), "number"),
        _ColumnSpec("description",  "Short product description",          SimilarityAlgorithm.COSINE,  lambda f: f.sentence(nb_words=12)),
    ],
)


# Public registry — add new schemas here to extend the system.
SYNTHETIC_SCHEMAS: Dict[str, SyntheticSchemaSpec] = {
    "persons":   _PERSONS_SCHEMA,
    "companies": _COMPANIES_SCHEMA,
    "products":  _PRODUCTS_SCHEMA,
}


def get_schema_spec(schema_name: str) -> SyntheticSchemaSpec:
    """
    Retrieve a schema spec by name.

    Raises:
        ValueError: if the name is not in the registry.
    """
    if schema_name not in SYNTHETIC_SCHEMAS:
        available = ", ".join(f'"{k}"' for k in SYNTHETIC_SCHEMAS)
        raise ValueError(
            f"Unknown schema name '{schema_name}'. "
            f"Available schemas: {available}"
        )
    return SYNTHETIC_SCHEMAS[schema_name]


# Convenience alias kept for backward compatibility
def get_default_table_schema(schema_name: str = "persons") -> TableSchema:
    """Return the TableSchema for the given named schema (default: 'persons')."""
    return get_schema_spec(schema_name).table_schema()


# ---------------------------------------------------------------------------
# Configuration model
# ---------------------------------------------------------------------------

class SyntheticConfig(BaseModel):
    """
    Configuration for the synthetic data generator.

    Select a domain schema by name:
        - "persons"   : people records (name, email, phone, city, address, birth_date)
        - "companies" : business entities (company_name, industry, city, country, revenue, ...)
        - "products"  : catalog entries (product_name, brand, category, sku, unit_price, description)
    """
    schema_name: str = Field(
        default="persons",
        description=(
            "Name of the domain schema to use. "
            f"Available: {list(SYNTHETIC_SCHEMAS.keys())}. "
            "Extend by adding entries to SYNTHETIC_SCHEMAS."
        )
    )
    num_entities: int = Field(
        default=200,
        ge=10,
        description="Size of the shared 'universe' of entities."
    )
    overlap_ratio: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Fraction of entities that appear in BOTH sources — these are the true matches."
    )
    noise_level: str = Field(
        default="medium",
        description="Noise intensity applied to shared entities in Source B: 'none', 'low', 'medium', 'high'."
    )
    null_injection_rate: float = Field(
        default=0.05,
        ge=0.0,
        le=0.5,
        description="Fraction of non-key cells randomly set to NaN in both sources."
    )
    duplicate_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=0.3,
        description="Fraction of within-source duplicate rows to inject."
    )
    seed: Optional[int] = Field(
        default=42,
        description="Random seed for reproducibility. Set to None for non-deterministic results."
    )
    locale: str = Field(
        default="en_US",
        description="Locale for Faker and localized noise (e.g., 'en_US', 'it_IT')."
    )
    table_name: str = Field(
        default="entities",
        description="Label used in evaluation reports and console output."
    )

    def get_spec(self) -> SyntheticSchemaSpec:
        """Resolve and return the SyntheticSchemaSpec for this config."""
        return get_schema_spec(self.schema_name)


# ---------------------------------------------------------------------------
# Noise helpers
# ---------------------------------------------------------------------------

_NOISE_PROFILES = {
    "none":   {"typo": 0.00, "abbrev": 0.00, "case": 0.00, "keyboard": 0.00},
    "low":    {"typo": 0.05, "abbrev": 0.10, "case": 0.05, "keyboard": 0.02},
    "medium": {"typo": 0.15, "abbrev": 0.20, "case": 0.10, "keyboard": 0.05},
    "high":   {"typo": 0.35, "abbrev": 0.40, "case": 0.20, "keyboard": 0.15},
}

_NUMERIC_JITTER_PROFILES = {
    "none":   {"prob": 0.00, "jitter": 0.00},
    "low":    {"prob": 0.02, "jitter": 0.01},
    "medium": {"prob": 0.05, "jitter": 0.02},
    "high":   {"prob": 0.15, "jitter": 0.05},
}

_NULL_PROFILES = {
    "none":   0.00,
    "low":    0.02,
    "medium": 0.05,
    "high":   0.10,
}

_ABBREVIATIONS = {
    "en": {
        "common": {
            "street": "st.", "avenue": "ave.", "boulevard": "blvd.", "road": "rd.",
            "north": "n.", "south": "s.", "east": "e.", "west": "w.",
            "apartment": "apt.", "suite": "ste.", "building": "bldg.",
        },
        "persons": {
            "william": "wm.", "robert": "rob.", "junior": "jr.", "senior": "sr.",
            "mister": "mr.", "missus": "mrs.", "doctor": "dr.", "professor": "prof.",
        },
        "companies": {
            "incorporated": "inc.", "limited": "ltd.", "corporation": "corp.", "company": "co.",
            "management": "mgmt.", "solutions": "sol.", "international": "intl.", "technology": "tech.",
            "limited liability company": "llc.", "partners": "ptnrs.",
        },
        "products": {
            "kilogram": "kg", "liter": "l", "package": "pkg", "electronics": "elec.",
            "furniture": "furn.", "extra large": "xl", "medium": "med.", "small": "sm.",
        }
    },
    "it": {
        "common": {
            "viale": "v.le", "corso": "c.so", "piazza": "p.za", "frazione": "fraz.",
            "numero": "n.", "via": "v.", "interno": "int.", "scala": "sc.",
        },
        "persons": {
            "dottore": "dott.", "ragioniere": "rag.", "ingegnere": "ing.", "architetto": "arch.",
            "avvocato": "avv.", "geometra": "geom.", "professore": "prof.",
        },
        "companies": {
            "società": "soc.", "limitata": "ltd.", "industria": "ind.", "tecnologia": "tecno.",
            "per azioni": "spa.", "responsabilità": "resp.", "semplice": "s.s.",
        },
        "products": {
            "pezzi": "pz.", "scatola": "scat.", "elettronica": "elettron.", "grammi": "gr.",
            "centimetri": "cm.", "metri": "m.", "litri": "lt.",
        }
    }
}

_KEYBOARD_LAYOUTS = {
    "qwerty": {
        "q": "was", "w": "qeas", "e": "wrds", "r": "etdf", "t": "ryfg", "y": "tugh", "u": "yijh", "i": "uokj", "o": "ilpk", "p": "ol",
        "a": "qwsz", "s": "wedaxz", "d": "erfcxs", "f": "rtgvcd", "g": "tyhbvf", "h": "yujnbg", "j": "uikmnh", "k": "iolmj", "l": "opk",
        "z": "asx", "x": "zsdc", "c": "xdfv", "v": "cfgb", "b": "vghn", "n": "bhjm", "m": "njk",
        "1": "2q", "2": "13qw", "3": "24we", "4": "35er", "5": "46rt", "6": "57ty", "7": "68yu", "8": "79io", "9": "80op", "0": "9p",
        "-": "0p", " ": "cvbnm"
    }
}


def _apply_typo(s: str, rng: random.Random) -> str:
    if len(s) < 3:
        return s
    idx = rng.randint(0, len(s) - 1)
    op = rng.choice(["swap", "delete", "insert"])
    if op == "swap" and idx < len(s) - 1:
        chars = list(s)
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
        return "".join(chars)
    elif op == "delete":
        return s[:idx] + s[idx + 1:]
    else:
        return s[:idx] + rng.choice(string.ascii_lowercase) + s[idx:]


def _apply_keyboard_noise(s: str, rng: random.Random) -> str:
    if len(s) < 3:
        return s
    idx = rng.randint(0, len(s) - 1)
    char = s[idx].lower()
    layout = _KEYBOARD_LAYOUTS["qwerty"]  # Default to qwerty for now
    if char in layout:
        replacement = rng.choice(layout[char])
        if s[idx].isupper():
            replacement = replacement.upper()
        return s[:idx] + replacement + s[idx + 1:]
    return s


def _apply_abbreviation(s: str, locale: str, schema_name: str, rng: random.Random) -> str:
    lang = locale.split("_")[0].lower()
    locale_map = _ABBREVIATIONS.get(lang, _ABBREVIATIONS["en"])
    
    # Merge common and schema-specific abbreviations
    mapping = locale_map.get("common", {}).copy()
    if schema_name in locale_map:
        mapping.update(locale_map[schema_name])

    words = s.split()
    new_words = []
    for word in words:
        # Strip punctuation for lookup but preserve it in result if possible
        clean_word = word.lower().rstrip(".,")
        if clean_word in mapping and rng.random() < 0.6:
            abbrev = mapping[clean_word]
            # Handle casing
            if word.isupper():
                res = abbrev.upper()
            elif word.istitle():
                res = abbrev.capitalize()
            else:
                res = abbrev
            new_words.append(res)
        else:
            new_words.append(word)
    return " ".join(new_words)


def _apply_case_noise(s: str, rng: random.Random) -> str:
    choice = rng.choice(["upper", "lower", "title"])
    return {"upper": s.upper, "lower": s.lower, "title": s.title}[choice]()


def _noisify_string(value: str, noise_level: str, locale: str, schema_name: str, rng: random.Random) -> str:
    if not isinstance(value, str) or not value.strip():
        return value
    profile = _NOISE_PROFILES.get(noise_level, _NOISE_PROFILES["medium"])
    if rng.random() < profile["typo"]:
        value = _apply_typo(value, rng)
    if rng.random() < profile["keyboard"]:
        value = _apply_keyboard_noise(value, rng)
    if rng.random() < profile["abbrev"]:
        value = _apply_abbreviation(value, locale, schema_name, rng)
    if rng.random() < profile["case"]:
        value = _apply_case_noise(value, rng)
    return value


def _inject_nulls(df: pd.DataFrame, rate: float, rng: random.Random) -> pd.DataFrame:
    if rate <= 0:
        return df
    df = df.copy()
    for col in df.columns:
        mask = pd.Series([rng.random() < rate for _ in range(len(df))], index=df.index)
        df.loc[mask, col] = np.nan
    return df


# ---------------------------------------------------------------------------
# Universe builder (schema-driven)
# ---------------------------------------------------------------------------

def _build_universe(num_entities: int, spec: SyntheticSchemaSpec, rng: random.Random, fake: Faker) -> pd.DataFrame:
    """Generate N canonical entity records using the given schema spec's Faker generators."""
    rows = [spec.generate_row(fake) for _ in range(num_entities)]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_synthetic_pair(
    config: SyntheticConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame, Set[Tuple[int, int]]]:
    """
    Generate a synthetic pair of DataFrames from a shared entity universe.

    The schema is determined by ``config.schema_name`` — one of:
    "persons", "companies", "products" (or any custom entry in SYNTHETIC_SCHEMAS).

    Returns:
        df_a          : Source A DataFrame (integer index).
        df_b          : Source B DataFrame (integer index, noisy copies of shared entities).
        ground_truth  : Set of (idx_a, idx_b) tuples — the known true match pairs.
    """
    spec = config.get_spec()

    seed = config.seed
    rng = random.Random(seed)
    fake = Faker(config.locale)
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)

    n = config.num_entities
    n_shared = max(1, int(round(n * config.overlap_ratio)))
    n_only_a = n - n_shared
    n_only_b = n - n_shared

    # Build universe using spec's generators
    universe = _build_universe(n + n_only_b, spec, rng, fake)

    shared_universe = universe.iloc[:n_shared].reset_index(drop=True)
    only_a_universe = universe.iloc[n_shared: n_shared + n_only_a].reset_index(drop=True)
    only_b_universe = universe.iloc[n_shared + n_only_a:].reset_index(drop=True)

    # Apply noise to shared entities for Source B
    noisy_shared_rows = []
    jitter_cfg = _NUMERIC_JITTER_PROFILES.get(config.noise_level, _NUMERIC_JITTER_PROFILES["medium"])

    for _, row in shared_universe.iterrows():
        noisy_row = {}
        for col, val in row.items():
            if isinstance(val, str):
                noisy_row[col] = _noisify_string(val, config.noise_level, config.locale, config.schema_name, rng)
            elif isinstance(val, (int, float)) and rng.random() < jitter_cfg["prob"]:
                j = jitter_cfg["jitter"]
                noisy_row[col] = round(val * rng.uniform(1 - j, 1 + j), 2)
            else:
                noisy_row[col] = val
        noisy_shared_rows.append(noisy_row)

    noisy_shared_df = pd.DataFrame(noisy_shared_rows)

    # Attach entity IDs for ground-truth tracking
    shared_universe = shared_universe.copy()
    shared_universe["__entity_id__"] = range(n_shared)

    only_a_universe = only_a_universe.copy()
    only_a_universe["__entity_id__"] = range(n_shared, n_shared + n_only_a)

    only_b_universe = only_b_universe.copy()
    only_b_universe["__entity_id__"] = range(n_shared + n_only_a, n_shared + n_only_a + n_only_b)

    noisy_shared_with_id = noisy_shared_df.copy()
    noisy_shared_with_id["__entity_id__"] = range(n_shared)

    df_a_tracked = pd.concat([shared_universe, only_a_universe], ignore_index=True)
    df_a_tracked = df_a_tracked.sample(frac=1, random_state=seed).reset_index(drop=True)

    df_b_tracked = pd.concat([noisy_shared_with_id, only_b_universe], ignore_index=True)
    df_b_tracked = df_b_tracked.sample(frac=1, random_state=(seed or 0) + 1).reset_index(drop=True)

    # Build ground-truth from entity ID positions
    a_entity_to_idx = {row["__entity_id__"]: idx for idx, row in df_a_tracked.iterrows() if row["__entity_id__"] < n_shared}
    b_entity_to_idx = {row["__entity_id__"]: idx for idx, row in df_b_tracked.iterrows() if row["__entity_id__"] < n_shared}

    ground_truth: Set[Tuple[int, int]] = {
        (a_entity_to_idx[eid], b_entity_to_idx[eid])
        for eid in range(n_shared)
        if eid in a_entity_to_idx and eid in b_entity_to_idx
    }

    df_a_final = df_a_tracked.drop(columns=["__entity_id__"])
    df_b_final = df_b_tracked.drop(columns=["__entity_id__"])

    # Null injection (scale with noise_level if default 0.05 is used, else respect override)
    null_rate = config.null_injection_rate
    if null_rate == 0.05: # Default value
        null_rate = _NULL_PROFILES.get(config.noise_level, 0.05)

    df_a_final = _inject_nulls(df_a_final, null_rate, rng)
    df_b_final = _inject_nulls(df_b_final, null_rate, rng)

    # Duplicate injection
    if config.duplicate_rate > 0:
        df_a_final = _inject_duplicates(df_a_final, config.duplicate_rate, rng)
        df_b_final = _inject_duplicates(df_b_final, config.duplicate_rate, rng)

    return df_a_final, df_b_final, ground_truth


def _inject_duplicates(df: pd.DataFrame, rate: float, rng: random.Random) -> pd.DataFrame:
    n_dups = max(1, int(round(len(df) * rate)))
    dup_indices = [rng.randint(0, len(df) - 1) for _ in range(n_dups)]
    dups = df.iloc[dup_indices].copy()
    return pd.concat([df, dups], ignore_index=True)
