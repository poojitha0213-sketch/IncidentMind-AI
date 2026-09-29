import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

load_dotenv()

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

hindsight_client = Hindsight(
    api_key=os.getenv("HINDSIGHT_API_KEY"),
    base_url=os.getenv("HINDSIGHT_BASE_URL")
)

BANK_ID = os.getenv("HINDSIGHT_BANK_ID")

st.set_page_config(
    page_title="IncidentMind AI",
    page_icon="🧠",
    layout="wide"
)


# ============================================================
# SESSION STATUS
# ============================================================

if "incident_observed" not in st.session_state:
    st.session_state.incident_observed = False

if "experience_recalled" not in st.session_state:
    st.session_state.experience_recalled = False

if "reason_completed" not in st.session_state:
    st.session_state.reason_completed = False

if "incident_retained" not in st.session_state:
    st.session_state.incident_retained = False

if "improvement_ready" not in st.session_state:
    st.session_state.improvement_ready = False

if "feedback_saved" not in st.session_state:
    st.session_state.feedback_saved = False

if "recalled_count" not in st.session_state:
    st.session_state.recalled_count = 0


# ============================================================
# HEADER
# ============================================================

st.title("🧠 IncidentMind AI")

st.subheader(
    "AI Incident Response Agent powered by Hindsight"
)

st.write(
    "Analyze software incidents using past incident experience "
    "and continuously improve through persistent Hindsight memory."
)


# ============================================================
# REPORT INCIDENT
# ============================================================

st.header("🚨 Report an Incident")

incident_title = st.text_input(
    "Incident Title",
    placeholder="Example: Payment API latency increased"
)

service = st.text_input(
    "Affected Service",
    placeholder="Example: Payment API"
)

severity = st.selectbox(
    "Severity",
    ["Low", "Medium", "High", "Critical"]
)

error_message = st.text_area(
    "Error / Incident Details",
    placeholder=(
        "Describe the error, symptoms, logs, "
        "or unusual behavior..."
    )
)

recent_change = st.text_input(
    "Recent Deployment or Change",
    placeholder=(
        "Example: Version 2.4 deployed 20 minutes ago"
    )
)


# ============================================================
# ANALYZE INCIDENT
# ============================================================

