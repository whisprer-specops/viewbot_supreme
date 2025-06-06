from core.encryption import generate_key, encrypt, decrypt

def test_encrypt_decrypt():
    key = generate_key()
    msg = "hello fren"
    token = encrypt(msg, key)
    result = decrypt(token, key)
    assert result == msg
