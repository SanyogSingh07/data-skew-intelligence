# Data Skew Intelligence — Code Optimization & De-cluttering Plan

> **Purpose:** Use this document as the cleanup/optimization specification before the project grows further.
>
> **Goal:** Keep the project small, reproducible, testable, and centered on the course concepts: Spark partitions, skew, EDA, statistics, feature engineering, ML classification, mitigation, and performance comparison.

---

## 1. Cleanup Objective

The project should have one clear flow:

```text
Generate data
    ↓
Run Spark baseline
    ↓
Measure skew + execution behavior
    ↓
Build experiment/ML features
    ↓
Classify skew severity
    ↓
Select mitigation
    ↓
Re-run Spark job
    ↓
Compare before vs after
    ↓
Display results
```

Anything that does not directly support this flow should be removed, postponed, or isolated as optional.

---

# 2. Scope Freeze

## Keep in the core project

- PySpark
- SparkSession / DataFrames
- Controlled synthetic data generation
- `groupBy()`-based skew experiment
- Partition statistics
- EDA/statistical skew analysis
- Feature engineering
- Simple ML classification
- Repartitioning
- Salting
- Before/after benchmarking
- Typer + Rich CLI
- Pytest
- Streamlit results dashboard
- Docker only after local functionality is stable

## Move to optional

- SHAP
- MLflow
- AQE experiments
- Large-scale stress tests
- Cloud deployment
- Advanced security analysis

## Remove from the implementation unless a later requirement explicitly appears

- Kubernetes
- Kafka
- Airflow
- Hadoop cluster setup
- React frontend
- FastAPI backend
- PostgreSQL/MongoDB
- TensorFlow/PyTorch
- GPU/CUDA
- Microservices
- Authentication
- Complex cloud infrastructure

**Reason:** these technologies add operational complexity without improving the core demonstration of Spark data skew.

---

# 3. Simplify the Architecture

Use this final architecture:

```text
                       CLI
                        │
        ┌───────────────┼────────────────┐
        ↓               ↓                ↓
     Generate        Analyze          Benchmark
        │               │                │
        └───────────────┼────────────────┘
                        ↓
                     Spark
                        │
               ┌────────┴────────┐
               ↓                 ↓
           Statistics        Telemetry
               │                 │
               └────────┬────────┘
                        ↓
                Feature Engineering
                        ↓
                  ML Classifier
                        ↓
                 Mitigation Choice
                        ↓
                Salting / Repartition
                        ↓
                  Re-run + Compare
                        ↓
                   Results Store
                        ↓
                    Dashboard
```

Do not split this into separate services.

---

# 4. Recommended Final Repository

Use this structure and remove duplicate/unused folders:

```text
data-skew-intelligence/
│
├── src/
│   └── data_skew/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── spark_session.py
│       ├── data_generator.py
│       ├── skew_analysis.py
│       ├── metrics.py
│       ├── features.py
│       ├── model.py
│       ├── mitigation.py
│       └── pipeline.py
│
├── dashboard/
│   └── app.py
│
├── tests/
│   ├── conftest.py
│   ├── test_data_generator.py
│   ├── test_skew_analysis.py
│   ├── test_metrics.py
│   ├── test_mitigation.py
│   ├── test_model.py
│   ├── test_cli.py
│   └── test_smoke.py
│
├── scripts/
│   └── run_experiment.py
│
├── configs/
│   └── default.yaml
│
├── results/
│   └── .gitkeep
│
├── notebooks/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── README.md
└── LICENSE
```

### Remove if currently present

- Duplicate Spark scripts in multiple directories
- Duplicate ML notebooks and scripts doing the same work
- Generated datasets committed to Git
- Temporary Spark warehouse directories
- Experimental scripts that are no longer imported
- Multiple requirement files with overlapping package declarations

---

# 5. Adopt a `src/` Layout

Do not keep application logic scattered across the repository root.