if st.button(
    "🔍 Analyze Incident",
    type="primary"
):

    if (
        not incident_title
        or not service
        or not error_message
    ):

        st.warning(
            "Please fill in the Incident Title, "
            "Affected Service, and Incident Details."
        )

    else:

        # Reset current workflow
        st.session_state.incident_observed = True
        st.session_state.experience_recalled = False
        st.session_state.reason_completed = False
        st.session_state.incident_retained = False
        st.session_state.improvement_ready = False
        st.session_state.feedback_saved = False
        st.session_state.recalled_count = 0

        incident_query = f"""
Incident Title: {incident_title}
Affected Service: {service}
Severity: {severity}
Error Details: {error_message}
Recent Change: {recent_change}
"""


        # ====================================================
        # 1. RECALL PAST EXPERIENCE
        # ====================================================

        with st.spinner(
            "🧠 Searching Hindsight for similar incidents..."
        ):

            memory_result = hindsight_client.recall(
                bank_id=BANK_ID,
                query=incident_query
            )


        if memory_result.results:

            display_memories = memory_result.results[:5]

            st.session_state.experience_recalled = True

            st.session_state.recalled_count = len(
                memory_result.results
            )

            memory_text = "\n\n".join(
                f"- {memory.text}"
                for memory in display_memories
            )

            st.success(
                f"🟢 Hindsight recalled "
                f"{len(memory_result.results)} "
                f"relevant experience(s)"
            )

            st.subheader(
                "🧠 Relevant Past Experience"
            )

            for memory in display_memories:

                st.write(
                    f"• {memory.text}"
                )

        else:

            memory_text = (
                "No similar past incidents were found."
            )

            st.session_state.experience_recalled = True

            st.session_state.recalled_count = 0

            st.info(
                "🔵 Hindsight searched previous experience, "
                "but no similar incidents were found."
            )


        # ====================================================
        # 2. AI REASONING
        # ====================================================

        st.subheader(
            "🤖 AI Incident Analysis"
        )

        prompt = f"""
You are IncidentMind AI, a software incident response assistant.

Analyze the following software incident.

CURRENT INCIDENT:
{incident_query}

PAST EXPERIENCE RETRIEVED FROM HINDSIGHT:
{memory_text}

Give a practical response with these sections:

1. Possible Root Cause
2. Investigation Steps
3. Recommended Resolution
4. Why This Recommendation
5. How Past Experience Helped

Important:
- Use past experience when relevant.
- Clearly say when there is not enough past experience.
- Do not invent historical incidents.
- Do not invent dates, incident numbers, deployments, or outcomes.
- Only use historical facts explicitly present in the retrieved memory.
- Keep the response useful and concise.
"""

        with st.spinner(
            "🤖 AI is analyzing the incident..."
        ):

            response = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert software incident "
                            "response assistant."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

        analysis = (
            response.choices[0]
            .message
            .content
        )

        st.session_state.reason_completed = True

        st.markdown(analysis)


        # ====================================================
        # 3. PERMANENTLY SAVE INCIDENT
        # ====================================================

        incident_memory = f"""
INCIDENTMIND INCIDENT RECORD

Incident Title:
{incident_title}

Affected Service:
{service}

Severity:
{severity}

Error / Incident Details:
{error_message}

Recent Deployment or Change:
{recent_change}

AI Analysis:
{analysis}

This is a permanent IncidentMind incident record.

It must remain available in Hindsight for:
- Future incident recall
- Similar incident troubleshooting
- Resolution comparison
- Continuous learning

IncidentMind Memory Type:
incident_analysis
"""

        with st.spinner(
            "💾 Permanently saving incident to Hindsight Cloud..."
        ):

            hindsight_client.retain(
                bank_id=BANK_ID,
                content=incident_memory,
                context=(
                    "IncidentMind permanent "
                    "software incident record"
                ),
                metadata={
                    "source": "IncidentMind AI",
                    "memory_type": "incident_analysis",
                    "incident_title": incident_title,
                    "service": service,
                    "severity": severity
                }
            )

        st.session_state.incident_retained = True

        st.success(
            "✅ Incident permanently saved to Hindsight Cloud."
        )

        st.info(
            "🧠 This incident is now available for "
            "future similar incident searches."
        )


# ============================================================
# ENGINEER FEEDBACK
# ============================================================

st.divider()

st.header("👨‍💻 Engineer Feedback")

st.write(
    "Tell IncidentMind what actually happened so it can "
    "learn from the outcome."
)

feedback_status = st.radio(
    "Was this recommendation useful?",
    [
        "✅ Worked",
        "❌ Didn't Work"
    ],
    horizontal=True
)

actual_root_cause = st.text_area(
    "Actual Root Cause",
    placeholder=(
        "Example: Database connection pool was exhausted "
        "after the deployment..."
    )
)

actual_resolution = st.text_area(
    "Actual Resolution",
    placeholder=(
        "Example: Increased connection pool size and "
        "rolled back the deployment..."
    )
)

