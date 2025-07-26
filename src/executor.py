import streamlit as st
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
import planner
import asyncio
import uuid  # Import the uuid module
import dotenv

dotenv.load_dotenv()

# --- A Helper Function to Run Our Agents ---


async def run_query(query: str, session_service: InMemorySessionService, session_id: str, user_id: str, status: st.status):
    """Runs the query against the agentic workflow, streaming progress to the UI."""
    runner = Runner(
        agent=planner.executor_agent,
        session_service=session_service,
        app_name=planner.executor_agent.name
    )

    final_response = "The agentic workflow did not produce a final answer."
    current_agent = None
    try:
        # Stream the events from the runner to find the final response from the synthesis agent.
        # This mirrors the more robust execution logic from main.py.
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=Content(parts=[Part(text=query)], role="user")
        ):
                        # Update status based on which agent is working
            if event.author != current_agent and event.author in ["react", "validator", "refiner", "synthesis"]:
                current_agent = event.author
                if current_agent == 'react':
                    status.update(label="🔍 Researching... The first agent is searching for relevant sources.")
                elif current_agent == 'validator':
                    status.update(label="🧐 Validating... The fact-checker is verifying the source.")
                elif current_agent == 'refiner':
                    status.update(label="🤔 Refining... The previous source was rejected, finding a better one.")
                elif current_agent == 'synthesis':
                    status.update(label="✍️ Summarizing... The writer is creating the final answer.")

            # Log tool calls inside the status box for more detail
            if event.get_function_calls():
                for tool_call in event.get_function_calls():
                    if tool_call.name == "exit_loop":
                        status.write("🔚 Exiting the loop as the plan was approved.")
                    else:
                        status.write(f"🤖 Agent is using the `{tool_call.name}` tool...")
            
            # The final response from the SequentialAgent comes from its last sub-agent,
            # which is the 'synthesis' agent. We check for its final output.
            if event.author == 'synthesis' and event.is_final_response():
                final_response = event.content.parts[0].text
                break
        return final_response
    except Exception as e: 
        status.update(label="🚨 Error!", state="error")
        status.write(f"An error occurred: {e}")
        st.error(f"An error occurred during agent execution: {e}")
        return "An error occurred during the execution. Please check the logs or try again."

async def _create_session():
    return InMemorySessionService()

async def run_workflow(agent: planner.Agent, user_id: str, query: str, status: st.status):
    """Creates a runner and executes the agentic workflow for a given query."""
    session_service = await _create_session()
    research_session = await session_service.create_session(
        app_name=agent.name,
        user_id=user_id
    )
    # chosen_route = await run_query(query, session_service, research_session.id, user_id)
    # chosen_route = chosen_route.strip().replace("'", "")
    # print(f"🚦 Router has selected route: '{chosen_route}'")
    return await run_query(query, session_service, research_session.id, user_id, status)

def main():
    st.title("CivicLink - Agentic AI Search")

    # Custom CSS to make the text input larger and more prominent
    st.markdown("""
    <style>
    /* Custom class for main descriptive text */
    .main-text {
        font-size: 1.1rem !important;
    }

    /* Target the label of the text_area */
    label[data-testid="stWidgetLabel"] {
        font-size: 1.25rem !important;
    }
    /* Target the text inside the text_area */
    .stTextArea textarea {
        font-size: 1.0rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="main-text">
    Welcome! This isn't just another search engine. Instead of giving you a long list of links to sort through, we use a team of specialized AI agents to find, verify, and summarize the best answer for you.

    **Here’s how it works:**
    1.  **The Researcher**: When you ask a question, our first agent scours the web to find the most relevant information.
    2.  **The Fact-Checker**: A meticulous validator agent then examines that source for credibility, relevance, and timeliness. If it doesn't meet our high standards, the researcher is sent back to find a better one.
    3.  **The Writer**: Once a source is approved, our final agent reads the content and writes a clear, concise summary, citing the original source.

    The result is a single, trustworthy answer, saving you time and effort. Go ahead and ask a question to see them in action!
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown(
        "#### Trying to figure out if your county allows you to grow a :blue[Blue Marble Tree] in your :green[backyard] :material/mystery: ####",
        
          )

    user_query = st.text_area(
        label='Does my county allow me to grow a Blue Marble Tree in my backyard?',
        placeholder="Or ask about any other public policy, zoning law, or civic question...",
        height=120
    )

    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    user_id = st.session_state.user_id

    main_agent = planner.executor_agent

    if st.button("Search"):
        if user_query:
            with st.status("🚀 Starting the agentic workflow...", expanded=True) as status:
                final_response = asyncio.run(run_workflow(main_agent, user_id, user_query, status))
                status.update(label="✅ All done!", state="complete")

            if final_response:
                st.header("Final Answer:")
                st.markdown(final_response, unsafe_allow_html=False)


if __name__ == "__main__":
    main()