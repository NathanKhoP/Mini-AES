import streamlit as st
import mini_aes
import os
from datetime import datetime

# Set page config and title
st.set_page_config(page_title="Mini-AES Encryption/Decryption", layout="wide")
st.title("Mini-AES Encryption/Decryption")

# --- DEFINE TEST CASES ---
TEST_CASES = [
    {
        'name': 'Test Case 1: Example 6F6B/A73B',
        'plaintext': '6F6B',
        'key': 'A73B',
    },
    {
        'name': 'Test Case 2: All Zeros',
        'plaintext': '0000',
        'key': '0000',
    },
    {
        'name': 'Test Case 3: All Fs',
        'plaintext': 'FFFF',
        'key': 'FFFF',
    },
    {
        'name': 'Test Case 4: Example 2D3B/1A5F',
        'plaintext': '2D3B',
        'key': '1A5F',
    },
    {
        'name': 'Test Case 5: Example 6F6B2D3B/A73B',
        'plaintext': '6F6B2D3B',  # Two blocks
        'key': 'A73B',
        'iv': '1234'
    }
]

# Initialize session state if not already initialized
if 'input_text' not in st.session_state:
    st.session_state.input_text = ''
if 'key_text' not in st.session_state:
    st.session_state.key_text = ''
if 'iv_text' not in st.session_state:
    st.session_state.iv_text = ''

# Create two columns for input fields
col1, col2 = st.columns(2)

with col1:
    # Input text field using session state
    input_text = st.text_input("Input Text (4 or more hex characters for CBC)", 
                              value=st.session_state.input_text).strip().upper()
    st.session_state.input_text = input_text
    
    # Mode selection
    mode = st.radio("Operation Mode", 
                    ["Encrypt", "Decrypt"],
                    horizontal=True)
    
    # Cipher mode selection
    cipher_mode = st.radio("Cipher Mode",
                          ["ECB", "CBC"],
                          horizontal=True)

with col2:
    # Key input field using session state
    key_text = st.text_input("Key (4 hex characters)", 
                            value=st.session_state.key_text,
                            max_chars=4).strip().upper()
    st.session_state.key_text = key_text
    
    # IV input for CBC mode
    if cipher_mode == "CBC":
        iv_text = st.text_input("IV (4 hex characters, optional)", 
                               value=st.session_state.iv_text,
                               max_chars=4).strip().upper()
        st.session_state.iv_text = iv_text

# Test Cases Section
st.subheader("Test Cases")
selected_test = st.selectbox(
    "Select a test case to auto-fill inputs",
    [case['name'] for case in TEST_CASES]
)

# Auto-fill button
if st.button("Apply Selected Test Case"):
    selected_case = next((case for case in TEST_CASES if case['name'] == selected_test), None)
    if selected_case:
        st.session_state.input_text = selected_case['plaintext']
        st.session_state.key_text = selected_case['key']
        if 'iv' in selected_case:
            st.session_state.iv_text = selected_case['iv']
        st.rerun()

st.markdown("---")

# Process button
if st.button("Process"):
    error = None
    
    # Basic input validation
    if not input_text or not key_text:
        error = "Input text and key cannot be empty."
    elif len(key_text) != 4:
        error = "Key must be exactly 4 hexadecimal characters long."
    elif cipher_mode == "ECB" and len(input_text) % 4 != 0:
        error = "In ECB mode, input text length must be a multiple of 4 hexadecimal characters."
    elif cipher_mode == "CBC" and len(input_text) % 4 != 0:
        error = "In CBC mode, input text length must be a multiple of 4 hexadecimal characters."
    else:
        try:
            int(input_text, 16)
            int(key_text, 16)
            if cipher_mode == "CBC" and iv_text:
                int(iv_text, 16)
            
            if cipher_mode == "ECB":
                if mode == "Encrypt": 
                    result, error, log = mini_aes.encrypt(input_text, key_text)
                else:
                    result, error, log = mini_aes.decrypt(input_text, key_text)
            else:  
                if mode == "Encrypt":
                    result, error, log = mini_aes.encrypt_cbc(input_text, key_text, iv_text if iv_text else None)
                else:
                    result, error, log = mini_aes.decrypt_cbc(input_text, key_text)

            if error:
                st.error(f"Error: {error}")
            elif result:
                st.success(f"Operation ({mode} in {cipher_mode} mode) successful!")
                st.subheader("Result")
                st.code(result, language="text")
                
                # Display detailed log in an expander
                with st.expander("Show detailed process log"):
                    for line in log:
                        st.text(line)
                
                # Store result and log in session state for export
                st.session_state.last_result = result
                st.session_state.last_log = log
                st.session_state.last_operation = {
                    'mode': mode,
                    'cipher_mode': cipher_mode,
                    'input_text': input_text,
                    'key': key_text,
                    'iv': iv_text if cipher_mode == "CBC" else None
                }

        except ValueError:
            error = "Input values must contain valid hexadecimal characters (0-9, A-F)."
            st.error(error)
        except Exception as e:
            error = f"An unexpected error occurred: {str(e)}"
            st.error(error)
    
    if error:
        st.error(error)

