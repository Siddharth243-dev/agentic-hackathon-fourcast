# Architecture Overview

This document outlines the architecture of the Agentic AI Search application, which uses a multi-agent system to find, validate, and summarize information from the web.

## Architectural Diagram (Flow)

The system follows a sequential, multi-step process orchestrated by a series of specialized agents.

```
User Input (Query)
      │
      ▼
┌─────────────────────┐
│   executor.py (UI)  │
│     (Streamlit)     │
└─────────────────────┘
      │
      ▼
┌───────────────────────────┐
│ executor_agent (Sequence) │
└───────────┬───────────────┘
            │ 1. Initial Research
            ▼
┌───────────────────────────┐
│      react_agent          │
│ (Search -> Select -> Get) │
└───────────┬───────────────┘
            │ 2. Validation & Refinement Loop
            ▼
┌──────────────────────────────────────────────────────────┐
│ research_loop_agent (Loop, max_iterations=5)             │
│   (Executes sub-agents sequentially in each iteration)   │
│                                                          │
│   ┌-----------------┐  ► Evaluates source, outputs       │
│   │ validator_agent │    "Approved" or "Rejected" verdict. │
│   └--------┬--------┘                                    │
│            │                                             │
│            ▼                                             │
│   ┌-----------------┐  ► If "Rejected", finds new source.│
│   │  refiner_agent  │  ► If "Approved", passes content on. │
│   └--------┬--------┘                                    │
│            │                                             │
│            ▼                                             │
│   ┌-----------------┐  ► If it receives approved content,│
│   │   exit_agent    │    it calls `exit_loop` to stop.   │
│   └-----------------┘  ► Otherwise, the loop continues.  │
└───────────┬────────────────────────────────────────────────┘
            │ 3. Summarization
            ▼
┌───────────────────────────┐
│     synthesis_agent       │
│       (Summarize)         │
└───────────┬───────────────┘
            │
            ▼
      Final Answer (Markdown)
```

## Components

1. **User Interface**  
   - **`executor.py`**: A web interface built with **Streamlit**. It captures the user's query, initiates the agentic workflow, and displays the final summarized answer in Markdown format.

2. **Agent Core**  
   - **Planner**: The planning is hierarchical.
     - **High-Level Plan**: A `SequentialAgent` (`executor_agent`) in `planner.py` defines the main workflow: Research -> Validate -> Synthesize.
     - **Iterative Sub-Plan**: A `LoopAgent` (`research_loop_agent`) handles the validation and refinement cycle.
     - **Individual Tasks**: Each agent (`react_agent`, `validator_agent`, etc.) uses a `BuiltInPlanner` which prompts the Gemini model with specific instructions and available tools to execute its task.
   - **Executor**: The `google.adk.runners.Runner` in `executor.py` is the primary executor. It manages the agent lifecycle, processes the event stream, and passes messages between agents according to the defined plan.
   - **Memory**: The system uses `google.adk.sessions.InMemorySessionService`. This acts as short-term memory, holding the state and data (like `react_output` and `validator_output`) for a single user session and passing it as context between agents.

3. **Tools / APIs**  
   - **Google Gemini API**: The core reasoning engine for all agents. The project uses `gemini-2.5-pro` for the initial research agent and `gemini-2.5-flash` for validation, refinement, and synthesis.
   - **`google_search`**: A built-in ADK tool used by `react_agent` and `refiner_agent` to find relevant web pages.
   - **`url_context`**: A built-in ADK tool used by `react_agent` and `refiner_agent` to fetch the text content from a given URL.
   - **`exit_loop` (Custom Tool)**: A `FunctionTool` defined in `planner.py` that is called by the `exit_agent` to programmatically terminate the `research_loop_agent`.

4. **Observability**  
   - **Logging**: The `executor.py` module provides real-time user feedback via a `streamlit.status` component. It displays which agent is currently active (`Researching`, `Validating`, etc.) and logs specific tool calls as they happen, offering a transparent view into the agent's reasoning process.
   - **Error Handling**: The primary error handling is in `executor.py`, where a `try...except` block catches exceptions during the agent run and displays a user-friendly error in the Streamlit UI. The `research_loop_agent` also has a `max_iterations=5` safeguard to prevent infinite loops.
