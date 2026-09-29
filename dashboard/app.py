"""Conversation Quality Reviewer — Dashboard

Persona: QA Manager at JetBlue
Two views: Quality Summary | Review Queue (with inline detail)
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import ConversationResult, SignalName, SIGNAL_WEIGHTS

# --- Config ---
st.set_page_config(
    page_title="Conversation Quality Reviewer",
    page_icon="🎯",
    layout="wide",
)

DATA_DIR = Path(__file__).parent.parent / "data"

# Tier bar thresholds
ABOVE_BAR = 0.80
MARGINAL_LOW = 0.50

# Hard block signals — these trigger mandatory review
HARD_BLOCK_SIGNALS = {"resolution", "compliance"}

SIGNAL_COLORS = {
    "resolution": "#2ecc71",
    "efficiency": "#3498db",
    "compliance": "#e74c3c",
    "sentiment": "#f39c12",
    "communication": "#9b59b6",
}

SIGNAL_LABELS = {
    "resolution": "Resolution",
    "efficiency": "Efficiency",
    "compliance": "Compliance",
    "sentiment": "Sentiment",
    "communication": "Communication",
}


# --- Helpers ---

def tier_status(score: float) -> tuple[str, str]:
    """Return (emoji, label) for a score's tier."""
    if score >= ABOVE_BAR:
        return "🟢", "Above Bar"
    elif score >= MARGINAL_LOW:
        return "🟡", "Marginal"
    else:
        return "🔴", "Below Bar"


def has_hard_block(result: ConversationResult) -> bool:
    """Check if a conversation has any hard block failures."""
    for signal in HARD_BLOCK_SIGNALS:
        if signal in result.scores and result.scores[signal].score < MARGINAL_LOW:
            return True
    return False


def hard_block_reasons(result: ConversationResult) -> list[str]:
    """Get plain-English reasons for hard blocks."""
    reasons = []
    if "resolution" in result.scores and result.scores["resolution"].score < MARGINAL_LOW:
        reasons.append(f"Resolution failure ({result.scores['resolution'].score:.2f})")
    if "compliance" in result.scores and result.scores["compliance"].score < MARGINAL_LOW:
        detail = result.scores["compliance"].compliance_detail
        if detail and detail.missing_actions:
            reasons.append(f"Compliance violation — missing: {', '.join(detail.missing_actions[:3])}")
        else:
            reasons.append(f"Compliance violation ({result.scores['compliance'].score:.2f})")
    return reasons


def warning_reasons(result: ConversationResult) -> list[str]:
    """Get plain-English reasons for warnings."""
    reasons = []
    for signal_name in ["sentiment", "communication", "efficiency"]:
        if signal_name in result.scores:
            score = result.scores[signal_name].score
            if score < MARGINAL_LOW:
                reasons.append(f"Low {SIGNAL_LABELS[signal_name]} ({score:.2f})")
    if "sentiment_deterioration" in result.flags:
        reasons.append("Sentiment deterioration during call")
    if "communication_issues" in result.flags:
        comm = result.scores.get("communication")
        if comm and comm.flagged_utterances:
            reasons.append(f"Flagged utterances ({len(comm.flagged_utterances)})")
    return reasons


def issue_summary(result: ConversationResult) -> str:
    """One-line issue description for the review queue."""
    hb = hard_block_reasons(result)
    if hb:
        return hb[0]
    wr = warning_reasons(result)
    if wr:
        return wr[0]
    return "Passing"


def priority_sort_key(result: ConversationResult) -> tuple:
    """Sort key: hard blocks first (worst first), then warnings, then passing."""
    is_hb = has_hard_block(result)
    flag_count = len(result.flags)
    return (
        0 if is_hb else 1,        # hard blocks first
        -flag_count,               # more flags = higher priority
        result.overall_score,      # lower score = higher priority
    )


# --- Data Loading ---

@st.cache_data
def load_precomputed_results() -> list[ConversationResult]:
    path = DATA_DIR / "precomputed_scores.json"
    if not path.exists():
        return []
    with open(path, "r") as f:
        raw = json.load(f)
    return [ConversationResult(**r) for r in raw]


@st.cache_data
def load_transcripts() -> dict:
    try:
        from src.ingest import load_dataset
        convos = load_dataset("train")
        return {c.convo_id: c for c in convos}
    except Exception:
        try:
            from src.ingest import load_sample
            convos = load_sample()
            return {c.convo_id: c for c in convos}
        except Exception:
            return {}


def results_to_df(results: list[ConversationResult]) -> pd.DataFrame:
    rows = []
    for r in results:
        row = {
            "convo_id": r.convo_id,
            "flow": r.flow,
            "subflow": r.subflow,
            "overall": r.overall_score,
            "flags": ", ".join(r.flags) if r.flags else "",
            "flag_count": len(r.flags),
            "hard_block": has_hard_block(r),
            "scored_at": r.scored_at,
        }
        for signal in SignalName:
            if signal.value in r.scores:
                row[signal.value] = r.scores[signal.value].score
            else:
                row[signal.value] = None
        rows.append(row)
    df = pd.DataFrame(rows)
    if "scored_at" in df.columns:
        df["scored_at"] = pd.to_datetime(df["scored_at"], utc=True)
    return df


# --- Load data ---
results = load_precomputed_results()
transcripts = load_transcripts()

if not results:
    st.warning(
        "No precomputed scores found. Run `python scripts/seed_data.py` to generate scores."
    )
    st.stop()

all_df = results_to_df(results)
results_dict = {r.convo_id: r for r in results}

# --- Sidebar ---
st.sidebar.title("Quality Reviewer")

# Initialize session state for cross-view navigation
if "nav_signal_filter" not in st.session_state:
    st.session_state.nav_signal_filter = "All signals"
if "nav_from_summary" not in st.session_state:
    st.session_state.nav_from_summary = False
if "view_radio" not in st.session_state:
    st.session_state.view_radio = "Quality Summary"