Use:

```text
src/data_skew/
```

This prevents accidental imports from the repository root and makes pytest/GitHub Actions behave more consistently.

Install the package in development mode:

```bash
pip install -e .
```

---

# 6. One Responsibility per Module

## `spark_session.py`

Only create/configure Spark sessions.

```python
def create_spark_session(app_name: str = "DataSkewIntelligence") -> SparkSession:
    ...
```

Do not generate data, train models, or print CLI output here.

## `data_generator.py`

Only generate deterministic synthetic datasets.

Required parameters:

```text
rows
skew_ratio
num_keys
seed
format
output_path
```

## `skew_analysis.py`

Only calculate distribution/skew metrics.

Examples:

```text
mean_key_frequency
max_key_frequency
std_key_frequency
top1_concentration
skew_ratio
```

## `metrics.py`

Only collect/normalize Spark experiment metrics.

## `features.py`

Convert raw experiment metrics into the ML feature vector.

## `model.py`

Only train/load/predict/evaluate the classifier.

## `mitigation.py`

Only implement:

- repartitioning
- salting

Keep AQE outside the core until the required experiments are stable.

## `pipeline.py`

Orchestrate the complete workflow.

It should call modules; it should not contain all implementation details.

## `cli.py`

Only user interaction, validation, and command routing.

---

# 7. Remove Global Side Effects

Avoid code like this at module import time:

```python
spark = SparkSession.builder.getOrCreate()
model = load_model()
run_experiment()
```

This causes import-time failures in tests and GitHub Actions.

Use functions instead:

```python
def main() -> None:
    spark = create_spark_session()
    try:
        run_pipeline(spark)
    finally:
        spark.stop()
```

Tests should import modules without starting Spark jobs automatically.

---

# 8. Centralize Configuration

Do not hard-code values throughout the codebase.

Keep defaults in one place:

```text
rows = 100000
skew_ratio = 0.70
num_keys = 10
seed = 42
shuffle_partitions = 8
```

Use a small configuration object/dataclass rather than repeated magic numbers.

Example:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ExperimentConfig:
    rows: int = 100_000
    skew_ratio: float = 0.70
    num_keys: int = 10
    seed: int = 42
    shuffle_partitions: int = 8
```

The CLI can override these values.

---

# 9. Validate Inputs Early

Bad input should fail immediately with a clear error.

Rules:

```text
rows > 0
0.0 <= skew_ratio < 1.0
num_keys >= 2
seed is an integer
shuffle_partitions >= 1
```

Do not allow silent fallback to incorrect values.

For Typer, use typed options and explicit validation.

---

# 10. Make Data Generation Deterministic

Every experiment must accept a seed.

Default:

```text
42
```

A repeated run with the same configuration should produce equivalent data/metrics within expected Spark runtime variability.

This is essential for:

- testing
- debugging
- reproducibility
- ML dataset generation
- viva demonstrations

---

# 11. Keep Raw Data Separate from Results

Use:

```text
results/
```

for experiment outputs only.

Do not mix:

```text
input data
models
logs
metrics
plots
```

in the same directory.

Recommended:

```text
artifacts/
├── data/
├── metrics/
├── models/
└── plots/
```

If generated artifacts become large, keep them out of Git.

---

# 12. Do Not Commit Large Generated Datasets

The dataset should be reproducible through the generator.

Good:

```bash
python -m data_skew.cli generate --rows 1000000 --skew 0.70 --seed 42
```

Bad:

```text
Git repository contains 1 GB of generated Parquet files.
```

Commit a small sample only if it helps users understand the schema.

---

# 13. Reduce the ML Scope

Do not build a large ML framework.

Use three models only:

```text
1. Logistic Regression — baseline
2. Decision Tree — interpretable
3. Random Forest — stronger nonlinear baseline
```

Evaluate using:

```text
precision
recall
F1
accuracy
confusion matrix
```

Use F1 as the primary comparison metric when class balance is imperfect.

Do not add deep learning.

---

# 14. Prevent Data Leakage in the ML Pipeline

The ML dataset should be generated from completed experiments.

Do not use post-mitigation metrics as input features when the target describes the pre-mitigation skew state.

Correct direction:

```text
Pre-mitigation experiment
        ↓
