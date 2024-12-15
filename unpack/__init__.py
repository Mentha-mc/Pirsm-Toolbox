# -*- encoding: utf-8 -*
__all__ = [
   "Crypto"
]


from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os, zipfile, shutil, io, json


class DecryptError(Exception):
    def __init__(self, message: str) -> None:
        self.__message = message

    def __str__(self) -> str:
        return f"DecryptError: {self.__message}"


class __Crypto(object):
    __instance__ = None

    def __new__(cls, *args: tuple[object], **kwargs: dict[str, object]) -> object:
        if cls.__instance__ is None:
            cls.__instance__ = object.__new__(cls)
        return cls.__instance__

    def __init__(self) -> None:
        pass

    def __decrypt(self, path: str, key: str, uuid: str) -> None:
        with open(path, "rb") as istream:
            content = istream.read()

        try:
            if content[4:40].decode() != uuid:
                raise DecryptError("uuid error")

            content = content[64:]
            length = len(content)

            if length & 0b1111:
                content += bytes([0] * (16 - (length & 0b1111)))

            content = AES.new(key.encode("ascii"), AES.MODE_CFB, iv=key.encode("ascii")).decrypt(content)[:length]
        except Exception as exception:
            pass

        os.remove(path)
        try:
            with zipfile.ZipFile(io.BytesIO(content), "r") as istream:
                istream.extractall(os.path.dirname(path))
        except Exception as exception:
            with open(path, "wb") as ostream:
                ostream.write(content)

    def __format_json(self, path: str) -> None:
        with open(path, "r") as istream:
            content = json.loads(istream.read())

        with open(path, "w") as ostream:
            ostream.write(json.dumps(content, indent=4, separators=(',', ': ')))

    def __find_files(self, directory: str, extension: str) -> list[str]:
        matching_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(extension):
                    matching_files.append(os.path.join(root, file))
        return matching_files

    def __decrypt_all(self, directory: str, key: str, uuid: str) -> None:
        for extension in (".mergedmcs", ".mczip", ".png", ".lang"):
            for path in self.__find_files(directory, extension):
                try:
                    self.__decrypt(path, key, uuid)
                except Exception as exception:
                    pass

        for json_path in self.__find_files(directory, ".json"):
            try:
                self.__format_json(json_path)
            except Exception as exception:
                pass

    def DecryptZip(self, path: str, key: str, uuid: str, decrypted_path: str) -> str:
        with zipfile.ZipFile(path, "r") as istream:
            istream.extractall(f"{decrypted_path}\\temp")

        item_directory = os.listdir(f"{decrypted_path}\\temp")[0]
        if os.path.exists(f"{decrypted_path}\\{item_directory}"):
            shutil.rmtree(f"{decrypted_path}\\{item_directory}")
        shutil.move(f"{decrypted_path}\\temp\\{item_directory}", f"{decrypted_path}")
        shutil.rmtree(f"{decrypted_path}\\temp")

        self.__decrypt_all(f"{decrypted_path}\\{item_directory}", key, uuid)
        return f"{decrypted_path}\\{item_directory}"


Crypto = __Crypto()
