from core.pipeline import run_pipeline


def test_pipeline_quick_mode():
    """Smoke test for end-to-end pipeline execution in quick mode."""
    exit_code = run_pipeline(quick=True)
    assert exit_code == 0, f"Expected pipeline exit code 0, got {exit_code}"


def test_pipeline_check_mode():
    """Test environment check mode."""
    exit_code = run_pipeline(check_only=True)
    assert exit_code == 0, f"Expected environment check exit code 0, got {exit_code}"
