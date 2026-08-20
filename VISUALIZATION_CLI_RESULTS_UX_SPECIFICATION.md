# VISUALIZATION, CLI UX & RESULTS MANAGEMENT SPECIFICATION

## Objective

Refactor the project so that:

- graphs display the actual experiment data correctly;
- distributions are never replaced by maximum values;
- charts and CLI use a consistent NVIDIA-inspired dark/green engineering theme;
- Spark/Pytest/Python noise does not flood the terminal;
- final results remain visible and are permanently persisted;
- historical experiments are retained;
- users can interactively choose which results, metrics, tables, and graphs to view;
- CLI and dashboard read from the same persisted result data;
- `python run.py` remains the one-click entry point.

---

## 1. Critical Graph Correctness Problem

The current graphs reportedly show the maximum value repeatedly.

This must be fixed before styling.

A distribution chart must consume the real distribution:

```python
partition_sizes = [8200, 9100, 10800, 72100, 9000, 8700, 8900, 9040]
```

It must **not** construct a distribution from:

```python
max_partition = 72100
values = [max_partition] * partition_count
```

If the required distribution data was not collected, do not fabricate it. Display:

```text
Partition-level distribution unavailable for this experiment.
```

---

## 2. Visualization Data Contract

Every chart receives explicit data matching its purpose.

### Key distribution

```python
{
    "HOT_KEY": 70000,
    "KEY_02": 1600,
    "KEY_03": 1500,
}
```

### Partition distribution

```python
[
    8200,
    9100,
    10800,
    72100,
    9000,
    8700,
    8900,
    9040,
]
```

### Experiment series

```python
[
    {"skew": 0.0, "runtime": 1.2, "partition_cv": 0.08},
    {"skew": 0.2, "runtime": 1.5, "partition_cv": 0.20},
    {"skew": 0.4, "runtime": 1.9, "partition_cv": 0.41},
]
```

The visualization layer must not guess or recreate missing values.

---

## 3. Visualization Validation

Before rendering:

```text
data exists
data is non-empty
expected fields exist
numeric values are valid
array lengths match
```

For distributions:

```python
if not partition_sizes:
    raise ValueError("No partition distribution data available")
```

If all partition values are identical:

```text
WARNING
All measured partition sizes are identical.
No partition imbalance is visible in this run.
```

Do not modify the data to make the graph look interesting.

---

## 4. Required Graphs

Keep the graph set small and meaningful.

### 4.1 Key Distribution

Horizontal bar chart of the top keys.

Show:

- key;
- record count;
- percentage.

Highlight the hot key with the accent color.

---

### 4.2 Partition Distribution

Plot:

```text
partition index → actual records
```

Add reference lines for:

- mean;
- median;
- maximum.

The bars must contain the real partition-level values.

---

### 4.3 Before vs After Partition Distribution

Compare actual baseline and mitigated partition sizes.

Do not force both arrays to the same number of partitions when they legitimately differ.

If partition counts differ, use two clearly labeled distributions.

---

### 4.4 Skew vs Runtime

X:

```text
skew percentage
```

Y:

```text
execution time
```

Use all experiment observations.

Never plot only the maximum runtime.

---

### 4.5 Skew vs Partition CV

X:

```text
skew percentage
```

Y:

```text
partition coefficient of variation
```

This is one of the most important project graphs because it demonstrates the relationship between key concentration and partition imbalance.

---

### 4.6 Performance Comparison

Compare:

```text
execution time
shuffle read
shuffle write
partition CV
max partition
```

Do not put incompatible units on one raw axis.

Use separate charts or normalized comparisons where appropriate.

---

## 5. NVIDIA-Inspired Theme

Use a modern GPU/data-engineering visual language without copying NVIDIA logos or proprietary branding.

Recommended palette:

```text
BACKGROUND = "#0B0F0C"
SURFACE    = "#111713"
SURFACE_2  = "#182019"
GREEN      = "#76B900"
GREEN_2    = "#A8E063"
TEXT       = "#F2F5F2"
MUTED      = "#9AA49D"
WARNING    = "#F5B942"
ERROR      = "#FF5C5C"
GRID       = "#273029"
```

Use bright green sparingly as an accent:

- hot key;
- mitigated state;
- success;
- selected model;
- primary progress state.