Features
        ↓
Label
        ↓
Train classifier
```

Then:

```text
New experiment
        ↓
Features
        ↓
Prediction
        ↓
Mitigation
```

Keep evaluation data isolated from training.

---

# 15. Simplify the Mitigation Strategy

The core decision table should be deterministic and easy to explain:

| Prediction | Action |
|---|---|
| NORMAL | No mitigation |
| LOW_SKEW | Repartition |
| HIGH_SKEW | Salting |

Do not automatically combine multiple mitigation techniques until the individual techniques have been measured independently.

This makes the experiment scientifically cleaner.

---

# 16. Salting Must Preserve Semantics

A common implementation bug is salting a key and then forgetting that the original key semantics are required for the final aggregation.

Use the normal pattern:

```text
Original key
    ↓
Add salt for distribution
    ↓
Aggregate by (key, salt)
    ↓
Remove salt / aggregate again by key
```

The final result must match the unsalted result.

Test this explicitly.

---

# 17. Do Not Measure Spark Performance with Tiny Data

Use two modes.

## Smoke mode

```text
10K–100K rows
```

Used for tests and development.

## Benchmark mode

```text
1M+ rows
```

Used manually for performance experiments.

Never run the full benchmark automatically inside GitHub Actions.

---

# 18. Separate Correctness from Performance

A test should answer:

> Did the code produce the correct result?

A benchmark should answer:

> How fast did it run?

Do not make correctness tests depend on an exact execution time.

Avoid assertions like:

```python
assert execution_time < 5
```

These are unstable across machines and CI runners.

Instead assert:

```text
row count preserved
schema preserved
aggregation correct
salted result == unsalted result
```

---

# 19. Fix Spark Test Stability

Use a shared local Spark fixture:

```python
.config("spark.ui.enabled", "false")
.config("spark.sql.shuffle.partitions", "4")
.config("spark.driver.bindAddress", "127.0.0.1")
```

Keep test datasets tiny.

Stop Spark after tests.

Do not call `SparkSession.builder.getOrCreate()` repeatedly from every test without a fixture.

---

# 20. Use `pyproject.toml` as the Main Tool Configuration

Instead of scattering configuration, centralize it.

Example structure:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "data-skew-intelligence"
version = "0.1.0"
dependencies = [
    "pyspark",
    "pandas",
    "numpy",
    "scikit-learn",
    "pyarrow",
    "plotly",
    "streamlit",
    "typer",
    "rich",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "ruff",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B"]
```

Do not maintain conflicting package lists in multiple places.

---

# 21. Dependency Cleanup

Keep production dependencies minimal.

## `requirements.txt`

```text
pyspark
pandas
numpy
scikit-learn
pyarrow
plotly
streamlit
typer
rich
```

## `requirements-dev.txt`

```text
-r requirements.txt
pytest
pytest-cov
ruff
```

Add SHAP/MLflow only when the feature is actually implemented.

### Known cleanup issue

The earlier testing specification contained a formatting error:

```text
 typer
```

Remove the leading space. It must be:

```text
typer
```

---

# 22. CLI Design — Keep It Premium but Small

Use only these commands initially:

```text
skew generate
skew analyze
skew benchmark
skew train
skew predict
skew mitigate
skew run
skew doctor
```

### `generate`

Generate a reproducible dataset.

### `analyze`

Run EDA + skew metrics.

### `benchmark`

Run the Spark performance experiment.

### `train`

Build the ML training dataset and train the three candidate models.

### `predict`

Predict skew severity for a new experiment.

### `mitigate`

