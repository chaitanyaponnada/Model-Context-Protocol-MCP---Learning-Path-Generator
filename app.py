import streamlit as st
from utils import run_agent_sync

st.set_page_config(page_title="MCP POC", page_icon="🤖", layout="wide")
st.title("LIGHT HOUSE")

# ─────────────────────────────────────────────
# Load API keys and URLs from secrets
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
YOUTUBE_PIPEDREAM_URL = st.secrets.get("YOUTUBE_PIPEDREAM_URL", "")
DRIVE_PIPEDREAM_URL = st.secrets.get("DRIVE_PIPEDREAM_URL", "")
NOTION_PIPEDREAM_URL = st.secrets.get("NOTION_PIPEDREAM_URL", "")

# ─────────────────────────────────────────────
# Initialize session state
for key, default in {
    "current_step": "",
    "progress": 0,
    "last_section": "",
    "is_generating": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# Sidebar for configuration
st.sidebar.header("Configuration")

google_api_key = st.sidebar.text_input("Google API Key", value=GOOGLE_API_KEY, type="password")
youtube_pipedream_url = st.sidebar.text_input("YouTube URL (Required)", value=YOUTUBE_PIPEDREAM_URL)

secondary_tool = st.sidebar.radio("Select Secondary Tool:", ["Drive", "Notion"])

if secondary_tool == "Drive":
    drive_pipedream_url = st.sidebar.text_input("Drive URL", value=DRIVE_PIPEDREAM_URL)
    notion_pipedream_url = None
else:
    notion_pipedream_url = st.sidebar.text_input("Notion URL", value=NOTION_PIPEDREAM_URL)
    drive_pipedream_url = None

# ─────────────────────────────────────────────
# Quick guide
st.info("""
**Quick Guide:**
1. Keys & URLs are preloaded from secrets, override if needed.
2. Select secondary tool and confirm its URL.
3. Enter a clear learning goal:
   - "I want to learn python basics in 3 days"
   - "I want to learn data science basics in 10 days"
""")

# ─────────────────────────────────────────────
# Main input
st.header("Enter Your Goal")
user_goal = st.text_input(
    "Enter your learning goal:",
    help="We'll generate a structured learning path using YouTube and your selected tool."
)

# ─────────────────────────────────────────────
# Progress UI
progress_container = st.container()
progress_bar = st.empty()

def update_progress(message: str):
    st.session_state.current_step = message
    if "Setting up agent with tools" in message:
        section, progress = "Setup", 0.1
    elif "Added Google Drive integration" in message or "Added Notion integration" in message:
        section, progress = "Integration", 0.2
    elif "Creating AI agent" in message:
        section, progress = "Setup", 0.3
    elif "Generating your learning path" in message:
        section, progress = "Generation", 0.5
    elif "Learning path generation complete" in message:
        section, progress = "Complete", 1.0
        st.session_state.is_generating = False
    else:
        section, progress = st.session_state.last_section or "Progress", st.session_state.progress

    st.session_state.last_section = section
    st.session_state.progress = progress
    progress_bar.progress(progress)

    with progress_container:
        if message == "Learning path generation complete!":
            st.success("All steps completed! 🎉")
        else:
            prefix = "✓" if progress >= 0.5 else "→"
            st.write(f"{prefix} {message}")

# ─────────────────────────────────────────────
# Run button
if st.button("Generate Learning Path", type="primary", disabled=st.session_state.is_generating):
    if not google_api_key:
        st.error("Please enter your Google API key.")
    elif not youtube_pipedream_url:
        st.error("YouTube URL is required.")
    elif (secondary_tool == "Drive" and not drive_pipedream_url) or (secondary_tool == "Notion" and not notion_pipedream_url):
        st.error(f"Please enter your Pipedream {secondary_tool} URL.")
    elif not user_goal:
        st.warning("Please enter your learning goal.")
    else:
        try:
            st.session_state.is_generating = True
            st.session_state.current_step = ""
            st.session_state.progress = 0
            st.session_state.last_section = ""

            result = run_agent_sync(
                google_api_key=google_api_key,
                youtube_pipedream_url=youtube_pipedream_url,
                drive_pipedream_url=drive_pipedream_url,
                notion_pipedream_url=notion_pipedream_url,
                user_goal=user_goal,
                progress_callback=update_progress
            )

            st.header("Your Learning Path")
            if result and "messages" in result:
                for msg in result["messages"]:
                    st.markdown(f"📚 {msg.content}")
            else:
                st.error("No results were generated. Please try again.")
                st.session_state.is_generating = False
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check your API keys and URLs, and try again.")
            st.session_state.is_generating = False
