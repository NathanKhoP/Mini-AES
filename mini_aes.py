import random
import csv
from datetime import datetime
import os

# S-Box (Substitution Box) 4-bit
S_BOX = {
    0x0: 0x9, 0x1: 0x4, 0x2: 0xA, 0x3: 0xB,
    0x4: 0xD, 0x5: 0x1, 0x6: 0x8, 0x7: 0x5,
    0x8: 0x6, 0x9: 0x2, 0xA: 0x0, 0xB: 0x3,
    0xC: 0xC, 0xD: 0xE, 0xE: 0xF, 0xF: 0x7,
}
INV_S_BOX = {v: k for k, v in S_BOX.items()}

# Round Constants for Key Expansion
RCON = [
    None, # index 0 unused
    [0x1, 0x0], # RCON(1) = [01, 00] = [0x1, 0x0] -> 10000000 in GF(2^8), but we use 4 bits so [0x1, 0x0]
    [0x2, 0x0], # RCON(2) = [02, 00] = [0x2, 0x0] -> 00100000
    [0x4, 0x0], # RCON(3) = [04, 00] = [0x4, 0x0] -> 01000000
]

NUM_ROUNDS = 3

# GF(2^4) multiplication for MixColumns
def gf_multiply(a, b):
    p = 0
    for _ in range(4):
        if b & 1:
            p ^= a
        hi_bit_set = a & 0x8
        a <<= 1
        if hi_bit_set:
            a ^= 0x3 # Modulo x^4 + x + 1 -> 0b10011 -> XOR with 0011 (0x3) after shift
            a &= 0xF # Keep it 4 bits
        b >>= 1
    return p & 0xF

MIX_COL_MATRIX = [
    [0x1, 0x4],
    [0x4, 0x1]
]
INV_MIX_COL_MATRIX = [
    [0x9, 0x2],
    [0x2, 0x9]
]

# helper conversion functions
def hex_to_nibbles(hex_string):
    if not isinstance(hex_string, str) or len(hex_string) != 4:
        raise ValueError("Input hex string must be 4 characters long")
    try:
        val = int(hex_string, 16)
    except ValueError:
        raise ValueError("Input must be a valid hexadecimal string")
    nibbles = [(val >> 12) & 0xF, (val >> 8) & 0xF, (val >> 4) & 0xF, val & 0xF]
    return nibbles

def nibbles_to_matrix(nibbles):
    if len(nibbles) != 4:
        raise ValueError("Nibble list must contain 4 elements")
    return [
        [nibbles[0], nibbles[2]],
        [nibbles[1], nibbles[3]]
    ]

def matrix_to_nibbles(matrix):
    return [matrix[0][0], matrix[1][0], matrix[0][1], matrix[1][1]]

def nibbles_to_hex_word(nibbles):
    if len(nibbles) != 2:
        raise ValueError("Nibble list must contain 2 elements")
    val = (nibbles[0] << 4) | nibbles[1]
    return "{:02X}".format(val)

def nibbles_to_hex(nibbles):
    if len(nibbles) != 4:
        raise ValueError("Nibble list must contain 4 elements")
    val = (nibbles[0] << 12) | (nibbles[1] << 8) | (nibbles[2] << 4) | nibbles[3]
    return "{:04X}".format(val)

def matrix_to_hex(matrix):
    return nibbles_to_hex(matrix_to_nibbles(matrix))

def xor_nibble_lists(list1, list2):
    return [n1 ^ n2 for n1, n2 in zip(list1, list2)]

def xor_matrices(matrix1, matrix2):
    result = [[0, 0], [0, 0]]
    for r in range(2):
        for c in range(2):
            result[r][c] = matrix1[r][c] ^ matrix2[r][c]
    return result

# main Mini-AES functions
def sub_nibbles(state_matrix, sbox=S_BOX):
    new_state = [[0, 0], [0, 0]]
    for r in range(2):
        for c in range(2):
            new_state[r][c] = sbox[state_matrix[r][c]]
    return new_state

