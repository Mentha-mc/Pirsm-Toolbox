# -*- encoding: utf-8 -*
__all__ = [
   "login",
    "DeveloperModuleIterator"
]


from .crypto import Crypto
import json, requests


class LoginError(Exception):
    def __init__(self, message: str) -> None:
        self.__message = message

    def __str__(self) -> str:
        return f"LoginError: {self.__message}"


class NetEaseClientProxy(object):
    def __init__(self, sauth: str) -> None:
        self.__sauth = sauth
        self.__user_id, self.__user_token = self.__login()

    @property
    def user_id(self) -> str:
        return self.__user_id

    @property
    def __release_server(self):
        return requests.get(
            url="https://x19.update.netease.com/serverlist/release.json",
            headers={
                "User-Agent": "WPFLauncher/0.0.0.0"
            }
        ).json()

    def __request_login_otp(self) -> dict:
        return requests.post(f"{self.__release_server["CoreServerUrl"]}/login-otp", self.__sauth).json()

    def __request_auth_otp(self, login_otp_response: dict) -> dict:
        request_data = json.dumps(
            {
                "version": {
                    "version": "0.0.0.0",
                    "launcher_md5": "",
                    "updater_md5": ""
                },
                "aid": str(login_otp_response["entity"]["aid"]),
                "otp_token": login_otp_response["entity"]["otp_token"],
                "sauth_json": json.loads(self.__sauth)["sauth_json"],
                "sa_data": '{"os_name": "windows", "os_ver": "Microsoft Windows 11", "mac_addr": "A11CF42FB51B", "udid": "3yiz0tEs+~", "app_ver": "0.0.0.0", "sdk_ver": "", "network": "", "disk": "613c0780", "is64bit": "1", "video_card1": "Nvidia RTX 4090", "video_card2": "", "video_card3": "", "video_card4": "", "launcher_type": "PC_java", "pay_channel": "netease"}',
                "sdkuid": None,
                "hasMessage": False,
                "hasGmail": False,
                "otp_pwd": None,
                "lock_time": 0,
                "env": None,
                "min_engine_version": None,
                "min_patch_version": None,
                "verify_status": 0,
                "unisdk_login_json": None,
                "token": None,
                "is_register": False,
                "entity_id": None
            }
        )
        decrypted_response = Crypto.HttpDecrypt(requests.post(
            url=f"{self.__release_server["CoreServerUrl"]}/authentication-otp",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "WPFLauncher/0.0.0.0",
                "user-id": "",
                "user-token": Crypto.CalculateDynamicToken("/authentication-otp", request_data, "")
            },
            data=Crypto.HttpEncrypt(request_data.encode())
        ).content)
        return json.loads(decrypted_response[:decrypted_response.find(b"}}") + 2])

    def __login(self) -> tuple[str, str]:
        login_otp_response = self.__request_login_otp()
        if login_otp_response["code"] != 0: raise LoginError("login-otp response error")

        auth_otp_response = self.__request_auth_otp(login_otp_response)
        if auth_otp_response["code"] != 0: raise LoginError("auth-otp response error")

        return auth_otp_response["entity"]["entity_id"], auth_otp_response["entity"]["token"]

    def simple_request(self, method: str, url: str, headers: dict = {}, **kwargs: dict[str, object]) -> requests.Response:
        return requests.request(
            method=method,
            url=url,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "WPFLauncher/0.0.0.0",
                **headers
            },
            **kwargs
        )

    def x19_request(self, method: str, url: str, api: str, headers: dict = {}, json: dict = {}) -> requests.Response:
        return requests.request(
            method=method,
            url=url + api,
            json=json,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "WPFLauncher/0.0.0.0",
                "user-id": self.__user_id,
                "user-token": Crypto.CalculateDynamicToken(api, __import__("json").dumps(json), self.__user_token),
                **headers
            }
        )

    def __load_encrypt_json(self, string: str) -> dict:
        length, layer = len(string), 0
        for index in range(0, length):
            if string[index] == "{":
                layer += 1

            elif string[index] == "}":
                layer -= 1

            if layer == 0:
                return json.loads(string[:index + 1])

    def x19_encrypt_request(self, method: str, url: str, api: str, json: dict = {}) -> dict:
        return self.__load_encrypt_json(Crypto.HttpDecrypt(requests.Session().send(requests.Request(
            method=method,
            url=url + api,
            headers={
                "Content-Type": "application/_json; charset=utf-8",
                "User-Agent": "WPFLauncher/0.0.0.0",
                "user-id": self.__user_id,
                "user-token": Crypto.CalculateDynamicToken(api, __import__("json").dumps(json), self.__user_token)
            },
            data=Crypto.HttpEncrypt(bytes(__import__("json").dumps(json).encode())),
        ).prepare()).content).decode("unicode_escape"))


def login(sauth: str) -> NetEaseClientProxy:
    return NetEaseClientProxy(sauth)


class DeveloperModuleIterator(object):
    def __init__(self, proxy: NetEaseClientProxy, developer_id: int, start: int = 0, types: tuple[int] = (2, )) -> None:
        self.__proxy, self.__developer_id, self.__current, self.__total, self.__types = proxy, developer_id, start, 0xFFF, types

    def __iter__(self) -> object:
        return self

    def __next__(self) -> tuple[int, str, str]:
        while True:
            if self.__current >= self.__total:
                raise StopIteration

            response = self.__proxy.x19_request(
                method="post",
                url="https://g79mclobt.minecraft.cn",
                api="/pe-developer-homepage/load_items_by_developer_info_id",
                json={
                    "channel_id": 5,
                    "length": 1,
                    "developer_info_id": self.__developer_id,
                    "offset": self.__current
                }
            ).json()

            self.__current += 1
            self.__total = response["total"]
            if response["entities"][0]["first_type"] in self.__types:
                return self.__current, response["entities"][0]["item_id"], response["entities"][0]["res_name"]
