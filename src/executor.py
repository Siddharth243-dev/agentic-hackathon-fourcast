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


async def run_query(query: str, session_service: InMemorySessionService, session_id: str, user_id: str = "streamlit_user"):
    """Runs the query against the agentic workflow."""

    runner = Runner(
        agent=planner.executor_agent,
        session_service=session_service,
        app_name=planner.executor_agent.name
    )

    final_response = "The agentic workflow did not produce a final answer."
    try:
        # Stream the events from the runner to find the final response from the synthesis agent.
        # This mirrors the more robust execution logic from main.py.
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=Content(parts=[Part(text=query)], role="user")
        ):
            # The final response from the SequentialAgent comes from its last sub-agent,
            # which is the 'synthesis' agent. We check for its final output.
            if event.author == 'synthesis' and event.is_final_response():
                final_response = event.content.parts[0].text
                # We can stop listening for events once we have what we need.
                break
        return final_response
    except Exception as e:
        st.error(f"An error occurred during agent execution: {e}")
        return "An error occurred during the execution. Please check the logs or try again."

async def _create_session():
    return InMemorySessionService()

async def run_workflow(agent: planner.Agent, user_id: str, query: str):
    """Creates a runner and executes the agentic workflow for a given query."""
    session_service = await _create_session()
    research_session = await session_service.create_session(
        app_name=agent.name,
        user_id=user_id
    )
    chosen_route = await run_query(query, session_service, research_session.id, user_id)
    chosen_route = chosen_route.strip().replace("'", "")
    print(f"🚦 Router has selected route: '{chosen_route}'")
    return chosen_route  # Un-comment this to return the result

def main():
    st.title("CivicLink - Agentic AI Search")
    st.markdown("""
    Welcome! This isn't just another search engine. Instead of giving you a long list of links to sort through, we use a team of specialized AI agents to find, verify, and summarize the best answer for you.

    **Here’s how it works:**
    1.  **The Researcher**: When you ask a question, our first agent scours the web to find the most relevant information.
    2.  **The Fact-Checker**: A meticulous validator agent then examines that source for credibility, relevance, and timeliness. If it doesn't meet our high standards, the researcher is sent back to find a better one.
    3.  **The Writer**: Once a source is approved, our final agent reads the content and writes a clear, concise summary, citing the original source.

    The result is a single, trustworthy answer, saving you time and effort. Go ahead and ask a question to see them in action!
    """)

    st.divider()

    user_query = st.text_input(
        "Trying to figure out if your county allows you to grow a Blue Marble Tree in your backyard?",
        placeholder="Or ask about any other public policy, zoning law, or civic question..."
    )

    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    user_id = st.session_state.user_id

    main_agent = planner.executor_agent

    if st.button("Search"):
        if user_query:
            with st.spinner("Agents are working..."):
                final_response = asyncio.run(run_workflow(main_agent, user_id, user_query))

            st.subheader("Final Answer:")
            st.markdown(final_response)


if __name__ == "__main__":
    main()