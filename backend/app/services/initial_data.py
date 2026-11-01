"""
Initial data loader for the transport management system.
Parsed directly from the company's Excel sheets.
"""
import re
from datetime import datetime, date
from typing import Optional, Tuple

def normalize_plate(plate: str) -> str:
    if not plate:
        return ""
    # Remove spaces, dashes, slashes, uppercase
    cleaned = re.sub(r'[\s\-\/\.]', '', str(plate)).upper()
    return cleaned

def format_plate_display(plate: str) -> str:
    norm = normalize_plate(plate)
    # KZ standard plates like 014GI02 -> 014 GI 02
    m = re.match(r'^(\d{3})([A-ZА-Я]{2,3})(\d{2})$', norm)
    if m:
        return f"{m.group(1)} {m.group(2)} {m.group(3)}"
    return norm

def parse_date(date_str: str) -> Optional[date]:
    if not date_str:
        return None
    val = str(date_str).strip()
    if val in ["***", "", "нет", "NaN", "списание", "продан"]:
        return None
    
    # Try YYYY-MM-DD
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except ValueError:
        pass
    
    # Try DD.MM.YYYY or DD.MM.YY
    try:
        parts = val.split('.')
        if len(parts) == 3:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            if year < 100:
                year += 2000
            return date(year, month, day)
    except Exception:
        pass
    return None

# Companies list
COMPANIES_DATA = [
    {"name": "ТОО «Meganet»", "code": "Meganet"},
    {"name": "ТОО «Elite ProBuilding»", "code": "EPB"},
    {"name": "ТОО «NLS KAZAKHSTAN»", "code": "NLS"},
    {"name": "ТОО «СвязьСервисКомплект»", "code": "CCK"},
]

# Departments list
DEPARTMENTS_DATA = [
    {"name": "Юго-Запад", "head_name": "Тордугулов Дархан Нурбекович", "head_phone": "87071105434"},
    {"name": "Юго-Восток", "head_name": "Онласынов Ернат Сакенович", "head_phone": "87479099392"},
    {"name": "Северный", "head_name": "Карчалов Санат", "head_phone": "87072214001"},
    {"name": "Каскелен", "head_name": "Аусадыков Мурат", "head_phone": "87082987689"},
    {"name": "Иссык", "head_name": "Новиков Анвар Ашимжанович", "head_phone": "87051521363"},
    {"name": "Капчагай", "head_name": "Лопушняк Иван", "head_phone": ""},
    {"name": "ВОЛС (Отдел развития)", "head_name": "Келгенбаев Райым", "head_phone": "87084013094"},
    {"name": "ЛКС (Линейно-кабельные сети)", "head_name": "Требухов Александр", "head_phone": ""},
    {"name": "ОИС (Инженерные системы)", "head_name": "Хасанов Марат", "head_phone": ""},
    {"name": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "head_name": "Козыбаев Торехан Абдижапарулы", "head_phone": ""},
    {"name": "Шымкент (Филиал)", "head_name": "Рахманалиев Бекзат", "head_phone": ""},
    {"name": "Закуп и Снабжение", "head_name": "Солодовник Роман", "head_phone": "87713930801"},
    {"name": "Служба безопасности (СБ)", "head_name": "Токтамуратов Ержан", "head_phone": "87715840744"},
    {"name": "Автобаза (Емцова 11)", "head_name": "Родько Михаил (Гл. механик)", "head_phone": ""},
]
