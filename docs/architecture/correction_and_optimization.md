# PROJECT CORRECTION & OPTIMIZATION SPECIFICATION
## Data Skew Intelligence — Spark Execution, ML, Testing, CLI, and Environment Fixes

## 0. Purpose

This document is the authoritative remediation plan for the current project state after the first successful `run.py` execution.

The software pipeline currently executes successfully, but the experiment is not yet demonstrating real Spark execution skew.

Observed result:

```text
Dataset                  100,000 records
Hot-key concentration      70.0%
Spark baseline              0.19 s
Max partition             1,000
Partition std. dev.          0.0
Prediction                  NORMAL
Mitigation                   NONE
Performance improvement      0.0%
Tests                       6 passed
```

The goal is to correct the **experimental methodology**, not merely make the output look better.

The final system must demonstrate:

```text
Controlled Data Skew
        ↓
Spark Shuffle
        ↓
Execution-Level Partition Imbalance
        ↓
Statistical Detection
        ↓
ML Severity Classification
        ↓
Mitigation
        ↓
Re-execution
        ↓
Measured Improvement
```

The project must remain simple enough for a course-level viva while demonstrating strong understanding of Spark fundamentals.

---

# 1. Current Problems

## 1.1 Input partition metrics are being mistaken for shuffle skew

Current observation:

```text
Max Partition Records     1,000
Partition Record Std Dev    0.0
```

This strongly indicates that the implementation is measuring input/read partition sizes rather than the partitions created by the relevant shuffle.

A dataset can contain:

```text
70% HOT_KEY
30% OTHER_KEYS
```

while the input file is physically distributed into equal-sized input partitions.

Therefore:

```text
equal input partitions
≠
equal post-shuffle workload
```

### Required fix

The baseline must execute an actual shuffle-producing operation and measure the resulting execution behavior.

Primary operation:

```python
df.groupBy("key").count()
```

For a more computationally meaningful workload, use:

```python
from pyspark.sql import functions as F

result = (
    df.groupBy("key")
      .agg(
          F.count("*").alias("record_count"),
          F.sum("value").alias("total_value"),
          F.avg("value").alias("avg_value")
      )
)
```

The project must measure the partition/task behavior associated with the shuffle stage rather than only the original file partitions.

---

# 2. Correct Experimental Model

The experiment must explicitly separate three concepts.

## A. Data skew

How concentrated the logical key distribution is.

Example:

```text
HOT_KEY = 70% of records
```

## B. Partition skew

How unevenly records are distributed across Spark partitions after a shuffle.

Example:

```text
Partition 1  ->  10,000
Partition 2  ->  11,200
Partition 3  ->  9,800
Partition 4  ->  68,000
```

## C. Performance impact

How the uneven distribution affects:

```text
task duration
stage duration
shuffle read
shuffle write
spill
wall-clock execution time
```

The final project must distinguish these three layers.

---

# 3. Baseline Experiment Fix

## 3.1 Force a relevant shuffle

Do not simply load the dataset and inspect input partitions.

Run a shuffle-producing transformation/action:

```python
grouped = (
    df.groupBy("key")
      .agg(
          F.count("*").alias("count"),
          F.sum("value").alias("sum_value")
      )
)

grouped.collect()
```

The action must actually execute the plan.

Prefer a realistic aggregation over a trivial `count()` if the workload remains too fast to observe.

---

# 4. Correct Spark Telemetry

## 4.1 Minimum metrics

Capture:

```text
execution_time
stage_duration
num_partitions
max_partition_records
min_partition_records
mean_partition_records
partition_std
shuffle_read_bytes
shuffle_write_bytes
```

Where available, also capture:

```text
task_duration_max
task_duration_mean
task_duration_std
spill_memory_bytes
spill_disk_bytes
```

Do not fabricate metrics that Spark does not provide.

---

# 5. Measure Post-Shuffle Partition Distribution

The existing code should be changed so that partition statistics refer to the dataset/RDD produced by the relevant shuffle.

Use a partition-size inspection function such as:

```python
def partition_sizes(df):
    return (
        df.rdd
          .mapPartitions(lambda rows: [sum(1 for _ in rows)])
          .collect()
    )
```

Important:

This function should be applied deliberately to the relevant post-shuffle representation, not blindly to the original input DataFrame.

Expected output:

```text
[8200, 9100, 8700, 67000, 9000, 9500, 8500, 9000]
```

rather than:

```text
[1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]
```

---

# 6. Use a Controlled Experiment Matrix

Do not train ML from a single 70% skew experiment.

Generate multiple controlled levels:

```text
0%
10%
20%
30%
40%
50%
60%
70%
80%
90%
95%
99%
```

For each level:

```text
Generate
→ Run Spark
→ Measure telemetry
→ Save experiment record
```

This creates a genuine experimental dataset.

Recommended baseline:

```text
100,000 records
```

For heavier stress testing:

```text
1,000,000 records
```

Optional:

```text
5,000,000 records
```

Do not begin at very large sizes.

---

# 7. Important Performance Correction

A runtime of:

```text
0.19 s
```

is too small to provide useful evidence for this experiment.

Do not artificially sleep or delay the program.

Instead increase computational work legitimately.

Use:

```python
groupBy("key").agg(...)
```

with several aggregations.

Optional workload:

```python
F.count("*")
F.sum("value")
F.avg("value")
F.min("value")
F.max("value")
```

Use a modestly larger dataset when needed.

The goal is:

```text
observable Spark behavior
```

not an artificially slow program.

---

# 8. Do Not Overfit the Experiment to Runtime

Runtime alone is noisy on a local machine.

Therefore the primary evidence should be the combination of:

```text
partition imbalance
+
task duration imbalance
+
shuffle metrics
+
runtime
```

A mitigation may be considered useful even if wall-clock time changes very little on a small local dataset, provided the partition imbalance and relevant execution metrics improve.

The final report must show all major metrics rather than only execution time.

---

# 9. Statistical Skew Detector

The current detector should not use a hard-coded label derived from the requested input skew.

It should calculate severity from actual measurements.

Recommended features:

```text
top1_key_concentration
skew_ratio
partition_cv
partition_std
max_to_mean_partition_ratio
```

A simple explainable rule system can be used before ML.

Example:

```text
NORMAL
    balanced partition distribution

LOW_SKEW
    noticeable imbalance

HIGH_SKEW
    severe partition concentration
```

Do not hide the thresholds.

Store them in configuration.

---

# 10. Skew Ratio

Use an explicit metric such as:

```text
skew_ratio =
max_partition_records / mean_partition_records
```

Example:

```text
max = 70,000
mean = 12,500

skew_ratio = 5.6
```

Also calculate:

```text
coefficient_of_variation =
partition_std / mean_partition_records
```

These metrics make the detector interpretable.

---

# 11. ML Problem Correction

Current result:

```text
Logistic Regression
F1 = 1.0
Prediction = NORMAL
```

This must not be accepted as meaningful until the ML dataset and labels are validated.

## Required training data

Build ML rows from independent Spark experiments:

```text
experiment_id
skew_percentage
top1_concentration
skew_ratio
partition_mean
partition_std
partition_cv
max_partition
shuffle_read
shuffle_write
execution_time
task_duration_variance
severity_label
```

---

# 12. Prevent Label Leakage

Do not use the target label directly or a trivially derived copy of it as an ML feature.

For example, if:

```text
severity_label = HIGH_SKEW
```

is assigned directly from:

```text
skew_percentage > 0.6
```

then using `skew_percentage` as the only deciding feature can make the problem trivial.

Use a deliberate experimental design.

Best approach:

## Feature set

Use execution/telemetry features:

```text
partition_cv
max_to_mean_ratio
shuffle_read
shuffle_write
task_duration_variance
spill
```

Keep the label based on independently defined severity criteria.

---

# 13. Unseen-Experiment Validation

The final ML evaluation should use experiments the model did not see during training.

Recommended split:

```text
Training experiments
→ lower/intermediate skew levels

Validation/Test experiments
→ held-out skew levels
```

This is stronger than randomly duplicating very similar observations.

Example:

```text
Train:
0%, 10%, 20%, 30%, 50%, 60%

Test:
40%, 70%, 80%, 90%, 95%
```

The exact split can be refined after inspecting the experiment dataset.

---

# 14. ML Models

Keep the model set small:

```text
Logistic Regression
Decision Tree
Random Forest
```

Compare:

```text
accuracy
precision
recall
F1
```

Prefer macro/weighted F1 for class imbalance.

Do not add deep learning.

Do not add an LLM.

