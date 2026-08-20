# GitHub Testing & CI Plan — Data Skew Intelligence

This file defines a GitHub-ready testing strategy for the **Data Skew Intelligence** project.

The goal is simple: every push and pull request should verify that the repository can be imported, the CLI starts, the core Spark logic works locally, the ML pipeline is valid, and the project does not depend on generated datasets or a remote Spark cluster.

---

## 1. Testing Philosophy

The project should use four testing layers:

```text
                    Git Push / Pull Request
                              │
                              ▼
                    GitHub Actions CI
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
     Unit Tests          Spark Smoke Test     CLI Validation
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                       ML Smoke Test
                              │
                              ▼
                       PASS / FAIL
```

The CI pipeline must remain lightweight. It should validate correctness, not run the full million-row performance benchmark.

---

# 2. Required Test Structure

Create this structure:

```text
tests/
├── __init__.py
├── conftest.py
├── test_data_generation.py
├── test_skew_analysis.py
├── test_mitigation.py
├── test_ml_pipeline.py
├── test_cli.py
└── test_smoke.py

.github/
└── workflows/
    └── ci.yml
```

Optional later:

```text
tests/
└── integration/
    ├── test_spark_job.py
    └── test_dashboard_import.py
```

---

# 3. Test Dependencies

Add these to `requirements-dev.txt`:

```text
pytest>=8,<9
pytest-cov>=5,<7
ruff>=0.8,<1
```

The runtime requirements remain in `requirements.txt`.

Recommended separation:

### requirements.txt

```text
pyspark
pandas
numpy
scikit-learn
pyarrow
matplotlib
plotly
streamlit
shap
rich
# typer is required if the CLI uses Typer
 typer
```

Remove the accidental leading space before `typer` when creating the actual file.

### requirements-dev.txt

```text
-r requirements.txt
pytest>=8,<9
pytest-cov>=5,<7
ruff>=0.8,<1
```

Pin exact versions later after the local environment is confirmed stable.

---

# 4. Test Environment Rules

Tests must:

- Run on a local Spark session.
- Use tiny generated DataFrames instead of large datasets.
- Never depend on files ignored by Git.
- Never require an external Spark cluster.
- Never require cloud credentials.
- Never require GPU/CUDA.
- Avoid long-running performance experiments in CI.
- Clean temporary files after execution.

The test suite should normally complete within a few minutes.

---

# 5. `tests/conftest.py`

Use a reusable local Spark fixture.

```python
import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("DataSkewIntelligenceTests")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .getOrCreate()
    )

    yield spark
    spark.stop()
```

Keep the test Spark configuration deliberately small.

---

# 6. Data Generation Tests

## `tests/test_data_generation.py`

Verify that the generator produces:

1. The requested row count.
2. A valid schema.
3. Multiple keys.
4. The requested approximate skew ratio.
5. No unexpected null key values.

Example test concept:

```python

def test_generated_dataset_has_requested_size(spark):
    # Replace with the actual generator API.
    df = generate_dataset(spark, rows=1000, skew_ratio=0.70, seed=42)

    assert df.count() == 1000
    assert "key" in df.columns
    assert df.filter("key IS NULL").count() == 0
```

Also test deterministic generation:

```python

def test_generator_is_reproducible(spark):
    df1 = generate_dataset(spark, rows=500, skew_ratio=0.70, seed=42)
    df2 = generate_dataset(spark, rows=500, skew_ratio=0.70, seed=42)

    assert df1.collect() == df2.collect()
```

This prevents difficult-to-debug experimental drift.

---

# 7. Skew Analysis Tests

## `tests/test_skew_analysis.py`

Test each metric independently.

Minimum checks:

```text
skew ratio
mean frequency
standard deviation
maximum frequency
minimum frequency
top-1 concentration
partition statistics
```

Example:

```python

def test_skew_ratio_increases_with_skew(spark):
    normal = generate_dataset(spark, rows=1000, skew_ratio=0.10, seed=42)
    skewed = generate_dataset(spark, rows=1000, skew_ratio=0.90, seed=42)

    normal_metrics = analyze_skew(normal)
    skewed_metrics = analyze_skew(skewed)

    assert skewed_metrics["skew_ratio"] > normal_metrics["skew_ratio"]
```

Test boundary behavior:

```python

def test_metrics_are_finite(spark):
    df = generate_dataset(spark, rows=100, skew_ratio=0.50, seed=42)
    metrics = analyze_skew(df)

    for value in metrics.values():
        if isinstance(value, (int, float)):
            assert value == value  # not NaN
```

The statistical layer should be deterministic and independent of the ML layer.

---

# 8. Mitigation Tests

## `tests/test_mitigation.py`

Verify both required mitigation approaches.

