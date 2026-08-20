# ⚡ Data Skew Intelligence — Implementation Blueprint

> **Project:** Intelligent Data Skew Detection and Mitigation in Apache Spark  
> **Course Context:** Data Engineering / Data Analysis with Spark  
> **Project ID:** 23BTRDC034  
> **Date:** 17/08/2026  
> **Primary Goal:** Build a simple, academically strong Spark project that demonstrates deep understanding of partitions, transformations, skew, EDA, statistics, feature engineering, ML classification, mitigation, and performance evaluation.

---

## 0. Project Philosophy

### The project should prove one idea

> **Data distribution affects distributed computation. We can measure that effect, classify its severity, and choose an appropriate mitigation strategy.**

Do **not** turn this into a collection of unrelated technologies.

The project follows the course progression:

```text
Data Loading
    ↓
Data Transformation
    ↓
Spark Execution
    ↓
EDA
    ↓
Statistical Analysis
    ↓
Feature Engineering
    ↓
Machine Learning
    ↓
Evaluation
    ↓
Decision Making
    ↓
Mitigation
    ↓
Performance Comparison
```

The professor's material establishes Spark's partitioned distributed model, DataFrames/SparkSession, transformations such as `groupBy()`, lazy evaluation, EDA, outlier analysis, feature engineering, Spark MLlib classification, pipelines, and model evaluation. The project should build directly on those foundations rather than introduce unnecessary technologies.

---

# 1. Final Project Scope

## Core requirement

Create intentionally skewed datasets where a small number of keys hold a disproportionate number of records.

Measure how skew affects Spark execution.

Apply salting and/or repartitioning to reduce the imbalance.

## Differentiating extension

Build a lightweight **Skew Intelligence Layer**:

```text
Spark telemetry + distribution statistics
                ↓
       Feature engineering
                ↓
      Skew severity classifier
                ↓
       Mitigation recommendation
                ↓
     Salting / repartitioning
                ↓
        Performance comparison
```

## Optional security interpretation

Extreme deliberately generated skew may be presented as an **adversarial workload scenario** or potential resource-exhaustion condition.

Important: do not claim that all data skew is inherently a cyberattack.

---

# 2. Final Architecture

```text
                         ┌─────────────────────┐
                         │   Data Generator    │
                         │ Normal / Skewed     │
                         │ Controlled Severity  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Apache Spark     │
                         │ SparkSession        │
                         │ DataFrame / SQL     │
                         └──────────┬──────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
              ┌─────────────┐              ┌───────────────┐
              │     EDA     │              │ Spark Metrics │
              │ Key counts  │              │ Tasks         │
              │ Statistics  │              │ Partitions    │
              │ Outliers    │              │ Shuffle       │
              └──────┬──────┘              │ Runtime       │
                     │                     └───────┬───────┘
                     └─────────────┬───────────────┘
                                   ▼
                         ┌─────────────────────┐
                         │ Feature Engineering │
                         │ skew_ratio           │
                         │ concentration        │
                         │ partition variance   │
                         │ shuffle metrics      │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │   ML Classifier     │
                         │ Logistic Regression │
                         │ Decision Tree       │
                         │ Random Forest       │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ Skew Decision       │
                         │ NORMAL / LOW / HIGH │
                         └──────────┬──────────┘
                                    ▼
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
               No Mitigation                Mitigation
                                                   │
                                  ┌────────────────┼───────────────┐
                                  ▼                ▼               ▼
                            Repartition        Salting        Optional AQE
                                  │                │               │
                                  └────────────────┼───────────────┘
                                                   ▼
                                        Spark Re-execution
                                                   ▼
                                      Before vs After Metrics
                                                   ▼
                                            Streamlit UI
```

---