def shift_rows(state_matrix):
    new_state = [row[:] for row in state_matrix]
    new_state[1][0], new_state[1][1] = state_matrix[1][1], state_matrix[1][0]
    return new_state

def mix_columns_transform(col, matrix):
    s0, s1 = col[0], col[1]
    m = matrix
    c0 = gf_multiply(m[0][0], s0) ^ gf_multiply(m[0][1], s1)
    c1 = gf_multiply(m[1][0], s0) ^ gf_multiply(m[1][1], s1)
    return [c0, c1]

def mix_columns(state_matrix, mix_matrix=MIX_COL_MATRIX):
    new_state = [[0, 0], [0, 0]]
    for c in range(2):
        col = [state_matrix[0][c], state_matrix[1][c]]
        new_col = mix_columns_transform(col, mix_matrix)
        new_state[0][c] = new_col[0]
        new_state[1][c] = new_col[1]
    return new_state

def add_round_key(state_matrix, round_key_matrix):
    return xor_matrices(state_matrix, round_key_matrix)

def sub_word(word, sbox=S_BOX):
    return [sbox[word[0]], sbox[word[1]]]

def rot_word(word):
    return [word[1], word[0]]

def key_expansion(key_nibbles):
    log = []
    if len(key_nibbles) != 4:
        raise ValueError("Key must be 4 nibbles long")

    log.append("--- Key Expansion ---")
    initial_key_hex = nibbles_to_hex(key_nibbles)
    log.append(f"Initial Key (K): {initial_key_hex}")

    w = [
        [key_nibbles[0], key_nibbles[1]], # W0
        [key_nibbles[2], key_nibbles[3]]  # W1
    ]
    log.append(f"W[0]: {nibbles_to_hex_word(w[0])}")
    log.append(f"W[1]: {nibbles_to_hex_word(w[1])}")

    for i in range(2, 2 * (NUM_ROUNDS + 1)): # W2 to W6
        log.append(f"\nCalculating W[{i}]:")
        prev_w = w[i-1]
        log.append(f"  Prev Word W[{i-1}]: {nibbles_to_hex_word(prev_w)}")
        temp = list(prev_w)

        if i % 2 == 0: # G function applied for even i
            log.append(f"  Applying G function to W[{i-1}]...")
            # 1. RotWord
            temp_rot = rot_word(temp)
            log.append(f"    RotWord({nibbles_to_hex_word(temp)}): {nibbles_to_hex_word(temp_rot)}")
            # 2. SubWord
            temp_sub = sub_word(temp_rot, S_BOX)
            log.append(f"    SubWord({nibbles_to_hex_word(temp_rot)}): {nibbles_to_hex_word(temp_sub)}")
            # 3. XOR with RCON
            rcon_index = i // 2
            current_rcon = RCON[rcon_index]
            log.append(f"    RCON[{rcon_index}]: {nibbles_to_hex_word(current_rcon)}")
            temp_rcon_xor = list(temp_sub)
            temp_rcon_xor[0] = temp_sub[0] ^ current_rcon[0]
            temp_rcon_xor[1] = temp_sub[1] ^ current_rcon[1] 
            log.append(f"    XOR RCON: {nibbles_to_hex_word(temp_sub)} XOR {nibbles_to_hex_word(current_rcon)} = {nibbles_to_hex_word(temp_rcon_xor)}")
            temp = temp_rcon_xor

        # W[i] = W[i-2] XOR temp
        w_i_minus_2 = w[i-2]
        log.append(f"  Calculating W[{i}] = W[{i-2}] XOR temp")
        log.append(f"    W[{i-2}]: {nibbles_to_hex_word(w_i_minus_2)}")
        log.append(f"    temp:   {nibbles_to_hex_word(temp)}")
        new_word = xor_nibble_lists(w_i_minus_2, temp)
        log.append(f"    Result W[{i}]: {nibbles_to_hex_word(new_word)}")
        w.append(new_word)

    log.append("\nGenerated Words:")
    for i in range(len(w)):
        log.append(f"  W[{i}]: {nibbles_to_hex_word(w[i])}")

    # Construct round keys from W
    round_keys = []
    log.append("\nRound Keys Construction:")
    for i in range(0, len(w), 2): # RK0 uses W0,W1; RK1 uses W2,W3 etc.
        rk_index = i // 2
        w0 = w[i]
        w1 = w[i+1]
        round_key_matrix = [
            [w0[0], w1[0]],
            [w0[1], w1[1]]
        ]
        round_keys.append(round_key_matrix)
        log.append(f"  RK{rk_index} (using W[{i}], W[{i+1}]): {matrix_to_hex(round_key_matrix)}")

    log.append("--- End Key Expansion ---")
    return round_keys, log