Use gray for secondary/baseline information.

Use amber/red only for warnings/errors.

---

## 6. Centralized Visualization Theme

Create:

```text
visualization/
├── theme.py
├── validators.py
├── charts.py
├── tables.py
└── exporter.py
```

`theme.py` owns all colors/layout constants.

Do not hard-code different colors inside individual chart functions.

The same theme must be reusable by:

- Matplotlib;
- Plotly;
- Rich CLI tables/panels.

---

## 7. Chart Functions

Use explicit functions:

```python
plot_key_distribution(data, output_path)
plot_partition_distribution(partition_sizes, output_path)
plot_before_after_partitions(before, after, output_path)
plot_skew_vs_runtime(experiments, output_path)
plot_skew_vs_partition_cv(experiments, output_path)
plot_performance_comparison(metrics, output_path)
```

Avoid a generic function such as:

```python
plot(metrics)
```

that guesses which field to display.

---

## 8. Graph Quality Checks

After each graph is generated, verify:

- file exists;
- file is non-empty;
- title exists;
- axis labels exist;
- expected data range is present.

Recommended report/dashboard chart size:

```text
1200 × 700 minimum
```

for exported raster charts.

---

## 9. Terminal Noise Problem

The terminal currently contains too much:

- Spark INFO/WARN output;
- Java warnings;
- PySpark warnings;
- pytest warning summaries;
- dependency warnings;
- internal logs.

The user-facing terminal must contain only useful project information.

---

## 10. Console vs Logs

Separate:

### User-facing console

```text
[3/8] Spark baseline       ✓
[4/8] Detection            ✓
```

### Diagnostic files

```text
logs/run.log
logs/spark.log
logs/pytest.log
logs/error.log
```

Detailed debugging information belongs in files.

---

## 11. Spark Log Reduction

Configure Spark to a quiet level for normal operation.

Do not allow internal Spark INFO lines to dominate the terminal.

Add:

```bash
python run.py --verbose
```

for detailed diagnostics.

Normal mode should show only:

- stage status;
- important warnings;
- metrics;
- final result.

---

## 12. Python and Pytest Warning Handling

Fix known dependency issues instead of hiding them.

For the current PySpark/pandas compatibility warning:

```text
pandas<3
```

should be pinned in `requirements.txt`.

For Pytest:

- use `pytest -q`;
- suppress successful warning output from the main console;
- write full output to `logs/pytest.log`.

On success:

```text
[TESTS] ✓ 10 passed
```

On failure:

```text
[TESTS] ✗ 2 failed
Details: logs/pytest.log
```

---

## 13. Preserve Results

The terminal is not the source of truth.

Every successful experiment gets a unique directory:

```text
results/
├── 2026-08-20_16-50-12/
├── 2026-08-20_17-02-31/
├── 2026-08-20_17-18-44/
└── latest/
```

Never overwrite historical experiment directories.

`latest/` must represent the most recent successful run.

---

## 14. Result Manifest

Every experiment must write:

```text
results/<timestamp>/manifest.json
```

Example:

```json
{
  "experiment_id": "2026-08-20_16-50-12",
  "status": "success",
  "rows": 100000,
  "skew_ratio": 0.70,
  "severity": "HIGH_SKEW",
  "model": "random_forest",
  "mitigation": "salting"
}
```

This lets the results menu discover experiment history.

---

## 15. Persist Raw Visualization Data

Each experiment should contain:

```text
results/<timestamp>/
├── data/
│   ├── key_distribution.csv
│   ├── partition_distribution.csv
│   ├── experiment_metrics.csv
│   └── before_after.csv
│
└── charts/
    ├── key_distribution.png
    ├── partition_distribution.png
    ├── before_after_partition.png
    ├── skew_vs_runtime.png
    ├── skew_vs_partition_cv.png
    └── performance_comparison.png
```

Raw graph data is the authoritative input.

The PNG/HTML/SVG files are derived artifacts.

---

## 16. User-Defined Results Menu

After a successful interactive run, launch a results console.

Example:

```text
╔══════════════════════════════════════════════════════════════╗
║  RESULTS CONSOLE                                            ║
╠══════════════════════════════════════════════════════════════╣
║  1  Latest Experiment                                       ║
║  2  Experiment History                                      ║
║  3  Dataset Profile                                         ║
║  4  Spark Metrics                                           ║
║  5  Before vs After                                         ║
║  6  ML Results                                              ║
║  7  View Graphs                                              ║
║  8  Run Again                                                ║
║  9  Exit                                                     ║
╚══════════════════════════════════════════════════════════════╝

Select:
```

Use Rich prompts rather than introducing a large TUI dependency unless necessary.

---

## 17. Menu Modes

Normal interactive terminal:

```text
python run.py
```

After completion:

```text
Open Results Console? [Y/n]
```

Force menu:

```text
python run.py --menu
```

Disable menu:

```text
python run.py --no-menu
```

This is required for CI and automation.

Non-interactive environments must never block waiting for input.

---

## 18. Latest Experiment Menu

Show:

```text
EXPERIMENT SUMMARY

Records                  100,000
Skew                     70.0%
Severity                 HIGH_SKEW
ML Model                 Random Forest
Mitigation               SALTING

Runtime Before            4.82 s
Runtime After             2.71 s

Partition CV Before       1.84
Partition CV After        0.42
```

All values must come from persisted files.

---

## 19. Experiment History Menu

Show a compact table:

```text
ID                   Rows       Skew     Severity      Improvement
-------------------------------------------------------------------
16-50-12             100k       70%      HIGH          43.8%
17-02-31             100k       50%      LOW             8.4%
17-18-44             1M         90%      HIGH           51.2%
```

Allow the user to select one historical experiment.

---

## 20. Graph Viewer Menu

Provide:

```text
1. Key Distribution
2. Partition Distribution
3. Before / After Partitions
4. Skew vs Runtime
5. Skew vs Partition CV
6. Performance Comparison
7. Back
```

Graphs must be loaded from persisted data.

Do not rerun Spark merely to display a graph.

---

## 21. Spark Metrics Menu

Show:

```text
SPARK EXECUTION

Metric                    Baseline       Mitigated
---------------------------------------------------
Partitions                ...
Max partition             ...
Mean partition            ...
Partition std             ...
Partition CV              ...
Shuffle read              ...
Shuffle write             ...
Runtime                   ...
```

Use actual values from the experiment.

---

## 22. ML Results Menu

Show:

```text
MODEL COMPARISON

Model                  Precision   Recall   F1
------------------------------------------------
Logistic Regression       ...        ...    ...
Decision Tree             ...        ...    ...
Random Forest             ...        ...    ...

Selected model: ...
```

Then:

```text
CURRENT PREDICTION

Severity: HIGH_SKEW
Confidence: ...
```

Only display confidence when the model actually provides a valid probability estimate.

---

## 23. Dataset Profile Menu

Show:

```text
DATASET PROFILE

Records                 100,000
Unique keys                  20
Hot key                  HOT_KEY
Hot key concentration      70.0%
Mean key frequency          ...
Std key frequency           ...
Top 5 concentration         ...
```

Add a top-key table rather than another repetitive chart.

---

## 24. Shared Source of Truth

Architecture:

```text
Spark
  ↓
Telemetry
  ↓
Persisted Results Dataset
  ↓
Visualization Functions
      ├── CLI tables
      ├── PNG charts
      └── Streamlit charts
```

Do not recalculate the same metrics independently in:

- CLI;
- dashboard;
- notebook;
- graph exporter.

One metric calculation should feed every output.

---

## 25. Dashboard

The Streamlit dashboard must read:

```text
results/latest/data/
```

and use the same visualization theme as the CLI.

It must not rerun the Spark pipeline simply to display existing results.

---

## 26. Do Not Erase Useful Terminal Output

Avoid full-console clear operations after the final report.

Progress spinners may refresh locally, but the completed report must remain visible.

The final terminal sequence should be:

```text
Header
↓
Progress
↓
Key findings
↓
Final performance report
↓
Result location
↓
Interactive menu
```

Not:

```text
logs
warnings
tests
logs
warnings
final report
screen cleared
```

---

## 27. Clean Final CLI

Target:

```text
╔══════════════════════════════════════════════════════════════╗
║  S K E W C T L                                              ║
║  INTELLIGENT DATA SKEW ENGINE                               ║
╚══════════════════════════════════════════════════════════════╝

[1/8] Dataset              ✓
[2/8] Spark baseline       ✓
[3/8] Telemetry            ✓
[4/8] Detection            ✓
[5/8] ML                   ✓
[6/8] Mitigation           ✓
[7/8] Tests                ✓
[8/8] Visualization       ✓

EXPERIMENT COMPLETE

                 BEFORE          AFTER
Runtime           ...             ...
Partition CV     ...             ...
Max partition    ...             ...
Shuffle read     ...             ...

Results:
results/2026-08-20_16-50-12/

Open Results Console? [Y/n]
```

The CLI should be concise but information-dense.

---

## 28. CLI Modes

Support:

```bash
python run.py
python run.py --menu
python run.py --no-menu
python run.py --verbose
python run.py --quick
python run.py --check
```

The standard Run button should execute:

```bash
python run.py
```

---

## 29. Avoid Boring Charts

Do not make everything a green bar chart.

Use:

- green for the important signal;
- muted gray for background/baseline;
- dark surface panels;
- reference lines for mean/median;
- warning/red only for abnormal states;
- labels only where they improve comprehension.

The graph should visually explain:

```text
where the skew is;
how severe it is;
what changed;
whether mitigation helped.
```

---

## 30. Avoid Misleading Charts

Never:

- duplicate the maximum value;
- replace missing values with zero;
- hide outliers;
- silently drop observations;
- mix baseline and mitigated data;
- use incompatible units on one axis;
- normalize without labeling;
- truncate the axis solely to exaggerate improvement.

Numerical correctness comes before visual style.

---

## 31. Visualization Module

Recommended structure:

```text
visualization/
├── __init__.py
├── theme.py
├── validators.py
├── charts.py
├── tables.py
└── exporter.py
```

Responsibilities:

### `theme.py`

Centralized colors/layout.

### `validators.py`

Data integrity checks before plotting.

### `charts.py`

Actual plots.

### `tables.py`

Rich terminal tables/panels.

### `exporter.py`

PNG/SVG/HTML outputs.

---

## 32. Implementation Priority

Do these in order:

```text
P0  Fix graph data correctness
 ↓
P1  Persist complete graph-ready data
 ↓
P2  Centralize metric calculation
 ↓
P3  Implement NVIDIA-inspired theme
 ↓
P4  Suppress terminal noise
 ↓
P5  Preserve historical results
 ↓
P6  Implement interactive results menu
 ↓
P7  Connect dashboard to the same results
 ↓
P8  Add chart export and quality checks
```

Do not polish the UI before P0-P2 are correct.

---

## 33. Definition of Done

```text
[ ] Partition graphs display actual partition distributions
[ ] Key graphs display actual key frequencies
[ ] Max values are used only as KPI/reference markers
[ ] Before/after charts use real matched measurements
[ ] Skew-vs-runtime uses all relevant experiments
[ ] Skew-vs-partition-CV uses all relevant experiments
[ ] Graph-ready data is persisted
[ ] Charts use centralized NVIDIA-inspired colors
[ ] CLI uses the same theme
[ ] Spark logs no longer flood the terminal
[ ] Pytest warnings do not bury results
[ ] Final report remains visible
[ ] Historical experiments are preserved
[ ] results/latest is updated safely
[ ] Interactive results menu works
[ ] Historical experiments are selectable
[ ] User can view tables and graphs from the menu
[ ] Dashboard reads the same results
[ ] --no-menu works for CI
[ ] --verbose provides diagnostics
[ ] No graph fabricates missing data
[ ] No visualization silently substitutes maximum values
```

---

## 34. Final User Experience

```text
User clicks Run
      ↓
Premium CLI
      ↓
Clean progress
      ↓
Correct Spark results
      ↓
Correct NVIDIA-inspired graphs
      ↓
Persistent result directory
      ↓
Interactive Results Console
      ↓
User chooses:
    latest
    history
    dataset
    Spark metrics
    before/after
    ML
    graphs
    rerun
    exit
```

The terminal is the **control center**.

The `results/` directory is the **source of truth**.

The dashboard is a **read-only visualization layer** over persisted results.

The visualization layer must never change, invent, duplicate, or discard the underlying experimental data.
