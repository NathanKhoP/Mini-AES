import streamlit as st
import mini_aes

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
                        
        except ValueError:
            error = "Input values must contain valid hexadecimal characters (0-9, A-F)."
            st.error(error)
        except Exception as e:
            error = f"An unexpected error occurred: {e}"
            st.error(error)
    
    if error:
        st.error(error)

# Add some helpful information at the bottom
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
7. Alternatively, select a test case and click "Apply Selected Test Case" to auto-fill the inputs

### Notes for CBC Mode
- When encrypting, if no IV is provided, a random one will be generated
- When encrypting, the result will include the IV as the first 4 characters
- When decrypting, input should include the IV as the first 4 characters
""")