def encrypt(plaintext_hex, key_hex):
    """
    Encrypt using ECB mode.
    plaintext_hex must be a multiple of 4 hex characters (16-bit blocks)
    """
    log = []
    log.append("--- ECB Mode Encryption ---")
    
    # Validate input length
    if len(plaintext_hex) % 4 != 0:
        return None, "Plaintext length must be a multiple of 4 hex characters (16-bit blocks)", log
    
    blocks = [plaintext_hex[i:i+4] for i in range(0, len(plaintext_hex), 4)]
    log.append(f"Split into {len(blocks)} blocks: {blocks}")
    
    ciphertext_blocks = []
    
    for i, block in enumerate(blocks):
        log.append(f"\nProcessing Block {i+1}")
        log.append(f"Current Block: {block}")
        
        try:
            # Convert inputs to nibble lists
            plain_nibbles = hex_to_nibbles(block)
            key_nibbles = hex_to_nibbles(key_hex)
            
            # Convert nibble lists to state matrix and key matrix
            state_matrix = nibbles_to_matrix(plain_nibbles)
            key_matrix = nibbles_to_matrix(key_nibbles)
            
            log.append(f"Initial State Matrix:\n{state_matrix[0]}\n{state_matrix[1]}")
            log.append(f"Key Matrix:\n{key_matrix[0]}\n{key_matrix[1]}")
            
            # Key Expansion
            round_keys, key_expansion_log = key_expansion(key_nibbles)
            log.extend("  " + line for line in key_expansion_log)
            
            # Initial AddRoundKey
            log.append("\nRound 0: Initial AddRoundKey")
            rk0 = round_keys[0]
            state_matrix = add_round_key(state_matrix, rk0)
            log.append(f"After AddRoundKey: {matrix_to_hex(state_matrix)}")
            
            # Main Rounds (1 to NUM_ROUNDS-1)
            for r in range(1, NUM_ROUNDS):
                log.append(f"\nRound {r}:")
                
                # SubNibbles
                state_matrix = sub_nibbles(state_matrix, S_BOX)
                log.append(f"After SubNibbles: {matrix_to_hex(state_matrix)}")
                
                # ShiftRows
                state_matrix = shift_rows(state_matrix)
                log.append(f"After ShiftRows: {matrix_to_hex(state_matrix)}")
                
                # MixColumns
                state_matrix = mix_columns(state_matrix, MIX_COL_MATRIX)
                log.append(f"After MixColumns: {matrix_to_hex(state_matrix)}")
                
                # AddRoundKey
                state_matrix = add_round_key(state_matrix, round_keys[r])
                log.append(f"After AddRoundKey: {matrix_to_hex(state_matrix)}")
            
            # Final Round (no MixColumns)
            log.append(f"\nRound {NUM_ROUNDS} (Final):")
            
            # SubNibbles
            state_matrix = sub_nibbles(state_matrix, S_BOX)
            log.append(f"After SubNibbles: {matrix_to_hex(state_matrix)}")
            
            # ShiftRows
            state_matrix = shift_rows(state_matrix)
            log.append(f"After ShiftRows: {matrix_to_hex(state_matrix)}")
            
            # AddRoundKey
            state_matrix = add_round_key(state_matrix, round_keys[NUM_ROUNDS])
            log.append(f"After final AddRoundKey: {matrix_to_hex(state_matrix)}")
            
            cipher_block = matrix_to_hex(state_matrix)
            ciphertext_blocks.append(cipher_block)
            log.append(f"Block {i+1} Result: {cipher_block}")
            
        except ValueError as e:
            return None, str(e), log
        except Exception as e:
            return None, f"Unexpected error in block {i+1}: {str(e)}", log
    
    final_ciphertext = "".join(ciphertext_blocks)
    log.append(f"\nFinal ciphertext (all blocks): {final_ciphertext}")
    return final_ciphertext, None, log

