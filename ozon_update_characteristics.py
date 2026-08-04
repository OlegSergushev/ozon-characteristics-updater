import os
import sys
import pandas as pd
import numpy as np
import json
import requests
from pathlib import Path
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from logger_setup import setup_logger
from bitrix_bot import BitrixBot

SCRIPT_NAME = "ozon_update_characteristics"

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

LOG_DIRECTORY = f"M:/Pricing/ВБ/Логи скриптов/{SCRIPT_NAME}/"  # Путь к директории с логами
LOG_FILENAME = f"{SCRIPT_NAME}_{current_time}.log"

NET_LOG_PATH = os.path.join(LOG_DIRECTORY, LOG_FILENAME)
LOCAL_LOG_PATH = f"local_logs/{SCRIPT_NAME}_{current_time}.log"

logger = setup_logger(LOCAL_LOG_PATH, level_console="INFO", level_file="DEBUG",
                      net_log_path=NET_LOG_PATH)

BITRIX_CHAT_ID = None # Добавьте свой

bitrix_bot = BitrixBot(api_url='https://case-place.bitrix24.ru/rest/409/gr0aj9pvi8g8c2qn/',
                       bot_id=413,
                       client_id='96tveccre473vojfi3gupdqnf0kepb3w',
                       folder='own')

PATH_TOKENS = "tokens/ozon.xlsx" # Путь к токенам

DESCRIPTION_CATEGORY_ID = 17028650
TYPE_ID = 97011

ROOT_MAPPING = {
        'ип': 'ip', 
        'артикул': 'offer_id',
        'штрихкод товара': 'barcode',
        'маркетинговый цвет': 'color_image',
        'валюта': 'currency_code',
        'глубина упаковки': 'depth',
        'идентификатор категории': 'description_category_id',
        'единица измерения габаритов': 'dimension_unit',
        'высота упаковки': 'height',
        'фото': 'images',
        'фото 360': 'images360',
        'название товара': 'name',
        'цена до скидок': 'old_price',
        'цена товара с учётом скидок': 'price',
        'ссылка на главное изображение товара': 'primary_image',
        'идентификатор типа товара': 'type_id',
        'ставка ндс для товара': 'vat',
        'вес товара в упаковке': 'weight',
        'единица измерения веса': 'weight_unit',
        'ширина упаковки': 'width',
}
    
ATTRIBUTES_MAPPING = {
        'вид чехла': 5938,
        '#хештеги': 23171,
        'rich-контент json': 11254,
        'название модели (для объединения в одну карточку)': 9048,
        'вид выпуска товара': 22270,
        'бренд': 85,
        'страна-изготовитель': 4389,
        'тн вэд коды еаэс': 22232,
        'признак 18+': 9070,
        'цвет товара': 10096,
        'название': 4180,
        'макс. диагональ экрана, дюймы': 8590,
        'количество заводских упаковок': 11650,
        'мин. диагональ, дюймы': 8591,
        'застежка': 5940,
        'код продавца': 9024,
        'вес товара, г': 4383,
        'комплектация': 4384,
        'особенности': 5941,
        'гарантия': 10400,
        'размеры, мм': 4382,
        'материал': 21615,
        'аннотация': 4191,
        'название цвета': 10097,
        'нужен код маркировки': 23536,
}
  
COMPLEX_ATTRIBUTES_MAPPING = {
        'подходит для': 22898,
        'озон.видео: ссылка': 21841,
        'модель устройства': 22900,
        'озон.видео: название': 21837,
        'озон.видеообложка: ссылка': 21845,
}

TYPING_CHARACTERISTIC = {'ип': (object,), 'артикул': (object,), 'штрихкод товара': ('int64', 'float64'), 'маркетинговый цвет': (object,), 'валюта': (object,), 
                        'глубина упаковки': ('int64', 'float64'), 'идентификатор категории': ('int64', 'float64'), 'единица измерения габаритов': (object,), 
                        'высота упаковки': ('int64', 'float64'), 'фото': (object, str), 'фото 360': (object, str), 'название товара': (object, str), 
                        'цена до скидок': ('int64', 'float64'), 'цена товара с учётом скидок': ('int64', 'float64'), 'ссылка на главное изображение товара': (object, str), 
                        'идентификатор типа товара': ('int64', 'float64'), 'ставка ндс для товара': ('int64', 'float64'), 'вес товара в упаковке': ('int64', 'float64'), 
                        'единица измерения веса': (object, str), 'ширина упаковки': ('int64', 'float64'), 'вид чехла': (object, str),'#хештеги': (object, str), 
                        'название модели (для объединения в одну карточку)': (object, str), 'вид выпуска товара': (object, str), 'бренд': (object, str), 
                        'страна-изготовитель': (object, str), 'тн вэд коды еаэс': (object, str), 'признак 18+': (object, str), 'цвет товара': (object, str), 'название': (object, str), 
                        'макс. диагональ экрана, дюймы': ('int64', 'float64'), 'количество заводских упаковок': ('int64', 'float64'), 'мин. диагональ, дюймы': ('int64', 'float64'), 
                        'застежка': (object, str), 'код продавца': (object, str), 'вес товара, г': ('int64', 'float64'), 'комплектация': object, 'особенности': object, 'гарантия': object, 
                        'размеры, мм': ('int64', 'float64'), 'материал': (object, str), 'аннотация': (object, str), 'название цвета': (object, str), 'нужен код маркировки': (bool,), 
                        'подходит для': (object, str), 'озон.видео: ссылка': (object, str), 'модель устройства': (object, str), 'rich-контент json': (object, str),
                        'озон.видео: название': (object, str), 'озон.видеообложка: ссылка': (object, str)}


ТYPING_ATTRIBUTES = {
        11254: str,
        5938: str,
        23171: str,
        9048: str,
        22270: str,
        85: str,
        4389: str,
        22232: str,
        9070: str,
        10096: str,
        4180: str,
        8590: str,
        11650: int,
        8591: str,
        5940: str,
        9024: str,
        4383: str,
        4384: str,
        5941: str,
        10400: str,
        4382: str,
        21615: str,
        4191: str,
        10097: str,
        22898: str,
        21841: str,
        22900: str,
        21837: str,
        21845: str,
        23536: bool,
}


