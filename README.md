# Travel Agent Practice

A simple travel assistant application built with Python. This project utilizes an LLM agent equipped with weather and attraction search tools to help users plan their trips, running via the Groq API using the OpenAI-compatible SDK.

## Project Structure

```
travel-agent-practice/
│
├── .env                    # Local environment secrets (e.g. API keys)
├── .gitignore              # Files/folders ignored by Git
├── requirements.txt        # Python dependency packages
├── README.md               # Project documentation
├── app.py                  # Entry point for testing / running the application
│
├── agents/                 # Directory for agent definitions
│   └── travel_agent.py     # Travel agent logic
│
├── tools/                  # Directory for agent tools
│   ├── weather_tool.py     # Tool to check the weather
│   └── attraction_tool.py  # Tool to search for local attractions
│
├── data/                   # Directory for storing data
│
└── tests/                  # Directory for unit tests
```

## Setup & Running

1. **Clone the repository** (if not already done).
2. **Create a virtual environment** and activate it:
   ```bash
   python -m venv .venv
   # On Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables**:
   Create a `.env` file in the root directory (or edit the existing one) and fill in your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
5. **Run the test script**:
   ```bash
   python app.py
   ```
