# SINGLE-ENTRYPOINT PROJECT RUNNER

## Data Skew Intelligence — Antigravity One-Click Execution Specification

## Objective

Refactor the project so the user only needs to click **Run** on `run.py`.

The standard command must be:

```bash
python run.py
```

It must orchestrate:

```text
Environment Check
      ↓
Dependency Check
      ↓
Directory Preparation
      ↓
Synthetic Dataset Generation
      ↓
EDA / Skew Analysis
      ↓
Spark Baseline
      ↓
ML Feature Engineering
      ↓
ML Training / Prediction
      ↓
Mitigation
      ↓
Post-Mitigation Spark Run
      ↓
Before/After Comparison
      ↓
Automated Tests
      ↓
Results Export
      ↓
Premium CLI Summary
```

No manual sequence of commands should be required for the normal workflow.

---

## 1. One-Button User Experience

The intended workflow:

1. Open the repository in Antigravity.
2. Select the project virtual environment.
3. Open `run.py`.
4. Click **Run**.
5. Let the full experiment execute.
6. Read the final terminal report.
7. Inspect `results/latest/` when deeper analysis is required.

Do not require users to remember commands such as:

```text
python -m cli.app ...
python generate.py
python baseline.py
python train.py
pytest
```

Those remain internal implementation details.

---

## 2. Primary Entry Point

Create:

```text
run.py
```

`run.py` should be a thin orchestrator. It must not contain every implementation detail.

Recommended architecture:

```text
project/
│
├── run.py
│
├── cli/
│   ├── __init__.py
│   └── console.py
│
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── environment.py
│   ├── pipeline.py
│   └── results.py
│
├── data/
│   ├── __init__.py
│   ├── generator.py
│   └── profiler.py
│
├── spark/
│   ├── __init__.py
│   ├── session.py
│   ├── baseline.py
│   ├── metrics.py
│   └── mitigation.py
│
├── ml/
│   ├── __init__.py
│   ├── features.py
│   ├── train.py
│   ├── predict.py
│   └── evaluate.py
│
├── tests/
│   ├── test_data.py
│   ├── test_spark.py
│   ├── test_ml.py
│   └── test_pipeline.py
│
├── dashboard/
│   └── app.py
│
├── results/
├── models/
├── logs/
├── requirements.txt
├── pytest.ini
├── .gitignore
└── README.md
```

Preserve existing working modules where possible. Do not create duplicate implementations merely to match this structure.

---

## 3. Runner Responsibilities

`run.py` must orchestrate:

```python
prepare_environment()
prepare_directories()
generate_dataset()
profile_dataset()
run_baseline()
build_ml_features()
train_models()
predict_severity()
select_mitigation()
run_mitigation()
run_post_mitigation()
compare_results()
run_tests()
write_results()
display_final_report()
```

These can be implemented in different modules, but `run.py` owns the sequence.

---

## 4. Premium CLI

Use `Rich` for all user-facing terminal output.

Use a dark terminal aesthetic with a green engineering accent inspired by modern GPU/data-platform consoles. Do not copy NVIDIA logos or proprietary branding.

Style:

```text
background    near-black
accent        green
text          white
secondary     dim gray
warning       yellow
error         red
```

Example:

```text
╔══════════════════════════════════════════════════════════════╗
║  S K E W C T L                                              ║
║  INTELLIGENT DATA SKEW ENGINE                               ║
║  Distributed Data • Spark • ML • Mitigation                 ║
╚══════════════════════════════════════════════════════════════╝
```

Use compact progress indicators:

```text
[1/9] Environment       ✓
[2/9] Dataset           ✓
[3/9] EDA               ✓
[4/9] Spark baseline    ✓
[5/9] ML                ✓
[6/9] Detection         ✓
[7/9] Mitigation        ✓
[8/9] Tests             ✓
[9/9] Results           ✓
```

Do not print raw Spark logs to the user interface.

Write detailed logs to files instead.

---

## 5. Automatic Environment Checks

