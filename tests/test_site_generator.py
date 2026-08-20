import shutil
from pathlib import Path
from visualization.site_generator import export_static_site, generate_html_content


def test_generate_html_content():
    summary = {
        "experiment_id": "EXP-TEST-101",
        "rows": 10000,
        "skew": 0.7,
        "predicted_class": "HIGH_SKEW",
        "ml_model": "logistic_regression",
        "mitigation": "SALTING",
        "baseline_execution_time": 1.25,
        "mitigated_execution_time": 0.85,
        "improvement_pct": 32.0,
    }
    profile = {"top1_concentration": 0.70}
    baseline = {"max_partition_size": 7000, "partition_std": 2000.0}
    mitigated = {"max_partition_size": 2500, "partition_std": 400.0}
    ml_metrics = {"best_model": "logistic_regression"}

    html = generate_html_content(summary, profile, baseline, mitigated, ml_metrics)

    assert "EXP-TEST-101" in html
    assert "HIGH_SKEW" in html
    assert "SALTING" in html
    assert "./assets/style.css" in html
    assert "./assets/script.js" in html
    assert "./charts/key_distribution.png" in html


def test_export_static_site(tmp_path):
    # Setup mock results structure
    latest_dir = tmp_path / "latest"
    charts_dir = latest_dir / "charts"
    data_dir = latest_dir / "data"
    charts_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)

    (charts_dir / "key_distribution.png").write_text("fake_png")
    (data_dir / "key_distribution.csv").write_text("key,count\nA,100")
    (latest_dir / "summary.json").write_text('{"experiment_id": "EXP-MOCK"}')

    site_path = export_static_site(run_dir=latest_dir)

    assert site_path.exists()
    assert (site_path / "index.html").exists()
    assert (site_path / "assets" / "style.css").exists()
    assert (site_path / "assets" / "script.js").exists()
    assert (site_path / "charts" / "key_distribution.png").exists()
    assert (site_path / "data" / "key_distribution.csv").exists()
    assert (site_path / "data" / "summary.json").exists()
