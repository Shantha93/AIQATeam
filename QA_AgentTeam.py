import os
import subprocess
import operator
from typing import TypedDict, Annotated, List, Dict, Any

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

# --- 0. Environment Setup ---
# Ensure your OPENAI_API_KEY is set in your environment

model = AzureChatOpenAI(
    azure_endpoint="https://testdemotest.openai.azure.com/",
    api_key="YOUR API KEY",
    api_version="2024-12-01-preview",
    azure_deployment="gpt-4o-mini",
    temperature=0,
)
SCRIPT_FILE_PATH = "test_logingenerated.py"



# --- 1. Define the State for the Workflow ---
# This dictionary will be passed between our agents, carrying the data at each step.
class AgentState(TypedDict):
    manual_test_case: str
    playwright_script: str
    execution_logs: str
    final_report: Dict[str, Any]

# --- 2. Define Tools for the Agents ---

@tool
def write_playwright_script(manual_test_case: str) -> Dict[str, str]:
    """
    Generates an efficient Playwright script from a manual test case.
    The script includes detailed logging and is saved to a file.
    """
    print("--- SCRIPT WRITER AGENT: Engaged ---")
    
    # A powerful prompt to guide the LLM
    prompt = f"""
    You are an expert Senior QA Automation Engineer specializing in Playwright with Python.
    Your task is to convert the following manual test case into a robust and efficient Playwright script using pytest.

    Manual Test Case:
    ---
    {manual_test_case}
    ---

    Requirements for the script:
    1.  Use Python with the `pytest` framework.
    2.  Import `test` and `expect` from `playwright.sync_api`.
    3.  Create a test function, for example, `def test_example_scenario(page):`.
    4.  **CRITICAL:** Add detailed print statements for logging. Before every action (like `click`, `fill`, `goto`), print an "INFO:" line. Before every validation (`expect`), print a "VALIDATE:" line. After a successful validation, print a "SUCCESS:" line. This logging is essential for the validator agent.
    5.  Use best practices like using `page.locator()` for selecting elements.
    6.  The final script should be a single block of Python code, ready to be executed.
    
Note: DO not add any additional line like '```python' or 'phrases or words' other than a valid python code in your final output. DO not include anything apart from python code in your final output.
    """
    
    response = model.invoke([HumanMessage(content=prompt)])
    script_content = response.content.strip('`').strip('python\n').strip()
    
    print(f"--- SCRIPT WRITER AGENT: Script generated. Saving to {SCRIPT_FILE_PATH} ---")
    print(f"Generated python content : {script_content}")
    with open(SCRIPT_FILE_PATH, "w") as f:
        f.write(script_content)
        
    return {"script": script_content}


@tool
def execute_playwright_script(script_code: str) -> Dict[str, str]:
    """
    Executes the provided Playwright script using pytest and captures the output.
    The script is assumed to be already saved to SCRIPT_FILE_PATH.
    """
    print(f"--- SCRIPT RUNNER AGENT: Executing {SCRIPT_FILE_PATH} ---")
    
    # We don't need the script_code argument since it's already written to a file,
    # but it's good for lineage to know what was intended to be run.
    
    try:
        # Use pytest to run the script. This is the standard way.
        # `capture_output=True` is key to getting stdout and stderr.
        result = subprocess.run(
            [ "pytest","--headed","-rP"],
            capture_output=True,
            text=True,
            timeout=120 # 2 minute timeout to prevent hangs
        )
        
        stdout = result.stdout
        stderr = result.stderr
        
        logs = f"--- STDOUT ---\n{stdout}\n\n--- STDERR ---\n{stderr}"
        
        print("--- SCRIPT RUNNER AGENT: Execution complete. ---")
        return {"logs": logs}
        
    except FileNotFoundError:
        error_message = "Error: `pytest` command not found. Make sure pytest is installed (`pip install pytest`)."
        print(f"--- SCRIPT RUNNER AGENT: {error_message} ---")
        return {"logs": error_message}
    except Exception as e:
        error_message = f"An unexpected error occurred during execution: {e}"
        print(f"--- SCRIPT RUNNER AGENT: {error_message} ---")
        return {"logs": error_message}

