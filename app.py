import streamlit as st
from Orchestrator import LangGraphOrchestrator

# ── 1. Page Config & Custom CSS ───────────────────────────────────────────────
st.set_page_config(page_title="Agentic Editorial Team", page_icon="🪄", layout="centered")

st.markdown("""
<style>
    .stTextArea textarea { border-radius: 8px; border: 1px solid #d1d5db; }
    .output-box { background-color: #f8fafc; padding: 25px; border-radius: 10px; border-left: 5px solid #6366f1; margin-top: 15px;}
</style>
""", unsafe_allow_html=True)

st.title("🪄 Agentic Editorial Team")
st.caption("Watch 8 specialized AI agents collaborate in real-time to write your article.")

# ── 2. Clean Input Layout ─────────────────────────────────────────────────────
with st.container(border=True):
    query = st.text_area("What should the team write about?", placeholder="e.g., The future of AI in healthcare...", height=100)
    col1, col2 = st.columns([1, 1])
    with col1:
        output_language = st.selectbox("Output Language:", ["english", "hindi", "telugu", "tamil"])
    with col2:
        st.write("") # Spacing
        st.write("") # Spacing
        run_btn = st.button("🚀 Generate Article", type="primary", use_container_width=True)

# ── 3. Execution & Live Chat Communication ────────────────────────────────────
if run_btn and query:
    st.divider()
    st.subheader("📡 Live Agent Communication")
    
    # Use a scrollable container for the chat logs so it doesn't take up the whole page
    chat_container = st.container(height=450, border=True)

    # Dictionary to assign custom avatars to each agent
    avatars = {
        "Language Detector Agent": "🌍", "Translation Agent": "🌐", 
        "Content Writer Agent": "✍️", "SEO Specialist Agent": "📈", 
        "Fact Checker Agent": "🕵️", "Brand Voice Agent": "🎨", 
        "Editor Agent": "✒️", "Synthesis Agent": "🎯",
        "Router": "🚦", "System": "⚙️", "PIPELINE": "🚀"
    }

    try:
        orchestrator = LangGraphOrchestrator()
        original_log = orchestrator.logger._log

        def streamlit_chat_log(agent_name, message):
            original_log(agent_name, message) # Keep original logging intact
            
            # Grab the agent's specific avatar, default to a robot
            avatar = avatars.get(agent_name, "🤖")
            
            # Format the message text to look cleaner
            if "▶ START" in message:
                msg = f"*(Thinking...)* {message.replace('▶ START: ', '')}"
            elif "✔ DONE" in message:
                msg = f"**Done!** {message.replace('✔ DONE: ', '')}"
            elif agent_name == "Router":
                msg = f"🔀 *{message}*"
            else:
                msg = message

            # Write directly to the chat container in real-time
            with chat_container:
                with st.chat_message(name=agent_name, avatar=avatar):
                    st.markdown(f"**{agent_name}**\n\n{msg}")

        # Apply our live-update function to the logger
        orchestrator.logger._log = streamlit_chat_log

        with st.spinner("The editorial team is working..."):
            result = orchestrator.run(query=query, output_language=output_language)

        # ── 4. The Final Output ───────────────────────────────────────────────
        st.success("✨ Article successfully generated!")
        st.divider()
        st.subheader(f"📄 Final Published Piece ({output_language.title()})")
        
        # Wrap the markdown in our custom CSS class
        st.markdown(f'<div class="output-box">\n\n{result["final_content"]}\n\n</div>', unsafe_allow_html=True)
        
        st.write("") # Spacing
        st.download_button(
            "⬇️ Download Markdown File", 
            data=result["final_content"], 
            file_name=f"article_{output_language}.md",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Pipeline crashed: {str(e)}")

elif run_btn and not query:
    st.warning("Please enter a topic first.")