class ExcelFileProcessor:
    """
    Класс для обработки входного Excel-файла с характеристиками.
    
    Ожидаемая структура файла:
    - Обязательная колонка: "Артикул" (offer_id товара)
    - Обязательная колонка: "ИП" (юрлицо, для выбора токенов)
    - Остальные колонки: названия характеристик (например, "Цвет", "Материал", "Бренд")
    """
    
    def __init__(self, file_path: str):
        """
        Args:
            file_path: путь к Excel-файлу
        """
        self.file_path = Path(file_path)
        self.df = None
        self._load()
        self._drop_empty_columns()
        self._check_columns()
        self._convert_types_bool()
        self._validate()
        self._map_columns()
    
    def _load(self):
        """Загружает Excel-файл"""
        if not self.file_path.exists():
            logger.error(f"Файл не найден: {self.file_path}")
            raise FileNotFoundError(f"Файл не найден: {self.file_path}")
        
        self.df = pd.read_excel(self.file_path)
        self.df.columns = self.df.columns.str.lower()
        logger.info(f"Загружен файл {self.file_path.name}: {len(self.df)} строк, {len(self.df.columns)} колонок")
    
    def _check_columns(self):
        """Проверяет колонки df"""
        all_columns = ['ип', 'артикул', 'штрихкод товара', 'маркетинговый цвет', 'валюта', 'глубина упаковки', 'идентификатор категории', 
                       'единица измерения габаритов', 'высота упаковки', 'фото', 'фото 360', 'название товара', 'цена до скидок', 
                       'цена товара с учётом скидок', 'ссылка на главное изображение товара', 'идентификатор типа товара',
                       'ставка ндс для товара', 'вес товара в упаковке', 'единица измерения веса', 'ширина упаковки', 'вид чехла',
                       '#хештеги', 'название модели (для объединения в одну карточку)', 'вид выпуска товара', 'бренд', 'страна-изготовитель',
                       'тн вэд коды еаэс', 'признак 18+', 'цвет товара', 'название', 'макс. диагональ экрана, дюймы', 'количество заводских упаковок',
                       'мин. диагональ, дюймы', 'застежка', 'код продавца', 'вес товара, г', 'комплектация', 'особенности', 'гарантия', 'размеры, мм',
                       'материал', 'аннотация', 'название цвета', 'нужен код маркировки', 'подходит для', 'озон.видео: ссылка', 'модель устройства',
                       'озон.видео: название', 'озон.видеообложка: ссылка', 'ссылки на дополнительные фото', 'rich-контент json',
                       'доп. фото 360', 'доп. озон.видео: ссылка', 'доп. озон.видео: название']
        
        error_columns = []
        
        for column in self.df.columns:
            if column not in all_columns:
                error_columns.append(column)
        
        if error_columns:
            logger.warning(f"Колонки названы неправильно={error_columns}. Данные характеристики обновлены не будут!")
            input("Нажмите Enter, чтобы продолжить")
    
    def _map_columns(self):
        """Преобразуем root колонки в API формат"""
        
        rename = {}
        for col in self.df.columns:
            if col in ROOT_MAPPING:
                rename[col] = ROOT_MAPPING[col]
            
        self.df = self.df.rename(columns=rename)
        
        logger.info("Колонки-root переименованы в API форматы")
    
    def _drop_empty_columns(self):
        """Удаляет колонки в которых все значения пустые"""
        
        initial_cols = len(self.df.columns)
        
        # Оставляем колонки , где есть хотя бы одно непустое значение
        self.df = self.df.dropna(axis=1, how='all')
        
        dropped = initial_cols - len(self.df.columns)
        
        if dropped > 0:
            logger.info(f"Удаленно {dropped} полность пустых колонок")
        
        self.df = self.df.replace(np.nan, None)
        
    def _convert_types_bool(self):
        """Преобразуем bool колонки с типу bool"""
        
        bool_cols = ['признак 18+', 'нужен код маркировки']
        
        for col in bool_cols:
            if col not in self.df.columns:
                continue
            
            self.df[col] = self.df[col].map({
                'да': 'true',
                'нет': 'false',
                'Да': 'true',
                'Нет': 'false',
                'true': 'true',
                'false': 'false',
                '+': 'true',
                '-': 'false',
            }).fillna(False)
            
            self.df[col] = self.df[col].astype(str)
    
    def _validate(self) -> None:
        """
        Проверяет наличие обязательных колонок и корректность данных.
         
        """
        errors = []
        
        # 1. Проверка обязательных колонок (в API-формате)
        required = ['ип', 'артикул']
        for col in required:
            if col not in self.df.columns:
                errors.append(f"Отсутствует обязательная колонка: '{col}'")
        
        # 2. Проверка колонки offer_id на пустые значения
        articul_col = self.df['артикул']
        empty_mask = articul_col.isna() | (articul_col.astype(str).str.strip() == '')
        if empty_mask.any():
            bad_indices = articul_col.index[empty_mask].tolist()[:10]
            errors.append(f"Колонка 'Артикул' содержит пустые значения (индексы: {bad_indices})")
        
        # 3. Проверка колонки ip на пустые значения
        ip_col = self.df['ип']
        ip_empty_mask = ip_col.isna() | (ip_col.astype(str).str.strip() == '')
        if ip_empty_mask.any():
            bad_indices = ip_col.index[ip_empty_mask].tolist()[:10]
            errors.append(f"Колонка 'ИП' содержит пустые значения (индексы: {bad_indices})")
        
        # 4. Проверка каждой колонки на тип данных
        for column in self.df.columns:
            if column in TYPING_CHARACTERISTIC:
                if self.df[column].dtype not in TYPING_CHARACTERISTIC[column]:
                    logger.warning(f"Колонка '{column}' содержит неверные значения! Либо вместо строк цифры, либо цифры вместо строк!")
                    input("Нажмите Enter, чтобы продолжить...")
        
        if errors:
            for error in errors:
                logger.error(error)
            logger.warning(f"Валидация Excel файла не пройдена!")
            raise ValueError("\n".join(errors))
        
        logger.info(f"Валидация Excel файла пройдена {len(self.df)} строк, {len(self.df.columns)} колонок")
    
    def get_offer_ids(self) -> List[str]:
        """
        Возвращает список offer_id из файла.
        
        Returns:
            список offer_id (строки)
        """
        return self.df['offer_id'].astype(str).str.strip().tolist()
    
    
    def get_characteristics_for_offer(self, offer_id: str) -> Dict[str, Any]:
        """
        Возвращает словарь характеристик для конкретного offer_id.
        
        Args:
            offer_id: offer_id товара
        
        Returns:
            словарь {название_характеристики: значение}
        """
        row = self.df[self.df['offer_id'] == offer_id]
        if row.empty:
            return {}
        
        row = row.iloc[0]
        result = {}
        
        for col in self.df.columns:
            value = row[col]
            # Пропускаем пустые значения
            if pd.isna(value):
                continue
            result[col] = value
        
        return result
    
    def get_all_rows(self) -> List[Dict[str, Any]]:
        """
        Возвращает список всех строк с характеристиками.
        
        Returns:
            список словарей [{'offer_id': ..., 'ip': ..., 'characteristics': {...}}, ...]
        """
        rows = []
        
        for _, row in self.df.iterrows():
            ip_value = str(row['ip']).strip()
            offer_id = str(row['offer_id']).strip()
            if not offer_id or offer_id == 'nan':
                continue
            
            characteristics = {}
            for col in self.get_characteristics_columns():
                value = row[col]
                if pd.notna(value) and str(value).strip():
                    characteristics[col] = value
            
            rows.append({
                'offer_id': offer_id,
                'ip': ip_value,
                'characteristics': characteristics
            })
        
        return rows
    
    def get_status_list(self):
        """
        Возвращает список статусов. Статус по умолчанию ОК
        
        Returns:
            список словарей [{'offer_id': ..., 'ip': ..., 'status': 'ОК', }, ...]
        """
        rows = []
        
        for _, row in self.df.iterrows():
            ip_value = str(row['ip']).strip()
            offer_id = str(row['offer_id']).strip()
            if not offer_id or offer_id == 'nan':
                continue
            
            rows.append({
                'offer_id': offer_id,
                'ip': ip_value,
                'status': 'OK'
            })
        
        return rows

        
class OzonAuth:
    """Класс для получения токенов Ozon из Excel"""
    
    def __init__(self, tokens_path: str):
        self.tokens_path = Path(tokens_path)
        self._tokens_df = None
        self._load_tokens()
    
    def _load_tokens(self):
        """Загружает токены из Excel"""
        if not self.tokens_path.exists():
            raise FileNotFoundError(f"Файл токенов не найден: {self.tokens_path}")
        
        self._tokens_df = pd.read_excel(self.tokens_path)
        logger.info(f"Загружено {len(self._tokens_df)} записей токенов")
        
        # Нормализуем, срезаем ИП
        self._tokens_df['ip_name'] = self._tokens_df['ip_name'].str.replace('ИП ', '')
    
    def get_credentials(self, ip_name: str) -> Dict[str, any]:
        """Возвращает client_id и api_key по названию ИП"""
        
        # Поиск по имени
        mask = self._tokens_df['ip_name'] == ip_name
        matched = self._tokens_df[mask]
        
        if matched.empty:
            available = self._tokens_df['ip_name'].tolist()
            raise ValueError(f"ИП '{ip_name}' не найден. Доступные: {available}")
        
        row = matched.iloc[0]
        return {
            'client_id': int(row['ID']),
            'api_key': str(row['token']).strip(),
            'ip_name': row['ip_name']
        }


