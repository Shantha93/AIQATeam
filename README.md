# 🤖 AI-Powered QA Automation Agent Team

Turn manual test cases into automated Playwright scripts and get a final Pass/Fail report—all with a single click.

 
## 📸 Demo / Screenshot

![App Screenshot](https://github.com/Shantha93/AIQATeam/blob/main/AIQATeam.mp4)

---

## ✨ How It Works

This project uses a team of specialized AI agents, orchestrated by **LangGraph**, to automate the entire QA testing cycle. You provide a plain-text test case, and the agents collaborate to deliver the result.

**The Workflow:**
`Manual Test Case` → `📝 Script Writer Agent` → `▶️ Script Runner Agent` → `🧐 Report Validator Agent` → `✅ Final Report`

---

## 🛠️ Tech Stack

*   **Orchestration:** LangGraph & LangChain
*   **AI:** OpenAI (GPT-4 via Azure)
*   **Automation:** Playwright & Pytest
*   **UI:** Streamlit

---

## 🚀 Quick Start

Get the agent team running in 4 steps:

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/your-username/ai-qa-agent-team.git
    cd ai-qa-agent-team
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    playwright install
    ```

3.  **Configure API Key:**
    Open `QA_AgentTeam.py` and add your Azure OpenAI credentials to the `AzureChatOpenAI` client.
    ```python
    # In QA_AgentTeam.py
    model = AzureChatOpenAI(
        azure_endpoint="YOUR_AZURE_ENDPOINT",
        api_key="YOUR_API_KEY",
        # ... other params
    )
    ```

4.  **Run the app:**
    ```bash
    streamlit run UICode.py
    ```

Now open your browser to the local Streamlit URL and start automating!