Before executing the project, verify:

```text
Python
Java
PySpark
PyArrow
pandas
NumPy
scikit-learn
Rich
pytest
Streamlit
```

Normal execution should fail clearly if a required dependency is missing.

Example:

```text
✗ ENVIRONMENT NOT READY

Missing:
Java 17+

Run:
python run.py --check
```

Do not silently install packages every time the project starts.

Optional:

```bash
python run.py --setup
```

may install dependencies from `requirements.txt`.

---

## 6. Path Handling

Never assume the current working directory.

Use:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
```

Then resolve paths from `PROJECT_ROOT`.

Bad:

```python
"data/generated/skew_70.parquet"
```

Preferred:

```python
PROJECT_ROOT / "data" / "generated" / "skew_70.parquet"
```

This is important for Antigravity, VS Code, GitHub Actions, and terminal execution.

---

## 7. Configuration

Keep experiment defaults in one configuration module.

Example:

```python
ROWS = 100_000
SKEW_RATIO = 0.70
RANDOM_SEED = 42
NUM_KEYS = 20
NUM_PARTITIONS = 8
RUN_ML = True
RUN_TESTS = True
RUN_DASHBOARD = False
```

Do not scatter these values across scripts.

---

## 8. Dataset Generation

The project should use a synthetic dataset generated by the repository itself.

Default:

```text
100,000 records
70% hot-key concentration
20 total keys
seed = 42
Parquet
```

Expected output:

```text
data/generated/skew_70.parquet
```

The generator must be deterministic for the same configuration.

Regenerate automatically when:

- the expected file does not exist;
- configuration changed;
- the user requests `--clean`.

Do not require an external dataset for the standard run.

---

## 9. Dataset Validation

Before Spark processing, validate:

```text
file exists
schema is valid
record count is correct
required columns exist
null constraints
key distribution
```

Example:

```text
[2/9] DATASET

✓ 100,000 records
✓ Parquet
✓ 20 keys
✓ Hot-key concentration: 70.0%
```

---

## 10. Spark Session

Centralize Spark session creation.

Use local Spark:

```python
SparkSession.builder     .appName("SkewCTL")     .master("local[*]")     .getOrCreate()
```

Avoid unnecessary multiple Spark sessions.

Stop Spark cleanly after execution.

Configure logging so the application output is readable.

The project should not require a cloud Spark cluster or physical multi-node cluster.

---

## 11. Baseline Experiment

Run the unmitigated workload first.

Collect at least:

```text
execution_time
partition_count
max_partition_size
min_partition_size
mean_partition_size
partition_std
shuffle_read
shuffle_write
```

Save:

```text
results/latest/baseline_metrics.json
results/latest/baseline_metrics.csv
```

Use identical metric collection for before/after comparisons.

---

## 12. Statistical Skew Detection

Create an explainable severity mechanism using:

```text
top-key concentration
partition imbalance
partition-size variance
```

Classify:

```text
NORMAL
LOW_SKEW
HIGH_SKEW
```

Keep the logic simple enough to explain in a viva.

Do not over-engineer the scoring system.

---

## 13. ML Pipeline

Use a small tabular classification workflow.

Recommended models:

```text
Logistic Regression
Decision Tree
Random Forest
```

Pipeline:

```text
Experiment Metrics
      ↓
Feature Engineering
      ↓
Train/Test Split
      ↓
Model Training
      ↓
Evaluation
      ↓
Best Model
      ↓
Severity Prediction
```

Recommended features include:

```text
skew_ratio
top1_concentration
partition_std
max_partition_size
mean_partition_size
shuffle_read
shuffle_write
execution_time
```

Target:

```text
NORMAL
LOW_SKEW
HIGH_SKEW
```

The ML layer must use actual generated experiment data. Never fabricate training or evaluation metrics.

---

## 14. ML Evaluation

Report:

```text
accuracy
precision
recall
f1
```

Prefer macro/weighted metrics where appropriate.

Save:

```text
models/best_model.joblib
results/latest/ml_metrics.json
results/latest/ml_predictions.csv
```

If there is insufficient experiment data for meaningful ML training, report that honestly and fall back to statistical detection rather than fabricating results.

---

## 15. Mitigation Decision

Use a transparent mapping:

```text
NORMAL
→ no mitigation

