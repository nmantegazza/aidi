#!/usr/bin/env python3
"""
generate_figure_data.py

Reproducible verification and metric extraction script for Chapter 5, Figure 5.8
and Table 5.8 (Entity Resolution Pairwise Matching Performance).

Reads ground-truth benchmark metrics from:
outputs/final_runs/entity-res-matching/datasets/*/*/ternary/dynamic_weighted/metrics.json
and cross-verifies against:
outputs/final_runs/entity-res-matching/summary.csv

Generates:
1. figure_data.json: Structured metrics and coordinates
2. figure_coordinates.tex: Pgfplots coordinate blocks for Figure 5.8
3. matching_table.tex: LaTeX table for Table 5.8
"""

import os
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
SUMMARY_CSV = os.path.join(BASE_DIR, "summary.csv")

CANONICAL_DATASETS = [
    ("DBLP-ACM", "dblp", r"\texttt{dblp-acm}"),
    ("amazon-walmart", "amzn", r"\texttt{amazon-wm}"),
    ("febrl1", "feb1", r"\texttt{febrl1}"),
    ("febrl4", "feb4", r"\texttt{febrl4}"),
    ("fodors-zagats", "fzr", r"\texttt{fodors-zg}"),
    ("itunes-apple", "apl", r"\texttt{itunes-apl}"),
    ("itunes-ebooks", "ebk", r"\texttt{itunes-ebk}"),
    ("rogerebert-imdb", "imdb", r"\texttt{rebert-imdb}"),
]

CANONICAL_MODELS = [
    ("gpt-5.6-sol", "gptcolor", "GPT-5.6 Sol"),
    ("gemini-3.8-flash", "geminicolor", "Gemini 3.8 Flash"),
    ("deepseek-v4.1-flash", "deepseekcolor", "DeepSeek v4.1 Flash"),
    ("mistral-medium-latest", "mistralcolor", "Mistral Medium 3.5"),
]