class AttributesUpdater:
    """Класс для обновления атрибутов товаров"""
    
    def __init__(self, client):
        self.client = client
    
    def send_batch(self, batch: list) -> Dict:
        """
        Отправляем батч товаров (до 100) в Ozon API.

        Args:
            batch: {'offer_id': '12559-9C506764', 'name': 'Чехол на Айфон 12 с картой', 'description_category_id': 17028650, ...}
        
        Returns:
        {
            "result": {
            "task_id": 172549793
            }
        }

        """
        
        if not batch:
            return {'error_detail': 'Пустой батч',
                    'task_id': None,
                    'offer_ids': [p['offer_id'] for p in batch]}
        
        # Формируем данные для запроса
        items = []
        for product_data in batch:
            item = {
                'attributes': product_data.get('attributes'),
                'barcode': product_data.get('barcode'),
                'color_image': product_data.get('color_image'),
                'complex_attributes': product_data.get('complex_attributes'),
                'currency_code': product_data.get('currency_code'),
                'depth': product_data.get('depth'),
                'description_category_id': product_data.get('description_category_id'),
                'dimension_unit': product_data.get('dimension_unit'),
                'height': product_data.get('height'),
                'images': product_data.get('images'),
                'images360': product_data.get('images360'),
                'name': product_data.get('name'),
                'offer_id': product_data.get('offer_id'),
                'old_price': product_data.get('old_price'),
                'pdf_list': product_data.get('pdf_list'),
                'price': product_data.get('price'),
                'primary_image': product_data.get('primary_image'),
                'promotions': product_data.get('promotions'),
                'service_type': product_data.get('service_type'),
                'type_id': product_data.get('type_id'),
                'vat': product_data.get('vat'),
                'weight': product_data.get('weight'),
                'weight_unit': product_data.get('weight_unit'),
                'width': product_data.get('width'),
            }
            
            items.append(item)
        
        data = {"items": items}
        logger.debug(f"Отравляем батч: {data}")
        try:
            response = self.client.post('/v3/product/import', data)
            
            result = response.get('result', {})
            task_id = result.get('task_id')
            
            if task_id:
                logger.info(f"Батч отправлен, task_id={task_id}, товаров={len(batch)}")
                return {
                    'task_id': task_id,
                    'offer_ids': [p['offer_id'] for p in batch]
                }
            else:
                # Логируем ошибку подробно
                error_msg = response.get('message', 'Unknown error')
                error_code = response.get('code', 'Unknown code')
                logger.error(f"Ошибка API: code={error_code}, message={error_msg}")
                logger.error(f"Полный ответ: {response}")
                return {
                    'error_detail': f"code={error_code}, message={error_msg}",
                    'task_id': None,
                    'offer_ids': [p['offer_id'] for p in batch]
                }
        except Exception as e:
            logger.error(f"Исключение при отправке батча: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'error_detail': str(e),
                'task_id': None,
                'offer_ids': [p['offer_id'] for p in batch]
            }
        
    
    def check_task_status(self, task_id: int) -> Dict[str, Any]:
        """
        Проверяет статус задачи импорта
        
        Args:
            task_id: ID задачи
        Returns:
            {
                "result": {
                "items": [
                {
                "offer_id": "143210608",
                "product_id": 137285792,
                "status": "imported",
                "errors": [ ]
                }
                ],
                "total": 1
            }
        }
        """
        
        response = self.client.post('/v1/product/import/info', {"task_id": task_id})
        result = response.get('result', {})
        items = result.get('items', [])
            
        return items
        
             
    def get_product_specifications(self, offer_ids: List[str]) -> Dict:
        """
        Получает полные данные для батча товаров из API Ozon

        Args:
            offer_ids: список offer_ids (до 1000 штук)

        Returns:
            Dict[str, Dict[str], Any]: {'321650-9R10376': {'offer_id': '321650-9R10376',
                                        'name': 'Чехол на Редми Нот 13 Про 4G / Poco M6 Pro 4G',
                                        'description_category_id': 17028650,
                                        'currency_code': 'RUB',
                                        'price': '499.00',
                                        'old_price': '1999.00',
                                        'vat': '0.22',
                                        'height': 11,
                                        'depth': 233,
                                        'width': 130,
                                        'dimension_unit': 'mm',
                                        'weight': 29,
                                        'weight_unit': 'g',
                                        'attributes': [{'id': 85,
                                                        'complex_id': 0,
                                                        'values': [{'dictionary_value_id': 970617589}]},
            
        """
        
        if not offer_ids:
            return {}
        
        # Убираем дубликаты
        unique_offer_ids = list(set(offer_ids))
        
        result = {}
        
        try:
            # 1. Получаем базовую информацию через /v3/product/info/list
            logger.info(f"Запрос /v3/product/info/list для {len(unique_offer_ids)} товаров...")
            info_response = self.client.post('/v3/product/info/list', {"offer_id": unique_offer_ids})
            info_items = info_response.get('items', [])
            
            # Строим словарь {offer_id: item}
            info_dict = {}
            
            for item in info_items:
                offer_id = item.get('offer_id')
                if offer_id:
                    info_dict[offer_id] = item
            
            logger.info(f"Получено {len(info_dict)} товаров из /v3/product/info/list")
            
            # 2. Получаем атрибуты через /v4/product/info/attributes
            logger.info(f"Запрос /v4/product/info/attributes для {len(unique_offer_ids)} товаров...")
            attrs_response = self.client.post('/v4/product/info/attributes', {"filter": {"offer_id": unique_offer_ids}, "limit": len(unique_offer_ids)})
            attrs_items = attrs_response.get('result', [])
            
            # Строим словарь {offer_id: attributes}
            attrs_dict = {}
            for item in attrs_items:
                offer_id = item.get('offer_id')
                
                if offer_id:
                    attrs_dict[offer_id] = item
            
            logger.info(f"Получено {len(attrs_dict)} товаров из /v4/product/info/attributes")
            
            # 4. Объединяем данные из обоих источников
            for offer_id in unique_offer_ids:
                info_item = info_dict.get(offer_id, {})
                attrs_item = attrs_dict.get(offer_id, {})
                
                if not info_item and not attrs_item:
                    logger.warning(f"Товар {offer_id} не найден в API")
                    continue
                
                product_data = {
                    'offer_id': offer_id,
                    'name': info_item.get('name'),
                    'description_category_id': attrs_item.get('description_category_id'),
                    'currency_code': info_item.get('currency_code'),
                    'price': info_item.get('price'),
                    'old_price': info_item.get('old_price'),
                    'vat': info_item.get('vat'),
                    'height': attrs_item.get('height'),
                    'depth': attrs_item.get('depth'),
                    'width': attrs_item.get('width'),
                    'dimension_unit': attrs_item.get('dimension_unit'),
                    'weight': attrs_item.get('weight'),
                    'weight_unit': attrs_item.get('weight_unit'),
                    'attributes': attrs_item.get('attributes'),
                    'images': attrs_item.get('images'),
                    'primary_image': attrs_item.get('primary_image'),
                    'barcode': attrs_item.get('barcode'),
                    'images360': info_item.get('images360'),
                    'promotions': info_item.get('promotions'),
                    'color_image': attrs_item.get('color_image'),
                    'complex_attributes': attrs_item.get('complex_attributes'),
                    'pdf_list': attrs_item.get('pdf_list'),
                    'type_id': attrs_item.get('type_id')
                }
                
                result[offer_id] = product_data
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения данных батча {e}")
    
    def get_reference_characteristic_values_from_api(self, offer_id, attribute_id: int, description_category_id: int, type_id: int, value: str, status_products, limit: int = 100):
        """
        Получает справочник значений характеристики.

        Args:
            attribute_ids: Список идентификаторов характеристик.
            description_category_id: Идентификатор категории.
            type_id: Идентификатор типа товара.
            status_products: Список со статусами
            
        Returns:
            Dict: {'HWHR10-10-7W056': 
                            {4389: 
                            {'Россия': 90295, 'Китай': 90296, 'Не указана': 90297, ...
            
        """
        # Получаем справочник для характеристки через /v1/description-category/attribute/values/search
        logger.info(f"Запрос /v1/description-category/attribute/values/search для ID: {attribute_id}")
        
        reference_guide = self.client.post('/v1/description-category/attribute/values/search', {"attribute_id": attribute_id, 
                                                                                                "description_category_id": description_category_id, 
                                                                                                "limit": limit, 
                                                                                                "type_id": type_id,
                                                                                                "value": value})
        attrs_items = reference_guide.get('result', [])
        if not attrs_items:
            for status in status_products:
                if status['offer_id'] == offer_id:
                    status['status'] = f'ERROR атрибут="{value}" отсутствует в справочнике Озон'
        
        time.sleep(1)
        
        return attrs_items, status_products
    
    def get_category_characteristics_from_api(self, description_category_id: int, type_id: int):
        """
        Получает справочник значений характеристики.

        Args:
            description_category_id: Идентификатор категории.
            type_id: Идентификатор типа товара.
        Returns:
            Dict: {
                        "result": [
                        {
                        "id": 31,
                        "attribute_complex_id": 32,
                        "name": "Бренд в одежде и обуви",
                        "description": "Укажите наименование бренда, под которым произведён товар. Если товар не имеет бренда, используйте значение \"Нет бренда\"",
                        "type": "string",
                        "is_collection": false,
                        "is_required": true,
                        "is_aspect": false,
                        "max_value_count": 30,
                        "group_name": "",
                        "group_id": 33,
                        "dictionary_id": 28732849,
                        "category_dependent": true,
                        "complex_is_collection": true
                        }
                    ]
                }
        """
        
        # Получаем характеристки товара через /v1/description-category/attribute
        logger.info(f"Запрос /v1/description-category/attribute")
        reference_guide = self.client.post('/v1/description-category/attribute', {"description_category_id": description_category_id, "language": "DEFAULT", "type_id": type_id})
        characteristic_items = reference_guide.get('result', [])
        
        return characteristic_items
        
            
