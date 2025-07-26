from google.genai import Client, types
from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.planners import BuiltInPlanner
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.google_search_tool import google_search
from google.adk.tools.url_context_tool import url_context
from google.adk.tools import ToolContext, FunctionTool
    
react_agent = Agent(
    name = 'react',
    model = 'gemini-2.5-pro',
    planner=BuiltInPlanner(
    thinking_config = types.ThinkingConfig(
        include_thoughts=False,
        thinking_budget=250)
    ),
    description = 'A research agent that uses Google Search to find relevant URLs for a given query, selects the most promising one, and extracts its content and metadata for further analysis.',
    instruction = """
    You are a specialized research agent. Your primary function is to process a user's query by performing a web search to find the most relevant and up-to-date information.
    Your steps are as follows:
    1.  Take the user's query and use the `google_search_tool` to get a list of relevant URLs.
    2.  From the search results, carefully select the single most promising and credible URL.
    3.  Use the `url_context_tool` to fetch the full content of your chosen URL.
    4.  From the content, extract the publication date or timestamp.
    5.  After gathering all information, you MUST output a single block of text containing all the following details, clearly labeled:
        - "Original Query": [The original user query]
        - "Search Results": [A comma-separated list of URLs from the search]
        - "Chosen URL": [The single URL you chose]
        - "Reasoning": [Your reasoning for choosing that URL]
        - "Timestamp": [The timestamp you found]
        - "Raw Content": [The full raw text content from the chosen URL]
    """,
    tools = [google_search, url_context],
    output_key="react_output",
)


def exit_loop(tool_context: ToolContext):
    """Call this function ONLY when the plan is approved, signaling the loop should end."""
    print(f" [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    # tool_context.actions.transfer_to_agent = 'synthesis'  # This will transfer control to the synthesis agent.
    # tool_context.actions.transfer_to_agent = 'synthesis'  # This will transfer control back to the orchestrator agent.
    return {}

validator_agent = Agent(
    name = 'validator',
    model = 'gemini-2.5-flash',
    planner=BuiltInPlanner(
        thinking_config = types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=100)
        ),
    description = 'Validator agent that checks the accuracy of the source provided by the ReAct agent.',
    instruction = """
    You are a meticulous fact-checker and research analyst. Your sole purpose is to evaluate the credibility and relevance of a web source based on the context provided to you. You will be given the original user query, the source URL, and the pre-fetched text from that URL. Do NOT attempt to fetch the URL content yourself; analyze only the text you are given.

    User Question: {{session.query}}
    React Output: {{react_output}}

    You must evaluate the source based on the following criteria in order of importance:

    Source Domain Authority:

    High Trust: .gov and .mil domains are official government sources. .edu domains from known universities are highly trustworthy for academic topics.

    Medium Trust: Reputable, well-known news organizations (e.g., Reuters, Associated Press, BBC). Be cautious of opinion pieces.

    Low Trust: .com, .org, .net domains require scrutiny. They could be official businesses, non-profits, or personal blogs. You must identify which.

    Very Low Trust: Personal blogs (e.g., on Blogspot, Medium), forums (e.g., Reddit), or unknown sites. These are generally unacceptable as primary sources for factual claims.

    Content-Query Alignment: Does the provided text actually answer the user's original query? A source can be official but irrelevant. The text must directly address the user's intent.

    Timeliness: Check the document for publication or "last updated" dates. For queries about current events or laws (e.g., "what are the rules right now?"), information older than 1-2 years should be flagged as potentially outdated.
    You must return a single block of text with the following fields, clearly labeled:
    - "Analysis": A concise, single-sentence explanation for your verdict.
    - "Confidence Score": A score from 0.0 to 1.0 indicating confidence in the source's credibility.
    - "Trustworthiness": The final verdict. Must be either Approved or Rejected. If you approve, you must also return the raw content
    from the URL. If you reject, this field must be blank.
    - "Raw Content": The raw content from the URL that was validated. Only provided if the source is approved. This MUST be blank if the source is rejected.

    Only approve sources that are directly relevant to the user's query if the confidence in the source's credibility is high, atleast 0.95. 
    """
    ,
    output_key="validator_output",
    # output_schema = models.ValidatorOutput,
)