def _on_view_change():
    """When user manually switches view via radio, clear cross-nav state."""
    st.session_state.nav_from_summary = False
    st.session_state.nav_signal_filter = "All signals"
    if hasattr(st.session_state, "nav_flow"):
        del st.session_state.nav_flow

view = st.sidebar.radio(
    "Navigate",
    ["Quality Summary", "Review Queue"],
    help="Quality Summary: How are we doing? | Review Queue: Which calls need attention?",
    key="view_radio",
    on_change=_on_view_change,
)

# --- Date Range Selector ---
DATE_RANGE_OPTIONS = {
    "Last 24 hours": timedelta(hours=24),
    "Last 7 days": timedelta(days=7),
    "Last 30 days": timedelta(days=30),
    "All time": None,
}
selected_range = st.sidebar.radio(
    "Time Window",
    list(DATE_RANGE_OPTIONS.keys()),
    index=1,  # Default: Last 7 days
    help="Filter conversations by when they were scored. Deltas compare to the equivalent prior period.",
)
range_delta = DATE_RANGE_OPTIONS[selected_range]

# Compute current and comparison periods
now = datetime.now(timezone.utc)
if range_delta is not None:
    current_start = now - range_delta
    prior_start = current_start - range_delta
    prior_end = current_start
    range_label = selected_range.replace("Last ", "last ")
else:
    current_start = None
    prior_start = None
    prior_end = None
    range_label = None

# Apply date filtering
has_timestamps = "scored_at" in all_df.columns and all_df["scored_at"].notna().any()
if has_timestamps and current_start is not None:
    current_start_ts = pd.Timestamp(current_start)
    prior_start_ts = pd.Timestamp(prior_start)
    prior_end_ts = pd.Timestamp(prior_end)
    time_filtered_df = all_df[all_df["scored_at"] >= current_start_ts]
    prior_df = all_df[(all_df["scored_at"] >= prior_start_ts) & (all_df["scored_at"] < prior_end_ts)]
else:
    time_filtered_df = all_df
    prior_df = pd.DataFrame()

# Flow filter
all_flows = sorted(all_df["flow"].unique())
selected_flow = st.sidebar.selectbox("Filter by Call Reason", ["All Call Reasons"] + all_flows)

# Apply flow filter on top of time filter
df = time_filtered_df if selected_flow == "All Call Reasons" else time_filtered_df[time_filtered_df["flow"] == selected_flow]
prior_period_df = prior_df if selected_flow == "All Call Reasons" else prior_df[prior_df["flow"] == selected_flow] if not prior_df.empty else pd.DataFrame()
filtered_results = [r for r in results if r.convo_id in set(df["convo_id"])]

# --- Judge Info (sidebar) ---
st.sidebar.divider()
st.sidebar.markdown("**Judge Info**")
st.sidebar.caption(
    "**LLM-judged**: Resolution, Sentiment, Communication\n\n"
    "**Heuristic**: Efficiency\n\n"
    "**Hybrid**: Compliance (heuristic + LLM)\n\n"
    "**Calibration**: Not yet calibrated — scores are directional. "
    "Production deployment requires human-LLM agreement validation."
)

# --- Quality bar reference ---
st.sidebar.divider()
st.sidebar.markdown("**Quality Bar**")
st.sidebar.caption(
    "🟢 Above Bar: ≥ 0.80\n\n"
    "🟡 Marginal: 0.50 – 0.79\n\n"
    "🔴 Below Bar: < 0.50\n\n"
    "**Hard Block**: Resolution < 0.50 OR Compliance < 0.50 → must review"
)

# --- API Reference ---
st.sidebar.divider()
with st.sidebar.expander("API Reference"):
    st.sidebar.markdown(
        "**Base URL**: `http://localhost:8000`\n\n"
        "| Endpoint | Method | Description |\n"
        "|----------|--------|-------------|\n"
        "| `/health` | GET | System status |\n"
        "| `/analyze` | POST | Submit batch for scoring |\n"
        "| `/results/{batch_id}` | GET | Fetch batch results |\n"
        "| `/conversation/{id}` | GET | Single conversation scores |\n"
        "| `/conversations` | GET | List/filter scored conversations |\n"
        "| `/summary` | GET | Aggregate quality metrics |\n\n"
        "**Docs**: `http://localhost:8000/docs` (Swagger UI)\n\n"
        "**Example**:\n"
        "```\n"
        "curl localhost:8000/conversation/3592\n"
        "```"
    )