class OzonAPIClient:
    """Клиент для Ozon API"""
    
    BASE_URL = "https://api-seller.ozon.ru"
    
    def __init__(self, client_id: int, api_key: str, max_retries: int = 5):
        self.client_id = client_id
        self.api_key = api_key
        self.max_retries = max_retries
        
        self.session = requests.Session()
        self.session.headers.update({
            'Client-Id': str(client_id),
            'Api-Key': api_key,
            'Content-Type': 'application/json'
        })
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Выполняет запрос к API"""
        if endpoint.startswith('/'):
            endpoint = endpoint
        
        url = f"{self.BASE_URL}{endpoint}"
        logger.debug(f"Запрос к URL: {url}")
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=30)
                else:
                    response = self.session.post(url, json=data, timeout=30)
                
                # 429 Too Many Requests
                if response.status_code == 429:
                    delay = min(20, 0.5 * 2**attempt)
                    try:
                        error_text = response.json()
                        logger.error(f"Не удалось выполнить запрос к API. \
                                    Статус: {response.status_code} : {error_text}. Повтор через {delay} сек. Попытка[{attempt+1}/{self.max_retries}]")
                    except Exception as e:
                        logger.error(f"Ошибка парсинга 429: {e}")
                    time.sleep(delay)
                    continue
                            
                # 5xx ошибки сервера
                if 500 <= response.status_code < 600:
                    delay = min(30, 2 ** attempt)
                    logger.warning(f"Ошибка сервера {response.status_code}. Повтор через {delay} сек.")
                    time.sleep(delay)
                    continue
                
                # Успех
                if response.status_code == 200:
                    return response.json()
                
                # Остальные ошибки
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise RuntimeError(f"Ozon API error: {error_msg}")
                
            except requests.Timeout as e:
                logger.warning(f"Таймаут, попытка {attempt+1}/{self.max_retries}: {e}")
                time.sleep(2 ** attempt)
            except requests.ConnectionError as e:
                logger.warning(f"Ошибка соединения, попытка {attempt+1}/{self.max_retries}: {e}")
                time.sleep(2 ** attempt)
        
        raise RuntimeError(f"Не удалось выполнить запрос после {self.max_retries} попыток")
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        """POST запрос"""
        return self._request('POST', endpoint, data)


def chunks(lst: list, n: int):
    """Разбивает список на чанки по n элементов"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def apply_root_changes(all_products_from_api: Dict, df: pd.DataFrame):
    """
    Применяет изменение из Excel к root-полям для всех товаров.

    Args:
        all_products_from_api: словарь {ip: {offer_id: {product_data}}} {'Название': {'HWHN10XL-10-7Q00060': {'offer_id': 'HWHN10XL-10-7Q00060',
                                                                'name': 'Чехол на Хонор 10Х Лайт силиконовый с принтом "Динозаврики"',
                                                                'attributes': [{'id': 85,
                                                                'complex_id': 0,
                                                                'values': [{'dictionary_value_id': 970617589, 'value': 'Значение'}]},
        df: колонки - ip, offer_id, name..
        
    Returns: Обновленный all_products_from_api - будут обновлены root поля: {'Название': 
                                                                            {'HWHR10-10-7W056': 
                                                                            {'offer_id': 'HWHR10-10-7W056', 'name': 'Чехол на Хонор 10 с цветочками...
    """
    
    updater_product = all_products_from_api.copy()
    
    df_dict = {}
    
    TYPING_MAPPING = {
        'offer_id': str,
        'barcode': str,
        'color_image': str,
        'currency_code': str,
        'depth': int,
        'description_category_id': int,
        'dimension_unit': str,
        'height': int,
        'name': str,
        'old_price': str,
        'price': str,
        'primary_image': str,
        'type_id': int,
        'vat': str,
        'weight': int,
        'weight_unit': str,
        'width': int,
    }
    
    # Преобразуем датафрейм в словарь
    for row_dict in df.to_dict('records'):
        df_dict[row_dict['offer_id']] = row_dict
    
    # Меняем root атрибуты в целевом словаре словарей        
    for _, product_data in updater_product.items():
        for offer_id, product in product_data.items():
            for name_attr, value_attr in df_dict[offer_id].items():
                if value_attr and name_attr in product:
                    if name_attr == 'images':
                        product[name_attr] = [i.strip() for i in value_attr.split(';')]
                    elif name_attr == 'images360':
                        product[name_attr] = [i.strip() for i in value_attr.split(';')]
                    else:
                        product[name_attr] = TYPING_MAPPING[name_attr](value_attr)
    
    for offer_id, product_data in df_dict.items():
        try:
            if product_data['ссылки на дополнительные фото']:
                item = [i.strip() for i in product_data['ссылки на дополнительные фото'].split(';')]
                updater_product[product_data['ip']][offer_id]['images'].extend(item)
        except Exception:
            continue
    
    for offer_id, product_data in df_dict.items():
        try:
            if product_data['доп. фото 360']:
                item = [i.strip() for i in product_data['доп. фото 360'].split(';')]
                updater_product[product_data['ip']][offer_id]['images360'].extend(item)
        except Exception:
            continue    
   
                
    return updater_product               

                     
