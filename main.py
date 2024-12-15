import sys
import os
import base64
import json
from colorama import init, Fore, Style
import network
import unpack
import shutil
import yaml
import io
import urllib3
import re
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QDialog
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import Qt
from PyQt6 import uic
from datetime import datetime
import sys
from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6 import uic
from colorama import init, Fore, Style
import network
import unpack
import shutil
import yaml
import io
import urllib3
import re
from datetime import datetime
from PyQt6 import uic, QtWidgets
from PyQt6.QtWidgets import QApplication, QDialog, QToolButton, QLineEdit, QDialogButtonBox, QVBoxLayout, QPushButton, QMessageBox
from PyQt6 import QtCore, QtGui, QtWidgets
# 禁用不安全请求的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)
from PyQt6.QtCore import QThread, pyqtSignal
class Worker(QThread):
    progress_signal = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super(Worker, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result = self.func(*self.args, **self.kwargs)
        self.progress_signal.emit(result)



# 加载账户配置
try:
    with open("C:/Users/Mentha/Downloads/ecd/account.yml", "rb") as istream:
        account = yaml.load(istream, yaml.FullLoader)["accounts"]["716457034"]["sauth"]
    print(f"{Fore.GREEN}账户加载成功。{Style.RESET_ALL}")
except Exception as e:
    print(f"{Fore.RED}加载账户失败：{e}{Style.RESET_ALL}")

from PyQt6.QtCore import QObject, pyqtSignal

class Downloader(QObject):
    update_output = pyqtSignal(str)  # 定义一个信号
    def __init__(self, sauth: str, device_id: str = "c95f0134ae6042a3b851e269a0631f10"):
        super().__init__()  # 调用 QObject 的构造函数
        self.__proxy, self.__device_id = network.login(sauth), device_id
        update_output = pyqtSignal(list)
        self.update_output.emit(f"Downloader初始化完成{Style.RESET_ALL}")
        self.update_output.emit(f"欢迎使用 NetEase Toolbox{Style.RESET_ALL}")

    def get_proxy(self):
        """获取代理对象"""
        return self.__proxy

    def __convert_key(self, key: str) -> str:
        """转换密钥"""
        text = "TG8hVJD3Lt1r86Cv" + self.__proxy.user_id + self.__device_id
        length, text, key = len(text), text.encode("utf-8"), bytearray(base64.b64decode(key))
        for index in range(0, length):
            key[index % 16] ^= text[index]
        return key.decode("ascii")

    def __get_download_url(self, item_ids: list[str]) -> dict[str, str]:
        """获取项目ID列表的下载URL"""
        try:
            result = dict()
            self.update_output.emit(f"正在获取项目ID列表的下载URL：{item_ids}")
            for item_info in self.get_proxy().x19_request(
                method="post",
                url="https://g79mclobtgray.nie.netease.com",
                api="/pe-item/query/search-lobby-by-id-list",
                json={
                    "device_id": self.__device_id,
                    "item_ids": item_ids
                }
            ).json()["entities"]:
                result[item_info["iid"]] = item_info["lobby_res_url"]
            return result
        except Exception as exception:
            self.update_output.emit(f"{Fore.RED}获取下载URL时出错：{exception}")
            return {}

    def __get_key_and_uuid(self, item_ids: list[str]) -> dict[str, tuple[str, str]]:
        """获取项目ID列表的密钥和UUID"""
        try:
            result = dict()
            self.update_output.emit(f"正在获取项目ID列表的密钥和UUID：{item_ids}")
            for item_info in self.get_proxy().x19_encrypt_request(
                method="post",
                url="https://x19apigatewayobt.nie.netease.com",
                api="/pe-item/get-encryption-key-list",
                json={
                    "device_id": self.__device_id,
                    "item_ids": item_ids
                }
            )["entities"]:
                content = json.loads(base64.b64decode(item_info["jwt"][37:].split(".", 1)[0]).decode("ascii"))
                result[item_info["item_id"]] = (self.__convert_key(content["contentKey"]), content["contentUuid"])
            
            return result
        except Exception as exception:
            self.update_output.emit(f"{Fore.RED}获取密钥和UUID时出错：{exception}")
            raise

    def developer_modules(self, developer_id: int, start: int = 0, types: tuple[int] = (2, 3)) -> network.DeveloperModuleIterator:
        """获取开发者模块"""
        return network.DeveloperModuleIterator(self.get_proxy(), developer_id, start, types)

    def download(self, item_id: str, developer_name: str, res_name: str) -> None:
        """下载资源"""
        target_path = f"./decrypted/{developer_name}/{item_id}_{res_name}"
        if os.path.exists(target_path):
            self.update_output.emit(f"资源 {item_id}_{res_name} 已存在。跳过下载。")
            return

        download_url = self.__get_download_url([item_id])[item_id]
        if download_url:
            key, uuid = self.__get_key_and_uuid([item_id])[item_id]
            temp_path = io.BytesIO(self.get_proxy().simple_request("get", download_url).content)
            decrypted_file_path = unpack.Crypto.DecryptZip(temp_path, key, uuid, "./decrypted")
            temp_path.close()

            if not os.path.exists(os.path.dirname(target_path)):
                os.makedirs(os.path.dirname(target_path))

            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            os.rename(decrypted_file_path, target_path)
            self.update_output.emit(f"{Fore.GREEN}下载并解密完成 {item_id}_{res_name}")
        else:
            self.update_output.emit(f"{Fore.RED}获取 {item_id} 的下载URL失败")

    def search_user(self, username: str):
        """搜索用户"""
        response = self.get_proxy().x19_request(
            method="post",
            url="https://g79mclobtgray.nie.netease.com",
            api="/user-search-friend",
            json={"name_or_mail": username, "mail_flag": False}
        ).json()
        
        if response and 'entities' in response:
            entities = response['entities']
            if entities:
                user_entity = entities[0]  # 假设我们只关心第一个匹配的用户
                uid = user_entity.get('uid')
                if uid:
                     
                    self.update_output.emit(f"用户信息：")
                    self.update_output.emit(f"  用户ID：{user_entity.get('uid')}")
                    self.update_output.emit(f"  昵称：{user_entity.get('nickname')}")
                    self.update_output.emit(f"  头像：{user_entity.get('headImage')}")
                    self.update_output.emit(f"  相框：{user_entity.get('frame_id')}")
                    self.update_output.emit(f"  动态ID：{user_entity.get('moment_id')}")
                    self.update_output.emit(f"  公开标志：{'是' if user_entity.get('public_flag') else '否'}")
                    self.update_output.emit(f"  在线状态：{user_entity.get('online_status')}")
                    self.update_output.emit(f"  在线平台：{user_entity.get('online_pcpe')}")
                    self.update_output.emit(f"  在线类型：{user_entity.get('online_type')}")
                    self.update_output.emit(f"  游戏信息：{user_entity.get('game_info')}")
                    # 将时间戳转换为具体时间
                    t_logout = datetime.fromtimestamp(user_entity.get('tLogout')).strftime('%Y-%m-%d %H:%M:%S')
                    self.update_output.emit(f"  上次登出时间：{t_logout}")

                    self.update_output.emit(f"  成长信息：")
                    growth =user_entity.get('pe_growth', {})
                    self.update_output.emit(f"    经验值：{growth.get('exp')}")
                    self.update_output.emit(f"    等级：{growth.get('lv')}")
                    self.update_output.emit(f"    装饰：{growth.get('decorate')}")
                    self.update_output.emit(f"    消息背景ID：{growth.get('msg_background_id')}")
                    self.update_output.emit(f"    聊天气泡ID：{growth.get('chat_bubble_id')}")
                    self.update_output.emit(f"    VIP状态：{'是' if growth.get('is_vip') else '否'}")
                    self.update_output.emit(f"    VIP表情状态：{'是' if growth.get('is_vip_expr') else '否'}")
                    self.update_output.emit(f"    所需经验：{growth.get('need_exp')}")
                self.update_output.emit(f"用户 {username} 的 UID 是: {uid}")
                # 调用 get_user_settings 方法
                self.get_user_settings(uid)
            else:
                self.update_output.emit(f"{Fore.RED}未找到用户 {username} 的 UID。")
        else:
            self.update_output.emit(f"{Fore.RED}未找到用户 {username}。")
            print("搜索玩家按钮被点击")
            username = input("请输入用户名：")
            self.downloader.search_user(username)

    def get_user_settings(self, user_id: str):
        """获取用户设置"""
        try:
            response = self.get_proxy().x19_request(
                method="post",
                url="https://g79mclobt.minecraft.cn",
                api="/pe-get-other-user-setting-list",
                json={
                    "with_pet_info": True,
                    "user_id": user_id,
                    "settings": ["skin_type", "skin_data", "persona_data", "screen_config"]
                }
            ).json()
            if response and response.get("code") == 0:
                self.update_output.emit(f"获取用户设置成功。")
            entity = response.get("entity", {})
            pet_info = entity.get("pet_info", {})
            entity = response.get("entity", {})
            skin_type = entity.get("skin_type", {})
            skin_data = entity.get("skin_data", {})
            screen_config = entity.get("screen_config", {})
        
            self.update_output.emit(f"皮肤信息：\n")
            self.update_output.emit(f"    皮肤类型：{skin_type.get('type')}")
            self.update_output.emit(f"    皮肤数据：")
            self.update_output.emit(f"    类型：{skin_data.get('type')}")
            self.update_output.emit(f"    稀有度：{skin_data.get('rarity')}")
            self.update_output.emit(f"    是否苗条：{skin_data.get('is_slim')}")
            self.update_output.emit(f"    皮肤ID：{skin_data.get('item_id')}")
            self.update_output.emit(f"    资源名称：{skin_data.get('res_name')}")
            self.update_output.emit(f"    标题图片URL：{skin_data.get('title_image_url')}")
            self.update_output.emit(f"    个人资料：{pet_info.get('persona_data')}\n")
            self.update_output.emit(f"屏幕配置：")
            for key, config in screen_config.items():
                self.update_output.emit(f"  {key}: 资源ID {config.get('item_id')}, 等级 {config.get('outfit_level')}")
            self.update_output.emit(f"宠物信息：")
            self.update_output.emit(f"  宠物数量：{pet_info.get('pet_num')}")
            self.update_output.emit(f"  宠物名称：{pet_info.get('pet_name')}")
            pet_skin_info = pet_info.get("skin_info", {})
            self.update_output.emit(f"  皮肤名称：{pet_skin_info.get('name')}")
            self.update_output.emit(f"  稀有度：{pet_skin_info.get('rarity')}")
            self.update_output.emit(f"  分数：{pet_skin_info.get('score')}")
            self.update_output.emit(f"  类型：{pet_skin_info.get('type')}")
            self.update_output.emit(f"  描述：{pet_skin_info.get('desc')}")
            self.update_output.emit(f"  图标：{pet_skin_info.get('icon')}")
            self.update_output.emit(f"  预览图标：{pet_skin_info.get('preview_icon')}")
        

            return response
        except Exception as exception:
            self.update_output.emit(f"{Fore.RED}获取用户设置时出错：{exception}")
        return None

    def get_download_info(self, item_id: str):
        """获取下载信息"""
        try:
            response = self.get_proxy().x19_request(
                method="post",
                url="https://g79apigatewayobt.minecraft.cn",
                api="/pe-download-item/get-download-info",
                json={"item_id": item_id}
            )
        
            if response is not None and response.status_code == 200:
                response_data = response.json()
                self.update_output.emit(f"完整的响应数据: {response_data}")  
                if response_data is not None:
                    entity = response_data.get("entity", {})
                    if entity:  
                        
                        return entity.get("res_url", None)
                    else:
                        self.update_output.emit(f"{Fore.RED}响应数据中 'entity' 键为空。")
                        return None
                else:
                    self.update_output.emit(f"{Fore.RED}JSON解析失败或响应数据为空。")
                    return None
            else:
                self.update_output.emit(f"{Fore.RED}请求失败，状态码：{response.status_code if response else '请求返回 None'}")
                return None
        except Exception as exception:
            self.update_output.emit(f"{Fore.RED}获取下载信息时出错：{exception}")
            return None

    def search_and_crack_resources_pc(self, keyword: str):
        """根据关键词搜索资源（PC端），并尝试下载和解密每个资源"""
        offset = 0
        while True:
            response = self.get_proxy().x19_request(
                method="post",
                url="https://g79mclobtgray.nie.netease.com",
                api="/item/query/search-by-keyword",
                json={
                    "item_type": 2,
                    "keyword": keyword,
                    "master_type_id": "0",
                    "secondary_type_id": "0",
                    "sort_type": 1,
                    "order": 0,
                    "offset": offset,
                    "length": 24,  # 每次请求24个结果
                    "is_has": True,
                    "year": 0,
                    "is_sync": 0,
                    "price_type": 0
                }
            ).json()
            
            if 'entities' in response and response['entities']:
                self.update_output.emit(f"找到 {len(response['entities'])} 个匹配结果。")
                for entity in response['entities']:
                    item_id = entity.get('entity_id', '未知ID')
                    resource_name = entity.get('name', '未知名称')
                    author = entity.get('developer_name', '未知作者')
                    self.update_output.emit(f"资源ID: {item_id}, 名称: {resource_name}, 作者: {author}")
                    # 尝试下载和解密资源
                    self.download(item_id, author, resource_name)
                offset += 24  # 增加offset以便获取下一页结果
            else:
                self.update_output.emit(f"{Fore.RED}没有找到更多匹配的资源。")
                break  # 如果没有更多结果，则退出循环

    def search_and_crack_resources(self, keyword: str):
        """根据关键词搜索资源，并尝试下载和解密每个资源"""
        offset = 0
        while True:
            response = self.get_proxy().x19_request(
                method="post",
                url="https://g79mclobtgray.nie.netease.com",
                api="/pe-item/query/search-by-keyword",
                json={
                    "keyword": keyword,
                    "offset": offset,
                    "length": 24  # 每次请求24个结果
                }
            ).json()
            
            if 'entities' in response and response['entities']:
                self.update_output.emit(f"找到 {len(response['entities'])} 个匹配结果。")
                for entity in response['entities']:
                    item_id = entity.get('item_id', '未知ID')
                    res_name = entity.get('res_name', '未知名称')
                    developer_name = entity.get('developer_name', '未知作者')
                    self.update_output.emit(f"资源ID: {item_id}, 名称: {res_name}, 作者: {developer_name}")
# 尝试下载和解密资源
                self.download(item_id, developer_name, res_name)
                offset += 24  # 增加offset以便获取下一页结果
            else:
                self.update_output.emit(f"{Fore.RED}没有找到更多匹配的资源。")
                break  # 如果没有更多结果，则退出循环

class InputDialog(QDialog):
    def __init__(self, parent=None):
        super(InputDialog, self).__init__(parent)
        self.setWindowTitle('请输入关键词')
        self.setFixedSize(242, 101)  # 设置对话框大小

        layout = QVBoxLayout(self)  # 创建垂直布局

        # 创建一个标签和输入框
        self.lineEdit = QLineEdit(self)
        layout.addWidget(self.lineEdit)

        # 创建按钮框
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttonBox)

        # 连接信号和槽
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def get_input(self):
        return self.lineEdit.text()  # 返回输入框中的文字
    
