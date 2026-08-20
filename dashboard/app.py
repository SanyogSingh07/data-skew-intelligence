"""Interactive Streamlit Dashboard for Data Skew Intelligence.

Reads persisted experiment data and charts directly from results/latest/data/ without
re-running Spark execution. Styled using the NVIDIA-inspired engineering theme.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from spark.config import get, resolve_path
from visualization.theme import BACKGROUND, GREEN, GREEN_2, MUTED, SURFACE, SURFACE_2, TEXT, WARNING

st.set_page_config(page_title="Data Skew Intelligence", page_icon="⚡", layout="wide")

st.markdown(
    f"""
    <style>
        .main {{ background-color: {BACKGROUND}; color: {TEXT}; }}
        .stApp {{ background-color: {BACKGROUND}; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {SURFACE};
            border-radius: 4px;
            color: {MUTED};
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {SURFACE_2} !important;
            color: {GREEN} !important;
            border-bottom: 2px solid {GREEN} !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("⚡ Data Skew Intelligence Dashboard")
st.caption("Intelligent Data Skew Detection & Mitigation Engineering Console")

tab_experiments, tab_data, tab_ml = st.tabs(["Experiments Benchmark", "Persisted Data & Distributions", "ML Model Diagnostics"])

# ----------------------------------------------------------------- Tab 1 ---
with tab_experiments:
    exp_dir = resolve_path(get("paths", "results_experiments", default="results/experiments"))
    exp_files = sorted(exp_dir.glob("*.json")) if exp_dir.exists() else []

    latest_summary = resolve_path("results/latest/summary.json")
    if not exp_files and latest_summary.exists():
        exp_files = [latest_summary]

    if not exp_files:
        st.info("No saved experiment records found. Run `python run.py` to generate experiment results.")
    else:
        rows = []
        payload_map = {}
        for path in exp_files:
            try:
                with open(path, encoding="utf-8") as f:
                    payload = json.load(f)
                exp_id = payload.get("experiment_id", path.stem)
                payload_map[exp_id] = payload

                before = payload.get("before", {})
                after = payload.get("after", {})

                rt_before = before.get("execution_time_sec", payload.get("baseline_execution_time", 0.0))
                rt_after = after.get("execution_time_sec", payload.get("mitigated_execution_time", 0.0))
                skew_val = payload.get("skew", payload.get("skew_ratio", 0.0))
                num_rows = payload.get("rows", 0)
                mit_strat = payload.get("mitigation", payload.get("mitigation_strategy", "NONE"))
                imp_val = payload.get("improvement_pct")
                if imp_val is None and rt_before > 0:
                    imp_val = round(((rt_before - rt_after) / rt_before) * 100, 2)

                max_before = before.get("max_partition_size", payload.get("baseline_max_partition_records", 0))
                max_after = after.get("max_partition_size", payload.get("mitigated_max_partition_records", 0))

                rows.append(
                    {
                        "Experiment": exp_id,
                        "Skew": skew_val,
                        "Rows": num_rows,
                        "Mitigation": mit_strat,
                        "Runtime Before (s)": round(float(rt_before), 4),
                        "Runtime After (s)": round(float(rt_after), 4),
                        "Improvement (%)": imp_val,
                        "Max Partition Before": max_before,
                        "Max Partition After": max_after,
                    }
                )
            except Exception:
                pass

        if rows:
            exp_df = pd.DataFrame(rows)
            st.dataframe(exp_df, width="stretch", hide_index=True)

            selected = st.selectbox("Select Experiment to Inspect", exp_df["Experiment"].tolist())
            payload = payload_map.get(selected, {})
            if payload:
                col1, col2 = st.columns([3, 2])
                with col1:
                    before = payload.get("before", {})
                    after = payload.get("after", {})
                    rt_b = before.get("execution_time_sec", payload.get("baseline_execution_time", 0.0))
                    rt_a = after.get("execution_time_sec", payload.get("mitigated_execution_time", 0.0))
                    max_b = before.get("max_partition_size", 0)
                    max_a = after.get("max_partition_size", 0)

                    fig = go.Figure(
                        data=[
                            go.Bar(name="Baseline", x=["Runtime (s)", "Max Partition Records"], y=[rt_b, max_b], marker_color=MUTED),
                            go.Bar(name="Mitigated", x=["Runtime (s)", "Max Partition Records"], y=[rt_a, max_a], marker_color=GREEN),
                        ]
                    )
                    fig.update_layout(
                        barmode="group",
                        title=f"Before vs After — {selected}",
                        paper_bgcolor=BACKGROUND,
                        plot_bgcolor=SURFACE,
                        font=dict(color=TEXT),
                        height=380,
                    )
                    st.plotly_chart(fig, width="stretch")
                with col2:
                    st.json(payload)

# ----------------------------------------------------------------- Tab 2 ---
with tab_data:
    st.subheader("Persisted Visualization Datasets & Physical Distributions")
    latest_data_dir = resolve_path("results/latest/data")
    latest_charts_dir = resolve_path("results/latest/charts")

    if not latest_data_dir.exists():
        st.info("No persisted data folder found under `results/latest/data/`. Run `python run.py` first.")
    else:
        d_col1, d_col2 = st.columns(2)

        with d_col1:
            st.markdown("### Top Keys Frequency Distribution")
            key_csv = latest_data_dir / "key_distribution.csv"
            if key_csv.exists():
                df_key = pd.read_csv(key_csv)
                st.dataframe(df_key, width="stretch", hide_index=True)
                fig_key = px.bar(
                    df_key,
                    y="key",
                    x="count",
                    orientation="h",
                    color_discrete_sequence=[GREEN],
                    title="Key Frequency Distribution",
                )
                fig_key.update_layout(paper_bgcolor=BACKGROUND, plot_bgcolor=SURFACE, font=dict(color=TEXT))
                st.plotly_chart(fig_key, width="stretch")

        with d_col2:
            st.markdown("### Physical Partition Distributions")
            part_csv = latest_data_dir / "partition_distribution.csv"
            if part_csv.exists():
                df_part = pd.read_csv(part_csv)
                st.dataframe(df_part, width="stretch", hide_index=True)
                fig_part = go.Figure()
                fig_part.add_trace(go.Bar(x=df_part["partition_index"], y=df_part["baseline_records"], name="Baseline", marker_color=MUTED))
                if "mitigated_records" in df_part.columns:
                    fig_part.add_trace(go.Bar(x=df_part["partition_index"], y=df_part["mitigated_records"], name="Mitigated", marker_color=GREEN))
                fig_part.update_layout(barmode="group", title="Partition Record Distributions", paper_bgcolor=BACKGROUND, plot_bgcolor=SURFACE, font=dict(color=TEXT))
                st.plotly_chart(fig_part, width="stretch")

        st.markdown("---")
        st.markdown("### Exported Chart PNG Artifacts")
        if latest_charts_dir.exists():
            chart_files = sorted(latest_charts_dir.glob("*.png"))
            if chart_files:
                cols = st.columns(2)
                for idx, c_path in enumerate(chart_files):
                    with cols[idx % 2]:
                        st.image(str(c_path), caption=c_path.name, width="stretch")

# ----------------------------------------------------------------- Tab 3 ---
with tab_ml:
    report_path = resolve_path(get("paths", "results_reports", default="results/reports")) / "ml_comparison.json"
    if not report_path.exists():
        st.info("No trained ML model comparison report found yet. Run `python run.py` or `python -m cli.app ml train`.")
    else:
        with open(report_path) as f:
            ml_payload = json.load(f)

        st.success(f"Selected Best Classifier: **{ml_payload.get('best_model', 'N/A')}**")

        results_df = pd.DataFrame(ml_payload.get("results", []))
        if not results_df.empty:
            display_cols = [c for c in ["model_name", "accuracy", "precision_macro", "recall_macro", "f1_macro"] if c in results_df.columns]
            st.dataframe(results_df[display_cols], width="stretch", hide_index=True)

            fig_ml = px.bar(
                results_df,
                x="model_name",
                y=[c for c in ["accuracy", "precision_macro", "recall_macro", "f1_macro"] if c in results_df.columns],
                barmode="group",
                title="Classifier Performance Metrics Comparison",
                color_discrete_sequence=[GREEN, GREEN_2, MUTED, WARNING],
            )
            fig_ml.update_layout(paper_bgcolor=BACKGROUND, plot_bgcolor=SURFACE, font=dict(color=TEXT))
            st.plotly_chart(fig_ml, width="stretch")