if st.button(
    "💾 Save Feedback"
):

    if (
        not incident_title
        or not service
        or not error_message
    ):

        st.warning(
            "Please analyze an incident first."
        )

    elif (
        not actual_root_cause
        or not actual_resolution
    ):

        st.warning(
            "Please enter the Actual Root Cause "
            "and Actual Resolution."
        )

    else:

        feedback_memory = f"""
INCIDENTMIND ENGINEER FEEDBACK

Incident Title:
{incident_title}

Affected Service:
{service}

Recommendation Outcome:
{feedback_status}

Actual Root Cause:
{actual_root_cause}

Actual Resolution:
{actual_resolution}

This feedback represents the actual engineer-confirmed
outcome of the incident.

Future IncidentMind recommendations may use this
experience when a similar incident occurs.

IncidentMind Memory Type:
engineer_feedback
"""

        with st.spinner(
            "🧠 Learning from engineer feedback..."
        ):

            hindsight_client.retain(
                bank_id=BANK_ID,
                content=feedback_memory,
                context=(
                    "IncidentMind engineer feedback "
                    "and actual incident outcome"
                ),
                metadata={
                    "source": "IncidentMind AI",
                    "memory_type": "engineer_feedback",
                    "incident_title": incident_title,
                    "service": service,
                    "outcome": feedback_status
                }
            )

        st.session_state.feedback_saved = True

        st.session_state.improvement_ready = True

        st.success(
            "✅ Engineer feedback permanently saved to Hindsight."
        )

        st.success(
            "🔄 IncidentMind has learned from the actual outcome."
        )

        st.info(
            "🧠 Future similar incidents can use this "
            "root cause and resolution."
        )


# ============================================================
# MEMORY ON VS MEMORY OFF
# ============================================================

st.divider()

st.header(
    "🧠 Memory ON vs Memory OFF"
)

st.write(
    "Compare the agent's response when it starts from zero "
    "with the response when it uses Hindsight experience."
)

if st.button(
    "⚖️ Compare Memory ON vs OFF"
):

    if (
        not incident_title
        or not service
        or not error_message
    ):

        st.warning(
            "Please enter the Incident Title, "
            "Affected Service, and Incident Details first."
        )

    else:

        incident_query = f"""
Incident Title: {incident_title}
Affected Service: {service}
Severity: {severity}
Error Details: {error_message}
Recent Change: {recent_change}
"""

        with st.spinner(
            "Preparing Memory OFF and Memory ON comparison..."
        ):

            memory_result = hindsight_client.recall(
                bank_id=BANK_ID,
                query=incident_query
            )

            if memory_result.results:

                comparison_results = (
                    memory_result.results[:5]
                )

                comparison_memory = "\n\n".join(
                    f"- {memory.text}"
                    for memory in comparison_results
                )

            else:

                comparison_memory = (
                    "No previous incident experience found."
                )


            memory_off_prompt = f"""
You are a software incident response assistant.

Analyze this incident WITHOUT using previous incident memory.

INCIDENT:
{incident_query}

Give:
1. Possible Root Cause
2. Investigation Steps
3. Recommended Resolution

Keep the response concise.
"""


            memory_on_prompt = f"""
You are IncidentMind AI.

Analyze this incident using previous experience
retrieved from Hindsight.

CURRENT INCIDENT:
{incident_query}

PREVIOUS EXPERIENCE:
{comparison_memory}

Give:
1. Possible Root Cause
2. Investigation Steps
3. Recommended Resolution
4. How Previous Experience Helped

Important:
- Use previous experience only when relevant.
- Do not invent historical facts.
- Do not assume two incidents have the same root cause without evidence.
"""


            memory_off_response = (
                groq_client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a software incident "
                                "response assistant."
                            )
                        },
                        {
                            "role": "user",
                            "content": memory_off_prompt
                        }
                    ]
                )
            )


            memory_on_response = (
                groq_client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are IncidentMind AI."
                            )
                        },
                        {
                            "role": "user",
                            "content": memory_on_prompt
                        }
                    ]
                )
            )


            memory_off_analysis = (
                memory_off_response
                .choices[0]
                .message
                .content
            )

            memory_on_analysis = (
                memory_on_response
                .choices[0]
                .message
                .content
            )


        col1, col2 = st.columns(2)

        with col1:

            st.subheader(
                "🔵 Memory OFF"
            )

            st.caption(
                "Agent starts without previous incident experience."
            )

            st.markdown(
                memory_off_analysis
            )


        with col2:

            st.subheader(
                "🟢 Memory ON"
            )

            st.caption(
                "Agent uses Hindsight's previous incident experience."
            )

            st.markdown(
                memory_on_analysis
            )


        st.success(
            "🧠 Comparison complete — Hindsight allows "
            "IncidentMind to use previous experience "
            "instead of starting from zero."
        )