def load_and_verify_data():
    print(f"[1/4] Loading summary CSV: {SUMMARY_CSV}")
    df_summary = pd.read_csv(SUMMARY_CSV)
    
    print(f"[2/4] Parsing raw per-iteration metrics.json from: {DATASETS_DIR}")
    dataset_results = {}
    
    for ds_name, ds_sym, ds_label in CANONICAL_DATASETS:
        dataset_results[ds_name] = {}
        for model_id, model_color, model_label in CANONICAL_MODELS:
            metrics_path = os.path.join(
                DATASETS_DIR, ds_name, model_id, "ternary", "dynamic_weighted", "metrics.json"
            )
            if not os.path.exists(metrics_path):
                raise FileNotFoundError(f"Missing raw metrics: {metrics_path}")
            
            with open(metrics_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            iters = data["iterations"]
            assert len(iters) == 3, f"Expected 3 iterations for {ds_name}/{model_id}, found {len(iters)}"
            
            f1_list = [it["f1"] for it in iters]
            pf1_list = [it["potential_f1"] for it in iters]
            prec_list = [it["precision"] for it in iters]
            rec_list = [it["recall"] for it in iters]
            pot_rec_list = [it["potential_recall"] for it in iters]
            workload_list = [it["llm_workload_ratio"] for it in iters]
            unrec_loss_list = [it["unrecoverable_loss"] for it in iters]
            
            mean_f1 = float(np.mean(f1_list))
            std_f1 = float(np.std(f1_list, ddof=1))
            mean_pf1 = float(np.mean(pf1_list))
            std_pf1 = float(np.std(pf1_list, ddof=1))
            mean_prec = float(np.mean(prec_list))
            std_prec = float(np.std(prec_list, ddof=1))
            mean_rec = float(np.mean(rec_list))
            std_rec = float(np.std(rec_list, ddof=1))
            mean_pot_rec = float(np.mean(pot_rec_list))
            std_pot_rec = float(np.std(pot_rec_list, ddof=1))
            mean_workload = float(np.mean(workload_list))
            mean_unrec_loss = float(np.mean(unrec_loss_list))
            
            # Cross-verify against summary.csv
            csv_row = df_summary[(df_summary["dataset"] == ds_name) & (df_summary["model"] == model_id)]
            assert len(csv_row) == 1, f"Expected 1 matching CSV row for {ds_name}/{model_id}"
            csv_f1 = csv_row["mean_f1"].values[0]
            csv_pf1 = csv_row["mean_potential_f1"].values[0]
            
            assert np.isclose(mean_f1, csv_f1, atol=1e-4), f"F1 mismatch for {ds_name}/{model_id}: {mean_f1} vs {csv_f1}"
            assert np.isclose(mean_pf1, csv_pf1, atol=1e-4), f"PF1 mismatch for {ds_name}/{model_id}: {mean_pf1} vs {csv_pf1}"
            
            dataset_results[ds_name][model_id] = {
                "f1_iterations": f1_list,
                "pf1_iterations": pf1_list,
                "f1_mean": mean_f1,
                "f1_std": std_f1,
                "pf1_mean": mean_pf1,
                "pf1_std": std_pf1,
                "prec_mean": mean_prec,
                "prec_std": std_prec,
                "rec_mean": mean_rec,
                "rec_std": std_rec,
                "pot_rec_mean": mean_pot_rec,
                "pot_rec_std": std_pot_rec,
                "workload_mean": mean_workload,
                "unrec_loss_mean": mean_unrec_loss,
            }

    print("✔ All 32 configurations cross-verified successfully against summary.csv and raw JSON traces!")
    return dataset_results

def compute_macro_aggregates(dataset_results):
    print("[3/4] Computing run-level macro metrics across iterations and datasets...")
    model_macros = {}
    
    for model_id, model_color, model_label in CANONICAL_MODELS:
        # Run-level iteration macros
        iter_macros_f1 = [0.0, 0.0, 0.0]
        iter_macros_pf1 = [0.0, 0.0, 0.0]
        
        for i in range(3):
            iter_f1s = [dataset_results[ds_name][model_id]["f1_iterations"][i] for ds_name, _, _ in CANONICAL_DATASETS]
            iter_pf1s = [dataset_results[ds_name][model_id]["pf1_iterations"][i] for ds_name, _, _ in CANONICAL_DATASETS]
            iter_macros_f1[i] = float(np.mean(iter_f1s))
            iter_macros_pf1[i] = float(np.mean(iter_pf1s))
        
        macro_f1_mean = float(np.mean(iter_macros_f1))
        macro_f1_std = float(np.std(iter_macros_f1, ddof=1))
        macro_pf1_mean = float(np.mean(iter_macros_pf1))
        macro_pf1_std = float(np.std(iter_macros_pf1, ddof=1))
        
        # Macro averages across datasets
        macro_prec = float(np.mean([dataset_results[ds_name][model_id]["prec_mean"] for ds_name, _, _ in CANONICAL_DATASETS]))
        macro_rec = float(np.mean([dataset_results[ds_name][model_id]["rec_mean"] for ds_name, _, _ in CANONICAL_DATASETS]))
        macro_pot_rec = float(np.mean([dataset_results[ds_name][model_id]["pot_rec_mean"] for ds_name, _, _ in CANONICAL_DATASETS]))
        macro_workload = float(np.mean([dataset_results[ds_name][model_id]["workload_mean"] for ds_name, _, _ in CANONICAL_DATASETS]))
        macro_unrec_loss = float(np.mean([dataset_results[ds_name][model_id]["unrec_loss_mean"] for ds_name, _, _ in CANONICAL_DATASETS]))
        
        model_macros[model_id] = {
            "macro_f1_mean": macro_f1_mean,
            "macro_f1_std": macro_f1_std,
            "macro_pf1_mean": macro_pf1_mean,
            "macro_pf1_std": macro_pf1_std,
            "macro_prec": macro_prec,
            "macro_rec": macro_rec,
            "macro_pot_rec": macro_pot_rec,
            "macro_workload": macro_workload,
            "macro_auto_throughput": 1.0 - macro_workload,
            "macro_unrec_loss": macro_unrec_loss,
            "iter_macros_f1": iter_macros_f1,
            "iter_macros_pf1": iter_macros_pf1,
        }
        
        print(f"  {model_label}:")
        print(f"    Macro F1:  {macro_f1_mean:.4f} ± {macro_f1_std:.4f}")
        print(f"    Macro PF1: {macro_pf1_mean:.4f} ± {macro_pf1_std:.4f}")
        print(f"    Prec: {macro_prec:.4f} | Rec: {macro_rec:.4f} | Pot Rec: {macro_pot_rec:.4f}")
        print(f"    Workload: {macro_workload*100:.2f}% (Autonomous Throughput: {(1.0-macro_workload)*100:.2f}%)")

    return model_macros

def generate_tikz_coordinates(dataset_results, model_macros):
    print("[4/4] Generating TikZ coordinate blocks and export artifacts...")
    tikz_blocks = {
        "f1": {},
        "pf1": {}
    }
    
    for model_id, model_color, model_label in CANONICAL_MODELS:
        # F1 coordinates
        f1_coords = []
        for ds_name, ds_sym, _ in CANONICAL_DATASETS:
            val = dataset_results[ds_name][model_id]["f1_mean"]
            std = dataset_results[ds_name][model_id]["f1_std"]
            f1_coords.append(f"        ({ds_sym}, {val:.4f}) +- (0, {std:.4f})")
        # Add macro coordinate
        mac_val = model_macros[model_id]["macro_f1_mean"]
        mac_std = model_macros[model_id]["macro_f1_std"]
        f1_coords.append(f"        (macro, {mac_val:.4f}) +- (0, {mac_std:.4f})")
        tikz_blocks["f1"][model_id] = "\n".join(f1_coords)
        
        # PF1 coordinates
        pf1_coords = []
        for ds_name, ds_sym, _ in CANONICAL_DATASETS:
            val = dataset_results[ds_name][model_id]["pf1_mean"]
            std = dataset_results[ds_name][model_id]["pf1_std"]
            pf1_coords.append(f"        ({ds_sym}, {val:.4f}) +- (0, {std:.4f})")
        # Add macro coordinate
        mac_pf1_val = model_macros[model_id]["macro_pf1_mean"]
        mac_pf1_std = model_macros[model_id]["macro_pf1_std"]
        pf1_coords.append(f"        (macro, {mac_pf1_val:.4f}) +- (0, {mac_pf1_std:.4f})")
        tikz_blocks["pf1"][model_id] = "\n".join(pf1_coords)

    # Save data json
    out_json = os.path.join(BASE_DIR, "figure_5_8_data.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "datasets": dataset_results,
            "macros": model_macros,
            "tikz_coordinates": tikz_blocks
        }, f, indent=2)
    print(f"✔ Saved structured data to: {out_json}")

    return tikz_blocks

if __name__ == "__main__":
    results = load_and_verify_data()
    macros = compute_macro_aggregates(results)
    generate_tikz_coordinates(results, macros)
    print("Verification complete. Outputs are reproducible and verified.")