Do not add unnecessary model frameworks.

---

# 15. Model Selection

Choose the best model using actual evaluation results.

Example:

```text
Logistic Regression   F1 0.84
Decision Tree         F1 0.89
Random Forest         F1 0.93

Selected: Random Forest
```

The values above are examples only.

Never hard-code them.

If a simple model performs best, use the simple model.

---

# 16. Correct Detection Flow

The final detection path should be:

```text
Spark Experiment
      ↓
Telemetry
      ↓
Feature Engineering
      ↓
Statistical Severity
      ↓
ML Prediction
      ↓
Final Decision
```

Do not allow the ML model to overwrite a clearly invalid statistical result without explanation.

When model confidence is low:

```text
ML confidence < threshold
        ↓
fall back to statistical detector
```

This makes the system safer and easier to defend.

---

# 17. Salting Implementation

The salting implementation must be a real mitigation.

For a hot key:

```text
HOT_KEY
```

transform logically into:

```text
HOT_KEY_0
HOT_KEY_1
HOT_KEY_2
...
```

The project must validate:

### A. Distribution

Partition imbalance decreases.

### B. Correctness

The final aggregated result remains equivalent to the unsalted logical aggregation.

This is mandatory.

---

# 18. Correctness Test for Salting

Create a test:

```text
baseline aggregation
        vs
salted aggregation
        ↓
same logical results
```

Do not compare row ordering.

Compare normalized key/value results after sorting.

Example requirement:

```text
assert baseline_result == reconstructed_salted_result
```

after deterministic normalization.

---

# 19. Mitigation Strategy

Use a simple strategy map:

```text
NORMAL
→ NONE

LOW_SKEW
→ REPARTITION

HIGH_SKEW
→ SALTING
```

Do not add many mitigation methods unless experiments show a clear benefit.

AQE can be discussed as an advanced Spark capability, but it does not need to become another major subsystem.

---

# 20. Before/After Experiment

Run the exact same logical workload:

```text
BEFORE
→ skewed input
→ Spark workload
→ telemetry

AFTER
→ mitigated input
→ same Spark workload
→ telemetry
```

Compare:

```text
partition_cv
max_partition
task-duration variance
shuffle
runtime
```

The comparison must use identical measurement code.

---

# 21. Result Interpretation

The system must support all outcomes.

### Positive result

```text
partition imbalance decreased
runtime decreased
```

### Mixed result

```text
partition imbalance decreased
runtime nearly unchanged
```

### Negative result

```text
mitigation increased runtime
```

Do not force a positive conclusion.

A legitimate experimental finding can be:

> Salting improved partition balance but did not produce a measurable local runtime improvement at the tested scale.

That is academically stronger than fake optimization.

---

# 22. Fix Pandas Compatibility

Current warning:

```text
PySpark does not yet fully support pandas >= 3.0.0
```

Pin:

```text
pandas<3
```

in `requirements.txt`.

Then regenerate the environment.

Do not suppress this warning without addressing the dependency range.

---

# 23. Fix NumPy / Joblib Warning

Current warning:

```text
Setting the shape on a NumPy array has been deprecated
```

This originates in the installed dependency combination.

First inspect versions:

```bash
python -c "import numpy, joblib; print(numpy.__version__, joblib.__version__)"
```

Then pin compatible versions only if the warning persists in the actual project environment.

Do not blindly downgrade packages without verifying the dependency graph.

---

# 24. Java Standardization

Current environment:

```text
OpenJDK 25.0.3
```

The project should standardize on:

```text
Java 17 LTS
```

for reproducibility.

Document Java 17 in:

```text
README.md
requirements/setup documentation
GitHub Actions
```

Do not make Java version switching part of every `run.py` execution.

The program should clearly report an unsupported Java version.

---

# 25. Windows Spark Warnings

Current warnings include:

```text
Did not find winutils.exe
Unable to load native-hadoop library
```

Do not chase these warnings as the first priority.

The current Spark job successfully executed.

Handle them by:

```text
reducing terminal noise
documenting known Windows warnings
keeping detailed Spark logs available
```

Only introduce additional Hadoop compatibility tooling if the project actually requires a feature that fails without it.

---

# 26. Spark Logging Cleanup

The terminal should not be dominated by:

```text
WARN Shell
WARN NativeCodeLoader
INFO SparkContext
INFO BlockManager
```