# ============================================================
# LEARNING PROGRESS
# ============================================================

st.divider()

st.header(
    "🧠 Learning Progress"
)

col1, col2, col3 = st.columns(3)


# ------------------------------------------------------------
# 1. INCIDENT OBSERVED
# ------------------------------------------------------------

with col1:

    if st.session_state.incident_observed:

        st.success(
            "### 1️⃣ Incident Observed\n"
            "✅ Incident has been reported and analyzed."
        )

    else:

        st.info(
            "### 1️⃣ Incident Observed\n"
            "Waiting for an incident to be reported."
        )


# ------------------------------------------------------------
# 2. EXPERIENCE RECALLED
# ------------------------------------------------------------

with col2:

    if st.session_state.experience_recalled:

        if st.session_state.recalled_count > 0:

            st.success(
                "### 2️⃣ Experience Recalled\n"
                f"✅ Hindsight retrieved "
                f"{st.session_state.recalled_count} "
                f"relevant experience(s)."
            )

        else:

            st.warning(
                "### 2️⃣ Experience Recalled\n"
                "⚠️ Hindsight searched memory, "
                "but no similar experience was found."
            )

    else:

        st.info(
            "### 2️⃣ Experience Recalled\n"
            "Waiting for Hindsight recall."
        )


# ------------------------------------------------------------
# 3. AGENT IMPROVES
# ------------------------------------------------------------

with col3:

    if st.session_state.improvement_ready:

        st.success(
            "### 3️⃣ Agent Improves\n"
            "✅ Engineer feedback was learned and "
            "stored permanently."
        )

    else:

        st.info(
            "### 3️⃣ Agent Improves\n"
            "Waiting for engineer feedback and actual outcome."
        )


# ============================================================
# LEARNING LOOP
# ============================================================

if st.session_state.incident_observed:

    loop_steps = []

    if st.session_state.incident_observed:
        loop_steps.append("Incident")

    if st.session_state.experience_recalled:
        loop_steps.append("Recall")

    if st.session_state.reason_completed:
        loop_steps.append("Recommend")

    if st.session_state.incident_retained:
        loop_steps.append("Remember")

    if st.session_state.feedback_saved:
        loop_steps.append("Improve")

    st.success(
        "🔄 Learning Loop: "
        + " → ".join(loop_steps)
    )

else:

    st.info(
        "🔄 Learning Loop: "
        "Incident → Recall → Recommend → Remember → "
        "Feedback → Improve"
    )


# ============================================================
# HOW HINDSIGHT HELPS
# ============================================================

st.header(
    "🔗 How Hindsight Helps"
)

col1, col2, col3, col4 = st.columns(4)


# ------------------------------------------------------------
# RECALL
# ------------------------------------------------------------

with col1:

    if st.session_state.experience_recalled:

        st.success(
            "### 🔍 Recall\n"
            "Hindsight searched persistent memory and "
            f"returned {st.session_state.recalled_count} "
            "relevant experience(s)."
        )

    else:

        st.info(
            "### 🔍 Recall\n"
            "Hindsight searches previous incident experiences."
        )


# ------------------------------------------------------------
# REASON
# ------------------------------------------------------------

with col2:

    if st.session_state.reason_completed:

        st.success(
            "### 🤖 Reason\n"
            "Groq analyzed the current incident using "
            "the retrieved experience."
        )

    else:

        st.info(
            "### 🤖 Reason\n"
            "Groq analyzes the incident using recalled experience."
        )


# ------------------------------------------------------------
# RETAIN
# ------------------------------------------------------------

with col3:

    if st.session_state.incident_retained:

        st.success(
            "### 💾 Retain\n"
            "The incident analysis was permanently "
            "stored in Hindsight."
        )

    else:

        st.info(
            "### 💾 Retain\n"
            "The analyzed incident will be stored permanently."
        )