def get_all_attributes_for_update(df, map_mapping: Dict) -> Dict:
    """
    Маппинг атрибутов. Получаем только те атрибуты, которые нужно обновить в массиве attributes

    Args:
        df: с колонками ip, offer_id, name...
        map_mapping: {
                        'Вид чехла': 5938,
                        '#Хештеги': 23171,
                        'Название модели (для объединения в одну карточку)': 9048,
                        'Вид выпуска товара': 22270,
                        'Бренд': 85,
                        'Страна-изготовитель': 4389,
                        'ТН ВЭД коды ЕАЭС': 22232, ...
    
    Returns:
            Dict[int: {Any}]: {'HWHR10-10-7W056': {23171: '#хештег', 4389: 'Россия', 4383: 60, 4191: 'Описание товра'}}
    """
    
    all_id_attributes = {}
    
    # Извлекаем все id атрибутов, которые нужно обновить
    for row_dict in df.to_dict('records'):
        items = {}
        for key_df, value_df in row_dict.items():
            if key_df in map_mapping and value_df:
                items[map_mapping[key_df]] = value_df
                
        if items:
            all_id_attributes[row_dict['offer_id']] = items
    
    return all_id_attributes


def get_attributes_for_changes(all_attributes_for_update: Dict, category_characteristics_from_api: List[Dict]) -> Dict:
    """
    Формирует id по которым нужно получить справочники для массива attributes

    Args:
        all_attributes_for_update: Атрибуты, которые нужно обновить + значения - {'HWHR10-10-7W056': {23171: '#хештег', 4389: 'Россия', 4383: 60, 4191: 'Описание товра'}}
        category_characteristics_from_api: [{'id': 10096, 
                                            'attribute_complex_id': 0, 
                                            'name': 'Цвет товара', 
                                            'description': 'Основной или доминирующий цвет товара. Если точного соответствия нет, используйте ближайшие цвета.,
                                            'type': 'String', 
                                            'is_collection': True, 
                                            'is_required': False, 
                                            'is_aspect': True, 
                                            'max_value_count': 0, 
                                            'group_name': '', 
                                            'group_id': 0, 
                                            'dictionary_id': 1494, 
                                            'category_dependent': True, 
                                            'complex_is_collection': False}]
    Returns:
            Dict[List]: {'HWHR10-10-7W056': [4389]}
    """
    # Множество, где будут храниться только те id , для которых нужен справочник
    attributes_for_directory = {}
    
    # Определяеми, для каких атрибутов нужен справочник категорий        
    for offer_id, attributes in all_attributes_for_update.items():
        attributes_for_directory[offer_id] = []
        for id_for_update, _ in attributes.items():
            for directory in category_characteristics_from_api:
                if id_for_update == directory['id']:
                    if directory['dictionary_id'] > 0:
                        attributes_for_directory[offer_id].append(id_for_update)
                 
    return attributes_for_directory


def get_new_attributes_for_add(all_products_from_api: Dict, master_update_preparation: Dict, key: bool) -> set:
    """
    Возвращает множество с id атрибутами, которые нужно создать т.е. создать новые по причине их отсутсвия в данных АПИ

    Args:
        all_products_from_api: {ip: {offer_id: {product_data}}}
        master_update_preparation: {'302350-9R102': {4389: [{'dictionary_value_id': 90296, 'value': 'Китай'}],
    Returns:
            Dict: атрибуты, которые нужно обновить {offer_id: [1231, 3243, 4235]}
    """
    
    old_ids = {}
    new_ids = {}
    
    # Получаем все id атрибутов, которые у нас уже есть
    for _, product_data in all_products_from_api.items():
        for offer_id, products in product_data.items():
            old_ids[offer_id] = set()
            for attributes_product in products[key]:
                old_ids[offer_id].add(attributes_product['id'])
    
    # Получаем id атрибутов из датафрейма (возможно там будут новые)
    for offer_id, product_data in master_update_preparation.items():
        new_ids[offer_id] = set()
        for id, _ in product_data.items():
            new_ids[offer_id].add(id)
    
   
    result = {}
    for offer_id, _ in new_ids.items():
        ids = new_ids[offer_id] - old_ids[offer_id]
        result[offer_id] = list(ids)
    
    
    return result


def apply_attribute_changes(all_products_from_api: Dict, 
                            all_attributes_for_update: Dict, 
                            characteristic_for_attributes_from_api: Dict, 
                            attributes_complex_ids: Dict, 
                            attributes_or_complex_attributes: bool) -> Dict:
    """
    Обновляет массив attributes в словаре с характеристиками

    Args:
        all_products_from_api: {ip: {offer_id: {product_data}}} - {'Название': {'HWHR10-10-7W056': {'offer_id': 'HWHR10-10-7W056', 'name': 'Apple', 'description_category_id': 17028650, 'currency_code': 'RUB',
        all_attributes_for_update: словарь только тех атрибутов, которые нужно обновить - {'HWHR10-10-7W056': {23171: '#хештег', 4389: 'Россия', 4383: '60', 4191: 'Описание товра'}}
        characteristic_for_attributes_from_api: словарь со справочниками атрибутов - может быть пустым - {'HWHR10-10-7W056': {4389: {'Россия': 90295, 'Китай': 90296, 'Не указана': 90297, 'Италия': 90298, 'США': 90299,
        attributes_complex_ids: {23171: 0, 4389: 0, 4383: 0, 4191: 0}
        attributes_or_complex_attributes: Флаг для фильтра, если False, то атрибуты будем искать в массиве attributes, если True, то в complex_attributes
    Returns:
            Dict[int: str]: {ip: {offer_id: {product_data}}} - {'Название': {'HWHR10-10-7W056': {'offer_id': 'HWHR10-10-7W056', 'name': 'Apple', 'description_category_id': 17028650, 'currency_code': 'RUB', 
    """
    if attributes_or_complex_attributes:
        KEY = 'complex_attributes'
    else:
        KEY = 'attributes'
    
    
    upload_product = all_products_from_api.copy()
    
    master_update_preparation  = {}
    
    # Готовим updater для обновления. Проверяем значения - одно ли оно или их несколько.
    for offer_id, attributes in all_attributes_for_update.items():
        master_update_preparation[offer_id] = {}
        for id, value in attributes.items():
            master_update_preparation[offer_id].update({id: []})
            
    
    if characteristic_for_attributes_from_api:
        # Готовим атрибуты для обновления - обрабатываем справочные атрибуты
        for offer_id, attributes in all_attributes_for_update.items():
            if characteristic_for_attributes_from_api[offer_id]:
                for id_attr, directory in characteristic_for_attributes_from_api[offer_id].items():
                    if isinstance(attributes[id_attr], list):
                        for attr in attributes[id_attr]:
                            dictionary_value_id = directory[attr]
                            item = {'dictionary_value_id': dictionary_value_id, 'value': attr}
                            master_update_preparation[offer_id][id_attr].append(item)
                    else:
                        dictionary_value_id = directory[attributes[id_attr]]
                        item = {'dictionary_value_id': dictionary_value_id, 'value': attributes[id_attr]}
                        master_update_preparation[offer_id][id_attr].append(item)
        
            
    # Обрабатываем несправочные атрибуты 
    for offer_id, attributes in master_update_preparation.items():
        for id_attr, values in attributes.items():
            if not values:
                value = all_attributes_for_update[offer_id][id_attr]
                if isinstance(value, list):
                    for val in value:
                        item = {'dictionary_value_id': 0, 'value': val}
                        master_update_preparation[offer_id][id_attr].append(item)
                else:
                    item = {'dictionary_value_id': 0, 'value': value}
                    master_update_preparation[offer_id][id_attr].append(item)
    

    # Узнаем, существуют ли новые атрибуты, которые, есть в датафрейме, но не получены по АПИ
    new_ids = get_new_attributes_for_add(all_products_from_api, master_update_preparation, KEY)        
    
    # Меняем уже существующие attributes на новые
    for _, product_data in upload_product.items():
        for offer_id, products in product_data.items():
            if offer_id in master_update_preparation:
                for offer_id_values, attributes_values in master_update_preparation.items():
                    if offer_id == offer_id_values:
                        for attributes_product in products[KEY]:
                            if attributes_product['id'] in attributes_values:
                                attributes_product['values'] = attributes_values[attributes_product['id']]
                                attributes_product['complex_id'] = attributes_complex_ids[attributes_product['id']]
    
    # Добавляем новые атрибуты, которых пока нет в итоговом словаре словарей
    if any(new_ids.values()):
        for offer_id_new_ids, value_new_ids in new_ids.items():
            for _, product_data in upload_product.items():
                for offer_id, products in product_data.items():
                    if offer_id == offer_id_new_ids:
                        for new_id in value_new_ids:
                            item = {'id': new_id, 'complex_id': attributes_complex_ids[new_id], 'values': master_update_preparation[offer_id_new_ids][new_id]}
                            products[KEY].append(item)
                            
    return upload_product           
                        