### Repartitioning

Check that the resulting DataFrame remains valid and record count is preserved.

```python

def test_repartition_preserves_record_count(spark):
    df = generate_dataset(spark, rows=1000, skew_ratio=0.80, seed=42)

    result = mitigate_with_repartition(df, partitions=4)

    assert result.count() == df.count()
```

### Salting

Check that:

- A salt column exists.
- The salted key exists.
- Record count is preserved.
- Salt values are within the configured range.

```python

def test_salting_preserves_records(spark):
    df = generate_dataset(spark, rows=1000, skew_ratio=0.80, seed=42)

    result = apply_salt(df, key_col="key", salt_buckets=4, seed=42)

    assert result.count() == df.count()
    assert "salt" in result.columns
    assert "salted_key" in result.columns
```

Do not assert an exact runtime improvement in CI. Runtime depends on hardware and CI load.

---

# 9. ML Pipeline Tests

## `tests/test_ml_pipeline.py`

The ML tests should verify the complete basic lifecycle:

```text
features
  ↓
train/test split
  ↓
model training
  ↓
prediction
  ↓
evaluation
```

Example:

```python

def test_ml_pipeline_produces_predictions(spark):
    df = create_small_experiment_dataset(spark)

    model = train_classifier(df)
    predictions = model.transform(df)

    assert "prediction" in predictions.columns
    assert predictions.count() == df.count()
```

Validate that the expected metrics exist:

```python

def test_model_evaluation_returns_metrics(spark):
    df = create_small_experiment_dataset(spark)
    model = train_classifier(df)
    predictions = model.transform(df)

    metrics = evaluate_model(predictions)

    assert "accuracy" in metrics
    assert "f1" in metrics
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["f1"] <= 1.0
```

Do not demand a fixed accuracy such as `> 95%` in CI. Dataset generation or dependency updates may legitimately change the metric.

---

# 10. Intelligent Decision Tests

The decision layer should be deterministic.

Example behavior:

```text
NORMAL     → NONE
LOW_SKEW   → REPARTITION
HIGH_SKEW  → SALTING
```

Tests:

```python

def test_mitigation_policy():
    assert choose_mitigation("NORMAL") == "NONE"
    assert choose_mitigation("LOW_SKEW") == "REPARTITION"
    assert choose_mitigation("HIGH_SKEW") == "SALTING"
```

This is one of the most important tests because it proves that ML output is actually connected to system behavior.

---

# 11. CLI Tests

## `tests/test_cli.py`

If the project uses a Rich/Typer CLI, verify that the CLI starts and the main commands exist.

Recommended commands:

```text
skew --help
skew generate
skew analyze
skew benchmark
skew train
skew predict
skew mitigate
skew report
```

Example with Typer:

```python
from typer.testing import CliRunner

from cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "generate" in result.stdout
    assert "analyze" in result.stdout
```

Test one lightweight command:

```python

def test_cli_generate():
    result = runner.invoke(
        app,
        ["generate", "--rows", "50", "--skew", "0.70"]
    )

    assert result.exit_code == 0
```

Keep CLI tests small and temporary-file based.

---

# 12. End-to-End Smoke Test

## `tests/test_smoke.py`

This test should prove that the most important path works:

```text
create small data
      ↓
Spark load
      ↓
skew analysis
      ↓
feature creation
      ↓
ML prediction
      ↓
mitigation
      ↓
result generated
```

The smoke test should use approximately 100–1,000 records, not the production benchmark size.

Example structure:

```python

def test_end_to_end_smoke(spark, tmp_path):
    raw = generate_dataset(
        spark,
        rows=500,
        skew_ratio=0.80,
        seed=42,
    )

    metrics = analyze_skew(raw)
    features = build_features(raw, metrics)
    model = train_classifier(features)
    predictions = model.transform(features)
    label = classify_severity(predictions)
    mitigated = apply_mitigation(raw, label)

    assert raw.count() == mitigated.count()
    assert label in {"NORMAL", "LOW_SKEW", "HIGH_SKEW"}
```

Adapt function names to the implementation.

---

# 13. GitHub Actions CI

Create:

```text
.github/workflows/ci.yml
```

Use:

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11"]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Set up Java 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"
          cache: maven

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Check Python syntax
        run: |
          python -m compileall .

      - name: Ruff lint
        run: |
          ruff check .

      - name: Run tests
        env:
          JAVA_HOME: ${{ env.JAVA_HOME_17_X64 }}
        run: |
          pytest -q --cov=. --cov-report=term-missing
```

Important: If your actual GitHub Actions environment exposes Java under a different environment variable, use the path produced by `setup-java`. In many workflows, Java is already available after `actions/setup-java` and the explicit `JAVA_HOME` override can be omitted.

A safer final version is therefore:

```yaml
      - name: Run tests
        run: pytest -q --cov=. --cov-report=term-missing
