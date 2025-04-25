# mini_aes.py

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
    log = []
    try:
        plain_nibbles = hex_to_nibbles(plaintext_hex)
        key_nibbles = hex_to_nibbles(key_hex)
    except ValueError as e:
        return None, str(e), [f"Error: {e}"]

    # Key Expansion
    try:
        round_keys, key_expansion_log = key_expansion(key_nibbles)
        log.extend(key_expansion_log)
    except ValueError as e:
        return None, str(e), [f"Key Expansion Error: {e}"]

    log.append("\n--- Encryption Process ---")
    log.append(f"Plaintext (Hex): {plaintext_hex}")
    state_matrix = nibbles_to_matrix(plain_nibbles)
    log.append(f"Initial State (Matrix):\n{state_matrix[0]}\n{state_matrix[1]} -> Hex: {matrix_to_hex(state_matrix)}")
    log.append("-" * 20)

    # Initial ARK with RK0
    log.append(f"Round 0: Pre-round Transformation")
    rk0 = round_keys[0]
    log.append(f"  Round Key RK0: {matrix_to_hex(rk0)}")
    state_matrix = add_round_key(state_matrix, rk0)
    log.append(f"  Result after AddRoundKey(RK0): {matrix_to_hex(state_matrix)}")

    # Rounds 1 to NUM_ROUNDS - 1 (Round 1 and 2)
    for r in range(1, NUM_ROUNDS):
        log.append(f"\n--- Round {r} ---")
        round_start_state_hex = matrix_to_hex(state_matrix)

        # SB
        log.append(f"  Input to SubNibbles: {round_start_state_hex}")
        state_matrix = sub_nibbles(state_matrix, S_BOX)
        log.append(f"  Output of SubNibbles: {matrix_to_hex(state_matrix)}")

        # SR
        log.append(f"  Input to ShiftRows: {matrix_to_hex(state_matrix)}")
        state_matrix = shift_rows(state_matrix)
        log.append(f"  Output of ShiftRows: {matrix_to_hex(state_matrix)}")

        # MC
        log.append(f"  Input to MixColumns: {matrix_to_hex(state_matrix)}")
        state_matrix = mix_columns(state_matrix, MIX_COL_MATRIX)
        log.append(f"  Output of MixColumns: {matrix_to_hex(state_matrix)}")

        # ARK
        log.append(f"  Input to AddRoundKey: {matrix_to_hex(state_matrix)}")
        current_round_key = round_keys[r]
        log.append(f"  Round Key RK{r}: {matrix_to_hex(current_round_key)}")
        state_matrix = add_round_key(state_matrix, current_round_key)
        log.append(f"  Output of AddRoundKey(RK{r}) (End of Round {r}): {matrix_to_hex(state_matrix)}")

    # Final Round (Round 3) - No MC
    log.append(f"\n--- Round {NUM_ROUNDS} (Final) ---")
    final_round_start_state_hex = matrix_to_hex(state_matrix)

    # SB
    log.append(f"  Input to SubNibbles: {final_round_start_state_hex}")
    state_matrix = sub_nibbles(state_matrix, S_BOX)
    log.append(f"  Output of SubNibbles: {matrix_to_hex(state_matrix)}")

    # SR
    log.append(f"  Input to ShiftRows: {matrix_to_hex(state_matrix)}")
    state_matrix = shift_rows(state_matrix)
    log.append(f"  Output of ShiftRows: {matrix_to_hex(state_matrix)}")

    # ARK with RK3
    log.append(f"  Input to AddRoundKey: {matrix_to_hex(state_matrix)}")
    final_round_key = round_keys[NUM_ROUNDS]
    log.append(f"  Round Key RK{NUM_ROUNDS}: {matrix_to_hex(final_round_key)}")
    state_matrix = add_round_key(state_matrix, final_round_key)
    log.append(f"  Output of AddRoundKey(RK{NUM_ROUNDS}) (Final State): {matrix_to_hex(state_matrix)}")

    ciphertext_hex = matrix_to_hex(state_matrix)
    log.append("-" * 20)
    log.append(f"Final Ciphertext (Hex): {ciphertext_hex}")
    log.append("--- End Encryption ---")

    return ciphertext_hex, None, log