# ------------------------------------------------------------
# IMPROVE
# ------------------------------------------------------------

with col4:

    if st.session_state.improvement_ready:

        st.success(
            "### 🔄 Improve\n"
            "Engineer feedback is now stored and can "
            "help future similar incidents."
        )

    else:

        st.info(
            "### 🔄 Improve\n"
            "IncidentMind improves after learning from "
            "the actual incident outcome."
        )


# ============================================================
# INCIDENT HISTORY
# ============================================================

st.divider()

st.header(
    "📋 Incident History"
)

try:

    history = hindsight_client.list_memories(
        bank_id=BANK_ID,
        limit=100,
        offset=0
    )

    unique_incidents = {}

    for memory in history.items:

        memory_text = memory.text or ""

        metadata = memory.metadata or {}

        is_incident = (
            "INCIDENTMIND INCIDENT RECORD"
            in memory_text
            or metadata.get("source")
            == "IncidentMind AI"
            and metadata.get("memory_type")
            == "incident_analysis"
        )

        if not is_incident:
            continue

        incident_name = metadata.get(
            "incident_title",
            "IncidentMind Incident"
        )

        service_name = metadata.get(
            "service",
            "Unknown Service"
        )

        severity_name = metadata.get(
            "severity",
            "Unknown"
        )

        unique_key = (
            incident_name.strip().lower(),
            service_name.strip().lower()
        )

        if unique_key not in unique_incidents:

            unique_incidents[unique_key] = {
                "title": incident_name,
                "service": service_name,
                "severity": severity_name,
                "text": memory_text
            }


    if unique_incidents:

        st.success(
            f"🧠 {len(unique_incidents)} unique "
            "IncidentMind incidents permanently stored"
        )

        for incident in reversed(
            list(unique_incidents.values())
        ):

            with st.expander(
                f"🚨 {incident['title']}"
            ):

                st.caption(
                    f"Service: {incident['service']} | "
                    f"Severity: {incident['severity']}"
                )

                st.markdown(
                    incident["text"]
                )

    else:

        st.info(
            "No IncidentMind incidents have been saved yet."
        )


except Exception as e:

    st.warning(
        f"Could not load incident history from Hindsight: {e}"
    )


# ============================================================
# LEARNING SCORE
# ============================================================

st.divider()

st.header(
    "📈 IncidentMind Learning Score"
)

try:

    stored_memories = (
        hindsight_client.list_memories(
            bank_id=BANK_ID,
            limit=100,
            offset=0
        )
    )

    unique_incidents = set()

    feedback_count = 0

    for memory in stored_memories.items:

        memory_text = memory.text or ""

        metadata = memory.metadata or {}

        memory_type = metadata.get(
            "memory_type"
        )

        # Count incident records
        if (
            "INCIDENTMIND INCIDENT RECORD"
            in memory_text
            or memory_type
            == "incident_analysis"
        ):

            incident_name = metadata.get(
                "incident_title",
                "IncidentMind Incident"
            )

            service_name = metadata.get(
                "service",
                "Unknown Service"
            )

            unique_key = (
                incident_name.strip().lower(),
                service_name.strip().lower()
            )

            unique_incidents.add(
                unique_key
            )

        # Count engineer feedback
        if (
            memory_type
            == "engineer_feedback"
        ):

            feedback_count += 1


    incident_count = len(
        unique_incidents
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "🧠 Incidents Learned",
            incident_count
        )

    with col2:

        st.metric(
            "👨‍💻 Engineer Feedback",
            feedback_count
        )

    with col3:

        if feedback_count == 0:

            learning_status = "Starting"

        elif feedback_count < 3:

            learning_status = "Learning"

        else:

            learning_status = "Improving"

        st.metric(
            "📈 Learning Status",
            learning_status
        )


except Exception as e:

    st.warning(
        f"Could not load Hindsight learning score: {e}"
    )