refiner_agent = Agent(
    name = 'refiner',
    model = 'gemini-2.5-flash',
    planner=BuiltInPlanner(
    thinking_config = types.ThinkingConfig(
        include_thoughts=False,
        thinking_budget=100)
    ),
    description = 'Refines a search attempt based on feedback from the validator agent.',
    instruction = """
    You are a specialized research agent. Your primary function is to re-attempt a search query that has previously failed validation.
    You will be given the original user query and the feedback from the 'validator' agent. The feedback will explain why the previous attempt was rejected.

    User Question: {{session.query}}
    Validator Feedback: {{validator_output}}

    Your task is to perform a new search, avoiding the mistakes highlighted in the feedback.
    Your steps are as follows:
    1.  Analyze the validator's feedback to understand why the previous source was inadequate (e.g., low trust domain, irrelevant content, outdated).
    2.  Use the `google_search_tool` with the original query to get a list of relevant URLs.
    3.  From the search results, carefully select a NEW URL that does not have the same issues as the previous one. For example, if the last one was a blog, choose a news site or a .gov site.
    4.  Use the `url_context_tool` to fetch the full content of your chosen URL.
    5.  From the content, extract the publication date or timestamp.
    6.  After gathering all information, you MUST output a single block of text containing all the following details, clearly labeled:
        - "Original Query": [The original user query]
        - "Search Results": [A comma-separated list of URLs from the search]
        - "Chosen URL": [The single URL you chose]
        - "Reasoning": [Your reasoning for choosing this new URL, specifically addressing how it overcomes the previous failure]
        - "Timestamp": [The timestamp you found]
        - "Raw Content": [The full raw text content from the chosen URL]
    
    If validator has provided "Raw Content", you will simply pass {{validator_output}} to the next agent.
    """,
    tools = [google_search, url_context],
    output_key="react_output",
)

exit_agent = Agent(
    name = 'exit',
    model = 'gemini-2.0-flash',
    description = 'Exit agent that signals the end of the research loop.',
    instruction = """
    You are an exit agent. Your sole purpose is to signal the end of the research loop.
    You will receive the validated content from the 'research_loop' agent. You will pass this content to the synthesis agent for final summarization.
    Input : {{react_output}}
    If the 'react_output' contains "Raw Content", you MUST call the `exit_loop` tool to end the loop and send your output to the synthesis agent.
    Your output MUST be strictly {{react_output}}. You will not modify or analyze the content in any way.
    """,
    output_key="react_output",
    tools = [FunctionTool(func=exit_loop)],
)

research_loop_agent = LoopAgent(
    sub_agents=[validator_agent, refiner_agent, exit_agent],
    max_iterations=5,  # A safeguard to prevent infinite loops.
    name="research_loop",
    description="An agent that iteratively researches and validates sources until a trustworthy one is found."
)


synthesis_agent = Agent(
    name='synthesis',
    model='gemini-2.5-flash',
    planner=BuiltInPlanner(
    thinking_config = types.ThinkingConfig(
        include_thoughts=False,
        thinking_budget=100)
    ),
    description='Synthesis agent that creates a concise summary from a validated source.',
    instruction="""
    You are a synthesis agent. Your task is to take a validated source URL and its content, and produce a concise, well-formatted summary in Markdown.
    Raw Content: {{react_output}}
    The summary should be clear, informative, and directly related to the original user query. You MUST Highlight key points relevant to the user query and ensure the summary is easy to read!
    You will receive the validated content from the 'research_loop' agent. Your output MUST be a formatted markdown text containing the following fields:
    - "Source URL": The URL of the source you are synthesizing.
    - "Summary": The synthesized content from the source, which should be a concise summary or analysis. This should be in Markdown format to allow for rich text formatting (e.g., bold,
    Both 'Source URL' and 'Summary' fields should be formatted as Header 2 in Markdown. Their content should start with a newline character.
    """
)

executor_agent = SequentialAgent(
    name='sequential_agent',
    sub_agents=[react_agent, research_loop_agent, synthesis_agent],
    description='A sequential agent that executes a series of tasks using the provided callable agents.'
)