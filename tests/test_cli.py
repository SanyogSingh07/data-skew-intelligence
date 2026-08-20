import os

from typer.testing import CliRunner

from cli.app import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "skewctl" in result.stdout.lower() or "skew" in result.stdout.lower()
    assert "system" in result.stdout
    assert "data" in result.stdout
    assert "spark" in result.stdout
    assert "ml" in result.stdout


def test_cli_system_check():
    result = runner.invoke(app, ["system", "check"])
    assert result.exit_code == 0
    assert "Python" in result.stdout


def test_cli_data_generate_and_inspect(tmp_path):
    out_file = str(tmp_path / "test_skew.parquet")
    
    # 1. Test generate
    gen_result = runner.invoke(app, ["data", "generate", "--rows", "200", "--skew", "0.70", "--output", out_file])
    assert gen_result.exit_code == 0
    assert os.path.exists(out_file)
    
    # 2. Test inspect
    insp_result = runner.invoke(app, ["data", "inspect", "--input", out_file])
    assert insp_result.exit_code == 0
    assert "Unique Keys" in insp_result.stdout


def test_cli_spark_baseline(tmp_path):
    out_file = str(tmp_path / "test_baseline.parquet")
    runner.invoke(app, ["data", "generate", "--rows", "200", "--skew", "0.70", "--output", out_file])
    
    base_result = runner.invoke(app, ["spark", "baseline", "--input", out_file])
    assert base_result.exit_code == 0
    assert "Execution Time" in base_result.stdout


def test_cli_ml_train():
    train_result = runner.invoke(app, ["ml", "train"])
    assert train_result.exit_code == 0
    assert "Training complete" in train_result.stdout