# =====================================================
# SHARED: CONVERSATION DETAIL RENDERER
# =====================================================
def _show_conversation_detail(result: ConversationResult, convo):
    """Render full conversation detail. Used by both Review Queue and Conversation Detail views."""
    is_hb = has_hard_block(result)

    # --- Header banner ---
    overall_emoji, overall_label = tier_status(result.overall_score)
    if is_hb:
        st.error(
            f"**HARD BLOCK** — Overall: {result.overall_score:.2f} · "
            f"{' · '.join(hard_block_reasons(result))}"
        )
    elif result.flags:
        st.warning(
            f"**WARNING** — Overall: {result.overall_score:.2f} · "
            f"{' · '.join(warning_reasons(result))}"
        )
    else:
        st.success(f"**PASSING** — Overall: {result.overall_score:.2f} {overall_emoji}")

    # Context line
    st.caption(
        f"Call Reason: {result.flow.replace('_', ' ').title()} → {result.subflow.replace('_', ' ').title()}"
        + (f" · Customer: {convo.scenario.personal.customer_name} ({convo.scenario.personal.member_level} member)" if convo else "")
    )

    # --- KEY INSIGHTS (TL;DR at the top) ---
    st.markdown("#### Key Insights")

    # Collect all actionable findings, prioritized
    insights = []

    # 1. Missing compliance actions (most actionable)
    compliance = result.scores.get("compliance")
    if compliance and compliance.compliance_detail:
        missing = compliance.compliance_detail.missing_actions
        if missing:
            insights.append(("🔴", f"**Missing required actions**: {', '.join(missing)}"))

    # 2. Resolution failure
    resolution = result.scores.get("resolution")
    if resolution and resolution.score < MARGINAL_LOW:
        insights.append(("🔴", f"**Issue not resolved** — {resolution.reasoning[:120]}"))

    # 3. Sentiment deterioration
    sentiment_score = result.scores.get("sentiment")
    if sentiment_score and sentiment_score.turn_sentiments:
        scores = [ts.score for ts in sentiment_score.turn_sentiments]
        if len(scores) >= 2 and scores[-1] - scores[0] < -0.3:
            insights.append(("⚠️", f"**Customer sentiment dropped** from {scores[0]:+.1f} to {scores[-1]:+.1f} during the call"))

    # 4. Communication issues
    comm = result.scores.get("communication")
    if comm:
        if comm.communication_sub and comm.communication_sub.empathy < 0.4:
            insights.append(("⚠️", f"**Low empathy** ({comm.communication_sub.empathy:.2f}) — agent did not acknowledge customer's feelings"))
        if comm.flagged_utterances:
            insights.append(("⚠️", f"**{len(comm.flagged_utterances)} flagged utterance(s)** need review"))

    # 5. Strengths
    for signal in SignalName:
        if signal.value in result.scores and result.scores[signal.value].score >= ABOVE_BAR:
            insights.append(("🟢", f"**{SIGNAL_LABELS[signal.value]}** is above bar ({result.scores[signal.value].score:.2f})"))

    if not insights:
        st.caption("No significant findings.")
    else:
        for icon, text in insights:
            st.markdown(f"{icon} {text}")

    st.divider()

    # --- Score Card + Radar ---
    col_scores, col_radar = st.columns([1, 1])

    with col_scores:
        st.subheader("Score Card")
        for signal in SignalName:
            if signal.value not in result.scores:
                continue
            score_obj = result.scores[signal.value]
            emoji, label = tier_status(score_obj.score)
            is_hard = signal.value in HARD_BLOCK_SIGNALS
            gate_label = "Hard Block" if is_hard else "Warning"

            st.markdown(
                f"**{SIGNAL_LABELS[signal.value]}** · "
                f"<span style='font-size:1.2em;'>{score_obj.score:.2f}</span> "
                f"{emoji} · {gate_label}",
                unsafe_allow_html=True,
            )
            st.caption(score_obj.reasoning)

            if signal == SignalName.COMMUNICATION and score_obj.communication_sub:
                sub = score_obj.communication_sub
                st.caption(
                    f"Clarity: {sub.clarity:.2f} · Empathy: {sub.empathy:.2f} · "
                    f"Professionalism: {sub.professionalism:.2f} · Proactiveness: {sub.proactiveness:.2f}"
                )

    with col_radar:
        categories = []
        values = []
        for signal in SignalName:
            if signal.value in result.scores:
                categories.append(SIGNAL_LABELS[signal.value])
                values.append(result.scores[signal.value].score)

        if categories:
            fig = go.Figure(data=go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                fillcolor="rgba(52, 152, 219, 0.15)",
                line=dict(color="#3498db", width=2),
            ))
            fig.add_trace(go.Scatterpolar(
                r=[ABOVE_BAR] * (len(categories) + 1),
                theta=categories + [categories[0]],
                mode="lines",
                line=dict(color="green", dash="dash", width=1),
                name="Above Bar",
                showlegend=False,
            ))
            fig.add_trace(go.Scatterpolar(
                r=[MARGINAL_LOW] * (len(categories) + 1),
                theta=categories + [categories[0]],
                mode="lines",
                line=dict(color="red", dash="dash", width=1),
                name="Below Bar",
                showlegend=False,
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                height=350,
                margin=dict(l=60, r=60, t=30, b=30),
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- What Went Wrong / What Went Well ---
    col_bad, col_good = st.columns(2)

    with col_bad:
        st.subheader("What Needs Improvement")
        issues_found = False

        for signal in SignalName:
            if signal.value not in result.scores:
                continue
            score_obj = result.scores[signal.value]

            if signal.value in HARD_BLOCK_SIGNALS and score_obj.score < MARGINAL_LOW:
                issues_found = True
                st.markdown(f"🔴 **{SIGNAL_LABELS[signal.value]}** ({score_obj.score:.2f})")
                st.caption(score_obj.reasoning)
                if score_obj.compliance_detail and score_obj.compliance_detail.missing_actions:
                    st.caption(f"Missing: {', '.join(score_obj.compliance_detail.missing_actions)}")
            elif score_obj.score < ABOVE_BAR:
                issues_found = True
                st.markdown(f"⚠️ **{SIGNAL_LABELS[signal.value]}** ({score_obj.score:.2f})")
                st.caption(score_obj.reasoning)

            if score_obj.flagged_utterances:
                for fu in score_obj.flagged_utterances[:3]:
                    st.caption(f"  ↳ {fu}")

        if not issues_found:
            st.markdown("🟢 No significant issues found.")

    with col_good:
        st.subheader("What Went Well")
        strengths_found = False

        for signal in SignalName:
            if signal.value not in result.scores:
                continue
            score_obj = result.scores[signal.value]

            if score_obj.score >= ABOVE_BAR:
                strengths_found = True
                st.markdown(f"🟢 **{SIGNAL_LABELS[signal.value]}** ({score_obj.score:.2f})")
                if score_obj.evidence:
                    st.caption(score_obj.evidence[0] if score_obj.evidence else "")

        if not strengths_found:
            st.markdown("No signals above bar.")

    # --- Compliance Detail (if available) ---
    if compliance and compliance.compliance_detail:
        cd = compliance.compliance_detail
        with st.expander("Compliance Detail — Expected vs. Actual Actions"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Expected Sequence**")
                for i, action in enumerate(cd.expected_actions, 1):
                    in_actual = action in cd.actual_actions
                    st.markdown(f"{i}. {'✅' if in_actual else '❌'} {action}")
            with c2:
                st.markdown("**Actual Sequence**")
                for i, action in enumerate(cd.actual_actions, 1):
                    in_expected = action in cd.expected_actions
                    st.markdown(f"{i}. {'✅' if in_expected else '➕'} {action}")
            if cd.llm_adjustment != 0:
                st.caption(f"LLM adjustment: {cd.llm_adjustment:+.2f}")

    st.divider()

    # --- Sentiment Trajectory ---
    if sentiment_score and sentiment_score.turn_sentiments:
        st.subheader("Customer Sentiment Trajectory")
        sent_data = []
        for ts in sentiment_score.turn_sentiments:
            sent_data.append({
                "Turn": ts.turn_index,
                "Sentiment": ts.score,
                "Text": ts.text[:60],
            })
        sent_df = pd.DataFrame(sent_data)
        fig = px.line(
            sent_df, x="Turn", y="Sentiment",
            markers=True,
            hover_data=["Text"],
            labels={"Sentiment": "Sentiment (-1 to 1)"},
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3)
        fig.add_hrect(y0=-1, y1=-0.3, fillcolor="red", opacity=0.05)
        fig.add_hrect(y0=0.3, y1=1, fillcolor="green", opacity=0.05)
        fig.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=20))
        fig.update_traces(
            marker=dict(
                color=sent_df["Sentiment"],
                colorscale=[[0, "#e74c3c"], [0.5, "#f39c12"], [1, "#2ecc71"]],
                cmin=-1, cmax=1, size=8,
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

        if sentiment_score.evidence:
            for ev in sentiment_score.evidence:
                if "Frustration" in ev:
                    st.caption(f"🔴 {ev}")
                elif "Recovery" in ev:
                    st.caption(f"🟢 {ev}")

    # --- Transcript ---
    if convo:
        st.subheader("Transcript")

        for i, turn in enumerate(convo.original):
            speaker = turn.speaker.value
            text = turn.text

            if speaker == "agent":
                icon, label = "🟦", "Agent"
            elif speaker == "customer":
                icon, label = "🟩", "Customer"
            else:
                icon, label = "⚙️", "Action"

            bg_style = ""
            sentiment_badge = ""
            if speaker == "customer" and sentiment_score and sentiment_score.turn_sentiments:
                matching = [ts for ts in sentiment_score.turn_sentiments if ts.turn_index == i]
                if matching:
                    s = matching[0].score
                    if s < -0.3:
                        bg_style = "background-color: rgba(231, 76, 60, 0.08); border-left: 3px solid #e74c3c;"
                        sentiment_badge = f" <span style='color:#e74c3c;font-size:0.8em;'>({s:+.1f})</span>"
                    elif s > 0.3:
                        bg_style = "background-color: rgba(46, 204, 113, 0.08); border-left: 3px solid #2ecc71;"
                        sentiment_badge = f" <span style='color:#2ecc71;font-size:0.8em;'>({s:+.1f})</span>"
                    else:
                        sentiment_badge = f" <span style='color:#999;font-size:0.8em;'>({s:+.1f})</span>"

            flag_annotation = ""
            if speaker == "agent":
                comm_score = result.scores.get("communication")
                if comm_score and comm_score.flagged_utterances:
                    for fu in comm_score.flagged_utterances:
                        if text[:30] in fu:
                            flag_annotation = "<br><span style='color:#e74c3c;font-size:0.8em;'>⚠️ Flagged: " + fu.split(": ", 1)[-1][:80] + "</span>"

            st.markdown(
                f"<div style='padding:6px 10px;margin:2px 0;border-radius:4px;{bg_style}'>"
                f"{icon} <strong>{label}:</strong> {text}{sentiment_badge}{flag_annotation}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("Transcript not available. Load the ABCD dataset to view transcripts.")

    # --- Feedback placeholder ---
    st.divider()
    st.button(
        "📝 Add Feedback", disabled=True,
        help="In production: QA manager writes coaching notes here. Feedback also calibrates the LLM judge.",
        key=f"feedback_{result.convo_id}",
    )


# --- Quality table builder ---

def _build_quality_table(
    source_df: pd.DataFrame,
    group_col: str,
    label: str,
    signal_cols: list[str],
    prior_source_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build quality summary table grouped by group_col.

    Returns DataFrame with: Status, {label}, Quality, Quality_sort, Trend, Trend_sort,
    Biggest Gap, Biggest_gap_signal, Hard Blocks, HB_sort, Flagged, Flagged_pct, _raw_group
    """
    # Pre-compute prior period averages by group
    prior_avgs = {}
    if prior_source_df is not None and len(prior_source_df) > 0:
        for group_val in prior_source_df[group_col].unique():
            grp = prior_source_df[prior_source_df[group_col] == group_val]
            prior_avgs[group_val] = grp["overall"].mean()

    rows = []
    for group_val in sorted(source_df[group_col].unique()):
        grp_df = source_df[source_df[group_col] == group_val]
        avg_overall = grp_df["overall"].mean()
        emoji, tier_label = tier_status(avg_overall)
        hb_count = int(grp_df["hard_block"].sum())
        flagged_count = int(grp_df[grp_df["flag_count"] > 0].shape[0])

        # Find the weakest signal
        weakest_signal = ""
        weakest_signal_key = ""
        weakest_score = 1.0
        for sig in signal_cols:
            vals = grp_df[sig].dropna()
            if len(vals) > 0:
                avg = vals.mean()
                if avg < weakest_score:
                    weakest_score = avg
                    weakest_signal = SIGNAL_LABELS.get(sig, sig)
                    weakest_signal_key = sig

        if weakest_score >= ABOVE_BAR:
            primary_issue = "—"
        elif weakest_score >= MARGINAL_LOW:
            primary_issue = f"⚠️ {weakest_signal} ({weakest_score:.2f})"
        else:
            primary_issue = f"🔴 {weakest_signal} ({weakest_score:.2f})"

        total_count = len(grp_df)
        flagged_pct = (flagged_count / total_count * 100) if total_count > 0 else 0

        # Trend computation
        trend_delta = None
        if group_val in prior_avgs:
            trend_delta = avg_overall - prior_avgs[group_val]

        if trend_delta is None:
            trend_display = "—"
            trend_sort = 0.0
        elif trend_delta > 0.02:
            trend_display = f"🟢 ▲ {trend_delta:.2f}"
            trend_sort = trend_delta
        elif trend_delta < -0.02:
            trend_display = f"🔴 ▼ {abs(trend_delta):.2f}"
            trend_sort = trend_delta
        else:
            trend_display = "— stable"
            trend_sort = 0.0

        tier_emoji, _ = tier_status(avg_overall)
        rows.append({
            "Status": f"{emoji} {tier_label}",
            label: group_val.replace("_", " ").title(),
            "Quality": f"{tier_emoji} {avg_overall:.2f}",
            "Quality_sort": avg_overall,
            "Trend": trend_display,
            "Trend_sort": trend_sort,
            "Biggest Gap": primary_issue,
            "Biggest_gap_signal": weakest_signal_key,
            "Hard Blocks": f"🔴 {hb_count}" if hb_count > 0 else "—",
            "HB_sort": hb_count,
            "Flagged": f"{flagged_count}/{total_count} ({flagged_pct:.0f}%)",
            "Flagged_pct": flagged_pct,
            "_raw_group": group_val,
        })
    return pd.DataFrame(rows)


# =====================================================
# VIEW 1: QUALITY SUMMARY
# =====================================================
if view == "Quality Summary":
    st.title("Quality Summary")

    # --- KPI Cards ---
    total = len(df)
    avg_overall = df["overall"].mean() if total > 0 else 0
    overall_emoji, overall_label = tier_status(avg_overall)

    hard_block_count = int(df["hard_block"].sum())
    needs_review = int(df[df["flag_count"] > 0].shape[0])
    pass_rate = (total - needs_review) / total if total > 0 else 0

    # Compute prior period values for deltas
    has_prior = len(prior_period_df) > 0
    if has_prior:
        prior_total = len(prior_period_df)
        prior_avg_overall = prior_period_df["overall"].mean() if prior_total > 0 else 0
        prior_hb_count = int(prior_period_df["hard_block"].sum())
        prior_needs_review = int(prior_period_df[prior_period_df["flag_count"] > 0].shape[0])
        prior_pass_rate = (prior_total - prior_needs_review) / prior_total if prior_total > 0 else 0

        delta_quality = avg_overall - prior_avg_overall
        delta_pass_rate = pass_rate - prior_pass_rate
        delta_hb = hard_block_count - prior_hb_count
        delta_review = needs_review - prior_needs_review
    else:
        delta_quality = delta_pass_rate = delta_hb = delta_review = None

    def _format_delta(delta: float | None, fmt: str = "pct", invert: bool = False) -> str:
        """Format a delta value with arrow and color.

        Args:
            delta: The change value, or None if no prior data.
            fmt: 'pct' for percentage points, 'int' for integer count.
            invert: If True, a decrease is good (green) — used for Hard Blocks/Needs Review.
        """
        if delta is None:
            return '<span style="color:gray;font-size:0.85em;">— No prior data</span>'
        if abs(delta) < 0.001 and fmt == "pct":
            return f'<span style="color:gray;font-size:0.85em;">— Stable vs {range_label}</span>'
        if delta == 0 and fmt == "int":
            return f'<span style="color:gray;font-size:0.85em;">— Stable vs {range_label}</span>'

        is_positive_direction = (delta > 0) != invert
        color = "#2ecc71" if is_positive_direction else "#e74c3c"
        arrow = "▲" if delta > 0 else "▼"

        if fmt == "pct":
            text = f"{arrow} {abs(delta):.1%} vs {range_label}"
        else:
            text = f"{arrow} {abs(int(delta))} vs {range_label}"
        return f'<span style="color:{color};font-size:0.85em;">{text}</span>'

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall Quality", f"{avg_overall:.0%}")
    c1.caption(f"{overall_emoji} {overall_label}")
    c1.markdown(_format_delta(delta_quality, "pct"), unsafe_allow_html=True)

    c2.metric("Pass Rate", f"{pass_rate:.0%}")
    pr_emoji, _ = tier_status(pass_rate)
    c2.caption(f"{pr_emoji} {total - needs_review}/{total} conversations")
    c2.markdown(_format_delta(delta_pass_rate, "pct"), unsafe_allow_html=True)

    c3.metric("Hard Blocks", hard_block_count)
    if hard_block_count > 0:
        c3.caption("🔴 Action required")
    else:
        c3.caption("🟢 None")
    c3.markdown(_format_delta(delta_hb, "int", invert=True), unsafe_allow_html=True)

    c4.metric("Needs Review", needs_review)
    c4.caption(f"Flagged for QA attention")
    c4.markdown(_format_delta(delta_review, "int", invert=True), unsafe_allow_html=True)

    if hard_block_count > 0 or needs_review > 0:
        st.info(f"**{hard_block_count} hard blocks + {needs_review - hard_block_count} warnings** need review. Switch to **Review Queue** in the sidebar to triage.")

    # --- Quality bar definition ---
    st.caption(
        "🟢 Above Bar (≥0.80) · 🟡 Marginal (0.50–0.79) · 🔴 Below Bar (<0.50) · "
        "Hard Block = Resolution < 0.50 OR Compliance < 0.50"
    )
    if range_label:
        st.caption(f"Showing: {range_label} · Deltas vs. prior equivalent period")

    st.divider()

    # --- Quality by Flow / Subflow (status table) ---
    signal_cols = [s.value for s in SignalName if s.value in df.columns and df[s.value].notna().any()]

    is_filtered = selected_flow != "All Call Reasons"

    if is_filtered:
        # When filtered to a specific call reason, show subflow breakdown
        st.subheader(f"Quality by Subflow — {selected_flow.replace('_', ' ').title()}")
        st.caption("Which subflows are driving quality issues?")
        group_col, group_label = "subflow", "Subflow"
    else:
        st.subheader("Quality by Call Reason")
        st.caption("Which conversation types are meeting quality standards? Sorted worst-first.")
        group_col, group_label = "flow", "Call Reason"

    # Build table with prior period for trend computation
    prior_for_table = prior_period_df if not prior_period_df.empty else None
    quality_table = _build_quality_table(df, group_col, group_label, signal_cols, prior_for_table)

    # Sort toggle
    sort_options = [
        "Quality (low → high)",
        "Flagged % (high → low)",
        "Hard Blocks (high → low)",
        "Biggest Decline",
    ]
    sort_by = st.selectbox("Sort by", sort_options, index=0)
    if sort_by == "Flagged % (high → low)":
        quality_table = quality_table.sort_values("Flagged_pct", ascending=False)
    elif sort_by == "Hard Blocks (high → low)":
        quality_table = quality_table.sort_values("HB_sort", ascending=False)
    elif sort_by == "Biggest Decline":
        quality_table = quality_table.sort_values("Trend_sort", ascending=True)
    else:
        quality_table = quality_table.sort_values("Quality_sort", ascending=True)

    # Drop hidden sort columns before display
    hidden_cols = ["Quality_sort", "HB_sort", "Flagged_pct", "Trend_sort", "Biggest_gap_signal", "_raw_group"]
    display_table = quality_table.drop(columns=[c for c in hidden_cols if c in quality_table.columns])

    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Quality": st.column_config.TextColumn(
                "Quality Score",
                help="Weighted average across all signals. 🟢 ≥0.80, 🟡 0.50–0.79, 🔴 <0.50",
            ),
            "Trend": st.column_config.TextColumn(
                "Trend",
                help="Quality score change vs. prior period. 🟢▲ = improving, 🔴▼ = declining, — = stable (±0.02)",
            ),
            "Biggest Gap": st.column_config.TextColumn(
                "Biggest Gap",
                help=f"The lowest-scoring signal for this {group_label.lower()} — where to focus improvement",
            ),
            "Hard Blocks": st.column_config.TextColumn(
                "Hard Blocks",
                help="Conversations with resolution failure or compliance violation — must review",
            ),
            "Flagged": st.column_config.TextColumn(
                "Flagged",
                help="Conversations needing QA review out of total (hard blocks + warnings)",
            ),
        },
    )

    # --- Cross-View Navigation: Click a row to jump to Review Queue ---
    if not is_filtered:
        st.caption("Click a call reason below to jump to its flagged conversations in the Review Queue.")
        nav_cols = st.columns(min(len(quality_table), 5))
        for i, (_, row) in enumerate(quality_table.iterrows()):
            col_idx = i % min(len(quality_table), 5)
            raw_group = row["_raw_group"]
            display_name = row[group_label]
            gap_signal = row.get("Biggest_gap_signal", "")
            flagged_pct = row.get("Flagged_pct", 0) if "Flagged_pct" in quality_table.columns else 0
            hb = row.get("HB_sort", 0) if "HB_sort" in quality_table.columns else 0

            # Build button label
            btn_label = f"{display_name}"
            if hb > 0:
                btn_label += f" (🔴 {int(hb)})"
            elif flagged_pct > 0:
                btn_label += f" ({flagged_pct:.0f}%)"

            with nav_cols[col_idx]:
                if st.button(btn_label, key=f"nav_{raw_group}", use_container_width=True):
                    # Navigate to Review Queue filtered by this flow + signal
                    st.session_state.view_radio = "Review Queue"
                    st.session_state.nav_from_summary = True
                    # Map gap signal to flag filter
                    signal_to_filter = {
                        "resolution": "Resolution flags",
                        "compliance": "Compliance flags",
                        "sentiment": "Sentiment flags",
                        "communication": "Communication flags",
                        "efficiency": "Efficiency flags",
                    }
                    st.session_state.nav_signal_filter = signal_to_filter.get(gap_signal, "All signals")
                    st.session_state.nav_flow = raw_group
                    st.rerun()

    # Signal detail per group (expandable)
    breakdown_label = "subflow" if is_filtered else "call reason"
    with st.expander(f"Signal breakdown by {breakdown_label}"):
        detail_rows = []
        for group_val in sorted(df[group_col].unique()):
            grp_df = df[df[group_col] == group_val]
            row = {group_label: group_val.replace("_", " ").title()}
            for sig in signal_cols:
                vals = grp_df[sig].dropna()
                if len(vals) > 0:
                    avg = vals.mean()
                    e, _ = tier_status(avg)
                    row[SIGNAL_LABELS.get(sig, sig)] = f"{e} {avg:.2f}"
                else:
                    row[SIGNAL_LABELS.get(sig, sig)] = "—"
            detail_rows.append(row)
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

    # --- Top Issues (only when filtered to a specific call reason) ---
    if is_filtered:
        st.divider()
        st.subheader("Top Issues")
        st.caption("What specifically is failing, and what should training focus on?")

        # 3a. Signal failure counts
        failure_counts = []
        for sig in signal_cols:
            vals = df[sig].dropna()
            if len(vals) > 0:
                below_bar = int((vals < MARGINAL_LOW).sum())
                failure_counts.append((SIGNAL_LABELS.get(sig, sig), below_bar, below_bar / len(vals)))
        failure_counts.sort(key=lambda x: x[1], reverse=True)

        st.markdown("**Top Failure Signals**")
        for sig_label, count, pct in failure_counts:
            if count > 0:
                st.markdown(f"🔴 **{sig_label}**: {count} below bar ({pct:.0%})")
            else:
                st.markdown(f"🟢 **{sig_label}**: {count} below bar ({pct:.0%})")

        # 3b. Top missing compliance actions
        compliance_failures = [
            r for r in filtered_results
            if "compliance" in r.scores and r.scores["compliance"].score < MARGINAL_LOW
        ]
        if compliance_failures:
            missing_counter: Counter = Counter()
            for r in filtered_results:
                comp = r.scores.get("compliance")
                if comp and comp.compliance_detail and comp.compliance_detail.missing_actions:
                    missing_counter.update(comp.compliance_detail.missing_actions)

            if missing_counter:
                st.markdown("**Top Missing Compliance Actions**")
                for i, (action, count) in enumerate(missing_counter.most_common(5), 1):
                    st.markdown(f"  {i}. **{action}** — missing in {count} conversations")

    st.divider()

    # --- Signal Breakdown (horizontal bars) ---
    st.subheader("Signal Breakdown")

    signal_avg_data = []
    for sig in SignalName:
        if sig.value in df.columns:
            vals = df[sig.value].dropna()
            if len(vals) > 0:
                avg = vals.mean()
                emoji, label = tier_status(avg)
                is_hb = sig.value in HARD_BLOCK_SIGNALS
                signal_avg_data.append({
                    "Signal": SIGNAL_LABELS[sig.value],
                    "Score": round(avg, 3),
                    "Status": f"{emoji} {label}",
                    "Weight": f"{SIGNAL_WEIGHTS[sig]:.0%}",
                    "Type": "Hard Block" if is_hb else "Warning",
                })

    if signal_avg_data:
        sig_df = pd.DataFrame(signal_avg_data)
        fig = go.Figure()
        for _, row in sig_df.iterrows():
            score = row["Score"]
            if score >= ABOVE_BAR:
                color = "#2ecc71"  # green
            elif score >= MARGINAL_LOW:
                color = "#f39c12"  # yellow/orange
            else:
                color = "#e74c3c"  # red
            fig.add_trace(go.Bar(
                y=[row["Signal"]],
                x=[row["Score"]],
                orientation="h",
                marker_color=color,
                text=f"{row['Score']:.2f}  {row['Status']}",
                textposition="outside",
                showlegend=False,
            ))
        # Add threshold lines
        fig.add_vline(x=ABOVE_BAR, line_dash="dash", line_color="green", opacity=0.4,
                      annotation_text="Above Bar", annotation_position="top")
        fig.add_vline(x=MARGINAL_LOW, line_dash="dash", line_color="red", opacity=0.4,
                      annotation_text="Below Bar", annotation_position="top")
        fig.update_layout(
            xaxis=dict(range=[0, 1.15], title="Average Score"),
            height=250,
            margin=dict(l=20, r=100, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- Charts row (secondary) ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Score Distribution")
        st.caption(
            "How quality scores are distributed across all conversations. "
            "A healthy center clusters right of the green line. Scores spread "
            "across the full range indicate inconsistent quality — a systemic issue."
        )

        # Tier zone summary
        n_total = len(df)
        n_above = int((df["overall"] >= ABOVE_BAR).sum())
        n_marginal = int(((df["overall"] >= MARGINAL_LOW) & (df["overall"] < ABOVE_BAR)).sum())
        n_below = int((df["overall"] < MARGINAL_LOW).sum())
        t1, t2, t3 = st.columns(3)
        t1.markdown(f"🟢 **Above Bar**: {n_above} ({n_above/n_total:.0%})")
        t2.markdown(f"🟡 **Marginal**: {n_marginal} ({n_marginal/n_total:.0%})")
        t3.markdown(f"🔴 **Below Bar**: {n_below} ({n_below/n_total:.0%})")

        fig = px.histogram(
            df, x="overall", nbins=20,
            color_discrete_sequence=["#3498db"],
            labels={"overall": "Overall Score", "count": "Conversations"},
        )
        fig.add_vline(x=ABOVE_BAR, line_dash="dash", line_color="green", opacity=0.5)
        fig.add_vline(x=MARGINAL_LOW, line_dash="dash", line_color="red", opacity=0.5)
        fig.update_layout(showlegend=False, height=320, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Coaching Pattern Map")
        st.caption(
            "Each dot is a conversation. The quadrants reveal coaching patterns: "
            "top-right = ideal, bottom-right = follows rules but doesn't resolve, "
            "top-left = resolves but breaks rules (compliance risk), bottom-left = needs coaching."
        )
        if "resolution" in df.columns and "compliance" in df.columns:
            scatter_df = df.dropna(subset=["resolution", "compliance"])
            if not scatter_df.empty:
                fig = px.scatter(
                    scatter_df, x="compliance", y="resolution",
                    color="flow", hover_data=["convo_id", "subflow", "overall"],
                    labels={"compliance": "Policy Compliance", "resolution": "Resolution"},
                    opacity=0.7,
                )
                fig.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.4)
                fig.add_vline(x=0.5, line_dash="dash", line_color="gray", opacity=0.4)
                fig.add_annotation(x=0.25, y=0.95, text="⚠️ Cowboys<br>(compliance risk)",
                                   showarrow=False, font=dict(size=9, color="#e74c3c"))
                fig.add_annotation(x=0.75, y=0.95, text="✅ Ideal",
                                   showarrow=False, font=dict(size=9, color="#2ecc71"))
                fig.add_annotation(x=0.25, y=0.05, text="🔴 Needs coaching",
                                   showarrow=False, font=dict(size=9, color="#e74c3c"))
                fig.add_annotation(x=0.75, y=0.05, text="📋 By-the-book<br>but ineffective",
                                   showarrow=False, font=dict(size=9, color="#f39c12"))
                fig.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Run LLM scoring to see the Coaching Pattern Map.")
        else:
            st.info("Run LLM scoring to see the Coaching Pattern Map.")


# =====================================================
# VIEW 2: REVIEW QUEUE (with master-detail navigation)
# =====================================================
elif view == "Review Queue":
    # Initialize session state for master-detail navigation
    if "selected_review" not in st.session_state:
        st.session_state.selected_review = None

    # --- Handle cross-view navigation from Quality Summary ---
    # If we arrived here via a cross-view click, override the flow filter
    if st.session_state.nav_from_summary and hasattr(st.session_state, "nav_flow"):
        nav_flow = st.session_state.nav_flow
        cross_view_results = [r for r in results if r.convo_id in set(time_filtered_df["convo_id"]) and r.flow == nav_flow]
    else:
        cross_view_results = filtered_results

    # --- Signal filter (works both independently and via cross-view nav) ---
    SIGNAL_FILTER_OPTIONS = ["All signals", "Resolution flags", "Compliance flags", "Sentiment flags", "Communication flags", "Efficiency flags"]
    SIGNAL_FILTER_MAP = {
        "Resolution flags": {"resolution_failure", "low_resolution"},
        "Compliance flags": {"compliance_violation", "low_compliance"},
        "Sentiment flags": {"sentiment_deterioration", "low_sentiment"},
        "Communication flags": {"communication_issues", "low_communication"},
        "Efficiency flags": {"low_efficiency"},
    }

    def _apply_signal_filter(results_list: list, signal_filter: str) -> list:
        if signal_filter == "All signals":
            return results_list
        flag_set = SIGNAL_FILTER_MAP.get(signal_filter, set())
        return [r for r in results_list if flag_set & set(r.flags)]

    # Sort by priority
    sorted_results = sorted(cross_view_results, key=priority_sort_key)

    # Counts (before signal filter, for summary bar)
    hb_results = [r for r in sorted_results if has_hard_block(r)]
    warn_results = [r for r in sorted_results if not has_hard_block(r) and r.flags]
    pass_results = [r for r in sorted_results if not has_hard_block(r) and not r.flags]

    # ---- DETAIL VIEW (if a conversation is selected) ----
    if st.session_state.selected_review is not None:
        selected_id = st.session_state.selected_review
        if selected_id in results_dict:
            if st.button("← Back to Queue"):
                st.session_state.selected_review = None
                st.rerun()

            result = results_dict[selected_id]
            convo = transcripts.get(selected_id)
            st.markdown(f"## Conversation #{selected_id}")
            _show_conversation_detail(result, convo)
        else:
            st.error(f"Conversation #{selected_id} not found.")
            if st.button("← Back to Queue"):
                st.session_state.selected_review = None
                st.rerun()

    # ---- LIST VIEW (default) ----
    else:
        st.title("Review Queue")

        # Back to Summary link (when arriving via cross-view navigation)
        if st.session_state.nav_from_summary:
            nav_flow_label = st.session_state.get("nav_flow", "").replace("_", " ").title()
            st.caption(
                f"Showing **{nav_flow_label}** conversations "
                f"(filtered from Quality Summary — {st.session_state.nav_signal_filter})"
            )
            if st.button("← Back to Summary"):
                st.session_state.view_radio = "Quality Summary"
                st.session_state.nav_from_summary = False
                st.session_state.nav_signal_filter = "All signals"
                if hasattr(st.session_state, "nav_flow"):
                    del st.session_state.nav_flow
                st.rerun()
        else:
            st.caption("Sorted by priority — hard blocks first, then warnings. Click Review to inspect a conversation.")

        # Summary bar
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Hard Blocks", len(hb_results), help="Must review — resolution failure or compliance violation")
        c2.metric("⚠️ Warnings", len(warn_results), help="Review recommended — quality concerns")
        c3.metric("🟢 Passing", len(pass_results), help="No action needed")

        st.divider()

        # Search box for direct conversation lookup
        search_id = st.text_input("Look up conversation ID", placeholder="e.g. 1234")
        if search_id.strip():
            try:
                lookup_id = int(search_id.strip())
            except ValueError:
                lookup_id = None
                st.warning("Please enter a numeric conversation ID.")
            if lookup_id is not None:
                if lookup_id in results_dict:
                    st.session_state.selected_review = lookup_id
                    st.rerun()
                else:
                    st.warning(f"Conversation #{lookup_id} not found.")

        # Filter controls row
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            show_filter = st.radio(
                "Show",
                ["Hard Blocks First", "Warnings Only", "All"],
                horizontal=True,
                index=0,
            )

        with filter_col2:
            # Signal filter — default from cross-view nav or "All signals"
            default_signal_idx = 0
            if st.session_state.nav_signal_filter in SIGNAL_FILTER_OPTIONS:
                default_signal_idx = SIGNAL_FILTER_OPTIONS.index(st.session_state.nav_signal_filter)
            signal_filter = st.selectbox(
                "Filter by Signal",
                SIGNAL_FILTER_OPTIONS,
                index=default_signal_idx,
                help="Show only conversations flagged for a specific signal",
            )

        if show_filter == "Hard Blocks First":
            display_results = hb_results + warn_results
        elif show_filter == "Warnings Only":
            display_results = warn_results
        else:
            display_results = sorted_results

        # Apply signal filter
        display_results = _apply_signal_filter(display_results, signal_filter)

        # Limit display
        max_display = max(10, min(200, len(display_results)))
        show_count = st.slider("Show top N", min_value=10, max_value=max(10, max_display), value=min(20, max_display))
        display_results = display_results[:show_count]

        if not display_results:
            if signal_filter != "All signals":
                st.info(f"No conversations match the **{signal_filter}** filter. Try selecting 'All signals'.")
            else:
                st.success("No conversations to review — all passing!")
        else:
            # Render each conversation as a row
            for r in display_results:
                is_hb = has_hard_block(r)
                severity_icon = "🔴" if is_hb else ("⚠️" if r.flags else "🟢")
                issue = issue_summary(r)
                score = r.overall_score
                score_emoji, _ = tier_status(score)

                col_sev, col_info, col_score, col_btn = st.columns([0.5, 4, 1, 1])
                with col_sev:
                    st.markdown(f"### {severity_icon}")
                with col_info:
                    st.markdown(
                        f"**#{r.convo_id}** · {r.flow.replace('_', ' ').title()} → {r.subflow.replace('_', ' ').title()}"
                    )
                    st.caption(issue)
                with col_score:
                    st.markdown(f"**{score_emoji} {score:.2f}**")
                with col_btn:
                    if st.button("Review →", key=f"review_{r.convo_id}"):
                        st.session_state.selected_review = r.convo_id
                        st.rerun()
