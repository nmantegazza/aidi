# ER Matching Benchmark Summary

- **Run ID**: `run_20260919_135357`
- **Timestamp**: `2026-09-19T15:13:37.820120+00:00`
- **Datasets**: DBLP-ACM, amazon-walmart, febrl1, febrl4, fodors-zagats, itunes-apple, itunes-ebooks, rogerebert-imdb
- **Strategies**: dynamic_weighted
- **Models**: deepseek-v4.1-flash, gemini-3.8-flash, gpt-5.6-sol, mistral-medium-latest
- **Iterations**: 3
- **Failed Iterations**: 0 / 96

## Performance Comparison

| Dataset | Model | Strategy | Mode | F1 (Mean ± Std) | Potential F1 | Precision | Recall | Time (s) | Peak Mem (MB) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DBLP-ACM | deepseek-v4.1-flash | Dynamic Weighted | ternary | 0.9853 ± 0.0022 | 0.9926 ± 0.0011 | 0.9914 | 0.9793 | 8.1244 | 65.50 | 3/3 OK |
| DBLP-ACM | gemini-3.8-flash | Dynamic Weighted | ternary | 0.9861 ± 0.0012 | 0.9922 ± 0.0012 | 0.9909 | 0.9814 | 6.9748 | 43.17 | 3/3 OK |
| DBLP-ACM | gpt-5.6-sol | Dynamic Weighted | ternary | 0.9851 ± 0.0021 | 0.9942 ± 0.0009 | 0.9934 | 0.9769 | 6.7660 | 45.50 | 3/3 OK |
| DBLP-ACM | mistral-medium-latest | Dynamic Weighted | ternary | 0.9815 ± 0.0022 | 0.9919 ± 0.0016 | 0.9903 | 0.9729 | 7.0220 | 45.49 | 3/3 OK |
| amazon-walmart | deepseek-v4.1-flash | Dynamic Weighted | ternary | 0.4062 ± 0.0683 | 0.8048 ± 0.0226 | 0.7466 | 0.2808 | 37.3198 | 290.08 | 3/3 OK |
| amazon-walmart | gemini-3.8-flash | Dynamic Weighted | ternary | 0.4320 ± 0.0063 | 0.7974 ± 0.0023 | 0.7400 | 0.3050 | 24.9469 | 274.75 | 3/3 OK |
| amazon-walmart | gpt-5.6-sol | Dynamic Weighted | ternary | 0.5998 ± 0.0586 | 0.8460 ± 0.0796 | 0.8318 | 0.4734 | 30.5760 | 292.46 | 3/3 OK |
| amazon-walmart | mistral-medium-latest | Dynamic Weighted | ternary | 0.5117 ± 0.0769 | 0.7929 ± 0.0033 | 0.7225 | 0.4027 | 31.1840 | 284.17 | 3/3 OK |
| febrl1 | deepseek-v4.1-flash | Dynamic Weighted | ternary | 0.9301 ± 0.0947 | 0.9997 ± 0.0006 | 1.0000 | 0.8787 | 0.3255 | 0.93 | 3/3 OK |
| febrl1 | gemini-3.8-flash | Dynamic Weighted | ternary | 0.7700 ± 0.0040 | 0.9993 ± 0.0006 | 1.0000 | 0.6260 | 0.3864 | 0.94 | 3/3 OK |
| febrl1 | gpt-5.6-sol | Dynamic Weighted | ternary | 0.8930 ± 0.0254 | 0.9993 ± 0.0006 | 1.0000 | 0.8073 | 0.2142 | 0.82 | 3/3 OK |
| febrl1 | mistral-medium-latest | Dynamic Weighted | ternary | 0.8334 ± 0.1419 | 0.9980 ± 0.0027 | 1.0000 | 0.7327 | 0.3336 | 0.80 | 3/3 OK |
| febrl4 | deepseek-v4.1-flash | Dynamic Weighted | ternary | 0.9865 ± 0.0026 | 1.0000 ± 0.0000 | 1.0000 | 0.9734 | 11.7472 | 36.44 | 3/3 OK |
| febrl4 | gemini-3.8-flash | Dynamic Weighted | ternary | 0.9917 ± 0.0009 | 1.0000 ± 0.0000 | 1.0000 | 0.9836 | 8.7841 | 37.34 | 3/3 OK |
| febrl4 | gpt-5.6-sol | Dynamic Weighted | ternary | 0.9881 ± 0.0020 | 1.0000 ± 0.0000 | 1.0000 | 0.9764 | 8.4962 | 31.90 | 3/3 OK |
| febrl4 | mistral-medium-latest | Dynamic Weighted | ternary | 0.9930 ± 0.0040 | 1.0000 ± 0.0000 | 1.0000 | 0.9862 | 10.5589 | 37.14 | 3/3 OK |
| fodors-zagats | deepseek-v4.1-flash | Dynamic Weighted | ternary | 0.9910 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 | 0.9821 | 0.6696 | 1.98 | 3/3 OK |
| fodors-zagats | gemini-3.8-flash | Dynamic Weighted | ternary | 0.9686 ± 0.0000 | 0.9819 ± 0.0000 | 0.9730 | 0.9643 | 0.6252 | 2.04 | 3/3 OK |
| fodors-zagats | gpt-5.6-sol | Dynamic Weighted | ternary | 0.9558 ± 0.0000 | 0.9730 ± 0.0000 | 0.9474 | 0.9643 | 0.5764 | 1.89 | 3/3 OK |
| fodors-zagats | mistral-medium-latest | Dynamic Weighted | ternary | 0.9836 ± 0.0180 | 0.9939 ± 0.0105 | 0.9881 | 0.9792 | 0.6221 | 1.97 | 3/3 OK |
| itunes-apple | deepseek-v4.1-flash | Dynamic Weighted | ternary | 0.8280 ± 0.0197 | 0.8880 ± 0.0025 | 0.8610 | 0.7980 | 1.2538 | 8.80 | 3/3 OK |
| itunes-apple | gemini-3.8-flash | Dynamic Weighted | ternary | 0.8870 ± 0.0000 | 0.9481 ± 0.0000 | 0.9907 | 0.8030 | 1.0089 | 8.47 | 3/3 OK |
| itunes-apple | gpt-5.6-sol | Dynamic Weighted | ternary | 0.8464 ± 0.0187 | 0.9247 ± 0.0073 | 0.9357 | 0.7727 | 1.2594 | 8.32 | 3/3 OK |
| itunes-apple | mistral-medium-latest | Dynamic Weighted | ternary | 0.7838 ± 0.0195 | 0.8605 ± 0.0076 | 0.8090 | 0.7601 | 1.0978 | 7.34 | 3/3 OK |
| itunes-ebooks | deepseek-v4.1-flash | Dynamic Weighted | ternary | 0.9538 ± 0.0024 | 0.9959 ± 0.0000 | 0.9918 | 0.9186 | 0.8179 | 6.73 | 3/3 OK |
| itunes-ebooks | gemini-3.8-flash | Dynamic Weighted | ternary | 0.9385 ± 0.0044 | 0.9943 ± 0.0049 | 0.9888 | 0.8931 | 0.5998 | 6.75 | 3/3 OK |
| itunes-ebooks | gpt-5.6-sol | Dynamic Weighted | ternary | 0.9528 ± 0.0065 | 0.9918 ± 0.0070 | 0.9839 | 0.9237 | 0.7432 | 6.73 | 3/3 OK |
| itunes-ebooks | mistral-medium-latest | Dynamic Weighted | ternary | 0.9333 ± 0.0106 | 0.9794 ± 0.0043 | 0.9597 | 0.9084 | 0.6867 | 6.73 | 3/3 OK |
| rogerebert-imdb | deepseek-v4.1-flash | Dynamic Weighted | ternary | 0.7427 ± 0.0036 | 0.9818 ± 0.0039 | 0.9885 | 0.5947 | 0.4108 | 1.24 | 3/3 OK |
| rogerebert-imdb | gemini-3.8-flash | Dynamic Weighted | ternary | 0.7353 ± 0.0153 | 0.9819 ± 0.0014 | 0.9860 | 0.5864 | 0.3188 | 1.17 | 3/3 OK |
| rogerebert-imdb | gpt-5.6-sol | Dynamic Weighted | ternary | 0.7090 ± 0.0165 | 0.9789 ± 0.0022 | 0.9828 | 0.5546 | 0.4246 | 1.27 | 3/3 OK |
| rogerebert-imdb | mistral-medium-latest | Dynamic Weighted | ternary | 0.7250 ± 0.0225 | 0.9817 ± 0.0071 | 0.9926 | 0.5712 | 0.3549 | 1.18 | 3/3 OK |