# Import/Export
st.markdown("---")
st.subheader("Import/Export Operations")

imp_exp_tabs = st.tabs(["Export", "Import"])

with imp_exp_tabs[0]:  # Export tab
    st.write("Export operation to CSV")
    custom_filename = st.text_input("Custom filename (optional)", 
                                  placeholder="Leave empty for auto-generated name")
    
    if st.button("Export to CSV"):
        if 'last_result' not in st.session_state:
            st.warning("Please perform an operation first before exporting.")
        else:
            try:
                filename = custom_filename if custom_filename else None
                export_path = mini_aes.export_to_csv(
                    mode=st.session_state.last_operation['mode'],
                    cipher_mode=st.session_state.last_operation['cipher_mode'],
                    input_text=st.session_state.last_operation['input_text'],
                    key=st.session_state.last_operation['key'],
                    iv=st.session_state.last_operation['iv'],
                    output=st.session_state.last_result,
                    log=st.session_state.last_log,
                    filename=filename
                )
                st.success(f"Operation details exported to: {export_path}")
                
                # Provide download button for the exported file
                with open(export_path, 'rb') as f:
                    st.download_button(
                        label="Download CSV",
                        data=f,
                        file_name=os.path.basename(export_path),
                        mime="text/csv"
                    )
            except Exception as e:
                st.error(f"Could not export to CSV: {str(e)}")

with imp_exp_tabs[1]:  # Import tab
    st.write("Import operation from CSV")
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    if uploaded_file is not None:
        try:
            # Save the uploaded file temporarily
            temp_path = os.path.join('logs', uploaded_file.name)
            os.makedirs('logs', exist_ok=True)
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Import the operation details
            operation = mini_aes.import_from_csv(temp_path)
            if isinstance(operation, tuple):  # Error occurred
                st.error(f"Error importing file: {operation[1]}")
            else:
                # Display imported details
                st.success("Successfully imported operation details!")
                with st.expander("View imported details"):
                    for key, value in operation.items():
                        if key != 'Process Log':
                            st.write(f"{key}: {value}")
                        else:
                            st.write("Process Log:")
                            for line in value:
                                st.text(line)
                
                # Add button to apply imported values
                if st.button("Apply imported values"):
                    st.session_state.input_text = operation['Input Text']
                    st.session_state.key_text = operation['Key']
                    if 'IV' in operation:
                        st.session_state.iv_text = operation['IV']
                    st.rerun()
            
            # Clean up temp file
            os.remove(temp_path)
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

# Help section at the bottom
st.markdown("---")
st.markdown("""
### How to Use
1. Select the cipher mode (ECB or CBC)
2. Enter your input text - must be a multiple of 4 hexadecimal characters
3. Enter a 4-character hexadecimal key (0-9, A-F)
4. For CBC mode, optionally enter a 4-character hexadecimal IV
   - If not provided, a random IV will be generated for encryption
   - For decryption, the IV should be the first 4 characters of the ciphertext
5. Select operation mode (encrypt/decrypt)
6. Click "Process" to see the result
7. After processing, you can:
   - Export the operation details to a CSV file
   - Import a previously exported operation
8. Alternatively, select a test case and click "Apply Selected Test Case" to auto-fill the inputs

### Notes for CBC Mode
- When encrypting, if no IV is provided, a random one will be generated
- When encrypting, the result will include the IV as the first 4 characters
- When decrypting, input should include the IV as the first 4 characters
""")