# 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.11 | Main implementation |
| Distributed processing | Apache Spark / PySpark | Core project |
| JVM | Java 17 LTS | Spark runtime |
| Data | Parquet + CSV | Experiment inputs/outputs |
| Numerical | NumPy | Numerical operations |
| Data analysis | pandas | Small result analysis |
| ML | scikit-learn | Severity classification |
| Visualization | Plotly + Matplotlib | Results and distributions |
| CLI | Typer + Rich | Premium terminal interface |
| Dashboard | Streamlit | Demonstration UI |
| Explainability | SHAP (optional) | Model interpretation |
| Containerization | Docker | Reproducible environment |
| Version control | Git + GitHub | Source control |

### Deliberately excluded from the core

- Kubernetes
- Hadoop cluster
- Kafka
- Airflow
- React frontend
- FastAPI backend
- GPU
- TensorFlow/PyTorch
- Cloud Spark cluster

These are unnecessary for the stated academic objective.

---

# 4. Machine Setup

## Recommended

```text
OS:        Windows 10/11 or Linux
CPU:       6–8 cores
RAM:       16 GB
Storage:   20+ GB free
Python:    3.11
Java:      17 LTS
IDE:       VS Code
Git:       Latest stable
Docker:    Optional initially
```

## Why no GPU?

The project studies Spark partitioning and distributed CPU workload behavior. A GPU is not necessary for the core experiment or ML models.

---

# 5. Environment Setup

## 5.1 Create project

```bash
mkdir data-skew-intelligence
cd data-skew-intelligence
```

## 5.2 Create virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux/macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

## 5.3 Install dependencies

```bash
python -m pip install --upgrade pip
pip install pyspark pandas numpy scikit-learn pyarrow matplotlib plotly streamlit typer rich
```

Optional later:

```bash
pip install shap mlflow
```

## 5.4 Verify Java

```bash
java -version
```

Target:

```text
Java 17 LTS
```

## 5.5 Verify PySpark

```bash
python -c "from pyspark.sql import SparkSession; s=SparkSession.builder.master('local[*]').getOrCreate(); print(s.version); s.stop()"
```

---

# 6. Repository Structure

```text
data-skew-intelligence/
│
├── data/
│   ├── raw/
│   ├── normal/
│   ├── skewed/
│   └── generated/
│
├── spark/
│   ├── __init__.py
│   ├── session.py
│   ├── generate_data.py
│   ├── baseline.py
│   ├── analyze_skew.py
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
├── cli/
│   ├── __init__.py
│   └── app.py
│
├── dashboard/
│   └── app.py
│
├── results/
│   ├── experiments/
│   ├── metrics/
│   ├── models/
│   └── reports/
│
├── notebooks/
│
├── tests/
│   ├── test_generator.py
│   ├── test_skew_metrics.py
│   └── test_mitigation.py
│
├── docs/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── README.md
└── LICENSE
```

---

# 7. Configuration Design

Create one central configuration file instead of scattering constants.

Recommended settings:

```yaml
project:
  name: "Data Skew Intelligence"

spark:
  master: "local[*]"
  shuffle_partitions: 8
  adaptive_query_execution: false

experiment:
  rows: 1000000
  seed: 42
  skew_levels: [0.10, 0.30, 0.50, 0.70, 0.90]

ml:
  test_size: 0.20
  random_state: 42
```

Use `seed=42` consistently so experiments can be reproduced.

---

# 8. Dataset Design

## Record schema

Use a deliberately simple schema:

```text
record_id       string
key             string
value           double
category        string
timestamp       timestamp
```

The `key` column is the skew driver.

## Generate controlled distributions

Create at least:

```text
normal_10.parquet
skew_30.parquet
skew_50.parquet
skew_70.parquet
skew_90.parquet
```

Interpretation:

```text
10% → approximately normal / low concentration
30% → mild skew
50% → moderate skew
70% → high skew
90% → extreme skew
```

Keep the total row count approximately constant across experiments.

This allows the experiment to isolate **distribution** rather than simply dataset size.

---

# 9. Stage 1 — Spark Baseline

## Objective