def decrypt(ciphertext_hex, key_hex):
    """
    Decrypt using ECB mode.
    ciphertext_hex must be a multiple of 4 hex characters (16-bit blocks)
    """
    log = []
    log.append("--- ECB Mode Decryption ---")
    
    # Validate input length
    if len(ciphertext_hex) % 4 != 0:
        return None, "Ciphertext length must be a multiple of 4 hex characters (16-bit blocks)", log
    
    blocks = [ciphertext_hex[i:i+4] for i in range(0, len(ciphertext_hex), 4)]
    log.append(f"Split into {len(blocks)} blocks: {blocks}")
    
    plaintext_blocks = []
    
    for i, block in enumerate(blocks):
        log.append(f"\nProcessing Block {i+1}")
        log.append(f"Current Block: {block}")
        
        try:
            # Convert inputs to nibble lists
            cipher_nibbles = hex_to_nibbles(block)
            key_nibbles = hex_to_nibbles(key_hex)
            
            # Convert nibble lists to state matrix and key matrix
            state_matrix = nibbles_to_matrix(cipher_nibbles)
            key_matrix = nibbles_to_matrix(key_nibbles)
            
            log.append(f"Initial State Matrix:\n{state_matrix[0]}\n{state_matrix[1]}")
            log.append(f"Key Matrix:\n{key_matrix[0]}\n{key_matrix[1]}")
            
            # Key Expansion
            round_keys, key_expansion_log = key_expansion(key_nibbles)
            log.extend("  " + line for line in key_expansion_log)
            
            # Initial AddRoundKey with last round key
            log.append(f"\nRound 0: Initial AddRoundKey with RK{NUM_ROUNDS}")
            state_matrix = add_round_key(state_matrix, round_keys[NUM_ROUNDS])
            log.append(f"After AddRoundKey: {matrix_to_hex(state_matrix)}")
            
            # First Round - Special Case (no MixColumns)
            log.append("\nRound 1:")
            
            # Inverse ShiftRows
            state_matrix = shift_rows(state_matrix)  # ShiftRows is its own inverse
            log.append(f"After InvShiftRows: {matrix_to_hex(state_matrix)}")
            
            # Inverse SubNibbles
            state_matrix = sub_nibbles(state_matrix, INV_S_BOX)
            log.append(f"After InvSubNibbles: {matrix_to_hex(state_matrix)}")
            
            # AddRoundKey with second-to-last round key
            state_matrix = add_round_key(state_matrix, round_keys[NUM_ROUNDS-1])
            log.append(f"After AddRoundKey: {matrix_to_hex(state_matrix)}")
            
            # Main Rounds (NUM_ROUNDS-2 down to 0)
            for r in range(NUM_ROUNDS-2, -1, -1):
                log.append(f"\nRound {NUM_ROUNDS-r}:")
                
                # Inverse MixColumns
                state_matrix = mix_columns(state_matrix, INV_MIX_COL_MATRIX)
                log.append(f"After InvMixColumns: {matrix_to_hex(state_matrix)}")
                
                # Inverse ShiftRows
                state_matrix = shift_rows(state_matrix)
                log.append(f"After InvShiftRows: {matrix_to_hex(state_matrix)}")
                
                # Inverse SubNibbles
                state_matrix = sub_nibbles(state_matrix, INV_S_BOX)
                log.append(f"After InvSubNibbles: {matrix_to_hex(state_matrix)}")
                
                # AddRoundKey
                state_matrix = add_round_key(state_matrix, round_keys[r])
                log.append(f"After AddRoundKey: {matrix_to_hex(state_matrix)}")
            
            plain_block = matrix_to_hex(state_matrix)
            plaintext_blocks.append(plain_block)
            log.append(f"Block {i+1} Result: {plain_block}")
            
        except ValueError as e:
            return None, str(e), log
        except Exception as e:
            return None, f"Unexpected error in block {i+1}: {str(e)}", log
    
    final_plaintext = "".join(plaintext_blocks)
    log.append(f"\nFinal plaintext (all blocks): {final_plaintext}")
    return final_plaintext, None, log

