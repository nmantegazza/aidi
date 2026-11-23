# ER Indexing Benchmark Summary

- **Run ID**: `run_20260919_075502`
- **Timestamp**: `2026-09-19T08:34:57.379438+00:00`
- **Datasets**: DBLP-ACM, amazon-walmart, febrl1, febrl4, fodors-zagats, itunes-apple, itunes-ebooks, rogerebert-imdb
- **Strategies**: tfidf_index
- **Models**: deepseek-v4.1-flash, gemini-3.8-flash, gpt-5.6-sol, mistral-medium-latest
- **Iterations**: 3
- **Failed Iterations**: 0 / 96

## Performance Comparison

| Dataset | Strategy | Model | Recall (Mean ± Std) | Precision | Red. Ratio | Time (s) | Peak Mem (MB) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DBLP-ACM | TF-IDF Index | deepseek-v4.1-flash | 1.0000 ± 0.0000 | 0.0745 | 0.9950 | 0.9906 | 21.32 | 3/3 OK |
| DBLP-ACM | TF-IDF Index | gemini-3.8-flash | 1.0000 ± 0.0000 | 0.0846 | 0.9956 | 0.7489 | 13.75 | 3/3 OK |
| DBLP-ACM | TF-IDF Index | gpt-5.6-sol | 1.0000 ± 0.0000 | 0.0846 | 0.9956 | 0.8311 | 13.71 | 3/3 OK |
| DBLP-ACM | TF-IDF Index | mistral-medium-latest | 1.0000 ± 0.0000 | 0.0846 | 0.9956 | 0.8749 | 13.71 | 3/3 OK |
| amazon-walmart | TF-IDF Index | deepseek-v4.1-flash | 0.9948 ± 0.0000 | 0.0074 | 0.9972 | 23.8987 | 392.89 | 3/3 OK |
| amazon-walmart | TF-IDF Index | gemini-3.8-flash | 0.9983 ± 0.0000 | 0.0053 | 0.9962 | 4.4291 | 49.46 | 3/3 OK |
| amazon-walmart | TF-IDF Index | gpt-5.6-sol | 0.9948 ± 0.0000 | 0.0075 | 0.9973 | 23.3210 | 394.27 | 3/3 OK |
| amazon-walmart | TF-IDF Index | mistral-medium-latest | 0.9945 ± 0.0005 | 0.0077 | 0.9974 | 23.7564 | 395.06 | 3/3 OK |
| febrl1 | TF-IDF Index | deepseek-v4.1-flash | 1.0000 ± 0.0000 | 0.6385 | 0.9969 | 0.2964 | 1.95 | 3/3 OK |
| febrl1 | TF-IDF Index | gemini-3.8-flash | 1.0000 ± 0.0000 | 0.4525 | 0.9956 | 0.2129 | 1.05 | 3/3 OK |
| febrl1 | TF-IDF Index | gpt-5.6-sol | 1.0000 ± 0.0000 | 0.7009 | 0.9971 | 0.2730 | 1.87 | 3/3 OK |
| febrl1 | TF-IDF Index | mistral-medium-latest | 1.0000 ± 0.0000 | 0.5460 | 0.9962 | 0.2689 | 1.39 | 3/3 OK |
| febrl4 | TF-IDF Index | deepseek-v4.1-flash | 1.0000 ± 0.0000 | 0.2277 | 0.9991 | 1.6233 | 28.65 | 3/3 OK |
| febrl4 | TF-IDF Index | gemini-3.8-flash | 1.0000 ± 0.0000 | 0.2164 | 0.9991 | 1.2172 | 15.91 | 3/3 OK |
| febrl4 | TF-IDF Index | gpt-5.6-sol | 1.0000 ± 0.0000 | 0.2433 | 0.9992 | 1.4924 | 17.49 | 3/3 OK |
| febrl4 | TF-IDF Index | mistral-medium-latest | 0.9993 ± 0.0009 | 0.1469 | 0.9985 | 1.3859 | 23.47 | 3/3 OK |
| fodors-zagats | TF-IDF Index | deepseek-v4.1-flash | 1.0000 ± 0.0000 | 0.0195 | 0.9670 | 0.2758 | 2.08 | 3/3 OK |
| fodors-zagats | TF-IDF Index | gemini-3.8-flash | 1.0000 ± 0.0000 | 0.0164 | 0.9614 | 0.2435 | 2.18 | 3/3 OK |
| fodors-zagats | TF-IDF Index | gpt-5.6-sol | 1.0000 ± 0.0000 | 0.0251 | 0.9713 | 0.2560 | 1.84 | 3/3 OK |
| fodors-zagats | TF-IDF Index | mistral-medium-latest | 1.0000 ± 0.0000 | 0.0189 | 0.9662 | 0.2757 | 2.16 | 3/3 OK |
| itunes-apple | TF-IDF Index | deepseek-v4.1-flash | 1.0000 ± 0.0000 | 0.0000 | 0.9875 | 29.1341 | 1114.86 | 3/3 OK |
| itunes-apple | TF-IDF Index | gemini-3.8-flash | 1.0000 ± 0.0000 | 0.0000 | 0.9925 | 17.6326 | 602.10 | 3/3 OK |
| itunes-apple | TF-IDF Index | gpt-5.6-sol | 1.0000 ± 0.0000 | 0.0000 | 0.9887 | 26.8153 | 969.39 | 3/3 OK |
| itunes-apple | TF-IDF Index | mistral-medium-latest | 1.0000 ± 0.0000 | 0.0000 | 0.9892 | 26.0502 | 944.65 | 3/3 OK |
| itunes-ebooks | TF-IDF Index | deepseek-v4.1-flash | 0.9847 ± 0.0000 | 0.0003 | 0.9945 | 20.6462 | 273.02 | 3/3 OK |
| itunes-ebooks | TF-IDF Index | gemini-3.8-flash | 1.0000 ± 0.0000 | 0.0003 | 0.9947 | 4.0207 | 101.65 | 3/3 OK |
| itunes-ebooks | TF-IDF Index | gpt-5.6-sol | 0.9847 ± 0.0000 | 0.0003 | 0.9945 | 19.6278 | 272.87 | 3/3 OK |
| itunes-ebooks | TF-IDF Index | mistral-medium-latest | 0.9847 ± 0.0000 | 0.0003 | 0.9945 | 19.8672 | 272.95 | 3/3 OK |
| rogerebert-imdb | TF-IDF Index | deepseek-v4.1-flash | 1.0000 ± 0.0000 | 0.0037 | 0.9974 | 1.8363 | 55.09 | 3/3 OK |
| rogerebert-imdb | TF-IDF Index | gemini-3.8-flash | 1.0000 ± 0.0000 | 0.0054 | 0.9982 | 1.4050 | 17.06 | 3/3 OK |
| rogerebert-imdb | TF-IDF Index | gpt-5.6-sol | 0.9986 ± 0.0024 | 0.0041 | 0.9973 | 1.7086 | 41.98 | 3/3 OK |
| rogerebert-imdb | TF-IDF Index | mistral-medium-latest | 0.9972 ± 0.0024 | 0.0031 | 0.9967 | 1.8592 | 55.51 | 3/3 OK |
