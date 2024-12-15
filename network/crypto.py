# -*- encoding: utf-8 -*
__all__ = [
   "Crypto"
]


import random, base64, hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class __Crypto(object):
    __instance__, __keys__ = None, (
        "MK6mipwmOUedplb6", "OtEylfId6dyhrfdn", "VNbhn5mvUaQaeOo9", "bIEoQGQYjKd02U0J",
        "fuaJrPwaH2cfXXLP", "LEkdyiroouKQ4XN1", "jM1h27H4UROu427W", "DhReQada7gZybTDk",
        "ZGXfpSTYUvcdKqdY", "AZwKf7MWZrJpGR5W", "amuvbcHw38TcSyPU", "SI4QotspbjhyFdT0",
        "VP4dhjKnDGlSJtbB", "UXDZx4KhZywQ2tcn", "NIK73ZNvNqzva4kd", "WeiW7qU766Q1YQZI"
    )

    def __new__(cls, *args: tuple[object], **kwargs: dict[str, object]) -> object:
        if cls.__instance__ is None:
            cls.__instance__ = object.__new__(cls)
        return cls.__instance__

    def __init__(self) -> None:
        pass

    def __string_split(self, string: str, step: int) -> list:
        return [string[index:index + step] for index in range(0, len(string), step)]

    def __string_left_shift(self, string: str, number: int) -> str:
        number = number % len(string)
        return string[number:] + string[:number]

    def __string_to_bin(self, string: str) -> str:
        return ''.join(format(ord(char), '08b') for char in string)

    def __bin_to_string(self, string: str) -> str:
        return ''.join(chr(int(string[index:index + 8], 2)) for index in range(0, len(string), 8))

    def __string_xor(self, string1: str, string2: str) -> list:
        if len(string1) != len(string2): raise ValueError("Lengths of strings do not match")
        return [ord(c1) ^ ord(c2) for c1, c2 in zip(string1, string2)]

    def __string_to_base64(self, string: list) -> str:
        return base64.b64encode(bytes(string)).decode()

    def __encrypt_token(self, string: str) -> str:
        return string.replace('/', 'o').replace('+', 'm')[:16] + '1'

    def __random_string(self, length: int) -> str:
        return ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length))

    def HttpEncrypt(self, raw_content: bytes) -> bytes:
        content = bytearray(raw_content) + bytearray(random.choices(range(256), k=16))
        key_index, vector = random.randint(0, 15), bytearray(random.choices(range(256), k=16))
        encrypted = AES.new(self.__keys__[key_index].encode(), AES.MODE_CBC, vector).encrypt(pad(bytes(content), 16, "pkcs7"))
        return vector + encrypted + bytes([key_index << 4 | 2])

    def HttpDecrypt(self, encrypted_content: bytes) -> bytes:
        if len(encrypted_content) < 0x12:
            raise ValueError("encrypted_content is too short")

        key_index, vector = (encrypted_content[-1] >> 4) & 0xF, encrypted_content[:16]
        return AES.new(self.__keys__[key_index].encode(), AES.MODE_CBC, vector).decrypt(encrypted_content[16:-1])

    def CalculateDynamicToken(self, url: str, content: str, token: str) -> str:
        token_md5 = hashlib.md5(token.encode()).hexdigest()
        magic_md5 = hashlib.md5((token_md5 + content + '0eGsBkhl' + url).encode()).hexdigest()
        binary_magic_md5 = self.__string_to_bin(magic_md5)
        left_shifted_binary_magic_md5 = self.__string_left_shift(binary_magic_md5, 6)
        left_shifted_magic_md5 = self.__bin_to_string(left_shifted_binary_magic_md5)
        xor_two_magic_md5 = self.__string_xor(magic_md5, left_shifted_magic_md5)
        base64_xor_two_magic_md5 = self.__string_to_base64(xor_two_magic_md5)
        return self.__encrypt_token(base64_xor_two_magic_md5)


Crypto = __Crypto()
