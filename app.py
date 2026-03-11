import streamlit as st
import openai
import json
from datetime import datetime

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="ShiftReport AI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    /* Global */
    .stApp { font-family: 'DM Sans', sans-serif; }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 28px 32px;
        border-radius: 16px;
        border-bottom: 4px solid #f97316;
        margin-bottom: 24px;
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        margin: 4px 0 0;
    }

    /* Cards */
    .custom-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .card-desc {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 16px;
    }

    /* Report styling */
    .report-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    .report-header {
        padding: 14px 24px;
        background: #0f172a;
        border-bottom: 3px solid #f97316;
    }
    .report-header span {
        font-size: 0.78rem;
        font-weight: 700;
        color: #f97316;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .report-body {
        padding: 24px;
        font-size: 0.92rem;
        line-height: 1.8;
        color: #334155;
    }

    /* Equipment table */
    .equip-id {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        color: #f97316;
        font-size: 0.88rem;
    }

    /* Severity badges */
    .severity-critical { background: #fee2e2; color: #991b1b; padding: 2px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .severity-high { background: #ffedd5; color: #9a3412; padding: 2px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .severity-medium { background: #fef9c3; color: #854d0e; padding: 2px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .severity-low { background: #dcfce7; color: #166534; padding: 2px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .severity-unknown { background: #f3f4f6; color: #374151; padding: 2px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }

    /* Sample buttons */
    .sample-btn {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 16px;
        text-align: left;
        cursor: pointer;
        transition: all 0.2s;
        width: 100%;
    }
    .sample-btn:hover {
        border-color: #f97316;
        background: #fff8f3;
    }
    .sample-label {
        font-weight: 600;
        font-size: 0.85rem;
        color: #f97316;
        margin-bottom: 4px;
    }
    .sample-preview {
        font-size: 0.8rem;
        color: #94a3b8;
        line-height: 1.4;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0f172a;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] h2 {
        color: #f97316 !important;
    }

    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #fff8f3 !important;
        border-bottom: 2px solid #f97316 !important;
        color: #f97316 !important;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# EQUIPMENT DATABASE
# ──────────────────────────────────────────────
EQUIPMENT_LIST = [
    {"id": "M-01", "name": "CNC Milling Machine", "line": "Line A"},
    {"id": "M-02", "name": "CNC Lathe", "line": "Line A"},
    {"id": "M-03", "name": "Hydraulic Press", "line": "Line A"},
    {"id": "M-04", "name": "Injection Molder", "line": "Line A"},
    {"id": "M-05", "name": "Conveyor Belt System", "line": "Line B"},
    {"id": "M-06", "name": "Welding Robot Arm", "line": "Line B"},
    {"id": "M-07", "name": "CNC Milling Machine", "line": "Line B"},
    {"id": "M-08", "name": "Packaging Unit", "line": "Line B"},
    {"id": "M-09", "name": "Quality Inspection Scanner", "line": "Line C"},
    {"id": "M-10", "name": "Industrial Oven", "line": "Line C"},
    {"id": "M-11", "name": "Coolant Circulation Pump", "line": "Line C"},
    {"id": "M-12", "name": "Compressor Unit", "line": "Utilities"},
    {"id": "M-13", "name": "Backup Generator", "line": "Utilities"},
    {"id": "M-14", "name": "HVAC System", "line": "Utilities"},
    {"id": "M-15", "name": "Forklift #1", "line": "Logistics"},
    {"id": "M-16", "name": "Forklift #2", "line": "Logistics"},
]

EQUIPMENT_PROMPT_STR = "\n".join(
    [f"- {e['id']}: {e['name']} ({e['line']})" for e in EQUIPMENT_LIST]
)


# ──────────────────────────────────────────────
# SYSTEM PROMPT (v4 – Final Iteration)
# ──────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are ShiftReport AI, a manufacturing shift-handover report assistant. Your job is to take an informal, unstructured description from a floor supervisor and generate a professional, structured shift-handover report.

## PLANT EQUIPMENT LIST
{EQUIPMENT_PROMPT_STR}

## YOUR TASK
1. EXTRACT all machine references, issues, times, actions taken, and pending items from the supervisor's input.
2. MATCH machine references to the equipment list above. If a supervisor says "machine 7 line B," match it to M-07 CNC Milling Machine (Line B). If a reference cannot be matched, flag it as ⚠️ UNRECOGNIZED EQUIPMENT.
3. CLASSIFY each issue's severity:
   - 🔴 CRITICAL: Safety hazard, machine fully down, production stopped
   - 🟠 HIGH: Major malfunction, significant production impact
   - 🟡 MEDIUM: Partial issues, reduced performance
   - 🟢 LOW: Minor observations, cosmetic, no production impact
   - ⚪ UNKNOWN: Insufficient detail provided — needs clarification
4. NEVER invent or assume details not present in the input.
5. If critical information is missing (e.g., whether a machine was shut down, whether maintenance was called), explicitly flag it as "⚠️ NEEDS CLARIFICATION."

## OUTPUT FORMAT
Generate the report in this exact structure using clean markdown:

# SHIFT HANDOVER REPORT
**Date:** [Today's date or as mentioned]
**Shift:** [Infer from context or state "Not specified"]
**Prepared by:** [If mentioned, otherwise "Floor Supervisor"]

---

## ISSUES & EVENTS

### [Issue Number]. [Machine ID] — [Machine Name] ([Line])
- **Issue:** [Description]
- **Severity:** [🔴/🟠/🟡/🟢/⚪ + label]
- **Time Noticed:** [Time or "Not specified"]
- **Action Taken:** [What was done]
- **Status:** [Resolved / Ongoing / Pending]
- **Clarifications Needed:** [Any missing info flagged]

(Repeat for each issue)

---

## PENDING ITEMS FOR NEXT SHIFT
- [Bulleted list of items the next shift must address]

## GENERAL NOTES
- [Any overall observations, staffing notes, or other info]

---
*Report generated by ShiftReport AI*

## FEW-SHOT EXAMPLE

**Supervisor Input:** "Machine 7 on line B started making weird noises around 2pm, had to slow it down to 50%. Called maintenance but they haven't come yet. Also the hydraulic press on A has a small oil leak near the base, been like that since morning. Oh and we're low on coolant for line C."

**Expected Output:**

# SHIFT HANDOVER REPORT
**Date:** [Today]
**Shift:** Not specified
**Prepared by:** Floor Supervisor

---

## ISSUES & EVENTS

### 1. M-07 — CNC Milling Machine (Line B)
- **Issue:** Unusual noises detected; machine speed reduced to 50% capacity
- **Severity:** 🟠 HIGH — Machine operating at reduced capacity, production impacted
- **Time Noticed:** ~2:00 PM
- **Action Taken:** Speed reduced to 50%; maintenance called
- **Status:** Ongoing — Maintenance has not yet responded
- **Clarifications Needed:** ⚠️ Has machine been cleared for continued operation at 50%?

### 2. M-03 — Hydraulic Press (Line A)
- **Issue:** Oil leak detected near the base of the unit
- **Severity:** 🟡 MEDIUM — Leak is persistent (since morning), potential escalation risk
- **Time Noticed:** Morning (exact time not specified)
- **Action Taken:** Not specified
- **Status:** Ongoing
- **Clarifications Needed:** ⚠️ Has maintenance been notified? Is the leak worsening?

### 3. M-11 — Coolant Circulation Pump (Line C)
- **Issue:** Low coolant levels reported
- **Severity:** 🟡 MEDIUM — Could affect machine cooling if not addressed
- **Time Noticed:** Not specified
- **Action Taken:** Not specified
- **Status:** Pending
- **Clarifications Needed:** ⚠️ Has coolant been reordered? Current level estimate?

---

## PENDING ITEMS FOR NEXT SHIFT
- Follow up on maintenance visit for M-07 (Line B) — noises unresolved
- Monitor oil leak on M-03 (Line A) — check for worsening
- Replenish coolant for Line C machines

## GENERAL NOTES
- No staffing or safety incidents reported

---
*Report generated by ShiftReport AI*

Now process the supervisor's actual input following this exact approach."""


# ──────────────────────────────────────────────
# SAMPLE TEST SCENARIOS
# ──────────────────────────────────────────────
SAMPLE_INPUTS = {
    "🔧 Multi-Issue Shift": (
        "Machine 7 on line B has been making a grinding noise since around 2pm. "
        "We slowed it down to 60% but it's still going. Called maintenance, no response yet. "
        "The hydraulic press on line A started leaking oil again near the base — same spot as last week. "
        "Didn't shut it down because we needed to hit quota. Also, forklift 1 has a busted headlight, "
        "almost hit a pallet in aisle 3. Coolant's running low on line C again. "
        "Night shift needs to check all of this."
    ),
    "🌫️ Vague / Ambiguous Input": (
        "Something was off with the big machine on B today. It was making sounds. "
        "Also there was a leak somewhere near A but I'm not sure which one. "
        "We might need to look at it tomorrow."
    ),
    "⚡ Contradictory Input": (
        "Machine 7 line B is running fine, no issues at all. But also it threw an error code "
        "around 3pm and we had to restart it twice. The oven on C hit 450 which is way above spec "
        "but temps are normal now. Everything's good overall."
    ),
    "✅ Simple Single Issue": (
        "The packaging unit on line B jammed at 4:15pm. Cleared the jam, ran a test cycle, "
        "it's back to normal. No parts damaged."
    ),
}


# ──────────────────────────────────────────────
# LLM CALL FUNCTION
# ──────────────────────────────────────────────
def generate_report(user_input: str, api_key: str, model: str) -> str:
    """Send the supervisor's input to the LLM and return the generated report."""
    client = openai.OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Here is my shift update:\n\n{user_input.strip()}"},
        ],
        temperature=0.3,  # Low temperature for consistent, accurate extraction
        max_tokens=2000,
    )
    return response.choices[0].message.content