def decrypt(ciphertext_hex, key_hex):
    log = []
    try:
        cipher_nibbles = hex_to_nibbles(ciphertext_hex)
        key_nibbles = hex_to_nibbles(key_hex)
    except ValueError as e:
        return None, str(e), [f"Error: {e}"]

    # Key Expansion
    try:
        round_keys, _ = key_expansion(key_nibbles)
        # Optional: log.extend(key_expansion_log)
        log.append("--- Key Expansion Ran (details omitted in decryption log, see encryption) ---")
        log.append(f"Round Keys (Hex): {[matrix_to_hex(rk) for rk in round_keys]}") # Tampilkan keys yg digunakan
    except ValueError as e:
        return None, str(e), [f"Key Expansion Error: {e}"]

    log.append("\n--- Decryption Process ---")
    log.append(f"Ciphertext (Hex): {ciphertext_hex}")
    state_matrix = nibbles_to_matrix(cipher_nibbles)
    log.append(f"Initial State (Ciphertext Matrix):\n{state_matrix[0]}\n{state_matrix[1]} -> Hex: {matrix_to_hex(state_matrix)}")
    log.append("-" * 20)

    # Inverse Final Round (Round 3)
    log.append(f"\n--- Inverse Round {NUM_ROUNDS} ---")
    inv_round_3_start_hex = matrix_to_hex(state_matrix)

    # Inverse ARK with RK3
    log.append(f"  Input to InvAddRoundKey: {inv_round_3_start_hex}")
    final_round_key = round_keys[NUM_ROUNDS]
    log.append(f"  Round Key RK{NUM_ROUNDS}: {matrix_to_hex(final_round_key)}")
    state_matrix = add_round_key(state_matrix, final_round_key) # XOR is its own inverse
    log.append(f"  Output of InvAddRoundKey(RK{NUM_ROUNDS}): {matrix_to_hex(state_matrix)}")

    # Inverse SR
    log.append(f"  Input to InvShiftRows: {matrix_to_hex(state_matrix)}")
    state_matrix = shift_rows(state_matrix) # Inverse ShiftRows sama dengan ShiftRows
    log.append(f"  Output of InvShiftRows: {matrix_to_hex(state_matrix)}")

    # Inverse SB
    log.append(f"  Input to InvSubNibbles: {matrix_to_hex(state_matrix)}")
    state_matrix = sub_nibbles(state_matrix, INV_S_BOX)
    log.append(f"  Output of InvSubNibbles (End of Inv Round {NUM_ROUNDS}): {matrix_to_hex(state_matrix)}")

    # Inverse Rounds NUM_ROUNDS - 1 down to 1 (Round 2 and 1)
    for r in range(NUM_ROUNDS - 1, 0, -1):
        log.append(f"\n--- Inverse Round {r} ---")
        inv_round_r_start_hex = matrix_to_hex(state_matrix)

        # Inverse ARK
        log.append(f"  Input to InvAddRoundKey: {inv_round_r_start_hex}")
        current_round_key = round_keys[r]
        log.append(f"  Round Key RK{r}: {matrix_to_hex(current_round_key)}")
        state_matrix = add_round_key(state_matrix, current_round_key)
        log.append(f"  Output of InvAddRoundKey(RK{r}): {matrix_to_hex(state_matrix)}")

        # Inverse MC
        log.append(f"  Input to InvMixColumns: {matrix_to_hex(state_matrix)}")
        state_matrix = mix_columns(state_matrix, INV_MIX_COL_MATRIX)
        log.append(f"  Output of InvMixColumns: {matrix_to_hex(state_matrix)}")

        # Inverse SR
        log.append(f"  Input to InvShiftRows: {matrix_to_hex(state_matrix)}")
        state_matrix = shift_rows(state_matrix) # Inverse sama
        log.append(f"  Output of InvShiftRows: {matrix_to_hex(state_matrix)}")

        # Inverse SB
        log.append(f"  Input to InvSubNibbles: {matrix_to_hex(state_matrix)}")
        state_matrix = sub_nibbles(state_matrix, INV_S_BOX)
        log.append(f"  Output of InvSubNibbles (End of Inv Round {r}): {matrix_to_hex(state_matrix)}")

    # Inverse Initial ARK with RK0
    log.append(f"\n--- Inverse Round 0 ---")
    log.append(f"  Input to InvAddRoundKey: {matrix_to_hex(state_matrix)}")
    rk0 = round_keys[0]
    log.append(f"  Round Key RK0: {matrix_to_hex(rk0)}")
    state_matrix = add_round_key(state_matrix, rk0)
    log.append(f"  Output of InvAddRoundKey(RK0) (Final State): {matrix_to_hex(state_matrix)}")

    plaintext_hex = matrix_to_hex(state_matrix)
    log.append("-" * 20)
    log.append(f"Final Decrypted Plaintext (Hex): {plaintext_hex}")
    log.append("--- End Decryption ---")

    return plaintext_hex, None, log

# Test cases for Mini-AES
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