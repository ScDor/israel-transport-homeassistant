import datetime


def encrypt_key() -> str:
    key = "natan"
    return "".join(
        chr(ord(char) ^ ord(key[i % len(key)]))
        for i, char in enumerate(datetime.date.today().isoformat())
    )