Configure Spark logging to a reasonable level.

Keep:

```text
ERROR
```

visible.

Write detailed Spark logs to:

```text
logs/spark.log
```

The premium CLI should show only project-level status.

---

# 27. Spark Session Warning

Current warning:

```text
Using an existing Spark session; only runtime SQL configurations will take effect.
```

This means multiple parts of the application are attempting to create/reconfigure Spark sessions.

Fix:

```text
one Spark session factory
one shared session per pipeline execution
clean shutdown
```

Provide:

```python
get_spark_session()
```

from one central module.

Do not create Spark sessions inside utility functions.

---

# 28. Pipeline Lifecycle

The correct lifecycle is:

```text
run.py
  ↓
create Spark session
  ↓
pass session into required modules
  ↓
complete experiment
  ↓
run tests without creating unnecessary sessions
  ↓
stop Spark
  ↓
write final result
```

Avoid creating Spark sessions independently in every test/module.

---

# 29. Testing Improvements

Existing:

```text
6 passed
```

is good for software health but insufficient for scientific correctness.

Add domain-specific tests:

```text
test_skew_generation_distribution
test_partition_imbalance_detection
test_high_skew_classification
test_salting_reduces_hot_key_concentration
test_salting_preserves_aggregation
test_ml_feature_no_target_leakage
test_pipeline_smoke
```

---

# 30. Test Categories

## Fast unit tests

Run automatically:

```bash
pytest -q
```

Must finish quickly.

## Spark integration tests

Test real Spark behavior with a small deterministic dataset.

## Benchmark experiments

Run through:

```bash
python run.py
```

Do not mix expensive benchmarks into the default unit-test suite.

---

# 31. One-Click Runner

The project must remain a one-button application.

The user runs:

```bash
python run.py
```

or clicks the Antigravity **Run** button.

The runner must perform:

```text
Environment
→ Dataset
→ EDA
→ Spark baseline
→ Telemetry
→ ML
→ Detection
→ Mitigation
→ Post-run
→ Tests
→ Results
```

No manual chain of commands.

---

# 32. Runner Modes

Support:

```bash
python run.py
python run.py --check
python run.py --quick
python run.py --clean
python run.py --dashboard
```

Normal users only need:

```bash
python run.py
```

---

# 33. Quick Mode

`--quick` must use:

```text
10,000 records
small partition count
small experiment matrix
minimal ML workload
```

Purpose:

```text
debugging
CI
Antigravity testing
quick demonstration
```

It must still exercise:

```text
dataset
Spark
skew detection
mitigation
tests
```

---

# 34. Full Mode

Normal mode should run a reasonable experiment matrix such as:

```text
0%
20%
40%
60%
70%
80%
90%
```

Do not run dozens of massive experiments automatically.

The goal is maximum information per unit of runtime.

---

# 35. Experiment Caching

Avoid rerunning identical experiments unnecessarily.

Use a deterministic experiment ID derived from:

```text
row_count
skew_ratio
partitions
seed
workload_version
```

If an identical valid result exists:

```text
use cached result
```

unless the user specifies:

```bash
python run.py --clean
```

This will make iteration much faster.

---

# 36. Result Storage

Each run:

```text
results/
└── YYYY-MM-DD_HH-MM-SS/
    ├── config.json
    ├── experiment_matrix.csv
    ├── partition_metrics.csv
    ├── baseline_metrics.csv
    ├── mitigation_metrics.csv
    ├── ml_dataset.csv
    ├── ml_metrics.json
    └── summary.json
```

Also:

```text
results/latest/
```

---

# 37. Final CLI

The final CLI should expose the actual experiment.

Example:

```text
╔══════════════════════════════════════════════════════════════╗
║  S K E W C T L                                              ║
║  INTELLIGENT DATA SKEW ENGINE                               ║
╚══════════════════════════════════════════════════════════════╝

[1/8] DATASET
✓ 100,000 records
✓ Hot-key concentration: 70.0%

[2/8] SPARK BASELINE
✓ Shuffle completed
✓ Post-shuffle partitions measured

[3/8] DETECTION
✓ Partition CV: 1.84
✓ Severity: HIGH_SKEW

[4/8] ML
✓ Selected: Random Forest

[5/8] MITIGATION
✓ Strategy: SALTING

[6/8] RE-RUN
✓ Post-mitigation shuffle completed

[7/8] TESTS
✓ 10 passed

[8/8] RESULTS
✓ Saved to results/latest/
```