def generate_iv():
    """Generate a random 16-bit (4 hex characters) initialization vector."""
    return "{:04X}".format(random.randint(0, 0xFFFF))

def encrypt_cbc(plaintext_hex, key_hex, iv_hex=None):
    """
    Encrypt using CBC mode.
    plaintext_hex must be a multiple of 4 hex characters (16-bit blocks)
    """
    if not iv_hex:
        iv_hex = generate_iv()
    
    log = []
    log.append("--- CBC Mode Encryption ---")
    log.append(f"IV: {iv_hex}")
    
    # Validate input length
    if len(plaintext_hex) % 4 != 0:
        return None, "Plaintext length must be a multiple of 4 hex characters (16-bit blocks)", log
    
    blocks = [plaintext_hex[i:i+4] for i in range(0, len(plaintext_hex), 4)]
    log.append(f"Split into {len(blocks)} blocks: {blocks}")
    
    previous_block = iv_hex
    ciphertext_blocks = []
    
    for i, block in enumerate(blocks):
        log.append(f"\nProcessing Block {i+1}")
        log.append(f"Current Block: {block}")
        log.append(f"Previous Block (IV for first block): {previous_block}")
        
        # XOR with previous ciphertext (or IV for first block)
        xored_block = "{:04X}".format(int(block, 16) ^ int(previous_block, 16))
        log.append(f"After XOR with previous block: {xored_block}")
        
        # Encrypt the XORed block
        cipher_block, err, block_log = encrypt(xored_block, key_hex)
        if err:
            return None, f"Error in block {i+1}: {err}", log
            
        log.append("Block encryption log:")
        log.extend("  " + line for line in block_log)
        
        ciphertext_blocks.append(cipher_block)
        previous_block = cipher_block
    
    final_ciphertext = iv_hex + "".join(ciphertext_blocks)
    log.append(f"\nFinal ciphertext (IV + encrypted blocks): {final_ciphertext}")
    return final_ciphertext, None, log

