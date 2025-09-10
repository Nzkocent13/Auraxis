# generate_key.py
import secrets
import string
import hashlib

def gen_key(length=17):
    alphabet = string.ascii_uppercase + string.digits  # uniquement majuscules + chiffres
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def sha256_hex(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

if __name__ == "__main__":
    key = gen_key(17)
    h = sha256_hex(key)
    print("Clé générée :", key)
    print("SHA256 de la clé :", h)
    print()
    print("Copie ces deux valeurs dans ton script :")
    print(f'EMBEDDED_KEY = "{key}"')
    print(f'EXPECTED_KEY_HASH = "{h}"')
