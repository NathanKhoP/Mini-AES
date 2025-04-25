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
    }
]

# Initialize session state if not already initialized
if 'input_text' not in st.session_state:
    st.session_state.input_text = ''
if 'key_text' not in st.session_state:
    st.session_state.key_text = ''

# Create two columns for input fields
col1, col2 = st.columns(2)

with col1:
    # Input text field using session state
    input_text = st.text_input("Input Text (4 hex characters)", 
                              value=st.session_state.input_text,
                              max_chars=4).strip().upper()
    st.session_state.input_text = input_text
    
    # Mode selection
    mode = st.radio("Operation Mode", 
                    ["encrypt", "decrypt"],
                    horizontal=True)

with col2:
    # Key input field using session state
    key_text = st.text_input("Key (4 hex characters)", 
                            value=st.session_state.key_text,
                            max_chars=4).strip().upper()
    st.session_state.key_text = key_text

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
        st.rerun()

# Process button
if st.button("Process"):
    error = None
    
    # Basic input validation
    if not input_text or not key_text:
        error = "Input text and key cannot be empty."
    elif len(input_text) != 4 or len(key_text) != 4:
        error = "Input text and key must be exactly 4 hexadecimal characters long."
    else:
        try:
            # Try hex conversion for validation
            int(input_text, 16)
            int(key_text, 16)
            
            # Call backend functions
            if mode == 'encrypt':
                result, error, log = mini_aes.encrypt(input_text, key_text)
            else:
                result, error, log = mini_aes.decrypt(input_text, key_text)
            
            if error:
                st.error(f"Error: {error}")
            elif result:
                st.success(f"Operation ({mode}) successful!")
                st.subheader("Result")
                st.code(result, language="text")
                
                # Display detailed log in an expander
                with st.expander("Show detailed process log"):
                    for line in log:
                        st.text(line)
                        
        except ValueError:
            error = "Input text and key must contain valid hexadecimal characters (0-9, A-F)."
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
1. Enter a 4-character hexadecimal input text (0-9, A-F)
2. Enter a 4-character hexadecimal key (0-9, A-F)
3. Select operation mode (encrypt/decrypt)
4. Click "Process" to see the result
5. Alternatively, select a test case and click "Apply Selected Test Case" to auto-fill the inputs
""")