# ──────────────────────────────────────────────
# MAIN HEADER
# ──────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏭 ShiftReport AI</h1>
    <p>Intelligent Shift-Handover Report Generator for Manufacturing Plants</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# CONFIGURATION — Always visible at top
# ──────────────────────────────────────────────
with st.expander("⚙️ Configuration — API Key & Model", expanded="api_key" not in st.session_state or not st.session_state.get("api_key")):
    config_col1, config_col2 = st.columns([3, 1])
    with config_col1:
        api_key_input = st.text_input(
            "🔑 OpenAI API Key",
            type="password",
            value=st.session_state.get("api_key", ""),
            placeholder="sk-...",
            help="Your OpenAI API key. Never shared or stored beyond this session.",
        )
        if api_key_input:
            st.session_state["api_key"] = api_key_input
    with config_col2:
        model = st.selectbox(
            "🤖 Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-4.1-nano", "gpt-4.1-mini", "gpt-4.1"],
            index=0,
            help="gpt-4o-mini is fast and cheap (recommended). gpt-4o and gpt-4.1 give the best results but cost more.",
        )
    if api_key_input:
        st.success("✅ API key set. You can collapse this section.")
    else:
        st.warning("⚠️ Enter your OpenAI API key above to get started.")

api_key = st.session_state.get("api_key", "")


