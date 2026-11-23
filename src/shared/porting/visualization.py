from __future__ import annotations
from typing import List
from shared.porting.models import (
    Transformation,
    ConstructionRecipe,
    SingleTable,
    JoinTables,
)

def format_transformation(trans: Transformation) -> str:
    """
    Formats a single AST Transformation operation into a human-readable string.
    """
    if trans.type == "direct":
        return f"DirectMap({trans.source_column})"
    elif trans.type == "concat":
        cols_str = ", ".join(trans.source_columns)
        return f"Concat({cols_str}; delimiter='{trans.delimiter}')"
    elif trans.type == "split":
        return f"Split({trans.source_column}; delimiter='{trans.delimiter}', index={trans.index})"
    elif trans.type == "slice":
        return f"Slice({trans.source_column}; start={trans.start}, end={trans.end})"
    elif trans.type == "type_cast":
        return f"TypeCast({trans.source_column} -> {trans.target_type})"
    elif trans.type == "math_operation":
        return f"Math({trans.source_column} {trans.operator} {trans.operand})"
    else:
        return str(trans)

def format_column_transformations(trans_list: List[Transformation], source_label: str) -> str:
    """
    Formats a sequence of transformations corresponding to a specific source label.
    """
    relevant = [t for t in trans_list if t.source_label == source_label]
    if not relevant:
        return "N/A"
    
    formatted = [format_transformation(t) for t in relevant]
    return " -> ".join(formatted)

def format_construction_recipe(recipe: ConstructionRecipe) -> str:
    """
    Formats a table ConstructionRecipe into a descriptive text sentence.
    """
    if recipe.type == "single":
        return f"Load table `{recipe.table_name}` from `{recipe.source_label}`"
    elif recipe.type == "join":
        join_str = recipe.join_type.upper()
        return (
            f"{join_str} JOIN between table `{recipe.left_table}` (`{recipe.left_source}`) "
            f"and table `{recipe.right_table}` (`{recipe.right_source}`) "
            f"on `{recipe.left_on}` = `{recipe.right_on}`"
        )
    else:
        return str(recipe)