Run selected mitigation and compare results.

### `run`

Run the complete pipeline.

### `doctor`

Check Python, Java, PySpark, package imports, directories, and configuration.

Avoid creating dozens of CLI commands.

---

# 23. Premium CLI Rules

Rich should improve readability, not create noise.

Use:

- one header
- one concise status panel
- progress indicators for long operations
- compact summary tables
- clear success/failure messages
- consistent exit codes

Avoid:

- giant ASCII art on every command
- excessive emojis
- printing entire DataFrames
- dumping Spark logs into the terminal
- repeated banners

Example final output:

```text
╭──────────────────── Experiment Complete ────────────────────╮
│ Dataset        : skew_70.parquet                            │
│ Records        : 1,000,000                                 │
│ Skew level     : HIGH                                      │
│ Predicted      : HIGH_SKEW (0.91)                          │
│ Mitigation     : SALTING                                   │
│ Runtime        : 112.4s → 43.1s                            │
│ Improvement    : 61.6%                                     │
╰─────────────────────────────────────────────────────────────╯
```

---

# 24. Fix Logging

Do not mix `print()` statements with logging throughout the application.

Use one logging configuration.

Recommended levels:

```text
INFO     user-facing progress
DEBUG    development diagnostics
WARNING  recoverable issue
ERROR    operation failure
```

Rich can format CLI output while Python logging handles diagnostics.

---

# 25. Add a `doctor` Command

This is one of the highest-value additions for deployment reliability.

It should check:

```text
Python version
Java version
PySpark import
SparkSession startup
required package imports
write permissions
results directory
configuration validity
```

Example:

```bash
python -m data_skew.cli doctor
```

Output:

```text
✓ Python 3.11
✓ Java 17
✓ PySpark import
✓ Spark local session
✓ NumPy
✓ pandas
✓ scikit-learn
✓ PyArrow
✓ Streamlit
✓ CLI configuration

Environment ready.
```

---

# 26. Testing Requirements

Minimum tests:

### Data generation

- row count
- schema
- deterministic seed
- skew ratio direction

### Analysis

- correct key frequencies
- finite metrics
- higher skew produces higher skew score

### Mitigation

- row count preserved
- schema preserved
- salted aggregation equals baseline aggregation
- repartition does not lose records

### ML

- training completes
- expected feature columns exist
- prediction labels are valid
- metrics are finite

### CLI

- help command works
- doctor command works
- invalid arguments fail clearly
- core commands start successfully

### Smoke test

```text
Generate small dataset
      ↓
Analyze
      ↓
Train/predict
      ↓
Mitigate
      ↓
Verify outputs
```

---

# 27. GitHub Actions Optimization

CI should run:

```text
lint
↓
unit tests
↓
small Spark smoke test
↓
CLI smoke test
```

CI should NOT run:

```text
1M+ row benchmarks
large model tuning
long Spark performance comparisons
Streamlit deployment
Docker performance benchmarks
```

Keep CI deterministic and fast.

---

# 28. Ruff + Pytest Commands

Run locally:

```bash
ruff check .
pytest -q
```

Coverage:

```bash
pytest --cov=src/data_skew --cov-report=term-missing
```

Before pushing:

```bash
ruff check . && pytest -q
```

---

# 29. Fix Common Import Problems

Use package imports consistently.

Preferred:

```python
from data_skew.skew_analysis import analyze_skew
```

Avoid mixing:

```python
from src.data_skew...
from data_skew...
from skew_analysis...
```

The `pyproject.toml` `pythonpath = ["src"]` or editable install should provide a single import convention.

---

# 30. Avoid Circular Imports

Dependency direction should be:

```text
config
  ↓
spark_session
  ↓
data_generator / skew_analysis / metrics
  ↓
features
  ↓
model
  ↓
mitigation
  ↓
pipeline
  ↓
cli
```

Lower-level modules must not import the CLI.

