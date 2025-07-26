# Technical Explanation

## 1. Agent Workflow

Our agentic system processes a user query through a structured, multi-step workflow orchestrated by a `SequentialAgent`.

1.  **Receive User Input**: The Streamlit UI in `executor.py` captures the user's search query.
2.  **Initial Research (ReAct Pattern)**: The `react_agent` receives the query and begins a ReAct-style process:
    -   **Thought**: "I need to find relevant and up-to-date information for the user's query."
    -   **Action**: Calls the `google_search` tool with the query.
    -   **Observation**: Receives a list of URLs.
    -   **Thought**: "Based on the titles and snippets, URL 'X' seems most promising and credible."
    -   **Action**: Calls the `url_context` tool on the chosen URL.
    -   **Observation**: Receives the full text content of the page.
    -   **Action**: Formats all gathered information into a structured text block (`react_output`) and passes it to the next agent.
3.  **Validate & Refine (Iterative Loop)**: The `research_loop_agent` takes the `react_output` and begins its iterative process. In each loop:
    -   The `validator_agent` assesses the source based on domain trust, relevance, and timeliness. It outputs a verdict ("Approved" or "Rejected") and a confidence score.
    -   The `refiner_agent` receives the validator's output. If the verdict was "Rejected," it analyzes the feedback, performs a new `google_search` to find a better source, and generates a new `react_output`. If the verdict was "Approved," it simply passes the validated content along.
    -   The `exit_agent` receives the output from the refiner. If this output contains approved "Raw Content," it calls the `exit_loop` tool, which sets `tool_context.actions.escalate = True`, terminating the loop. Otherwise, the loop continues to the next iteration.
4.  **Synthesize and Return**: Once the loop is exited, the `synthesis_agent` receives the final, validated `react_output`. It reads the raw text and generates a concise, well-formatted Markdown summary. This summary is the final output returned to the user in the Streamlit UI.

## 2. Key Modules

- **`planner.py`**: This is the heart of the application. It defines all individual agents with their specific instructions, tools, and output keys. It then composes them into the `research_loop_agent` (a `LoopAgent`) and the main `executor_agent` (a `SequentialAgent`).
- **`executor.py`**: This module serves as the user-facing entry point. It contains the Streamlit UI, manages session state with unique IDs, and uses the `google.adk.runners.Runner` to execute the agentic workflow. It's responsible for initiating the run and displaying the final result.
- **`models.py`**: This file defines the Pydantic data structures (`ReActOutput`, `ValidatorOutput`, etc.). While not currently wired up to the agents' `output_schema` parameter, they serve as a clear definition for the expected structure of inter-agent communication.

## 3. Tool Integration

All tools are integrated via the `tools` parameter of an `Agent`, making them available to the Gemini model for function calling.

- **`google_search`**: A built-in tool from the `google.adk.tools` library. It is called by the `react_agent` and `refiner_agent` to get a list of URLs from a search query.
- **`url_context`**: Another built-in ADK tool. It is used by the `react_agent` and `refiner_agent` to fetch the raw text content from a specific URL.
- **`exit_loop`**: A custom `FunctionTool` defined in `planner.py`. It is called exclusively by the `exit_agent` when it receives approved content. The tool's function sets `tool_context.actions.escalate = True`, which signals to the `LoopAgent` that the loop should terminate.

## 4. Observability & Testing

Decisions can be traced by observing the console output when running `streamlit run src/executor.py`.

- **Agent Steps**: The `Runner` from the ADK produces a stream of events that could be logged for detailed tracing. For simplicity, this project uses `print()` statements (e.g., in the `exit_loop` tool) to show when key actions are triggered.
- **Final Output**: The final generated summary from the `synthesis_agent` is printed to the console and displayed on the web page.
- **Error Handling**: Any exceptions during the agent run are caught in `executor.py` and displayed in the Streamlit UI via `st.error()`, preventing the application from crashing.

## 5. Known Limitations

- **Performance**: The sequential nature of the agents, especially the potential for multiple loops in the `research_loop_agent`, can lead to long wait times for the user (30-60+ seconds). Each agent call is a separate, blocking LLM invocation.
- **Content Extraction**: The `url_context` tool may fail on heavily JavaScript-rendered sites, pages behind paywalls, or sites with aggressive bot detection. This can cause the research phase to fail.
- **Refinement Strategy**: The `refiner_agent`'s success depends heavily on the quality of the `validator_agent`'s feedback and the LLM's ability to interpret it to form a better search query. It may still pick a suboptimal source or get stuck in a loop of bad choices.
- **Structured Output**: The agents currently rely on prompt instructions to format their output as structured text rather than using the `output_schema` with Pydantic models. This is less robust and can lead to parsing errors if the LLM deviates from the requested format.
