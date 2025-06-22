import streamlit as st
import os
import subprocess
import operator
from  QA_AgentTeam import executeQA
import json

# ==============================================================================
# 2. FRONTEND: STREAMLIT UI
# ==============================================================================

st.set_page_config(page_title="QA Agent Team", layout="wide")
st.title("🤖 QA Multi Agent Team")
st.markdown("Enter a manual test case, and the agent team will write the Playwright script, execute it, and validate the results.")

# Default test case for user convenience
DEFAULT_TEST_CASE = """
Test Case ID: TC-LOGIN-01
Test Case Title: Successful User Login
Steps:
1. Open the browser and navigate to 'https://www.saucedemo.com/'.
2. Verify the page title is 'Swag Labs'.
3. Enter the username 'standard_user' into the username field.
4. Enter the password 'secret_sauce' into the password field.
5. Click the login button.
6. Verify the user is redirected to the inventory page by checking for the text 'Products'.
"""

# User input text area
manual_test_case_input = st.text_area(
    "Enter Manual Test Case (with steps):",
    height=250,
    value=DEFAULT_TEST_CASE
)

# Button to trigger the agent workflow
if st.button("Generate & Run Automation", type="primary"):
    if not manual_test_case_input.strip():
        st.warning("Please enter a manual test case.")
    else:
        results = None
        # Display a spinner while the agents are working
        with st.spinner("The QA Agent team is on the case... This may take a moment."):
            try:
                # Call the backend function
                results = executeQA(manual_test_case_input)
                start_index = results.find('{')


                end_index = results.find('}')

                # Slice the string to get only the JSON part
                if start_index != -1 and end_index != -1:
                    json_string = results[start_index : end_index + 1]
                    print(f"Extracted JSON String: {json_string}")
                else:
                    print("Could not find a JSON object in the string.")

              
                data_dict = json.loads(json_string)
                
                print(f"Parsed Dictionary: {data_dict}")
                print(f"Type of data_dict: {type(data_dict)}")


                st.subheader("✅ Final Validation Report")
                
                
                verdict = data_dict.get('verdict', 'unknown').upper()
                reason = data_dict.get('reason', 'No reason provided.')

                if verdict == "PASS":
                    st.success(f"**VERDICT: {verdict}**")
                elif verdict == "FAIL":
                    st.error(f"**VERDICT: {verdict}**")
                else:
                    st.warning(f"**VERDICT: {verdict}**")
                
                st.info(f"**Reason:** {reason}")
                
                # Use expanders for the detailed, generated artifacts
                with st.expander("View Generated Playwright Script"):
                    script_content = "Script generated"
                    st.code(script_content, language='python')
                    
                    # Add a download button for the generated script
                    st.download_button(
                        label="Download Script",
                        data=script_content,
                        file_name="test_logingenerated.py",
                        mime="text/x-python",
                    )

                
                
                
            except Exception as e:
                import traceback; traceback.print_exc();
                st.error(f"An error occurred during the workflow: {e}")