def get_complex_attributes_ids(all_attributes_for_update: Dict, category_characteristics_from_api: Dict) -> Dict:
    """
    Возвращает словарь id: attribute_complex_id

    Args:
        all_attributes_for_update: {offer_id: {id: value}} - {'HWHR10-10-7W056': {23171: '#хештег', 4389: 'Россия', 4383: 60, 4191: 'Описание товра'}}
        category_characteristics_from_api: список словарей [{name: value}] - [{'id': 21841, 
                                                                                'attribute_complex_id': 100001, 
                                                                                'name': 'Озон.Видео: ссылка', 
                                                                                'description': 'Укажите ссылку на видео (MP4, MOV). Продолжительность от 8 сек до 5 минут, размер файла не более 2ГБ', 
                                                                                'type': 'String', 
                                                                                'is_collection': False, 
                                                                                'is_required': False, 
                                                                                'is_aspect': False, 
                                                                                'max_value_count': 0, 
                                                                                'group_name': '', 
                                                                                'group_id': 0, 
                                                                                'dictionary_id': 0, 
                                                                                'category_dependent': False, 
                                                                                'complex_is_collection': True},
    Returns:
            Dict[int: int]: {23171: 0, 4389: 0, 4383: 0, 4191: 0}
    """
    
    attribute_complex_id = {}
    
    for _, attributes in all_attributes_for_update.items():
        for id in attributes:
            for characteristic in category_characteristics_from_api:
                if id == characteristic['id']:
                    attribute_complex_id[id] = characteristic['attribute_complex_id']
    
    return attribute_complex_id


def update_typing_attributes(all_attributes_for_update: Dict, typing_attributes: Dict):
    """
    Возвращает словарь c измененными типами данных

    Args:
        all_attributes_for_update: {'HWHR10-10-7W056': {23171: '#хештег', 4389: 'Россия', 4383: 60, 4191: 'Описание товра'}}
        typing_attributes: {5938: str, 23171: str, 9048: str, ...
    Returns:   
            Dict: {offer_id: {id: value}}: all_attributes_for_update с обновленными типами данных
    """
    
    for id, type in typing_attributes.items():
        for _, attributes in all_attributes_for_update.items():
            try:
                # Отдельная обработка для rich контента
                if id == 11254:
                    attributes[id] = json.dumps(json.loads(attributes[id]))
                else:
                    attributes[id] = type(attributes[id])  
            except Exception:
                continue
        
    return all_attributes_for_update


def update_video_attributes(df, all_products_from_api):
    """
    Возвращает словарь c измененными типами данных

    Args:
        all_attributes_for_update: словарь словарей {offer_id: {id: value}}
        ТYPING_ATTRIBUTES: словарь {id: type}
    Returns:
            Dict: {offer_id: {id: value}}
    """
    
    upload_product = all_products_from_api.copy()
    
    if 'доп. озон.видео: ссылка' in df.columns:
        video_url = df.set_index('offer_id')['доп. озон.видео: ссылка'].dropna().to_dict()
        for offer_id, attributes in video_url.items():
            urls = [i.strip() for i in attributes.split(';')]
            for _, product_data in upload_product.items():
                for offer_id_product, attributes_product in product_data.items():
                    if offer_id == offer_id_product:
                        for complex_attributres in attributes_product['complex_attributes']:
                            if complex_attributres['id'] == 21841:
                                for url in urls:
                                    complex_attributres['values'].append({'dictionary_value_id': 0, 'value': url})
    
    if 'доп. озон.видео: название' in df.columns:
        video_name = df.set_index('offer_id')['доп. озон.видео: название'].dropna().to_dict()
        for offer_id, attributes in video_name.items():
            names = [i.strip() for i in attributes.split(';')]
            for _, product_data in upload_product.items():
                for offer_id_product, attributes_product in product_data.items():
                    if offer_id == offer_id_product:
                        for complex_attributres in attributes_product['complex_attributes']:
                            if complex_attributres['id'] == 21837:
                                for name in names:
                                    complex_attributres['values'].append({'dictionary_value_id': 0, 'value': name})
                                
    return upload_product
    

def save_report_to_reports(df_report: pd.DataFrame, current_time, SCRIPT_NAME) -> str:
    """
    Создает папку reports
    Сохраняет ДатаФрейм в папку reports

    Args:
        df_report: DataFrame c  колонками ip, offer_id, task_id, status, error
    Returns:
        str: Путь к сохраненному файлу
    """
    try:
        script_dir = Path(__file__).resolve().parent
    except NameError:
        script_dir = Path.cwd()
        
    # Создаем папку reports
    report_dir = script_dir / "reports"
    report_dir.mkdir(exist_ok=True)
    
    # Формируем имя файла с датой и временем
    filename = f"{SCRIPT_NAME}_{current_time}.xlsx"
    file_path = report_dir / filename
    
    df_report.to_excel(file_path, index=False)
    
    return filename, str(file_path)


def fix_complex_attributes(product_data):
    
    if 'complex_attributes' not in product_data:
        return product_data
    
    old_coplex = product_data['complex_attributes']
    
    # Если уже правильный формат - пропускаем
    if old_coplex and 'attributes' in old_coplex[0]:
        return product_data
    
    # Преобразуем
    new_complex = [{'attributes': old_coplex}]
    product_data['complex_attributes'] = new_complex
    
    return product_data


def preparation_complex_attributes(all_products_from_api):
    """
        Возвращает словарь с измененной структурой комплексных атрибутов.
    
        Args:
            all_products_from_api: 'complex_attributes': [{'id': 21837, 'complex_id': 100001, 'values': [{'dictionary_value_id': 0, 'value': 'Обзор'}]}
        Returns:
            all_products_from_api: "complex_attributes": [
                                                            {
                                                                "attributes": [
                                                                {
                                                                    "id": 21845,
                                                                    "complex_id": 100002,
                                                                    "values": [
                                                                    {
                                                                    "dictionary_value_id": 0,
                                                                    "value": "ссылка на фото"
                                                                    }
                                                                    ]
                                                                }
                                                                ]
                                                            }
                                                            ]
        """
    for ip, products in all_products_from_api.items():
        for offer_id, product_data in products.items():
            all_products_from_api[ip][offer_id] = fix_complex_attributes(product_data)
    
    return all_products_from_api


def delete_error_characetristic(all_products_from_api, status_products, all_attributes_for_update=None):
    """
    Удаляет товар по offer_id, если он имеет статус ERROR

    Args:
        all_products_from_api: {'Seller': {'12559-9C506764': {'offer_id': '12559-9C506764', 'name': 'Чехол на Айфон 12 с картой', 'description_category_id': 17028650, 'currency_code': 'RUB', ...
        all_attributes_for_update: {'12559-9C506764': {4389: 'fdgdfhg', 10096: 'bxdcb'}}
        status_products: [{'offer_id': '12559-9C506764', 'ip': 'Seller', 'status': 'ERROR атрибут="bxdcb" отсутсвует в справочнике Озон'}]
    Returns:
        result: Обновленный all_products_from_api
    """
    result_all_product = {}
    result_all_attributes = {}
    
    delete_offer_ids = []
    
    # Собираем статусы ERROR
    for status in status_products:
        if status['status'] != 'OK':
            delete_offer_ids.append(status['offer_id'])
    
    # Если статусов ERROR нет - ничего не меняем
    if not delete_offer_ids:
        return all_products_from_api, all_attributes_for_update
    
    # Удаляем offer_id со статусом ERROR из all_products_from_api
    for ip, product_data in all_products_from_api.items():
        for offer_id, product in product_data.items():
            if offer_id not in delete_offer_ids:
                if ip in result_all_product:
                    result_all_product[ip].update({offer_id: product})
                else:
                    result_all_product[ip] = {offer_id: product}
    
    # Удаляем offer_id со статусом ERROR из all_attributes_for_update
    if all_attributes_for_update:
        for offer_id, product_data in all_attributes_for_update.items():
            if offer_id not in delete_offer_ids:
                result_all_attributes[offer_id] = product_data
    
    logger.warning(f"Справочные атрибуты товаров={delete_offer_ids} заполнены неверно!\nИх не удалось найти в справочнике Озон!\nТовары будут пропущены и не будут обновлены!")
    
    return result_all_product, result_all_attributes
    
    
