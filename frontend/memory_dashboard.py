import json
from typing import Any, Dict, Optional

import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Student Memory Dashboard",
    page_icon="🧠",
    layout="wide"
)


def check_api_status() -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def fetch_memory_context(student_id: int, concept_name: Optional[str] = None) -> Dict[str, Any]:
    if concept_name:
        url = f"{API_BASE_URL}/memory/context/{student_id}?concept_name={concept_name}"
    else:
        url = f"{API_BASE_URL}/memory/context/{student_id}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_student_profile(student_id: int) -> Dict[str, Any]:
    response = requests.get(f"{API_BASE_URL}/memory/student/{student_id}", timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_student_interactions(student_id: int, limit: int = 20) -> Dict[str, Any]:
    response = requests.get(
        f"{API_BASE_URL}/memory/student/{student_id}/interactions?limit={limit}",
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def post_memory_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}/memory/update", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def metric_card(label: str, value: Any):
    st.metric(label=label, value=value if value not in [None, ""] else "N/A")


def show_short_term_memory(short_term: Dict[str, Any]):
    st.subheader("Short-Term Memory")
    st.caption("Current session context and recent learning behavior.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Session ID", short_term.get("session_id"))
    with c2:
        metric_card("Current Concept", short_term.get("current_concept"))
    with c3:
        metric_card("Recent Accuracy", short_term.get("recent_accuracy"))
    with c4:
        metric_card("Session Status", short_term.get("session_status"))

    c5, c6, c7 = st.columns(3)
    with c5:
        metric_card("Recent Interactions", short_term.get("recent_interaction_count"))
    with c6:
        metric_card("Average Attempts", short_term.get("average_attempts"))
    with c7:
        metric_card("Recent Hint Usage", short_term.get("recent_hint_usage"))


def show_long_term_memory(long_term: Dict[str, Any]):
    st.subheader("Long-Term Memory")
    st.caption("Persistent learner behavior across sessions.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Interactions", long_term.get("total_interactions"))
    with c2:
        metric_card("Total Sessions", long_term.get("total_sessions"))
    with c3:
        metric_card("Total Concepts", long_term.get("total_concepts"))
    with c4:
        metric_card("Overall Accuracy", long_term.get("overall_accuracy"))

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        metric_card("Avg Attempts", long_term.get("average_attempts"))
    with c6:
        metric_card("Avg Hints", long_term.get("average_hint_count"))
    with c7:
        metric_card("Total Hints", long_term.get("total_hint_count"))
    with c8:
        metric_card("Support Style", long_term.get("preferred_support_style"))

    st.write("Average Response Time (ms):", long_term.get("average_response_time_ms", "N/A"))


def show_concept_memory(concept_memory: Dict[str, Any]):
    st.subheader("Concept-Based Memory")
    st.caption("Concept-level interaction history. This is stored data, not final mastery prediction.")

    if not concept_memory:
        st.warning("No concept-based memory available.")
        return

    display_rows = []
    for key, value in concept_memory.items():
        display_rows.append({"Field": key, "Value": value})

    st.dataframe(display_rows, use_container_width=True)


def show_integration_notes(notes: Dict[str, Any]):
    st.subheader("Integration Notes")
    st.caption("How other components should use this memory context.")

    if not notes:
        st.info("No integration notes available.")
        return

    for key, value in notes.items():
        st.markdown(f"**{key}**")
        st.write(value)


def show_interactions(interactions_response: Dict[str, Any]):
    st.subheader("Recent Student Interactions")
    st.caption("Raw recent interaction records stored for the student.")

    if not interactions_response.get("found", False):
        st.warning(interactions_response.get("message", "No interactions found."))
        return

    interactions = interactions_response.get("interactions", [])
    if len(interactions) == 0:
        st.info("No recent interactions to display.")
        return

    st.dataframe(interactions, use_container_width=True)


# Header
st.title("🧠 Student Memory Personalization Dashboard")
st.markdown("### Component 3: Memory (Student Personalization)")

st.write(
    "This UI prototype shows the three-layer student memory generated by the Memory Component: "
    "**Short-Term Memory**, **Long-Term Memory**, and **Concept-Based Memory**."
)

# API Status
api_online = check_api_status()

if api_online:
    st.success("FastAPI backend is connected.")
else:
    st.error("FastAPI backend is not connected. Start it using: `cd backend` then `uvicorn app:app --reload`")

st.divider()

# Sidebar controls
st.sidebar.title("Memory Controls")
student_id = st.sidebar.number_input("Student ID", min_value=1, value=14, step=1)
concept_name = st.sidebar.text_input("Concept Name Optional", value="")
interaction_limit = st.sidebar.slider("Recent Interaction Limit", min_value=5, max_value=100, value=20, step=5)

fetch_btn = st.sidebar.button("Fetch Student Memory")

st.sidebar.divider()
st.sidebar.markdown("### Dynamic Update Demo")
st.sidebar.caption("Use this to test `POST /memory/update`.")

with st.sidebar.form("update_memory_form"):
    update_student_id = st.number_input("Update Student ID", min_value=1, value=999001, step=1)
    update_session_id = st.number_input("Session ID", min_value=1, value=5001, step=1)
    update_problem_id = st.number_input("Problem ID", min_value=1, value=101, step=1)
    update_concept = st.text_input("Concept", value="Percent Of")
    update_correct = st.selectbox("Correct", options=[0, 1], index=0)
    update_attempt_count = st.number_input("Attempt Count", min_value=1, value=2, step=1)
    update_hint_count = st.number_input("Hint Count", min_value=0, value=1, step=1)
    update_hint_total = st.number_input("Hint Total", min_value=0, value=3, step=1)
    update_response_time = st.number_input("Response Time ms", min_value=0.0, value=45000.0, step=1000.0)

    update_btn = st.form_submit_button("Submit New Interaction")


# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Memory Context",
        "Recent Interactions",
        "Dynamic Update Result",
        "Component Boundary"
    ]
)