```

Start with this simpler form.

---

# 14. Recommended Final CI Workflow

Use this version unless a real project-specific constraint requires otherwise:

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Setup Java 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Syntax check
        run: python -m compileall .

      - name: Lint
        run: ruff check .

      - name: Tests
        run: pytest -q --cov=. --cov-report=term-missing
```

This is intentionally simple.

---

# 15. GitHub Repository Hygiene

Before pushing, confirm the following:

```text
✅ README.md exists
✅ requirements.txt exists
✅ requirements-dev.txt exists
✅ .gitignore exists
✅ tests/ exists
✅ .github/workflows/ci.yml exists
✅ No .venv/ committed
✅ No huge generated datasets committed
✅ No secrets committed
✅ No local absolute paths
✅ No Spark UI output committed
✅ No temporary warehouse directories committed
```

---

# 16. `.gitignore` Additions

Recommended entries:

```gitignore
# Python
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/

# Spark
spark-warehouse/
metastore_db/
*.crc

# Logs
*.log
logs/

# Generated experiment data
data/generated/
results/tmp/
checkpoints/

# Model artifacts generated locally
models/*.pkl
models/*.joblib
models/*.onnx

# OS
.DS_Store
Thumbs.db
```

Do not ignore small configuration or sample files that are intentionally part of the repository.

---

# 17. Pre-Push Local Validation

Before every major push, run:

```bash
python -m compileall .
ruff check .
pytest -q
```

Then check Git:

```bash
git status
git diff --stat
git ls-files
```

Finally:

```bash
git add .
git commit -m "test: add project validation and CI"
git push
```

---

# 18. What GitHub CI Should NOT Run

Do not put these into ordinary pull-request CI:

- Million-record benchmark
- Large synthetic-data generation
- Full Spark performance comparison
- Long hyperparameter search
- SHAP on a large dataset
- Full Streamlit deployment
- Docker image publishing
- Cloud deployment

Those belong in separate workflows or manual experiment runs.

Recommended future separation:

```text
CI
└── correctness

benchmark.yml
└── performance experiments

deploy.yml
└── dashboard deployment
```

---

# 19. Optional Benchmark Workflow

Once the project is stable, create:

```text
.github/workflows/benchmark.yml
```

Run it manually using:

```yaml
on:
  workflow_dispatch:
```

This keeps expensive Spark experiments out of normal PR validation.

Benchmark workflow can later generate:

```text
results/
├── normal.csv
├── skew_30.csv
├── skew_50.csv
├── skew_70.csv
├── skew_90.csv
└── mitigation_comparison.csv
```

Do not commit large benchmark artifacts unless they are intentionally selected as small reproducibility samples.

---

# 20. Testing Acceptance Criteria

The repository is ready for GitHub when all of the following are true:

```text
[ ] Fresh Python environment installs successfully
[ ] Java 17 is detected
[ ] PySpark starts in local mode
[ ] Dataset generator works
[ ] Skew analyzer works
[ ] Repartition mitigation works
[ ] Salting mitigation works
[ ] ML pipeline trains on a small sample
[ ] Prediction is produced
[ ] Metrics are calculated
[ ] CLI --help works
[ ] CLI smoke command works
[ ] pytest passes locally
[ ] ruff check passes
[ ] GitHub Actions passes
[ ] No large/generated files are accidentally committed
```

---

# 21. Definition of Done

The implementation is considered stable only when this command succeeds:

```bash
pytest -q
```

and the GitHub Actions status is:

```text
CI ✅
```

A successful GitHub upload is **not** the same as a successful project validation. The repository should be considered complete only after a clean checkout can install the dependencies and pass the automated tests.

---

# 22. Recommended Development Sequence

Implement the testing infrastructure in this order:

```text
1. tests/conftest.py
2. data-generation tests
3. skew-analysis tests
4. mitigation tests
5. ML tests
6. decision-policy tests
7. CLI tests
8. end-to-end smoke test
9. GitHub Actions CI
10. benchmark workflow
11. deployment workflow
```

Do not wait until the project is finished to add tests. Add each test immediately after the corresponding component is implemented.

---

# 23. Final Principle

The testing system should protect the core project idea:

```text
Spark fundamentals
      ↓
Correct data generation
      ↓
Correct skew analysis
      ↓
Correct mitigation
      ↓
Correct ML decision
      ↓
Reproducible experiment
      ↓
Reliable GitHub repository
```

The purpose of CI is not to make the project look sophisticated. Its purpose is to guarantee that the core Spark, data-analysis, ML, and mitigation logic remains reproducible and does not silently break.