@tool
def validate_test_outcome(manual_test_case: str, execution_logs: str) -> Dict[str, Any]:
    """

    Analyzes the manual test case and the execution logs to determine if the test passed or failed.
    """
    print("--- REPORT VALIDATOR AGENT: Engaged ---")

    prompt = f"""
    You are a meticulous Senior QA Analyst. Your job is to validate the outcome of an automated test run.
    You will be given the original manual test case and the execution logs from the Playwright script.

    1.  **Original Manual Test Case:**
    ---
    {manual_test_case} 
    ---

    2.  **Execution Logs (from stdout/stderr):**
    ---
    {execution_logs}
    ---

    **Your Task:**
    Carefully read the manual test case to understand the expected behavior for each step.
    Then, scrutinize the execution logs. Look for the "INFO:", "VALIDATE:", and "SUCCESS:" log lines to trace the script's actions.
    - If the logs show all steps were completed and validations passed (look for "SUCCESS" lines and a "passed" status from pytest at the end), the test is a "pass".
    - If the logs contain any errors, assertion failures, or a "failed" status from pytest, the test is a "fail".

    Provide your final verdict in a dictionary format: {{"verdict": "pass" | "fail", "reason": "Your concise explanation here."}} . Please ensure not to use charaters like "'" or any form of escape sequence in your response.. generate only plain english response.
    """
    
    response = model.invoke([HumanMessage(content=prompt)])
    
    # A simple but effective way to parse the dictionary-like string from the LLM
    try:
        report = eval(response.content)
    except:
        report = {"verdict": "error", "reason": "Could not parse the LLM's validation report."}

    print("--- REPORT VALIDATOR AGENT: Validation complete. ---")
    return response

# --- 3. Define the Agents ---

script_writer_agent = create_react_agent(
    model,
    tools=[write_playwright_script],
)

script_runner_agent = create_react_agent(
    model,
    tools=[execute_playwright_script],
)


# --- 4. Define the Nodes for the Graph ---

def script_writer_node(state: AgentState):
    """Node that runs the script writer agent."""
    result = script_writer_agent.invoke({
        "messages": [HumanMessage(content=state["manual_test_case"])]
    })
    # Extract the script content from the tool call in the last message
    for msg in reversed(result["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "write_playwright_script":
            return {"playwright_script": msg.content}
    return {}

def script_runner_node(state: AgentState):
    """Node that runs the script executor agent."""
    result = script_runner_agent.invoke({
        "messages": [HumanMessage(content=f"Execute the script: {state['playwright_script']}")]
    })
    for msg in reversed(result["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "execute_playwright_script":
            return {"execution_logs": msg.content}
    return {}

# Replace your existing report_validator_node with this more efficient version

def report_validator_node(state: AgentState):
    """
    This node calls the validation tool directly, without a ReAct agent.
    This is much more efficient as it saves an unnecessary LLM "thought" step.
    """
    print("--- Directly invoking validation logic ---")
    
    # Manually create the tool instance. 
    # This is a good practice if you need to call it outside an agent.
    validation_tool = validate_test_outcome

    # Call the tool function directly with the state variables
    report = validation_tool.invoke({
        "manual_test_case": state["manual_test_case"],
        "execution_logs": state["execution_logs"],
    })
    
    return {"final_report": report}

# --- 5. Construct the Graph ---

workflow = StateGraph(AgentState)

workflow.add_node("script_writer", script_writer_node)
workflow.add_node("script_runner", script_runner_node)
workflow.add_node("report_validator", report_validator_node)

workflow.set_entry_point("script_writer")
workflow.add_edge("script_writer", "script_runner")
workflow.add_edge("script_runner", "report_validator")
workflow.add_edge("report_validator", END)

app = workflow.compile()

# --- 6. Run the Workflow ---

def executeQA(manual_test_case_input:str): 

    # Initial state for the workflow
    initial_state = {"manual_test_case": manual_test_case_input}

    try:
        # Invoke the graph
        final_state = app.invoke(initial_state)

        # --- Display Final Results ---
        print("\n" + "="*80)
        print("                        QA AUTOMATION WORKFLOW COMPLETE")
        print("="*80)

        print("\n[1] MANUAL TEST CASE:")
        print("--------------------")
        print(final_state['manual_test_case'])

        print("\n[2] GENERATED PLAYWRIGHT SCRIPT:")
        print("-------------------------------")
        print(final_state['playwright_script'])

        print("\n[3] EXECUTION LOGS:")
        print("------------------")
        print(final_state['execution_logs'])

        print("\n[4] FINAL VALIDATION REPORT:")
        print("---------------------------")
        report = final_state['final_report']
        print(f"  VERDICT: {report}")
      
        print("="*80)
        
        return str(report)
    except Exception:
        import traceback; traceback.print_exc();

    
if __name__ == "__main__":
 # Define the manual test case from the user
    manual_test_case_input = """
    Test Case ID: TC-LOGIN-01
    Test Case Title: Successful User Login
    Steps:
    1. Open the browser and navigate to 'https://www.saucedemo.com/'.
    2. Verify the page title is 'Swag Labs'.
    3. Enter the username 'standard_user' into the username field.
    4. Enter the password 'secret_sauce' into the password field.
    5. Click the login button.
    6. Verify the user is redirected to the inventory page.
    """
    executeQA(manual_test_case_input)
   