if fetch_btn:
    if not api_online:
        st.error("Backend is offline. Start FastAPI first.")
    else:
        try:
            selected_concept = concept_name.strip() if concept_name.strip() else None
            memory_context = fetch_memory_context(student_id, selected_concept)
            interactions = fetch_student_interactions(student_id, interaction_limit)

            with tab1:
                if not memory_context.get("found", True):
                    st.warning(memory_context.get("message", "Memory not found."))
                else:
                    st.success("Memory context retrieved successfully.")

                    show_short_term_memory(memory_context.get("short_term_memory", {}))
                    st.divider()

                    show_long_term_memory(memory_context.get("long_term_memory", {}))
                    st.divider()

                    show_concept_memory(memory_context.get("concept_based_memory", {}))
                    st.divider()

                    show_integration_notes(memory_context.get("integration_note", {}))

                    with st.expander("View Full Memory Context JSON"):
                        st.json(memory_context)

            with tab2:
                show_interactions(interactions)

        except requests.exceptions.RequestException as error:
            st.error(f"API request failed: {error}")


if update_btn:
    if not api_online:
        st.error("Backend is offline. Start FastAPI first.")
    else:
        payload = {
            "student_id": int(update_student_id),
            "session_id": int(update_session_id),
            "problem_id": int(update_problem_id),
            "concept_name": update_concept,
            "correct": int(update_correct),
            "attempt_count": int(update_attempt_count),
            "hint_count": int(update_hint_count),
            "hint_total": int(update_hint_total),
            "response_time_ms": float(update_response_time)
        }

        try:
            update_result = post_memory_update(payload)

            with tab3:
                st.success("New interaction submitted and memory updated successfully.")
                st.json(update_result)

        except requests.exceptions.RequestException as error:
            with tab3:
                st.error(f"Memory update failed: {error}")


with tab4:
    st.subheader("Component Boundary")
    st.write(
        "The Memory Component stores and retrieves student learning data. "
        "It does not perform mastery prediction, BKT, regression detection, learning path generation, "
        "struggle prediction, or repair strategy selection."
    )

    st.markdown("""
| Component | Responsibility |
|---|---|
| Memory Component | Stores and retrieves student learning memory |
| Meta-Agent | Analyzes memory data for mastery, knowledge graph, regression, and learning path |
| FAPR-LB | Uses memory context to predict struggle and select repair strategy |
| Tutor Agent | Uses memory context to personalize explanations |
| Planner Agent | Uses memory context to break learning tasks into suitable steps |
| Evaluator Agent | Uses memory context to provide feedback with history awareness |
""")

    st.info(
        "Supervisor explanation: Memory is the storage and context provider. "
        "Meta-Agent and FAPR-LB are analytical/decision-making components that consume memory data."
    )