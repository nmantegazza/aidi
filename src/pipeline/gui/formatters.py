import pandas as pd

def format_profiles_md(profiles):
    """Converts profiling metadata into a concise markdown summary for the UI."""
    if not profiles:
        return "*Awaiting data ingestion...*"
    
    md = "#### Enhanced Data Profile\n\n"
    for table_name, profile in profiles.items():
        md += f"### Table: {table_name} ({profile.total_rows:,} rows)\n\n"
        
        for col_name in sorted(profile.column_profiles.keys()):
            p = profile.column_profiles[col_name]
            md += f"#### Column: `{col_name}`\n"
            md += f"- **Type:** `{p.dtype}` | **Nulls:** {p.null_percentage}% | **Unique:** {p.uniqueness_percentage}%\n"
            
            if p.top_frequencies:
                md += "- **Top Values:**\n"
                for val, pct in p.top_frequencies.items():
                    bar_len = int(pct / 10)
                    bar = "█" * bar_len + "░" * (10 - bar_len)
                    display_val = (val[:20] + '..') if len(val) > 22 else val
                    md += f"  - `{display_val:<22}` [{bar}] {pct}%\n"

            stats_line = []
            if p.numeric_stats:
                ns = p.numeric_stats
                stats_line.append(f"Min: {ns['min']} | Max: {ns['max']} | Mean: {ns['mean']}")
            if p.string_stats:
                ss = p.string_stats
                stats_line.append(f"Len Min: {ss['min_length']} | Max: {ss['max_length']} | Avg: {ss['avg_length']}")
            
            if stats_line:
                md += f"- **Stats:** {' / '.join(stats_line)}\n"

            samples = ", ".join([f"`{s}`" for s in p.distinct_samples[:5]])
            md += f"- **Samples:** {samples}\n"
            md += "\n"
        md += "---\n"
    return md

def prepare_column_stats_df(p):
    """Prepares a compact 2-column DataFrame for column metrics."""
    data = [
        ["Data Type", f"`{p.dtype}`"],
        ["Null Values", f"{p.null_percentage}% ({p.null_count})"],
        ["Uniqueness", f"{p.uniqueness_percentage}% ({p.cardinality})"]
    ]
    
    if p.string_stats:
        ss = p.string_stats
        data.append(["Length Stats", f"Min: {int(ss['min_length'])} | Max: {int(ss['max_length'])} | Avg: {ss['avg_length']}"])
    
    if p.numeric_stats:
        ns = p.numeric_stats
        data.append(["Numeric Stats", f"Mean: {ns['mean']} | Median: {ns['median']}"])
        data.append(["Range", f"Min: {ns['min']} | Max: {ns['max']}"])
        
    return pd.DataFrame(data, columns=["Metric", "Value"])

def prepare_column_freq_df(p):
    """Prepares a 2-column DataFrame for top value frequencies."""
    if not p.top_frequencies:
        return None
    data = [[k, f"{v}%"] for k, v in p.top_frequencies.items()]
    return pd.DataFrame(data, columns=["Value", "Frequency"])

def prepare_cleaning_stats_df(report):
    """Prepares a compact DataFrame for table-level cleaning statistics."""
    data = [
        ["Rows (Before/After)", f"{report.rows_before:,} / {report.rows_after:,}"],
        ["Duplicates Removed", f"{report.duplicates_removed:,}"],
        ["Whitespace Nullified", f"{report.whitespace_cells_nullified:,}"],
        ["Total Transformations", f"{report.total_transformations:,}"]
    ]
    return pd.DataFrame(data, columns=["Metric", "Value"])

def prepare_cleaning_samples_df(reports):
    """Creates a unified DataFrame from all cleaning examples in a source (limited to 30 samples)."""
    all_examples = []
    for table_name, report in reports.items():
        for ex in report.examples:
            all_examples.append({
                "Table": table_name,
                "Column": ex.column,
                "Operation": ex.operation.replace("_", " ").title(),
                "Before": f"'{ex.before}'" if ex.before is not None else "None",
                "After": f"'{ex.after}'" if ex.after is not None else "None"
            })
            if len(all_examples) >= 30:
                break
        if len(all_examples) >= 30:
            break
    
    if not all_examples:
        return None
        
    return pd.DataFrame(all_examples)[["Column", "Table", "Operation", "Before", "After"]]