Prove that Spark's execution behavior changes when the same overall volume of data has a different key distribution.

## Baseline operation

```python
result = df.groupBy("key").count()
result.show()
```

## Concepts to understand before proceeding

- SparkSession
- DataFrame
- partitions
- transformations
- actions
- lazy evaluation
- groupBy
- aggregation
- shuffle
- tasks
- stages

## Deliverable

A baseline report containing:

```text
Dataset
Rows
Number of partitions
Execution time
Shuffle read
Shuffle write
Max partition size
Average partition size
Partition standard deviation
```

---

# 10. Stage 2 — Spark UI Investigation

When a Spark job is active, inspect:

```text
http://localhost:4040
```

Study:

- Jobs
- Stages
- Tasks
- SQL
- Executors
- Storage
- Environment

### Evidence to capture

1. Normal workload screenshot
2. Skewed workload screenshot
3. Stage duration comparison
4. Task duration imbalance
5. Partition size imbalance

### Viva requirement

Be able to explain:

> Why can one task remain active significantly longer than the others?

---

# 11. Stage 3 — EDA

The professor's material places EDA before advanced modeling.

Analyze the key distribution:

```python
df.groupBy("key").count().orderBy("count", ascending=False)
```

Calculate:

```text
mean key frequency
median key frequency
standard deviation
maximum key frequency
minimum key frequency
top-1 concentration
top-5 concentration
```

## Visualizations

Create:

1. Key frequency bar chart
2. Key frequency histogram
3. Partition-size distribution
4. Normal vs skewed comparison

---

# 12. Stage 4 — Statistical Skew Detection

Start with a transparent statistical baseline before ML.

## Candidate metrics

### Skew ratio

```text
skew_ratio = max_partition_size / mean_partition_size
```

### Coefficient of variation

```text
CV = std(partition_sizes) / mean(partition_sizes)
```

### Top-1 concentration

```text
top1_concentration = records_for_most_frequent_key / total_records
```

### Outlier detection

Experiment with:

- standard deviation
- Z-score
- IQR

Do not add all methods automatically. Compare and retain the most interpretable approach.

---

# 13. Skew Severity Score

Create a simple normalized score so the project has a clear decision layer.

Example conceptual formula:

```text
SkewScore =
    w1 * normalized_skew_ratio
  + w2 * normalized_partition_variance
  + w3 * top1_concentration
```

The exact weights should be documented and experimentally justified.

Example interpretation:

```text
0.00 – 0.30  NORMAL
0.30 – 0.60  LOW SKEW
0.60 – 1.00  HIGH SKEW
```

Do not present these thresholds as universal Spark thresholds. They are project-defined thresholds and should be validated experimentally.

---

# 14. Stage 5 — Feature Engineering

Create an experiment-level ML dataset.

Recommended features:

```text
skew_ratio
top1_concentration
top5_concentration
partition_count
mean_partition_size
max_partition_size
partition_std
execution_time
shuffle_read
shuffle_write
```

Potential additional features:

```text
task_duration_mean
task_duration_max
task_duration_std
spill_memory
spill_disk
```

Start with the smaller feature set. Add more only when the baseline is stable.

---

# 15. ML Target

Use three classes:

```text
0 = NORMAL
1 = LOW_SKEW
2 = HIGH_SKEW
```

Avoid creating an "attack" class unless the experiment can support it convincingly.

The security interpretation can remain a controlled extension:

```text
Extreme intentional skew → adversarial workload scenario
```

---

# 16. Stage 6 — ML Models

Train models in this order:

## Model A — Logistic Regression

Purpose:

- baseline classifier
- simple decision boundary
- easy to interpret

## Model B — Decision Tree

Purpose:

- interpretable thresholds
- useful for explaining decisions

## Model C — Random Forest

Purpose:

- stronger nonlinear baseline
- robust tabular classification

Do not assume Random Forest will be best. Measure it.