def decrypt_cbc(ciphertext_hex, key_hex):
    """
    Decrypt using CBC mode.
    First 4 characters of ciphertext_hex are the IV.
    Rest must be a multiple of 4 hex characters (16-bit blocks)
    """
    log = []
    log.append("--- CBC Mode Decryption ---")
    
    if len(ciphertext_hex) < 8:  # Need at least IV (4) + one block (4)
        return None, "Ciphertext too short. Need at least IV (4 chars) + one block (4 chars)", log
    
    # Extract IV and ciphertext blocks
    iv_hex = ciphertext_hex[:4]
    ciphertext = ciphertext_hex[4:]
    log.append(f"IV: {iv_hex}")
    
    if len(ciphertext) % 4 != 0:
        return None, "Ciphertext length (excluding IV) must be a multiple of 4 hex characters", log
    
    blocks = [ciphertext[i:i+4] for i in range(0, len(ciphertext), 4)]
    log.append(f"Split into {len(blocks)} blocks: {blocks}")
    
    previous_block = iv_hex
    plaintext_blocks = []
    
    for i, block in enumerate(blocks):
        log.append(f"\nProcessing Block {i+1}")
        log.append(f"Encrypted Block: {block}")
        log.append(f"Previous Block (IV for first block): {previous_block}")
        
        # Decrypt the block
        decrypted_block, err, block_log = decrypt(block, key_hex)
        if err:
            return None, f"Error in block {i+1}: {err}", log
            
        log.append("Block decryption log:")
        log.extend("  " + line for line in block_log)
        
        # XOR with previous ciphertext (or IV for first block)
        plain_block = "{:04X}".format(int(decrypted_block, 16) ^ int(previous_block, 16))
        log.append(f"After XOR with previous block: {plain_block}")
        
        plaintext_blocks.append(plain_block)
        previous_block = block
    
    final_plaintext = "".join(plaintext_blocks)
    log.append(f"\nFinal plaintext: {final_plaintext}")
    return final_plaintext, None, log

