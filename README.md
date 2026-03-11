# 🏭 ShiftReport AI

**Intelligent Shift-Handover Report Generator for Manufacturing Plants**

ShiftReport AI transforms informal, unstructured supervisor shift descriptions into professional, structured handover reports using Large Language Models. Built with Streamlit and the OpenAI API.

---

## Features

- **Natural Language Input** — Type or paste a free-form description of shift events
- **Automatic Machine ID Extraction** — Matches informal references to the plant equipment registry
- **Severity Classification** — 🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low, ⚪ Unknown
- **Missing Info Detection** — Flags when critical details are absent with ⚠️ NEEDS CLARIFICATION
- **Hallucination Guardrails** — Only references known equipment; flags unrecognized machines
- **4 Test Scenarios** — Pre-built inputs for multi-issue, vague, contradictory, and simple cases
- **Prompt Engineering Log** — Full v1→v4 prompt iteration history documented in-app
- **Downloadable Reports** — Export generated reports as Markdown files

---

## Quick Start (Local)

### 1. Clone or download this project

```bash
cd shiftreport-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

### 4. Open in browser

Navigate to `http://localhost:8501`, enter your **OpenAI API key** in the sidebar, and start generating reports.

---

## Deploy to Streamlit Community Cloud (Free)

This is the recommended deployment method for student projects.

### Steps:

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - ShiftReport AI"
   git remote add origin https://github.com/YOUR_USERNAME/shiftreport-ai.git
   git push -u origin main
   ```

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Click "New app"** and connect your GitHub repo

4. **Set the following:**
   - Repository: `YOUR_USERNAME/shiftreport-ai`
   - Branch: `main`
   - Main file path: `app.py`

5. **Add your API key as a secret** (optional, for a shared demo):
   - Go to app settings → Secrets
   - Add:
     ```toml
     OPENAI_API_KEY = "sk-..."
     ```
   - Then modify `app.py` to read from `st.secrets["OPENAI_API_KEY"]` as a fallback

6. **Click Deploy!** Your app will be live at `https://YOUR_APP.streamlit.app`

---

## Deploy to Hugging Face Spaces (Free Alternative)

1. **Create a new Space** at [huggingface.co/spaces](https://huggingface.co/spaces)
   - Select **Streamlit** as the SDK

2. **Upload all project files** (`app.py`, `requirements.txt`, `.streamlit/config.toml`)

3. **Add your API key** in Space settings → Secrets:
   - Key: `OPENAI_API_KEY`
   - Value: `sk-...`

4. The Space will auto-build and deploy.

---

## Project Structure

```
shiftreport-ai/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml           # Streamlit theme & server config
└── README.md                 # This file
```

---

## Tech Stack

| Component       | Technology                          |
|-----------------|-------------------------------------|
| Frontend/UI     | Streamlit (Python)                  |
| LLM API         | OpenAI API (GPT-4 / GPT-3.5-turbo) |
| Language        | Python                              |
| Deployment      | Streamlit Cloud / HF Spaces         |

---

## Prompt Engineering

The app uses a carefully engineered system prompt (v4) that includes:

- **Equipment list** embedded directly in the prompt (16 machines across 5 zones)
- **Structured output format** with machine ID, severity, actions, and pending items
- **Few-shot example** demonstrating the messy-input → structured-report transformation
- **Constraint instructions** preventing hallucination and enforcing clarification flags
- **Edge case handling** for vague, contradictory, and incomplete inputs

The full prompt evolution (v1 → v4) is documented in the app's "Prompt Engineering Log" tab.

---

## Test Scenarios

| Scenario              | Description                                         |
|-----------------------|-----------------------------------------------------|
| Multi-Issue Shift     | 4 machines, mixed severity, missing info            |
| Vague / Ambiguous     | Unclear references, no specific machine IDs         |
| Contradictory Input   | Conflicting statements about machine status         |
| Simple Single Issue   | One resolved issue, clean input                     |

---

## License

Academic project — Class Assignment 5: Generative AI Project Proposal.