# ──────────────────────────────────────────────
# SIDEBAR — Info only (optional)
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏭 ShiftReport AI")
    st.markdown("---")
    st.markdown("## 📋 About")
    st.markdown(
        """
        **ShiftReport AI** transforms informal shift
        descriptions into professional handover reports
        using Large Language Models.

        Built for floor supervisors who need to
        communicate shift events quickly and clearly.

        **Features:**
        - Natural language input
        - Automatic machine ID extraction
        - Severity classification
        - Missing info detection
        - Structured report generation
        """
    )

    st.markdown("---")
    st.markdown("## 🎯 Prompt Version")
    st.markdown(
        """
        Currently running **Prompt v4**:
        - ✅ Structured system prompt
        - ✅ Equipment list embedded
        - ✅ Few-shot example
        - ✅ Constraint instructions
        - ✅ Edge case handling
        """
    )


# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab_input, tab_report, tab_equipment, tab_prompt = st.tabs([
    "✏️ Shift Input",
    "📋 Generated Report",
    "⚙️ Equipment Registry",
    "🧪 Prompt Engineering Log",
])


# ──────────────────────────────────────────────
# TAB 1: SHIFT INPUT
# ──────────────────────────────────────────────
with tab_input:
    st.markdown('<div class="card-title">Test Scenarios</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-desc">Load a sample supervisor input to test the system, or type your own below.</div>',
        unsafe_allow_html=True,
    )

    # Sample scenario buttons — use callback to set text_area widget key directly
    def load_sample(text):
        st.session_state["shift_text_area"] = text

    cols = st.columns(2)
    for i, (label, text) in enumerate(SAMPLE_INPUTS.items()):
        with cols[i % 2]:
            st.button(label, key=f"sample_{i}", use_container_width=True, on_click=load_sample, args=(text,))

    st.markdown("---")

    st.markdown('<div class="card-title">Supervisor Shift Input</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-desc">Type or paste a free-form description of what happened during your shift.</div>',
        unsafe_allow_html=True,
    )

    # Text area for shift input
    shift_input = st.text_area(
        "Shift Description",
        height=200,
        placeholder=(
            "e.g. Machine 7 on line B started making weird noises around 2pm, "
            "had to slow it down. Called maintenance but they haven't showed up yet. "
            "Also the press on A is leaking oil again…"
        ),
        label_visibility="collapsed",
        key="shift_text_area",
    )

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.caption(f"📝 {len(shift_input)} characters")
    with col_btn:
        generate_clicked = st.button(
            "🚀 Generate Report",
            type="primary",
            use_container_width=True,
            disabled=not shift_input.strip(),
        )

    # Handle generation
    if generate_clicked:
        if not api_key:
            st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        elif not shift_input.strip():
            st.warning("Please enter a shift description first.")
        else:
            with st.spinner("🔄 Analyzing shift input… extracting machine IDs, classifying issues, generating report…"):
                try:
                    report = generate_report(shift_input, api_key, model)
                    st.session_state["report"] = report
                    st.session_state["report_input"] = shift_input
                    st.session_state["report_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state["report_model"] = model
                    st.success("✅ Report generated! Switch to the **📋 Generated Report** tab to view it.")
                except openai.AuthenticationError:
                    st.error("❌ Invalid API key. Please check your OpenAI API key.")
                except openai.RateLimitError:
                    st.error("⚠️ Rate limit exceeded. Please wait a moment and try again.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# ──────────────────────────────────────────────
# TAB 2: GENERATED REPORT
# ──────────────────────────────────────────────
with tab_report:
    if "report" in st.session_state and st.session_state["report"]:
        # Report metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Model", st.session_state.get("report_model", "N/A"))
        with col2:
            st.metric("Generated At", st.session_state.get("report_time", "N/A"))
        with col3:
            input_len = len(st.session_state.get("report_input", ""))
            st.metric("Input Length", f"{input_len} chars")

        st.markdown("---")

        # Original input (collapsible)
        with st.expander("📥 Original Supervisor Input", expanded=False):
            st.markdown(f"```\n{st.session_state.get('report_input', '')}\n```")

        # Generated report
        st.markdown("""
        <div class="report-container">
            <div class="report-header">
                <span>AI-Generated Shift Handover Report</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(st.session_state["report"])

        # Download button
        st.download_button(
            label="📥 Download Report as Text",
            data=st.session_state["report"],
            file_name=f"shift_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
        )
    else:
        st.markdown("---")
        st.markdown(
            """
            <div style="text-align: center; padding: 60px 20px;">
                <div style="font-size: 3rem; margin-bottom: 12px;">📋</div>
                <h3 style="font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 8px;">No Report Generated Yet</h3>
                <p style="font-size: 0.9rem; color: #64748b;">
                    Go to the <strong>✏️ Shift Input</strong> tab, enter your shift description, and click "Generate Report."
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────
# TAB 3: EQUIPMENT REGISTRY
# ──────────────────────────────────────────────
with tab_equipment:
    st.markdown('<div class="card-title">Plant Equipment Registry</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-desc">This is the predefined equipment list embedded in the AI\'s system prompt. '
        'The model will only reference machines from this list and flag any unrecognized references.</div>',
        unsafe_allow_html=True,
    )

    # Color mapping for lines
    line_colors = {
        "Line A": "🔵",
        "Line B": "🟢",
        "Line C": "🟡",
        "Utilities": "🟣",
        "Logistics": "🔴",
    }

    # Build table data
    import pandas as pd

    df = pd.DataFrame(EQUIPMENT_LIST)
    df["line_display"] = df["line"].map(lambda x: f"{line_colors.get(x, '')} {x}")
    df = df.rename(columns={"id": "Machine ID", "name": "Equipment Name", "line_display": "Production Line"})
    df = df[["Machine ID", "Equipment Name", "Production Line"]]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=620,
    )

    # Summary stats
    st.markdown("---")
    cols = st.columns(5)
    line_counts = {}
    for e in EQUIPMENT_LIST:
        line_counts[e["line"]] = line_counts.get(e["line"], 0) + 1

    for i, (line, count) in enumerate(line_counts.items()):
        with cols[i]:
            st.metric(line, f"{count} machines")


# ──────────────────────────────────────────────
# TAB 4: PROMPT ENGINEERING LOG
# ──────────────────────────────────────────────
with tab_prompt:
    st.markdown('<div class="card-title">Prompt Engineering Log</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-desc">Iterative prompt development from v1 (basic) to v4 (production), '
        'as documented in the project methodology.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # v1
    with st.expander("📝 Prompt v1 — Basic Instruction", expanded=False):
        st.markdown("""
        **Approach:** Simple instruction telling the model to create a shift report.

        ```
        You are a shift report assistant. Take the supervisor's notes and
        create a professional shift handover report.
        ```

        **Result:** Generated reports but with inconsistent formatting, no severity
        classification, and occasionally invented machine details not mentioned in input.

        **Issues identified:**
        - No output format defined → inconsistent structure
        - No equipment context → model guessed machine names
        - No hallucination guardrails → fabricated details
        """)

    # v2
    with st.expander("📝 Prompt v2 — Added Structure & Equipment List", expanded=False):
        st.markdown("""
        **Approach:** Defined explicit output format and embedded the plant equipment list.

        **Changes from v1:**
        - Added structured output template (machine ID, issue, severity, etc.)
        - Embedded full equipment list in the system prompt
        - Added instruction to match informal references to equipment IDs

        **Result:** Much better structure and accurate machine matching. However,
        the model still assumed severity levels without evidence and didn't flag
        missing information.

        **Issues identified:**
        - Severity assigned without evidence → misleading reports
        - Missing info silently ignored → incomplete handovers
        """)

    # v3
    with st.expander("📝 Prompt v3 — Few-Shot Examples", expanded=False):
        st.markdown("""
        **Approach:** Added 1 complete input/output example demonstrating the expected transformation.

        **Changes from v2:**
        - Added a full few-shot example (messy input → structured report)
        - Example demonstrates proper severity classification with reasoning
        - Example shows flagging of missing information

        **Result:** Model now closely follows the demonstrated pattern. Severity
        ratings became more reasonable. Started flagging some missing information.
        However, edge cases (vague inputs, contradictions) still not handled well.

        **Issues identified:**
        - Vague inputs treated as normal → should flag ambiguity
        - Contradictory statements not caught → should highlight conflicts
        """)

    # v4
    with st.expander("📝 Prompt v4 — Edge Case Handling (CURRENT)", expanded=True):
        st.markdown("""
        **Approach:** Added explicit constraint instructions for hallucination prevention,
        unknown severity default, and edge case handling.

        **Changes from v3:**
        - Added "NEVER invent or assume details" instruction
        - Added ⚪ UNKNOWN severity for insufficient detail
        - Added "⚠️ NEEDS CLARIFICATION" flag system
        - Added instruction to flag unrecognized equipment
        - Added instruction to handle contradictory statements

        **Result:** Production-quality reports with proper guardrails. Model now:
        - Correctly defaults to UNKNOWN when evidence is insufficient
        - Flags missing critical information explicitly
        - Identifies contradictions in supervisor input
        - Only references known equipment; flags unknowns

        **This is the current production prompt.**
        """)

    st.markdown("---")

    # Show current system prompt
    with st.expander("🔍 View Full System Prompt (v4)", expanded=False):
        st.code(SYSTEM_PROMPT, language="markdown")
