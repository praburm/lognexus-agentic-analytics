# LogNexus Log Anomaly Eval

Benchmark evaluation framework for log anomaly detection on HDFS and BGL datasets.
Compares rule-based and TF-IDF + Logistic Regression approaches with ROC curve analysis.

## Project Structure

```
lognexus_log-anomaly-eval/
├── evaluation/
│   ├── evaluation_runner.py   # HDFS evaluation (TF-IDF + LR vs rule-based)
│   ├── bgl_evaluation.py      # BGL evaluation
│   └── combined_roc.py        # Combined ROC curve plot for both datasets
├── utils/
│   ├── hdfs_fetcher.py        # Groups HDFS logs by BlockId
│   ├── detector.py            # Rule-based anomaly detector
│   ├── log_normalizer.py      # Normalizes raw log lines
│   └── semantic_enricher.py   # Novelty scoring
├── data/                      # Place HDFS.log, BGL.log, anomaly_label.csv here
├── main.py                    # Runs both evaluations
└── requirements.txt
```

## Data Setup

Place the following files in the `data/` directory before running:

| File | Description |
|---|---|
| `HDFS.log` | Raw HDFS log file |
| `BGL.log` | Raw BGL log file |
| `anomaly_label.csv` | HDFS block-level anomaly labels (`BlockId`, `Label`) |

## Installation

```bash
cd src/anomaly-eval
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Execution

### Run both evaluations

```bash
source venv/bin/activate
python3 main.py
```

### Run individually

```bash
python3 -m evaluation.evaluation_runner   # HDFS only
python3 -m evaluation.bgl_evaluation      # BGL only
python3 -m evaluation.combined_roc        # ROC comparison plot
```

## Outputs

| Output | Description |
|---|---|
| Console metrics | Precision, Recall, F1, AUC per model |
| `roc_comparison.pdf` | Combined ROC curve comparing HDFS LR, BGL LR, and Rule-Based |

## License

Internal use only — VIAVI Solutions.
