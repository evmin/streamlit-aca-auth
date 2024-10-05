import streamlit as st
from lib import create_kernel_with_chat_completion, initialize_agents
from lib import single_agent
import asyncio

st.set_page_config(page_title="Multi agent post writer", layout="wide")

def run_async_task(async_func, *args):
    loop = None
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(async_func(*args))
    except:
        if loop is not None:
            loop.close()

def initialize_state():
        st.session_state.kernel = create_kernel_with_chat_completion("default")
        st.session_state.agents = initialize_agents(st.session_state.kernel)
        st.session_state.topic = ""

def flush_state():
        st.session_state.original_copy = ""
        st.session_state.critic_copy = ""

if "kernel" not in st.session_state or "agents" not in st.session_state or "topic" not in st.session_state:
    initialize_state()

PANEL_HEIGHT = 620



col_writer, col_review, col_panel = st.columns(3,gap="small",)

with col_writer:
    col_writer.markdown("##### Initial writer copy")
    panel_writer = col_writer.container(border=True, height=PANEL_HEIGHT)

with col_review:
    st.markdown("##### Reviewed copy")
    panel_review = col_review.container(border=True, height=PANEL_HEIGHT)

with col_panel:
    col_panel.markdown("##### Agentic (creative) debate")
    panel_container = col_panel.container(border=True, height=PANEL_HEIGHT)



async def process_chat(chat):
    first_copy = True
    async for content in chat.invoke():
        if first_copy:
            with panel_writer:
                panel_writer.markdown(content.content)
                st.session_state.original_copy = content.content
            first_copy = False
        with panel_container:
            # if content.name == "WRITER":
            #     avatar= ":material/edit_note:"
            # else:
            #     avatar= ":material/rate_review:"
            # with st.chat_message("ai", avatar=avatar):
            with st.chat_message("ai", avatar=":material/smart_toy:"):
                st.markdown(f"**{content.name}:**  \n  {content.content}")

# # Accept user input
prompt = st.chat_input("Please provide a topic for a blog post:")

# --- Sidebar ---
with st.sidebar:
    st.info("Multi-agent blog writer.")
    title = st.title(f"Topic: {st.session_state.topic}")
    cc = st.columns(1)
    with cc[0]:
        cc[0].container(border=False, height=300)
    buttn_click = st.button("Reset State")
        
# --- Reset state ---
if buttn_click:
    initialize_state()
    title.title("Topic:")

# --- Process Prompt ---
if prompt:
    initialize_state()
    st.session_state.topic = prompt
    title.title(f"Topic: {st.session_state.topic}")

    with st.spinner("Agents at work..."):
        chat_reflection = asyncio.run(single_agent(prompt, st.session_state.agents))
        run_async_task(process_chat, chat_reflection)

    st.session_state.original_copy = chat_reflection.history[1]
    if chat_reflection.is_complete:
        st.session_state.critic_copy = chat_reflection.history[-2]
    else:
        st.session_state.critic_copy = chat_reflection.history[-1]

    
    with panel_review:
        if "critic_copy" in st.session_state:
            st.markdown(st.session_state.critic_copy)

    with st.sidebar:
        if "history" in chat_reflection:
            st.markdown(f"# {len(chat_reflection.history)}")