def export_to_csv(mode, cipher_mode, input_text, key, iv, output, log, filename=None):
    """
    Export encryption/decryption operation details to a CSV file.
    Args:
        mode (str): 'Encrypt' or 'Decrypt'
        cipher_mode (str): 'ECB' or 'CBC'
        input_text (str): Input text (plaintext or ciphertext)
        key (str): Encryption/decryption key
        iv (str): Initialization vector (for CBC mode)
        output (str): Output text (ciphertext or plaintext)
        log (list): Process log
        filename (str, optional): Custom filename. If None, generates timestamp-based name
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mini_aes_{mode.lower()}_{cipher_mode.lower()}_{timestamp}.csv"
    
    # Create 'logs' directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    filepath = os.path.join('logs', filename)
    
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write operation details
        writer.writerow(['Operation Type', mode])
        writer.writerow(['Cipher Mode', cipher_mode])
        writer.writerow(['Input Text', input_text])
        writer.writerow(['Key', key])
        if iv:
            writer.writerow(['IV', iv])
        writer.writerow(['Output', output])
        writer.writerow([])  # Empty row as separator
        writer.writerow(['Process Log'])
        for line in log:
            writer.writerow([line])
    
    return filepath

def import_from_csv(filepath):
    """
    Import encryption/decryption operation details from a CSV file.
    Returns:
        dict: Dictionary containing operation details and log
    """
    try:
        with open(filepath, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            
            # Read operation details
            operation = {}
            log_started = False
            log_lines = []
            
            for row in reader:
                if not row:  # Skip empty rows
                    continue
                
                if row[0] == 'Process Log':
                    log_started = True
                    continue
                
                if log_started:
                    log_lines.append(row[0])
                else:
                    operation[row[0]] = row[1]
            
            operation['Process Log'] = log_lines
            return operation
            
    except Exception as e:
        return None, f"Error reading CSV file: {str(e)}"

# Update test cases
if __name__ == "__main__":
    print("--- Mini-AES Test Cases ---")

    # Test Case 1: Contoh dari beberapa sumber S-AES
    plaintext1 = "6F6B"
    key1 = "A73B"
    # Expected ciphertext bisa bervariasi tergantung S-Box dan MixCol Matrix
    # Mari kita jalankan enkripsi dan lihat hasilnya, lalu gunakan itu untuk tes dekripsi
    print(f"\nTest Case 1:")
    print(f"Plaintext: {plaintext1}")
    print(f"Key: {key1}")
    ciphertext1, err1_enc, log1_enc = encrypt(plaintext1, key1)
    if err1_enc:
        print(f"Encryption Error: {err1_enc}")
    else:
        print(f"Calculated Ciphertext: {ciphertext1}")
        print("\n--- Encryption Log ---")
        for line in log1_enc: print(line)

        # Dekripsi
        print(f"\n--- Starting Decryption for Test Case 1 ---")
        decrypted1, err1_dec, log1_dec = decrypt(ciphertext1, key1)
        if err1_dec:
            print(f"Decryption Error: {err1_dec}")
        else:
            print(f"\nDecrypted Plaintext: {decrypted1}")
            print(f"Original Plaintext: {plaintext1}")
            print("\n--- Decryption Log ---")
            for line in log1_dec: print(line)
            assert decrypted1 == plaintext1
            print("\nAssertion Passed: Decrypted text matches original plaintext.")

    # Test Case 2: Plaintext dan Key Nol
    plaintext2 = "0000"
    key2 = "0000"
    print(f"\n\n{'='*20} Test Case 2 {'='*20}")
    print(f"Plaintext: {plaintext2}")
    print(f"Key: {key2}")
    ciphertext2, err2_enc, log2_enc = encrypt(plaintext2, key2)
    if err2_enc: print(f"Encryption Error: {err2_enc}")
    else:
        print(f"Calculated Ciphertext: {ciphertext2}")
        print("\n--- Encryption Log ---")
        for line in log2_enc: print(line)
        print(f"\n--- Starting Decryption for Test Case 2 ---")
        decrypted2, err2_dec, log2_dec = decrypt(ciphertext2, key2)
        if err2_dec: print(f"Decryption Error: {err2_dec}")
        else:
            print(f"\nDecrypted Plaintext: {decrypted2}")
            print("\n--- Decryption Log ---")
            for line in log2_dec: print(line)
            assert decrypted2 == plaintext2
            print("\nAssertion Passed: Decrypted text matches original plaintext.")

    # Test Case 3: Plaintext dan Key 'F'
    plaintext3 = "FFFF"
    key3 = "FFFF"
    print(f"\n\n{'='*20} Test Case 3 {'='*20}")
    print(f"Plaintext: {plaintext3}")
    print(f"Key: {key3}")
    ciphertext3, err3_enc, log3_enc = encrypt(plaintext3, key3)
    if err3_enc: print(f"Encryption Error: {err3_enc}")
    else:
        print(f"Calculated Ciphertext: {ciphertext3}")
        print("\n--- Encryption Log ---")
        for line in log3_enc: print(line)
        print(f"\n--- Starting Decryption for Test Case 3 ---")
        decrypted3, err3_dec, log3_dec = decrypt(ciphertext3, key3)
        if err3_dec: print(f"Decryption Error: {err3_dec}")
        else:
            print(f"\nDecrypted Plaintext: {decrypted3}")
            print("\n--- Decryption Log ---")
            for line in log3_dec: print(line)
            assert decrypted3 == plaintext3
            print("\nAssertion Passed: Decrypted text matches original plaintext.")

    # Additional Multi-Block ECB Test
    print("\n=== Multi-Block ECB Mode Test ===")
    key = "A73B"
    plaintext = "6F6B2D3B"  # Two blocks
    
    print(f"Multi-Block ECB Encryption Test:")
    print(f"Plaintext: {plaintext}")
    print(f"Key: {key}")
    
    ciphertext, err_enc, log_enc = encrypt(plaintext, key)
    if err_enc:
        print(f"ECB Encryption Error: {err_enc}")
    else:
        print(f"ECB Ciphertext: {ciphertext}")
        print("\n--- ECB Encryption Log ---")
        for line in log_enc: print(line)
        
        print(f"\nMulti-Block ECB Decryption Test:")
        decrypted, err_dec, log_dec = decrypt(ciphertext, key)
        if err_dec:
            print(f"ECB Decryption Error: {err_dec}")
        else:
            print(f"ECB Decrypted: {decrypted}")
            print("\n--- ECB Decryption Log ---")
            for line in log_dec: print(line)
            assert decrypted == plaintext
            print("\nECB Multi-Block Assertion Passed: Decrypted text matches original plaintext.")