---

# 31. Make Functions Small and Testable

Prefer:

```python
def calculate_skew_ratio(max_frequency: float, mean_frequency: float) -> float:
    if mean_frequency <= 0:
        raise ValueError("mean_frequency must be positive")
    return max_frequency / mean_frequency
```

over a 200-line function that loads Spark, calculates statistics, prints output, trains a model, and writes files.

---

# 32. Avoid Recomputing Spark DataFrames

When the same expensive DataFrame is used multiple times, consider:

```python
df.cache()
```

or:

```python
df.persist()
```

Use caching only when reused enough to justify memory cost.

Unpersist after the experiment when appropriate:

```python
df.unpersist()
```

Do not blindly cache every DataFrame.

---

# 33. Avoid `collect()` on Large Data

Do not do:

```python
df.collect()
```

for million-row datasets.

Use Spark aggregations for metrics and collect only small summaries:

```python
summary = df.groupBy("key").count().orderBy(...).limit(10).collect()
```

The CLI and dashboard should receive compact result tables rather than entire Spark DataFrames.

---

# 34. Avoid Repeated Actions

A common Spark performance bug is:

```python
df.count()
df.collect()
df.show()
df.count()
```

Each action may trigger execution.

Group required aggregations into as few Spark jobs as practical and cache only when reuse justifies it.

---

# 35. Prefer Built-in Spark Functions

Use Spark SQL/DataFrame functions for distributed operations.

Avoid Python UDFs unless necessary.

Prefer:

```python
from pyspark.sql import functions as F

F.when(...)
F.count(...)
F.avg(...)
F.stddev(...)
F.rand(...)
```

over Python loops over Spark rows.

This keeps the implementation aligned with Spark's distributed execution model.

---

# 36. Keep pandas at the Edge

Spark should process the large dataset.

Use pandas only for small result sets such as:

```text
experiment metrics
model evaluation summary
top-key statistics
```

Do not convert the million-row input dataset into pandas.

---

# 37. Parquet Rules

Use Parquet for generated experiment datasets and large result tables.

Use CSV for:

- tiny summaries
- human inspection
- ML experiment index files

Do not repeatedly read/write large data as CSV during Spark benchmarking.

---

# 38. Fix the Benchmark Design

A valid benchmark should keep these controlled:

```text
record count
schema
Spark configuration
machine
number of repetitions
seed
```

Change primarily:

```text
skew ratio
```

Run each scenario more than once when practical and report the median or mean runtime.

Do not overinterpret tiny runtime differences.

---

# 39. Correct the Experimental Question

Do not optimize for:

> "What setup gives the fastest result?"

The project should answer:

> **How does increasing key skew affect Spark execution, and how effectively do repartitioning and salting reduce the resulting imbalance?**

The ML extension then answers:

> **Can simple engineered Spark/partition features classify skew severity well enough to guide mitigation?**

This keeps the project scientifically coherent.

---

# 40. Security Scope Cleanup

Keep cybersecurity as an interpretation of deliberately generated skew, not as a separate intrusion-detection product.

Use language such as:

```text
adversarial workload
resource-exhaustion scenario
intentional skew injection
```

Avoid claiming:

```text
all skew = attack
```

The core project remains a Spark data-engineering study.

---

# 41. Dashboard Cleanup

The dashboard should display stored experiment results.

Do not make Streamlit start the full Spark benchmark every time the browser loads.

Recommended flow:

```text
Local Spark experiment
        ↓
Save compact results
        ↓
Streamlit reads results
        ↓
Visualize
```

Core dashboard pages/sections:

```text
Overview
Skew Analysis
Performance
ML Detection
Mitigation Comparison
```

Avoid building a second application backend.

---

# 42. Deployment Strategy

Use a two-part deployment model:

```text
Spark + benchmark
        │
        │ local / Docker
        ▼
   result artifacts
        │
        ▼
 Streamlit dashboard
        │
        ▼
 lightweight hosting
```