LOW_SKEW
→ repartition

HIGH_SKEW
→ salting
```

The ML prediction can recommend the mitigation, but the decision logic should remain easy to understand.

---

## 16. Salting

Implement salting as a reusable Spark transformation.

The important requirement is to actually reduce hot-key concentration and preserve the logical result of the intended computation.

Validate partition distribution before and after mitigation.

Do not merely add a random column and claim the skew was fixed.

---

## 17. Post-Mitigation Experiment

After applying mitigation:

```text
run the same logical Spark workload
collect the same metrics
```

Save:

```text
results/latest/mitigated_metrics.json
results/latest/mitigated_metrics.csv
```

Use the same configuration and metric definitions as the baseline.

---

## 18. Performance Comparison

Automatically calculate:

```text
execution-time improvement
partition-imbalance improvement
shuffle change
```

Example:

```text
╭──────────────────────────────────────────────╮
│ PERFORMANCE COMPARISON                       │
├──────────────────────────────────────────────┤
│                 BEFORE       AFTER           │
│ Runtime         12.42 s      6.31 s          │
│ Max partition   68,421      21,302           │
│ Partition std    21,442       6,382           │
├──────────────────────────────────────────────┤
│ Runtime improvement: 49.2%                   │
╰──────────────────────────────────────────────╯
```

Never force a positive result.

If mitigation makes the result worse, report the negative result honestly.

---

## 19. Automated Testing

The normal runner should execute fast tests automatically:

```bash
python -m pytest -q
```

Tests should cover:

```text
dataset generation
schema validation
skew calculation
Spark smoke test
mitigation behavior
ML feature generation
pipeline smoke test
```

Do not put expensive benchmarks into the unit-test suite.

Example:

```text
[8/9] TESTS

✓ Dataset tests
✓ Skew tests
✓ Spark smoke test
✓ Mitigation tests
✓ ML tests
✓ Pipeline smoke test

6 passed
```

A test failure should result in a non-zero exit code.

---

## 20. Results Management

Each complete run should create a timestamped results directory:

```text
results/
└── 2026-08-20_15-45-10/
    ├── config.json
    ├── dataset_profile.json
    ├── baseline_metrics.json
    ├── mitigated_metrics.json
    ├── ml_metrics.json
    ├── predictions.csv
    └── summary.json
```

Also maintain:

```text
results/latest/
```

for the most recent run.

The dashboard reads only from `results/latest/`.

This prevents stale-result confusion.

---

## 21. Final Report

At the end of `run.py`, always show a concise final report.

Example:

```text
╭──────────────────────────────────────────────────────────────╮
│                    EXPERIMENT COMPLETE                      │
├──────────────────────────────────────────────────────────────┤
│ Dataset             100,000 records                         │
│ Skew                70.0%                                   │
│ Severity            HIGH_SKEW                               │
│ ML Model            Random Forest                           │
│ Mitigation          SALTING                                 │
│                                                              │
│ Runtime Before      12.42 s                                 │
│ Runtime After        6.31 s                                 │
│ Improvement         49.2%                                   │
│                                                              │
│ Tests               6 passed                                │
╰──────────────────────────────────────────────────────────────╯

Results:
results/latest/
```

---

## 22. Failure Handling

Do not dump long tracebacks into the normal CLI.

Bad:

```text
Traceback (most recent call last):
...
```

Good:

```text
✗ SPARK STARTUP FAILED

Reason:
Java runtime was not detected.

Expected:
Java 17+