The professor's material emphasizes model selection based on performance, training time, prediction time, interpretability, resources and overfitting rather than simply choosing the most complex model.

---

# 17. ML Pipeline

Use a reproducible pipeline:

```text
Raw experiment table
        ↓
Data validation
        ↓
Feature selection
        ↓
Train/Test Split
        ↓
Model training
        ↓
Prediction
        ↓
Evaluation
        ↓
Model selection
```

Use an 80/20 split initially.

Later use cross-validation for the final comparison.

---

# 18. ML Evaluation

Report:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion matrix

Optionally:

- ROC-AUC for suitable binary experiments
- Cross-validation score

## Most important metrics

Prioritize:

```text
F1-score
Recall
Precision
```

because a high accuracy value alone can hide poor performance on less frequent severity classes.

---

# 19. Stage 7 — Intelligent Decision Engine

The classifier now controls the mitigation strategy.

```text
Prediction
    │
    ├── NORMAL
    │      → no mitigation
    │
    ├── LOW_SKEW
    │      → repartition
    │
    └── HIGH_SKEW
           → salting
```

Decision function concept:

```python
def choose_mitigation(prediction: str) -> str:
    if prediction == "NORMAL":
        return "NONE"
    if prediction == "LOW_SKEW":
        return "REPARTITION"
    return "SALTING"
```

Keep this logic deterministic and easy to explain.

---

# 20. Stage 8 — Mitigation

## Technique A — Repartitioning

Evaluate whether changing partition distribution reduces the imbalance.

## Technique B — Salting

For hot keys, append a salt value:

```text
HOT_KEY → HOT_KEY_0
HOT_KEY → HOT_KEY_1
HOT_KEY → HOT_KEY_2
...
```

The goal is to distribute records belonging to the same logical hot key across multiple processing groups.

## Important

If you salt a grouped/joined workload, document how the final logical aggregation is reconstructed after the salted processing step.

---

# 21. Before vs After Experiment

For every severity level, compare:

```text
                    BEFORE        AFTER
Execution time      X             Y
Max partition       X             Y
Partition std       X             Y
Shuffle read        X             Y
Shuffle write       X             Y
Spill                X             Y
```

Calculate:

```text
improvement_% = ((before - after) / before) * 100
```

Only report improvements measured from real repeated runs.

---

# 22. Experimental Matrix

Run a controlled experiment matrix.

| Experiment | Skew | Partitions | Mitigation |
|---|---:|---:|---|
| E01 | 10% | 4 | None |
| E02 | 30% | 4 | None |
| E03 | 50% | 4 | None |
| E04 | 70% | 4 | None |
| E05 | 90% | 4 | None |
| E06 | 70% | 4 | Repartition |
| E07 | 70% | 4 | Salting |
| E08 | 90% | 8 | Repartition |
| E09 | 90% | 8 | Salting |
| E10 | 90% | 16 | Salting |

Repeat important experiments at least 3 times when practical and report mean + variability.

---

# 23. Premium CLI Design

The CLI should feel like a professional analytics tool, not a collection of Python scripts.

Use:

```text
Typer → commands and arguments
Rich  → panels, tables, progress bars, status, logs
```

## CLI name

```text
skewctl
```

## Suggested command tree

```text
skewctl
│
├── system
├── data
│   ├── generate
│   ├── inspect
│   └── profile
│
├── spark
│   ├── baseline
│   ├── analyze
│   └── benchmark
│
├── ml
│   ├── build-dataset
│   ├── train
│   ├── evaluate
│   └── predict
│
├── mitigate
│   ├── repartition
│   ├── salt
│   └── auto
│
├── experiment
│   ├── run
│   └── compare
│
└── dashboard
    └── launch
```

---

# 24. Premium CLI Startup Screen

Example:

```text
╭──────────────────────────────────────────────────────────────╮
│  S K E W C T L                                               │
│  Intelligent Data Skew Detection & Mitigation                │
│                                                              │
│  Spark Analytics Engine                                      │
│  ML Severity Classifier                                      │
│  Adaptive Mitigation                                         │
╰──────────────────────────────────────────────────────────────╯

  System        ● READY
  Spark         ● READY
  Python        ● 3.11.x
  Java          ● 17.x
  ML Engine     ● READY
```

---

# 25. Example CLI Session

```text
$ skewctl experiment run --skew 0.90 --rows 1000000 --mitigation auto

╭────────────── Experiment ──────────────╮
│ ID              EXP-0009               │
│ Records         1,000,000              │
│ Skew            90%                    │
│ Partitions      8                      │
╰────────────────────────────────────────╯

⠋ Generating dataset...
✓ Dataset generated
✓ Spark session initialized
✓ Baseline completed
✓ Metrics collected
✓ ML prediction: HIGH_SKEW (0.93)
✓ Mitigation selected: SALTING
✓ Mitigated run completed

                 PERFORMANCE
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Metric           ┃ Before   ┃ After    ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ Runtime          │ 112.4 s  │ 43.7 s   │
│ Max Partition    │ 781 MB   │ 192 MB   │
│ Shuffle Read     │ 8.4 GB   │ 3.1 GB   │
│ Partition Std    │ 217.3    │ 48.1     │
└──────────────────┴──────────┴──────────┘

  Improvement: 61.1%
```

The numbers above are illustrative only. Never hard-code them into the report.

---

# 26. CLI Commands to Implement

## System check

```bash
skewctl system check
```

Checks:

- Python
- Java
- PySpark
- dependencies
- available CPU
- available memory

## Generate data

```bash
skewctl data generate --rows 1000000 --skew 0.70 --output data/skewed/skew_70.parquet
```

## Inspect data

```bash
skewctl data inspect data/skewed/skew_70.parquet
```

## Run baseline

```bash
skewctl spark baseline --input data/skewed/skew_70.parquet
```

## Analyze skew

```bash
skewctl spark analyze --input data/skewed/skew_70.parquet
```

## Train model

```bash
skewctl ml train --input results/metrics/experiment_dataset.csv
```

## Evaluate model

```bash
skewctl ml evaluate --model results/models/random_forest.joblib
```

## Run automated mitigation

```bash
skewctl mitigate auto --input data/skewed/skew_70.parquet
```

## Compare experiments

```bash
skewctl experiment compare --runs results/experiments/
```

## Launch dashboard

```bash
skewctl dashboard launch
```

---

# 27. Result Storage Contract

Every experiment should produce a machine-readable record.

Example JSON:

```json
{
  "experiment_id": "EXP-0001",
  "rows": 1000000,
  "skew_ratio": 0.70,
  "partitions": 8,
  "execution_time_seconds": 0.0,
  "max_partition_records": 0,
  "mean_partition_records": 0,
  "partition_std": 0.0,
  "shuffle_read_bytes": 0,
  "shuffle_write_bytes": 0,
  "predicted_class": "HIGH_SKEW",
  "prediction_confidence": 0.0,
  "mitigation": "SALTING"
}
```

Never mix experiment results with raw data files.

---

# 28. Streamlit Dashboard

The dashboard is a **presentation layer**, not the Spark execution engine.

## Page 1 — Overview

Display:

- project status
- dataset size
- current experiment
- skew severity
- recommended mitigation

## Page 2 — Distribution

Charts:

- top keys
- key frequency
- partition distribution

## Page 3 — Spark Performance

Charts:

- execution time
- shuffle read/write
- partition imbalance
- task duration

## Page 4 — ML

Display:

- predicted severity
- confidence
- confusion matrix
- model comparison
- feature importance

## Page 5 — Mitigation

Display:

```text
Before → After
```

and calculate measured improvement.

---

# 29. Deployment Strategy

## Do not deploy Spark itself initially.

Use this architecture:

```text
Local / Docker
     │
     ├── Spark experiments
     ├── ML training
     └── result generation
              │
              ▼
          results/
              │
              ▼
        Streamlit app
              │
              ▼
        Cloud deployment
```

The dashboard consumes saved experiment outputs.

This avoids needing a cloud Spark cluster merely to demonstrate the project.

## Recommended deployment order

```text
1. Local Spark
2. Local ML
3. Local Streamlit
4. Docker
5. Docker validation
6. Deploy Streamlit dashboard
```

Do not start deployment before the experiment is stable.

---

# 30. Docker Plan

## Docker responsibilities

The container should provide:

- Python
- Java
- PySpark
- ML dependencies
- CLI
- dashboard runtime

## First target

Make this work:

```bash
docker compose up
```

Then:

```bash
docker compose exec app skewctl system check
```

Do not introduce Kubernetes unless the course specifically requires it.

---

# 31. Testing Strategy

Write small tests for the core logic.

## Test dataset generation

Check:

```text
row count
skew percentage approximately correct
schema
reproducibility with seed
```

## Test skew metrics

Use a tiny known dataset:

```text
A A A A B C
```

Verify expected counts and skew metrics.

## Test mitigation

Verify:

```text
salt column exists
salt range is valid
logical aggregation can be reconstructed
```

## Test CLI

At minimum:

```bash
skewctl --help
skewctl system check
skewctl data generate --help
```

---

# 32. Experiment Discipline

Every experiment must record:

```text
experiment ID
seed
row count
skew level
partition count
Spark configuration
mitigation method
runtime
shuffle metrics
partition metrics
ML prediction
```

Do not manually edit the results after execution.

---

# 33. Research Questions

Use these as the project's analytical backbone.

### RQ1
How does increasing key concentration affect Spark partition balance and execution time?

### RQ2
Which simple statistical features best characterize severe data skew?

### RQ3
Can a lightweight classification model identify skew severity from experiment telemetry?

### RQ4
Does salting reduce partition imbalance and execution overhead for highly skewed workloads?

### RQ5
Can a simple ML-driven decision rule select mitigation more appropriately than applying one fixed strategy to every workload?

---

# 34. Hypotheses

### H1
Increasing key concentration increases partition imbalance.

### H2
Increasing partition imbalance increases Spark execution cost.

### H3
Key concentration and partition-distribution metrics are useful predictors of skew severity.

### H4
A lightweight tabular ML classifier can distinguish normal, low-skew, and high-skew workloads.

### H5
Salting reduces the impact of extreme key concentration in the selected workload.

### H6
Conditional mitigation performs better than blindly applying one mitigation strategy to every workload.

---

# 35. Success Criteria

The project is considered complete only when all are true:

- [ ] Spark baseline runs successfully.
- [ ] Controlled skew datasets are generated reproducibly.
- [ ] Normal and skewed executions are compared.
- [ ] Spark UI behavior is understood and documented.
- [ ] EDA statistics are generated.
- [ ] At least one statistical skew detector exists.
- [ ] ML feature dataset is generated.
- [ ] At least three classifiers are compared.
- [ ] Proper evaluation metrics are reported.
- [ ] Repartitioning is tested.
- [ ] Salting is implemented.
- [ ] Before/after performance is quantified.
- [ ] Automatic mitigation selection works.
- [ ] CLI provides the major workflows.
- [ ] Streamlit dashboard displays experiment results.
- [ ] Project runs from a clean environment.
- [ ] README explains architecture and reproduction steps.
- [ ] Results are based on real measured runs.

---

# 36. Viva Preparation Checklist

You should be able to answer these without reading code.

## Spark fundamentals

- What is Spark?
- Why does Spark partition data?
- What is a DataFrame?
- What is a transformation?
- What is an action?
- What is lazy evaluation?
- What happens during `groupBy()`?
- What is a shuffle?
- What is a task?
- What is a stage?

## Skew