This avoids trying to run a full Spark environment as a public web service.

Deployment should be the final phase, not the first.

---

# 43. README Cleanup

The README should contain only:

```text
1. Project objective
2. Architecture
3. Key concepts
4. Installation
5. Quick start
6. CLI examples
7. Experiment methodology
8. Results
9. Testing
10. Deployment
11. Repository structure
```

Move deep implementation notes into this project document instead of creating a 2,000-line README.

---

# 44. Recommended Quick Start

After cleanup, the user workflow should be close to:

```bash
git clone <repo>
cd data-skew-intelligence
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
python -m data_skew.cli doctor
python -m data_skew.cli generate --rows 100000 --skew 0.70 --seed 42
python -m data_skew.cli analyze
python -m data_skew.cli run --rows 100000
pytest -q
```

The commands should work without manually editing Python files.

---

# 45. Definition of Done

The cleanup is complete when all of these are true:

- [ ] One canonical source directory exists.
- [ ] No duplicate implementation of the same operation exists.
- [ ] No module performs work automatically on import.
- [ ] Configuration is centralized.
- [ ] Data generation is deterministic.
- [ ] Generated large datasets are ignored by Git.
- [ ] Spark tests use a shared local fixture.
- [ ] Baseline and salted aggregations produce equivalent results.
- [ ] ML features do not leak post-mitigation information.
- [ ] ML models are evaluated consistently.
- [ ] CLI commands are small and predictable.
- [ ] `doctor` validates the environment.
- [ ] `ruff check .` passes.
- [ ] `pytest -q` passes.
- [ ] GitHub Actions passes.
- [ ] Streamlit reads results instead of launching expensive benchmarks on page load.
- [ ] Docker is optional for development and reproducibility, not required to understand the project.
- [ ] README explains the project without duplicating the implementation document.

---

# 46. Final Refactored Execution Flow

The final implementation should feel like one coherent program:

```text
                 ┌──────────────┐
                 │   `doctor`  │
                 └──────┬───────┘
                        │
                        ▼
                 Environment OK
                        │
                        ▼
                 `generate`
                        │
                        ▼
                 Synthetic Data
                        │
                        ▼
                  `analyze`
                        │
                        ▼
                Skew + EDA Metrics
                        │
                        ▼
                 `benchmark`
                        │
                        ▼
              Spark Execution Metrics
                        │
                        ▼
                    `train`
                        │
                        ▼
                Severity Classifier
                        │
                        ▼
                   `predict`
                        │
                        ▼
                 Severity Decision
                        │
                        ▼
                  `mitigate`
                        │
               ┌────────┴────────┐
               ▼                 ▼
          Repartition          Salting
               │                 │
               └────────┬────────┘
                        ▼
                 Before / After
                     Metrics
                        │
                        ▼
                 Streamlit View
```

---

# 47. Immediate Refactoring Order

Do not refactor everything at once.

Execute in this order:

```text
1. Clean repository structure
2. Move code into src/
3. Centralize configuration
4. Fix imports
5. Remove import-time Spark execution
6. Make data generator deterministic
7. Isolate skew analysis functions
8. Isolate mitigation functions
9. Build small Spark test fixture
10. Fix salting correctness
11. Simplify ML pipeline
12. Simplify CLI
13. Add `doctor`
14. Run Ruff
15. Run Pytest
16. Run full benchmark manually
17. Verify dashboard
18. Dockerize
19. Deploy dashboard
```

Do not start deployment until steps 1–15 are clean.

---

# 48. Final Principle

The project should look advanced because the **reasoning is strong**, not because the repository contains many technologies.

The target is:

```text
Less code
+ fewer dependencies
+ clearer modules
+ reproducible experiments
+ strong Spark fundamentals
+ measurable mitigation
+ simple ML decision layer
+ reliable tests
= stronger project
```
