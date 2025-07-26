# Agentic AI Search

This repository contains an advanced search application built for the **Agentic AI App Hackathon**. This project uses a multi-agent system powered by Google Gemini to provide users with reliable, validated, and summarized answers to their queries. It goes beyond simple search by employing a research loop that validates sources for credibility and relevance before presenting the final result.

## ✨ Features

- **Multi-Agent Workflow**: A sequential process involving research, validation, refinement, and synthesis agents.
- **ReAct-based Research**: The initial agent uses a ReAct (Reason+Act) pattern to search and select a primary source.
- **Iterative Validation Loop**: A core feature where a `validator_agent` scrutinizes the source. If rejected, a `refiner_agent` finds a better one.
- **Dynamic Summarization**: A `synthesis_agent` creates a clean, Markdown-formatted summary from the final approved source.
- **Interactive UI**: A simple and effective user interface built with Streamlit.

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Conda** (or another virtual environment manager like `venv`)
- A **Google Gemini API Key**. You can get one from Google AI Studio.

### 1. Clone the Repository
```bash
git clone https://github.com/Siddharth243-dev/civiclink-agentic-search.git
cd civiclink-agentic-search
```

### 2. Set Up The Environment

It is recommended to use a virtual environment. The `environment.yml` file is provided for Conda users.

```bash
# Create and activate the conda environment
conda env create -f environment.yml
conda activate agentic-hackathon
```

If you are not using Conda, you can install the dependencies using `pip`:
```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a file named `.env` in the root directory of the project and add your Google API key.

```
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```
The application uses `python-dotenv` to automatically load this key.

## 🏃 How to Run

1.  Make sure your virtual environment (`conda` or `venv`) is activated.
2.  Run the Streamlit application from the project's root directory:

    ```bash
    streamlit run src/executor.py
    ```

3.  Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).
4.  Enter your query in the text box and click "Search" to start the agentic workflow.
