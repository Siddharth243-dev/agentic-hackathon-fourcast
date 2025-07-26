from pydantic import BaseModel, Field
from typing import List

class OrchestrationOutput(BaseModel):
    next_agent: str = Field(
        description="The name of the next agent to call from the available agents."
    )
    task: str = Field(
        description="The specific task or question to pass to the next agent."
    )

class ReActOutput(BaseModel):
    """Output schema for the ReAct agent."""
    search_results: List[str] = Field(
        description="List of urls in descending order of relevancy for the user query"
    )
    url: str = Field(
        description="The chosen url for the next agent to validate."
    )
    raw_content: str = Field(
        description="Raw content from the web page at the chosen url, including text and metadata."
    )
    query: str = Field(
        description="The original user query that was searched."
    )
    timestamp: str = Field(
        description="Timestamp of the article or web page."
    )
    reasoning: str = Field(
        description="Reasoning for the choice of url, including why it is relevant to the query."
    )


class ValidatorOutput(BaseModel):
    """Output schema for the Validator agent."""
    analysis: str = Field(
        description="A concise, single-sentence explanation for the verdict."
    )
    confidence_score: float = Field(
        description="A score from 0.0 to 1.0 indicating confidence in the source's credibility."
    )
    trustworthiness: bool = Field(
        description="The final verdict. Must be either True (approve) or False (reject)."
    )
    raw_content: str = Field(
        description="The raw content from the URL that was validated. Only provided if the source is approved. This MUST be blank if the source is rejected."
    )

class SynthesisOutput(BaseModel):
    source_url: str = Field(
        description="The URL of the source that was synthesized."
    )
    summary: str = Field(
        description="The synthesized content from the source, which should be a concise summary or analysis. This should be in Markdown format to allow for rich text formatting (e.g., bold, italics, links, etc.)"
    )