---

# 38. Final Performance Table

Show:

```text
Metric                     Before       After
------------------------------------------------
Max partition              ...
Mean partition             ...
Partition CV               ...
Task duration variance     ...
Shuffle read               ...
Shuffle write              ...
Execution time             ...
```

This should become the central evidence of the project.

---

# 39. ML Output

Show:

```text
MODEL EVALUATION

Model                  F1
---------------------------
Logistic Regression    ...
Decision Tree          ...
Random Forest          ...

Selected model: ...
```

Then:

```text
CURRENT EXPERIMENT

Prediction: HIGH_SKEW
Confidence: ...
Recommended mitigation: SALTING
```

Only display confidence if the chosen model actually provides a calibrated/probability output.

---

# 40. Dashboard

The dashboard should consume:

```text
results/latest/
```

It should display:

```text
Dataset profile
Key distribution
Partition distribution
Before/after metrics
ML evaluation
Mitigation result
```

Do not rerun the entire Spark pipeline every time the page loads.

---

# 41. GitHub / CI Requirements

GitHub Actions should validate:

```text
Python setup
Java 17
dependency installation
pytest
quick pipeline
```

Recommended sequence:

```text
install dependencies
→ run fast tests
→ run quick Spark pipeline
```

Do not execute the full benchmark matrix in every CI run.

---

# 42. Repository Hygiene

Do not commit:

```text
.venv/
generated Parquet datasets
Spark warehouse
temporary logs
large model binaries
benchmark output
```

Commit:

```text
source code
tests
requirements.txt
configuration
README
small example output
CI workflow
```

---

# 43. Scientific Definition of Success

The project should be considered successful when:

```text
1. Increasing key concentration changes post-shuffle partition distribution.

2. Higher skew produces measurable partition/task imbalance.

3. Statistical metrics identify severity.

4. ML can classify severity on unseen experiments without leakage.

5. Salting reduces partition imbalance.

6. Logical aggregation correctness is preserved.

7. Before/after telemetry is measurable.

8. Results are reproducible.

9. The full system runs from one entry point.
```

Do not define success as:

```text
"the model achieved 100% accuracy."
```

The Spark experiment is the primary contribution.

ML is the supporting intelligent layer.

---

# 44. Priority Order for Implementation

Fix in exactly this order:

```text
P0 — EXPERIMENT CORRECTNESS
    ↓
P1 — SHUFFLE/PARTITION TELEMETRY
    ↓
P2 — EXPERIMENT MATRIX
    ↓
P3 — REAL MITIGATION
    ↓
P4 — ML DATASET + LEAKAGE CHECK
    ↓
P5 — DOMAIN TESTS
    ↓
P6 — ENVIRONMENT / DEPENDENCY CLEANUP
    ↓
P7 — CLI POLISH
    ↓
P8 — DASHBOARD
```

Do not work on the dashboard or visual polish before P0–P5 are correct.

---

# 45. Final Target Architecture

```text
                         run.py
                           │
                           ▼
                  Environment Validation
                           │
                           ▼
                  Controlled Data Generator
                           │
                           ▼
                         Spark
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                Baseline      Telemetry
                    │             │
                    └──────┬──────┘
                           ▼
                   Statistical Detector
                           │
                           ▼
                    ML Classifier
                           │
                           ▼
                  Mitigation Decision
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
             Repartition         Salting
                  │                 │
                  └────────┬────────┘
                           ▼
                    Spark Re-run
                           │
                           ▼
                  Before/After Metrics
                           │
                           ▼
                       Testing
                           │
                           ▼
                    Results Export
                           │
                           ▼
                    Premium CLI
                           │
                           ▼
                  Optional Dashboard
```

---

# 46. Final Engineering Principle

Do not hide a weak experiment behind a polished interface.

The correct progression is:

```text
Make Spark behavior correct
        ↓
Measure it correctly
        ↓
Make mitigation correct
        ↓
Make ML scientifically valid
        ↓
Test everything
        ↓
Only then polish the CLI/dashboard
```

The current project already proves that the orchestration, dataset generation, tests, and result export can execute. The next implementation pass must focus on making the **Spark experiment itself truthful and measurable** before adding more features.