from ui import BlurredLabel, MoveLabel

class PirsmToolbox(QDialog):
    def __init__(self, downloader: Downloader, parent=None):
        super(PirsmToolbox, self).__init__(parent)
        self.downloader = downloader
        self.setupUi(self)  # 使用Ui_Dialog的setupUi方法设置UI
        self.initUI()
        
        # 初始化动态模糊背景
        self.init_background()

    def init_background(self):
        # 创建动态模糊背景标签
        self.blurred_label = BlurredLabel(self)
        self.blurred_label.setGeometry(0, 0, self.width(), self.height())
        self.blurred_label.lower()  # 将背景标签置于最底层
        
        # 获取主布局
        main_layout = QVBoxLayout(self)
        
        # 将模糊背景标签设置为窗口的背景
        main_layout.addWidget(self.blurred_label)
        
        # 可以在这里添加更多的形状和动画
        shapes = [
            {"type": 11, "shape": 1, "color": "#7098da", "last_time": 6},
            {"type": 21, "shape": 3, "color": "#6eb6ff", "last_time": 5},
            {"type": 31, "shape": 1, "color": "#90f2ff", "last_time": 7},
            {"type": 41, "shape": 2, "color": "#e0fcff", "last_time": 8},
            {"type": 12, "shape": 1, "color": "#0000FF", "last_time": 9},
            {"type": 22, "shape": 1, "color": "#00FFFF", "last_time": 4}
        ]
        for shape in shapes:
            MoveLabel(self.blurred_label, **shape)
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1125, 582)
        font = QtGui.QFont()
        font.setFamily("汉仪力量黑简")
        font.setKerning(True)
        Dialog.setFont(font)
        Dialog.setSizeGripEnabled(False)
        self.toolButton = QtWidgets.QToolButton(parent=Dialog)
        self.toolButton.setGeometry(QtCore.QRect(20, 160, 181, 61))
        self.toolButton.setStyleSheet("color: rgb(54, 102, 250);\n"
"background-color: rgb(255, 255, 255);\n"
"font: 9pt \"汉仪力量黑简\";")
        self.toolButton.setAutoRaise(False)
        self.toolButton.setArrowType(QtCore.Qt.ArrowType.NoArrow)
        self.toolButton.setObjectName("toolButton")
        self.toolButton_2 = QtWidgets.QToolButton(parent=Dialog)
        self.toolButton_2.setGeometry(QtCore.QRect(20, 230, 181, 61))
        self.toolButton_2.setMouseTracking(False)
        self.toolButton_2.setTabletTracking(False)
        self.toolButton_2.setAcceptDrops(False)
        self.toolButton_2.setAutoFillBackground(False)
        self.toolButton_2.setStyleSheet("color: rgb(54, 102, 250);\n"
"background-color: rgb(255, 255, 255);\n"
"font: 9pt \"汉仪力量黑简\";")
        self.toolButton_2.setCheckable(False)
        self.toolButton_2.setObjectName("toolButton_2")
        self.toolButton_3 = QtWidgets.QToolButton(parent=Dialog)
        self.toolButton_3.setEnabled(True)
        self.toolButton_3.setGeometry(QtCore.QRect(20, 300, 181, 61))
        font = QtGui.QFont()
        font.setFamily("汉仪力量黑简")
        font.setPointSize(9)
        font.setBold(False)
        font.setItalic(False)
        font.setKerning(True)
        self.toolButton_3.setFont(font)
        self.toolButton_3.setMouseTracking(False)
        self.toolButton_3.setStyleSheet("color: rgb(54, 102, 250);\n"
"background-color: rgb(255, 255, 255);\n"
"font: 9pt \"汉仪力量黑简\";")
        self.toolButton_3.setCheckable(False)
        self.toolButton_3.setObjectName("toolButton_3")
        self.toolButton_4 = QtWidgets.QToolButton(parent=Dialog)
        self.toolButton_4.setEnabled(True)
        self.toolButton_4.setGeometry(QtCore.QRect(20, 370, 181, 61))
        font = QtGui.QFont()
        font.setFamily("汉仪力量黑简")
        font.setPointSize(9)
        font.setBold(False)
        font.setItalic(False)
        font.setKerning(True)
        self.toolButton_4.setFont(font)
        self.toolButton_4.setMouseTracking(False)
        self.toolButton_4.setStyleSheet("color: rgb(54, 102, 250);\n"
"background-color: rgb(255, 255, 255);\n"
"font: 9pt \"汉仪力量黑简\";")
        self.toolButton_4.setCheckable(False)
        self.toolButton_4.setObjectName("toolButton_4")
        self.textEdit = QtWidgets.QTextEdit(parent=Dialog)
        self.textEdit.setGeometry(QtCore.QRect(250, 130, 651, 421))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setItalic(False)
        self.textEdit.setFont(font)
        self.textEdit.setStyleSheet("font: 9pt \"微软雅黑\";")
        self.textEdit.setObjectName("textEdit")
        self.label_3 = QtWidgets.QLabel(parent=Dialog)
        self.label_3.setEnabled(True)
        self.label_3.setGeometry(QtCore.QRect(160, 20, 421, 91))
        self.label_3.setStyleSheet("font: 9pt \"汉仪力量黑简\";")
        self.label_3.setObjectName("label_3")
        self.label_2 = QtWidgets.QLabel(parent=Dialog)
        self.label_2.setGeometry(QtCore.QRect(20, 0, 131, 161))
        self.label_2.setText("")
        self.label_2.setPixmap(QtGui.QPixmap("./logo.svg"))
        self.label_2.setObjectName("label_2")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Pirsm Toolbox"))
        self.toolButton.setText(_translate("Dialog", "搜索玩家"))
        self.toolButton_2.setText(_translate("Dialog", "单独破解"))
        self.toolButton_3.setText(_translate("Dialog", "批量破解"))
        self.toolButton_4.setText(_translate("Dialog", "批量破解（PC端）"))
        self.textEdit.setHtml(_translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:\'微软雅黑\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.label_3.setText(_translate("Dialog", "<html><head/><body><p><span style=\" font-size:48pt;\">Pirsm Toolbox</span></p></body></html>"))


    def initUI(self):
        self.toolButton.clicked.connect(self.search_user)  # 连接搜索用户按钮的点击信号到槽函数
        self.toolButton_2.clicked.connect(self.download)  # 连接单独破解按钮的点击信号到槽函数
        self.toolButton_3.clicked.connect(self.search_and_crack_resources)  # 连接批量破解按钮的点击信号到槽函数
        self.toolButton_4.clicked.connect(self.search_and_crack_resources_pc)  # 连接批量破解（PC端）按钮的点击信号到槽函数
        self.setWindowIcon(QtGui.QIcon('./logo.svg'))  # 确保使用QtGui.QIcon
        self.downloader.update_output.connect(self.append_output)  # 连接信号

    def append_output(self, text):
        self.textEdit.append(text)  # 将文本添加到QTextEdit控件中

    def search_user(self):
        # 弹出输入对话框让用户输入用户名
        dialog = InputDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = dialog.get_input()
            self.downloader.search_user(username)  # 调用Downloader的search_user方法

    def download(self):
        # 弹出输入对话框让用户输入项目ID、作者名称和资源名称
        dialog = InputDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            item_id = dialog.get_input()  # 这里假设对话框返回的是项目ID
            developer_name = input("请输入作者名称：")
            res_name = input("请输入资源名称：")
            self.downloader.download(item_id, developer_name, res_name)  # 调用Downloader的download方法

    def search_and_crack_resources(self):
        # 弹出输入对话框让用户输入关键词
        dialog = InputDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            keyword = dialog.get_input()
            self.downloader.search_and_crack_resources(keyword)  # 调用Downloader的search_and_crack_resources方法

    def search_and_crack_resources_pc(self):
        # 弹出输入对话框让用户输入关键词
        dialog = InputDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            keyword = dialog.get_input()
            self.downloader.search_and_crack_resources_pc(keyword)  # 调用Downloader的search_and_crack_resources_pc方法


def main():
    downloader = Downloader(account)
    app = QApplication(sys.argv)
    toolbox = PirsmToolbox(downloader)
    toolbox.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