Detailed log:
logs/error.log
```

Keep full traceback information in the log file.

---

## 23. Command-Line Options

The project only needs a few optional modes.

### Normal

```bash
python run.py
```

Runs the complete project.

### Environment check

```bash
python run.py --check
```

Only validates the environment.

### Quick mode

```bash
python run.py --quick
```

Uses a smaller dataset and reduced experiment settings for rapid debugging.

### Clean mode

```bash
python run.py --clean
```

Removes generated datasets, temporary Spark output, old results, and logs, then runs a fresh pipeline.

### Dashboard mode

```bash
python run.py --dashboard
```

Runs the complete pipeline and launches the Streamlit dashboard at the end.

These are optional. The normal workflow remains:

```bash
python run.py
```

---

## 24. Dashboard

The dashboard is not required for the core pipeline.

It should consume:

```text
results/latest/
```

rather than rerunning Spark every time the page loads.

If the dashboard fails to launch, the Spark/ML experiment is still considered complete.

---

## 25. GitHub and CI

The project must work after cloning.

GitHub Actions should run at least:

```bash
python -m pytest -q
```

and a small smoke execution:

```bash
python run.py --quick
```

The project must not depend on:

```text
personal Windows paths
OneDrive
local absolute paths
GPU
CUDA
manually created folders
private files
```

---

## 26. Dependencies

Keep `requirements.txt` minimal and based only on packages actually used.

Suggested baseline:

```text
pyspark
pandas
numpy
pyarrow
scikit-learn
rich
streamlit
pytest
matplotlib
plotly
joblib
```

Do not add packages simply because they might be useful later.

---

## 27. Logging

Maintain:

```text
logs/run.log
logs/error.log
```

The terminal should show only meaningful application events.

Spark's detailed internal logs should be written to the logging layer rather than overwhelming the premium CLI.

---

## 28. Exit Codes

Use:

```text
0 → success
1 → project execution failure
2 → environment/setup failure
3 → test failure
```

This is important for GitHub Actions and automated tooling.

---

## 29. GitHub-Safe Artifacts

Do not commit:

```text
.venv/
__pycache__/
spark-warehouse/
metastore_db/
generated datasets
large benchmark outputs
logs
temporary files
```

Keep source code and lightweight configuration under version control.

The dataset generator must make the project reproducible from a clean clone.

---

## 30. GPU / NVIDIA Requirement

The CLI may use an NVIDIA-inspired visual design, but the core project must **not** require an NVIDIA GPU.

Do not add CUDA or GPU dependencies.

The engineering focus is:

```text
Apache Spark
CPU parallelism
partitioning
data skew
feature engineering
ML classification
mitigation
```

This keeps the repository portable.

---

## 31. Optional Security Interpretation

Extreme or intentionally generated skew may be described as an:

```text
adversarial workload / resource-exhaustion scenario
```

but a full intrusion-detection system is unnecessary.

The core remains:

```text
detect skew
→ classify severity
→ mitigate skew
→ measure improvement
```

---

## 32. Definition of Done

The refactor is complete when:

```text
[ ] Open repository
[ ] Click Run on run.py
[ ] Environment validates
[ ] Dataset generates automatically
[ ] Dataset is validated
[ ] Spark baseline runs
[ ] Skew is measured
[ ] ML stage runs when enough data exists
[ ] Mitigation executes
[ ] Post-mitigation run executes
[ ] Before/after comparison is produced
[ ] Tests run automatically
[ ] Results are saved
[ ] Final premium CLI report appears
[ ] python run.py --check works
[ ] python run.py --quick works
[ ] GitHub CI works
```

---

# Final Architecture

```text
                         ONE CLICK
                            │
                            ▼
                          run.py
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
       Spark             ML/XAI            Testing
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                      Mitigation
                            │
                            ▼
                      Comparison
                            │
                            ▼
                         Results
                            │
                            ▼
                     Premium CLI
                            │
                            ▼
                   Optional Dashboard
```

The goal is not to hide the underlying concepts. The goal is to remove repetitive manual operations while keeping each module understandable, testable, reproducible, and easy to defend in a viva.