# Создаем словарь токенов
try:
    auth = OzonAuth(PATH_TOKENS)
except Exception as e:
    logger.info(f'Произошла ошибка связанная с загрузкой токенов с сетевого диска.\nТекст ошибки: {e}\nПроверьте, если ли у вас доступ с сетевому диску!')
    input('\nНажмите Enter для выхода...')
    sys.exit(1)

# Валидация файла
try:
    source_file = ExcelFileProcessor("Обновление х-р Ozon.xlsx")
except Exception as e:
    logger.info(f'Произошла ошибка связанная с валидацией файла "Обновление х-р Ozon.xlsx".\nТекст ошибки: {e}\nПроверьте входной файл!')
    input('\nНажмите Enter для выхода...')
    sys.exit(1)

# Создаем список статусов, куда будем собирать ошибки
status_products = source_file.get_status_list()

df = source_file.df

groups = df.groupby('ip')
# Словарь словарей ИП: все данные по всем offer_id
all_products_from_api = {}

for ip, group_df in groups:
    # Получаем токен для определнного IP
    seller = auth.get_credentials(ip)
    # Готовим общий словарь словарей
    all_products_from_api[ip] = {}
    # Создаем клиент API
    client = OzonAPIClient(client_id=seller['client_id'], api_key=seller['api_key'], max_retries=5)
    updater = AttributesUpdater(client)
    # Обрабатываем товары этого IP
    offer_ids = group_df['offer_id'].tolist()
    logger.info(f"Обработка IP: {ip}, товаров: {len(offer_ids)}")
    
    # Обработка всех данных из API
    for chunk in chunks(offer_ids, 1000):
        # Запрос к двум методам API для получения характеристик
        try:
            batch_data = updater.get_product_specifications(chunk)
        except Exception as e:
            logger.info(f'Произошла ошибка связанная с получением информации о товарах по АПИ.\nТекст ошибки: {e}\nВозможные причины: 1. ошибка на стороне Озон, 2. offer_id не найден в системе Озон!')
            input('\nНажмите Enter для выхода...')
            for status in status_products:
                if status['offer_id'] in chunk:
                    status['status'] = f'ERROR ошибка связана с получением информации о товарах по АПИ={e}'
            continue
        time.sleep(1)
        # Добавляем все характеристики в один словарь словарей
        all_products_from_api[ip].update(batch_data)

# Извлекаем description_category_id и type_id для запроса к API, чтобы получить справочники атрибутов
description_category_id = None
type_id = None
for _, product_data in all_products_from_api.items():
    for _, characteristic in product_data.items():
        description_category_id = characteristic.get('description_category_id', DESCRIPTION_CATEGORY_ID)
        type_id = characteristic.get('type_id', TYPE_ID)
        if description_category_id and type_id:
            break

# Обновляем корень словаря словарей данными из Датафрейма
all_products_from_api = apply_root_changes(all_products_from_api, df)

# Загружаем характеристики товара по АПИ. Это нужно для того, чтобы точно узнать: 1. Какие характеристики существуют. 2. Для какие атрибутов нужны будут справочники
try:
    category_characteristics_from_api = updater.get_category_characteristics_from_api(description_category_id, type_id)
except Exception as e:
    logger.info(f'Произошла ошибка связанная с получением cписка характеристик категории по АПИ\nТекст ошибки: {e}\nВозможная причина: ошибка на стороне Озон')
    input('\nНажмите Enter для выхода...')
    sys.exit(1)


# Готовим атрибуты для обновления

# 1. Получаем атрибуты, которые нам нужно обновить + их значения
all_attributes_for_update = get_all_attributes_for_update(df, ATTRIBUTES_MAPPING)

# 2. Приводим атрибуты к нужным типам данным
if all_attributes_for_update:
    all_attributes_for_update = update_typing_attributes(all_attributes_for_update, ТYPING_ATTRIBUTES)

    # 3. Получаем id атрибута + complex_id
    attributes_complex_ids = get_complex_attributes_ids(all_attributes_for_update, category_characteristics_from_api)
    
    # 4. Получаем атрибуты для которых нужны справочники
    attributes_for_directory = get_attributes_for_changes(all_attributes_for_update, category_characteristics_from_api)

    # split если нужно
    for offer_id, attributes in all_attributes_for_update.items():
        for id, value in attributes.items():
            try:
                if ';' in value:
                    value = [i.strip() for i in value.split(';')]
                    all_attributes_for_update[offer_id][id] = value
            except Exception:
                continue
                        
    # Словарь для хранения справочников
    characteristic_for_attributes_from_api = {}
    
    if any(attributes_for_directory.values()):
        for offer_id, attribute_ids in attributes_for_directory.items():
            for attribute_id in attribute_ids:
                # Получаем значение к которому нужен ID
                value = all_attributes_for_update[offer_id][attribute_id]
                characteristic_for_attributes_from_api[offer_id] = {attribute_id:{}}
                if isinstance(value, list):
                    for val in value:
                        # Запрос к API
                        try:
                            attrs_items, status_products = updater.get_reference_characteristic_values_from_api(offer_id, attribute_id, description_category_id, type_id, val, status_products)
                            if attrs_items:
                                for attr in attrs_items:
                                    if attr['value'] == val:
                                        characteristic_for_attributes_from_api[offer_id][attribute_id].update({val: attr['id']})
                        except Exception as e:
                            logger.warning(f'Произошла ошибка связаная с получением справочной информации по АПИ.\nТекст ошибки: {e}\nВозможные причины: 1. ошибка на стороне Озон')
                            continue
                        
                else:
                    try:
                        attrs_items, status_products = updater.get_reference_characteristic_values_from_api(offer_id, attribute_id, description_category_id, type_id, value, status_products)
                        if attrs_items:
                            for attr in attrs_items:
                                if attr['value'] == value:
                                    characteristic_for_attributes_from_api[offer_id][attribute_id].update({value: attr['id']})   
                    except Exception as e:
                        logger.warning(f'Произошла ошибка связаная с получением справочной информации по АПИ.\nТекст ошибки: {e}\nВозможные причины: 1. ошибка на стороне Озон')
                        continue
                  
    # Удаляем товары со статусом ERROR
    all_products_from_api, all_attributes_for_update = delete_error_characetristic(all_products_from_api, status_products, all_attributes_for_update)
            
    # Обновляем атрибуты словаря словарей данными
    all_products_from_api = apply_attribute_changes(all_products_from_api, all_attributes_for_update, characteristic_for_attributes_from_api, attributes_complex_ids, attributes_or_complex_attributes=False)

# Готовим комплекс атрибуты для обновления

# 1. Получаем комплекс атрибуты, которые нам нужно обновить + их значения
all_complex_attributes_for_update = get_all_attributes_for_update(df, COMPLEX_ATTRIBUTES_MAPPING)

