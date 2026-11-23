"""Mermaid diagram visualizers for benchmark schemas and alignments."""

from __future__ import annotations

import re

from shared.schema_models import DataPackage


def _sanitize_id(text: str) -> str:
    """Sanitize string to produce a safe Mermaid entity/column identifier."""
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", text.strip())
    # Ensure it doesn't start with a digit
    if cleaned and cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    return cleaned or "entity"


def _sanitize_type(raw_type: str | None) -> str:
    """Sanitize data type for Mermaid ER diagrams."""
    if not raw_type:
        return "string"
    # Map common variations to single-word valid types
    t = raw_type.strip().lower()
    t = re.sub(r"\(.*\)", "", t).strip()
    t = re.sub(r"[^a-zA-Z0-9_]", "_", t)
    return t or "string"


def _escape_comment(text: str | None) -> str:
    """Escape comments for Mermaid ER attribute strings."""
    if not text:
        return ""
    cleaned = text.replace('"', "'").replace("\n", " ").strip()
    # Truncate long descriptions to keep diagrams compact
    if len(cleaned) > 40:
        cleaned = cleaned[:37] + "..."
    return f'"{cleaned}"'


def generate_schema_er_mermaid(pkg: DataPackage) -> str:
    """Generate a Mermaid erDiagram representing a DataPackage schema.

    Visualizes tables as entities with columns, data types, PK/FK flags,
    and relational links for foreign keys.

    Args:
        pkg: DataPackage containing resources and schema definitions.

    Returns:
        Formatted Mermaid erDiagram string.
    """
    if not pkg.resources:
        return "erDiagram\n    EMPTY_SCHEMA {\n        string none\n    }"

    lines: list[str] = ["erDiagram"]
    declared_entities: set[str] = set()

    for res in pkg.resources:
        entity_name = _sanitize_id(res.name)
        declared_entities.add(entity_name)
        lines.append(f"    {entity_name} {{")

        pk_cols = {
            str(c).strip().lower()
            for c in res.schema_info.primary_key_columns
        }

        fk_cols: dict[str, str] = {}
        for fk in res.schema_info.foreignKeys:
            fk_fields = [fk.fields] if isinstance(fk.fields, str) else fk.fields
            ref_tbl = fk.reference.resource
            for f in fk_fields:
                fk_cols[str(f).strip().lower()] = ref_tbl

        for field in res.schema_info.fields:
            f_name_clean = _sanitize_id(field.name)
            f_type_clean = _sanitize_type(field.type)
            f_lower = field.name.strip().lower()

            is_pk = f_lower in pk_cols
            is_fk = f_lower in fk_cols

            key_label = ""
            if is_pk and is_fk:
                key_label = "PK,FK"
            elif is_pk:
                key_label = "PK"
            elif is_fk:
                key_label = "FK"

            # Optional comment
            comment = _escape_comment(field.description)
            parts = [f"        {f_type_clean}", f_name_clean]
            if key_label:
                parts.append(key_label)
            if comment:
                parts.append(comment)

            lines.append(" ".join(parts))

        lines.append("    }")

    # Render relationships for foreign keys
    for res in pkg.resources:
        src_entity = _sanitize_id(res.name)
        for fk in res.schema_info.foreignKeys:
            ref_entity = _sanitize_id(fk.reference.resource)
            fk_fields = [fk.fields] if isinstance(fk.fields, str) else fk.fields
            fk_lbl = ", ".join(str(f) for f in fk_fields)
            if ref_entity in declared_entities:
                lines.append(f'    {src_entity} }}o--|| {ref_entity} : "{fk_lbl}"')

    return "\n".join(lines)


def generate_source_schemas_mermaid(
    source_a: DataPackage,
    source_b: DataPackage,
) -> str:
    """Generate ER diagrams for Source A and Source B packages.

    Args:
        source_a: First source DataPackage.
        source_b: Second source DataPackage.

    Returns:
        Formatted Mermaid erDiagram string.
    """
    # Combine or return individual diagrams
    return generate_schema_er_mermaid(source_a)