- What is data skew?
- What creates a hot key?
- Why does skew cause stragglers?
- Why does one partition become disproportionately expensive?
- Why does more partitioning not automatically eliminate skew?

## Statistics / EDA

- Why use standard deviation?
- What is an outlier?
- What is concentration?
- Why should EDA happen before ML?

## ML

- Why classification?
- Why these features?
- Why Random Forest?
- Why not deep learning?
- What does precision mean?
- What does recall mean?
- Why F1?
- Why use a confusion matrix?

## Mitigation

- What is repartitioning?
- What is salting?
- Why does salting help hot keys?
- What is the cost of mitigation?
- Can mitigation ever make performance worse?

## Deployment

- Why is Spark executed locally?
- Why is the dashboard separate from the Spark engine?
- Why use Docker?
- How would this architecture change for a real distributed production cluster?

---

# 37. Implementation Order — Do Not Deviate

## Phase 0 — Environment

```text
Java → Python → PySpark → VS Code → Git
```

## Phase 1 — Spark Fundamentals

```text
SparkSession → DataFrame → groupBy → action → Spark UI
```

## Phase 2 — Data Generation

```text
Normal → 30% → 50% → 70% → 90% skew
```

## Phase 3 — Measurement

```text
partition metrics → runtime → shuffle → EDA
```

## Phase 4 — Statistical Detector

```text
skew ratio → concentration → variance → severity score
```

## Phase 5 — ML

```text
features → train → compare models → evaluate
```

## Phase 6 — Mitigation

```text
repartition → salting → benchmark
```

## Phase 7 — Automation

```text
ML prediction → mitigation selection → re-run
```

## Phase 8 — CLI

```text
Typer + Rich → unified workflow
```

## Phase 9 — Dashboard

```text
Streamlit → charts → model → before/after
```

## Phase 10 — Reproducibility

```text
Docker → clean run → README
```

## Phase 11 — Deployment

```text
Deploy dashboard only
```

---

# 38. Definition of Done

The final demonstration should be executable as a single narrative:

```text
$ skewctl experiment run --skew 0.90 --rows 1000000 --mitigation auto
```

The terminal should show:

```text
1. Dataset generated
2. Spark job executed
3. Skew measured
4. ML classifier predicts severity
5. Mitigation selected
6. Mitigated Spark job executed
7. Before/after metrics printed
8. Results saved
```

Then:

```text
$ skewctl dashboard launch
```

The dashboard should visually explain the same experiment.

---

# 39. Final Project Narrative

The final presentation should tell one coherent story:

```text
We begin with the basic Spark problem:

A distributed workload is only efficient when work is reasonably balanced.

        ↓

We intentionally change the data distribution.

        ↓

Spark develops partition imbalance and straggler behavior.

        ↓

We quantify the problem using EDA and statistics.

        ↓

We engineer execution-level features.

        ↓

A lightweight ML model predicts skew severity.

        ↓

The system selects a mitigation strategy.

        ↓

Salting/repartitioning is applied.

        ↓

The Spark job is rerun.

        ↓

We measure whether the system actually improved performance.
```

That is the project.

Everything else exists to support that story.

---

# 40. Immediate Next Step

Start with **Phase 0 + Phase 1 only**.

Your first milestone is:

```bash
skewctl system check
```

followed by:

```bash
skewctl data generate --rows 1000000 --skew 0.10
skewctl data generate --rows 1000000 --skew 0.90
skewctl spark baseline --input data/generated/skew_90.parquet
```

Do not build the dashboard, Docker image, or ML model until those commands produce reliable Spark metrics.

---

## Source Alignment

This implementation is intentionally aligned with the professor-provided Spark material: SparkSession/DataFrame data loading, partitioned distributed processing, transformations and lazy evaluation; EDA, distribution analysis, outlier detection, statistical measures; feature engineering and vector assembly; Spark MLlib classification, pipelines, model evaluation, model selection and cross-validation; and the overall data-analysis workflow from raw data through prediction/decision making.