if all_complex_attributes_for_update:
    # 2. Приводим атрибуты к нужным типам данным
    all_complex_attributes_for_update = update_typing_attributes(all_complex_attributes_for_update, ТYPING_ATTRIBUTES)

    # 3. Получаем id атрибута + complex_id
    complex_attributes_complex_id = get_complex_attributes_ids(all_complex_attributes_for_update, category_characteristics_from_api)

    # 4. Получаем атрибуты для которых нужны справочники
    complex_attributes_for_directory = get_attributes_for_changes(all_complex_attributes_for_update, category_characteristics_from_api)
    
    # split если нужно
    for offer_id, attributes in all_complex_attributes_for_update.items():
        for id, value in attributes.items():
            try:
                if ';' in value:
                    value = [i.strip() for i in value.split(';')]
                    all_complex_attributes_for_update[offer_id][id] = value
            except Exception:
                continue

    # Словарь для хранения справочников
    characteristic_for_complex_attributes_from_api = {}
    
    if any(complex_attributes_for_directory.values()):
        for offer_id, attribute_ids in complex_attributes_for_directory.items():
            for attribute_id in attribute_ids:
                characteristic_for_complex_attributes_from_api[offer_id] = {attribute_id:{}}
                # Получаем значение к которому нужен ID
                value = all_complex_attributes_for_update[offer_id][attribute_id]
                if isinstance(value, list):
                    for val in value:
                        # Запрос к API
                        try:
                            attrs_items, status_products = updater.get_reference_characteristic_values_from_api(offer_id, attribute_id, description_category_id, type_id, val, status_products)
                            if attrs_items:
                                for attr in attrs_items:
                                    if attr['value'] == val:
                                        characteristic_for_complex_attributes_from_api[offer_id][attribute_id].update({val: attr['id']})
                        except Exception as e:
                            logger.warning(f'Произошла ошибка связаная с получением справочной информации по АПИ.\nТекст ошибки: {e}\nВозможные причины: 1. ошибка на стороне Озон')
                            continue
                        
                else:
                    try:
                        attrs_items, status_products = updater.get_reference_characteristic_values_from_api(offer_id, attribute_id, description_category_id, type_id, value, status_products)
                        if attrs_items:
                            for attr in attrs_items:
                                if attr['value'] == value:
                                    characteristic_for_complex_attributes_from_api[offer_id][attribute_id].update({value: attr['id']})   
                    except Exception as e:
                        logger.warning(f'Произошла ошибка связаная с получением справочной информации по АПИ.\nТекст ошибки: {e}\nВозможные причины: 1. ошибка на стороне Озон')
                        continue
        
    all_products_from_api, all_complex_attributes_for_update = delete_error_characetristic(all_products_from_api, status_products, all_complex_attributes_for_update)
    # Обновляем атрибуты словаря словарей данными, если нужно
    
    # Обновляем комплекс атрибуты словаря словарей данными, если нужно
    all_products_from_api = apply_attribute_changes(all_products_from_api, all_complex_attributes_for_update, characteristic_for_complex_attributes_from_api, complex_attributes_complex_id, attributes_or_complex_attributes=True)
      
if 'доп. озон.видео: ссылка' in df.columns or 'доп. озон.видео: название' in df.columns:
    all_products_from_api = update_video_attributes(df, all_products_from_api)

# Обрабатываем complex_attributes - приводим к API формату по документации
all_products_from_api = preparation_complex_attributes(all_products_from_api)

# Список результатов отправки
all_tasks_from_api = {}

for ip, product_by_offer in all_products_from_api.items():
    if not product_by_offer:
        continue
    # Получаем токен для определенного IP
    seller = auth.get_credentials(ip)
    # Создаем клиент API
    client = OzonAPIClient(client_id=seller['client_id'], api_key=seller['api_key'], max_retries=5)
    updater = AttributesUpdater(client)
    
    all_tasks_from_api[ip] = []
    product_list = list(product_by_offer.values())
    
    logger.info(f"Отправка {len(product_list)} товаров для IP: {ip}")
    
    # Разбиваем на батчи по 100
    for batch in chunks(product_list, 100):
        try:
            result = updater.send_batch(batch)
        except Exception as e:
            logger.info(f'Произошла ошибка, связанная с отправкой характеристик по АПИ.\nТекст ошибки: {e}\nВозможные причины: Ошибка на стороне Озон'
                        f'ИП: {seller['ip_name']}'
                        f'Артикулы: {[p['offer_id'] for p in batch]}')
            for product in batch:
                for status in status_products:
                    if status['offer_id'] == product['offer_id']:
                        status['status'] = f'ERROR Произошла ошибка при отправки товаров! Текст ошибки={e}'
            continue
        all_tasks_from_api[ip].append(result)
        logger.info(f"Батч отправлен: {len(batch)} товаров, task_id={result.get('task_id')}")

logger.debug(f"Сформирован all_tasks_from_api={all_tasks_from_api}")

# Ждем проверку от Озон. Модерация от Озон длится примерно 50 секунд.
logger.info("Ждём 50 секунд, пока Озон проверит товары!")
time.sleep(50)
logger.info("Проверяем статусы товаров!")

# Проверяем товары 
for ip, tasks in all_tasks_from_api.items():
     # Получаем токен для определенного IP
    seller = auth.get_credentials(ip)
    # Создаем клиент API
    client = OzonAPIClient(client_id=seller['client_id'], api_key=seller['api_key'], max_retries=5)
    updater = AttributesUpdater(client)
    
    for task in tasks:
        if task['task_id'] is not None:
            try:
                status_info = updater.check_task_status(task['task_id'])
                logger.debug(f'check_task_status={status_info}')
                for status in status_info:
                    if status["errors"]:
                        for status_pr in status_products:
                            if status['offer_id'] == status_pr['offer_id']:
                                for error in status["errors"]:
                                    if error["message"]:
                                        status_pr['status'] = f'ERROR {error["message"]}'
                    if status['status'] == 'skipped':
                        for status_pr in status_products:
                            if status['offer_id'] == status_pr['offer_id']:
                                status_pr['status'] = f'ERROR Статус "skipped" означает, что API не увидел изменений'
            except Exception as e:
                logger.error(f'Произошла ошибка, связанная с получением статуса по АПИ.\nТекст ошибки: {e}\nВозможные причины: Ошибка на стороне Озон'
                            f'ИП: {ip}'
                            f'ID задачи: {task['task_id']}'
                            f'Артикул: {task['offer_ids']}')
                for offer_id in task['offer_ids']:
                    for status in status_products:
                        if status['offer_id'] == offer_id:
                            status['status'] = f'ERROR Произошла ошибка при отправки товаров! Текст ошибки={e}'
                continue
        else:
            for offer_id in task['offer_ids']:
                for status in status_products:
                    if status['offer_id'] == offer_id:
                        status['status'] = f'Ошибка получения task_id! Текст ошибки={task['error_detail']}'

logger.debug(f"Сформирован финальный status_products={status_products}")

# Создаем датафрейм c отчетом по каждому offer_id
df_report = pd.DataFrame(status_products)

# Сохраняем отчет в папку reports
filename, file_path = save_report_to_reports(df_report, current_time, SCRIPT_NAME)
logger.info(f"Отчет сохранён: {file_path}")

report_message = f"(ozon_update_characteristics)\nОбновленно товаров : \
{df_report[df_report['status']=='OK'].shape[0]}\nОшибок : \
{df_report[df_report['status']!='OK'].shape[0]}"

# Отравляем отчет в Битрикс24
try:
    # Отправка файла
    bitrix_bot.send_file(
        dialog_id=BITRIX_CHAT_ID,
        file_path=file_path,
        message=report_message
    )
    logger.info(f"{filename} отправлен в битрикс чат")
finally:
    # Удаление файла после отправки
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.debug(f"Файл {filename} успешно удален")
        except Exception as e:
            logger.debug(f"Ошибка при удалении файла: {str(e)}")
    else:
        logger.error(f"Файл {filename} не найден для удаления")
