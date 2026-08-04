import requests
import base64
from datetime import datetime

import time
from typing import Literal, Self
from pathlib import Path


class SEND_MESSAGE_ERROR(Exception):
    pass


class GET_DISK_ERROR(Exception):
    pass


class UPLOAD_ERROR(Exception):
    pass


class BitrixBot:
    def __init__(
        self,
        api_url: str,
        bot_id: int,
        client_id: str,
        folder: Literal["shared", "own"] = "shared",
        max_retries: int = 1,      # количество попыток для запросов
        base_delay: float = 1.0,   # секунда
        timeout: float = 30.0,     # таймаут запроса
    ) -> None:
        self.api_url = api_url
        self.bot_id = bot_id
        self.client_id = client_id
        self.message_add = "imbot.message.add?"
        self._storage_id = None
        self._bot_folder_id = None
        self.file_path = None
        self.message_json = None
        self.folder = "common" if folder == "shared" else "user"
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.timeout = timeout

    def send_message(self, dialog_id: int | str, message: str) -> None:
        message_json = {
            "BOT_ID": self.bot_id,
            "CLIENT_ID": self.client_id,
            "DIALOG_ID": dialog_id,
            "MESSAGE": message,
        }
        last_error = None
        for attempt in range(self.max_retries):
            try:
                r = requests.post(self.api_url + self.message_add, json=message_json, timeout=self.timeout)
                if r.status_code == 200:
                    return
                last_error = f"HTTP {r.status_code}: {r.text}"
            except requests.RequestException as e:
                last_error = e
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)  # 1, 2, 4, 8, ...
                time.sleep(delay)
        else:
            raise SEND_MESSAGE_ERROR(
            f"Не удалось отправить сообщение после {self.max_retries} попыток: {last_error}"
        )

    def cook_message(self, dialog_id: int | str, message="Начало сообщения") -> Self:
        self.message_json = {
            "BOT_ID": self.bot_id,
            "CLIENT_ID": self.client_id,
            "DIALOG_ID": dialog_id,
            "MESSAGE": message,
            "ATTACH": [],
        }
        return self

    def add_message(self, message: str = "Это сообщение") -> Self:
        if not self.message_json:
            print("Ошибка! Сначала нужно создать cook_message")
            raise SEND_MESSAGE_ERROR
        self.message_json["ATTACH"].append({"MESSAGE": message})
        return self

    def add_delimiter(self) -> Self:
        if not self.message_json:
            print("Ошибка! Сначала нужно создать cook_message")
            raise SEND_MESSAGE_ERROR
        self.message_json["ATTACH"].append({"DELIMITER": {}})
        return self

    def add_image(self, image_path: str) -> Self:
        if not self.message_json:
            print("Ошибка! Сначала нужно создать cook_message")
            raise SEND_MESSAGE_ERROR
        file_id = self._upload_file(image_path)[1]
        self.message_json["ATTACH"].append(
            {
                "IMAGE": {
                    "LINK": f"https://bitrix24.ru/disk/showFile/{file_id}/"
                }
            }
        )
        return self

    def add_file(self, file_path: Path) -> Self:
        if not self.message_json:
            print("Ошибка! Сначала нужно создать cook_message")
            raise SEND_MESSAGE_ERROR
        file_url = self._upload_file(file_path)[0]
        self.message_json["ATTACH"].append(
            {"FILE": {"LINK": file_url, "NAME": file_path.name}}
        )
        return self

    def serve_message(self):
        last_error = None
        for attempt in range(self.max_retries):
            try:
                r = requests.post(self.api_url + self.message_add, json=self.message_json, timeout=self.timeout)
                if r.status_code == 200:
                    return
                last_error = f"HTTP {r.status_code}: {r.text}"
            except requests.RequestException as e:
                last_error = e
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)  # 1, 2, 4, 8, ...
                time.sleep(delay)
        else:
            raise SEND_MESSAGE_ERROR(
            f"Не удалось serve_message после {self.max_retries} попыток: {last_error}"
        )

    def send_image(
        self, dialog_id: int | str, image_path: str, message: str = str(datetime.now())
    ) -> None:
        file_id = self._upload_file(image_path)[1]
        message_json = {
            "BOT_ID": self.bot_id,
            "CLIENT_ID": self.client_id,
            "DIALOG_ID": dialog_id,
            "MESSAGE": message,
            "ATTACH": [
                {
                    "IMAGE": {
                        "LINK": f"https://bitrix24.ru/disk/showFile/{file_id}/",
                        "WIDTH": 1000,
                        "HEIGHT": 1000,
                    }
                }
            ],
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                r = requests.post(self.api_url + self.message_add, json=message_json, timeout=self.timeout)
                if r.status_code == 200:
                    return
                last_error = f"HTTP {r.status_code}: {r.text}"
            except requests.RequestException as e:
                last_error = e
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)  # 1, 2, 4, 8, ...
                time.sleep(delay)
        else:
            raise SEND_MESSAGE_ERROR(
            f"Не удалось send_image после {self.max_retries} попыток: {last_error}"
        )

    def send_file(
        self, dialog_id: int | str, file_path: Path | str, message: str = str(datetime.now())
    ) -> None:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if self.file_path == file_path:
            file_url = self.file[0]
        else:
            file_url = self._upload_file(file_path)[0]
        message_json = {
            "BOT_ID": self.bot_id,
            "CLIENT_ID": self.client_id,
            "DIALOG_ID": dialog_id,
            "MESSAGE": message,
            "ATTACH": [{"FILE": {"LINK": file_url, "NAME": file_path.name}}],
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                r = requests.post(self.api_url + self.message_add, json=message_json, timeout=self.timeout)
                if r.status_code == 200:
                    return
                last_error = f"HTTP {r.status_code}: {r.text}"
            except requests.RequestException as e:
                last_error = e
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)  # 1, 2, 4, 8, ...
                time.sleep(delay)
        else:
            raise SEND_MESSAGE_ERROR(
            f"Не удалось send_file после {self.max_retries} попыток: {last_error}"
        )

    def _get_storage_id(self) -> str:
        disk_getlist = "disk.storage.getlist"
        last_error = None
        for attempt in range(self.max_retries):
            try:
                r = requests.get(self.api_url + disk_getlist, timeout=self.timeout)
                if r.status_code == 200:
                    storage_list = r.json().get("result")
                    storage_id = next(
                        (
                            storage
                            for storage in storage_list
                            if storage.get("ENTITY_TYPE") == self.folder
                        ),
                        None,
                    )
                    if not storage_id:
                        raise GET_DISK_ERROR
                    return storage_id.get("ID")
                last_error = f"HTTP {r.status_code}: {r.text}"
            except requests.RequestException as e:
                last_error = e
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)  # 1, 2, 4, 8, ...
                time.sleep(delay)
        else:
            raise GET_DISK_ERROR(
            f"Не удалось send_file после {self.max_retries} попыток: {last_error}"
        )
        
    def _get_bot_folder_id(self) -> str:
        if not self._storage_id:
            self._storage_id = self._get_storage_id()
        api_children_folders = "disk.storage.getchildren"
        data = {"id": self._storage_id}
        last_error = None
        for attempt in range(self.max_retries):
            try:
                r = requests.get(self.api_url + api_children_folders, params=data, timeout=self.timeout)
                if r.status_code == 200:
                    break
                last_error = f"HTTP {r.status_code}: {r.text}"
            except requests.RequestException as e:
                last_error = e
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)  # 1, 2, 4, 8, ...
                time.sleep(delay)
        else:
            raise GET_DISK_ERROR(
            f"Не удалось _get_bot_folder_id после {self.max_retries} попыток: {last_error}"
        )

        for i in r.json().get("result"):
            if i["NAME"] == "BOT_MESSAGE":
                return i["ID"]
        add_folder = "disk.storage.addfolder"
        data = {"id": self._storage_id, "data": {"NAME": "BOT_MESSAGE"}}
        last_error = None
        for attempt in range(self.max_retries):
            try:
                r = requests.post(self.api_url + add_folder, json=data, timeout=self.timeout)
                if r.status_code == 200:
                    break
                last_error = f"HTTP {r.status_code}: {r.text}"
            except requests.RequestException as e:
                last_error = e
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)  # 1, 2, 4, 8, ...
                time.sleep(delay)
        else:
            raise GET_DISK_ERROR(
            f"Не удалось _get_bot_folder_id после {self.max_retries} попыток: {last_error}"
        )
        return r.json()["result"]["ID"]

    def _upload_file(self, file_path) -> tuple[str, str]:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if not self._bot_folder_id:
            self._bot_folder_id = self._get_bot_folder_id()
        disk_api = "disk.folder.uploadfile?"
        file = {
            "id": self._bot_folder_id,
            "generateUniqueName": True,
            "data[NAME]": f"{file_path.name}",
            "fileContent[]": [
                file_path.name,
                base64.b64encode(open(file_path, "rb").read()),
            ],
        }
        last_error = None
        for attempt in range(self.max_retries):
            try:
                r = requests.post(self.api_url + disk_api, data=file, timeout=self.timeout)
                if r.status_code == 200:
                    break
                last_error = f"HTTP {r.status_code}: {r.text}"
            except requests.RequestException as e:
                last_error = e
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)  # 1, 2, 4, 8, ...
                time.sleep(delay)
        else:
            raise UPLOAD_ERROR(
            f"Не удалось _upload_file после {self.max_retries} попыток: {last_error}"
        )
        self.file_path = file_path
        self.file = (r.json().get('result').get('DOWNLOAD_URL'),  r.json().get('result').get('ID'))
        return (
            r.json().get("result").get("DOWNLOAD_URL"),
            r.json().get("result").get("ID"),
        )

