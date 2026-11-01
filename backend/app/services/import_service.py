from datetime import date, datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.models import (
    User, Company, Department, Vehicle, Driver, DriverAssignment,
    Waybill, Fine, MaintenanceRecord, FuelLog, AuditLog
)
from app.core.security import get_password_hash
from app.services.initial_data import normalize_plate, format_plate_display, parse_date, COMPANIES_DATA, DEPARTMENTS_DATA

# Complete vehicles data extracted from the Excel sheets
RAW_VEHICLES = [
    {"plate": "014GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-18", "dept": "Юго-Запад", "notes": ""},
    {"plate": "027GP02", "brand": "CHANGAN", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-02-23", "insp": "2027-03-16", "dept": "Юго-Запад", "notes": ""},
    {"plate": "038FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-07-29", "dept": "Юго-Запад", "notes": ""},
    {"plate": "039GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-17", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №2 от 27.03.2026"},
    {"plate": "044GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-20", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "052GI02", "brand": "Chevrolet Cobalt", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-10-08", "insp": "2027-03-12", "dept": "Иссык", "notes": ""},
    {"plate": "058GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-19", "dept": "Юго-Запад", "notes": ""},
    {"plate": "059GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-17", "dept": "Северный", "notes": ""},
    {"plate": "061ЕО02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "Северный", "notes": "Шымкент Акт №5 от 22.07.26"},
    {"plate": "064GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-20", "dept": "Юго-Запад", "notes": ""},
    {"plate": "065GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-19", "dept": "Юго-Восток", "notes": ""},
    {"plate": "066GP02", "brand": "CHANGAN", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-02-23", "insp": "2027-02-24", "dept": "Юго-Восток", "notes": "Бригадир ЮВ"},
    {"plate": "067GI02", "brand": "Chevrolet Cobalt", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-10-08", "insp": "2026-10-14", "dept": "Иссык", "notes": ""},
    {"plate": "074GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-17", "dept": "Северный", "notes": ""},
    {"plate": "076GI02", "brand": "Chevrolet Cobalt", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-10-08", "insp": None, "dept": "Автобаза (Емцова 11)", "notes": "Гл.механик Родько М."},
    {"plate": "078GI02", "brand": "Chevrolet Cobalt", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-10-08", "insp": "2027-10-01", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "084FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-16", "dept": "Юго-Запад", "notes": ""},
    {"plate": "087GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-19", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "092DH02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "Иссык", "notes": ""},
    {"plate": "093GI02", "brand": "Chevrolet Cobalt", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-10-08", "insp": "2026-10-16", "dept": "Северный", "notes": ""},
    {"plate": "095GI02", "brand": "Chevrolet Cobalt", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-10-08", "insp": "2026-10-15", "dept": "Иссык", "notes": "АКПП"},
    {"plate": "097GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-17", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "105GW02", "brand": "DFSK C 35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-04-03", "insp": "2027-05-08", "dept": "ВОЛС (Отдел развития)", "notes": "Шымкент Акт №6 13.08.26"},
    {"plate": "106GW02", "brand": "DFSK C 35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-04-03", "insp": "2027-04-16", "dept": "ОИС (Инженерные системы)", "notes": ""},
    {"plate": "113GR02", "brand": "Foton", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-02-26", "insp": "2026-03-16", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №2 от 27.03.2026"},
    {"plate": "115DH02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-04-15", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "115GW02", "brand": "DFSK C 35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-04-03", "insp": "2027-04-10", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "118GR02", "brand": "Foton", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-02-26", "insp": "2027-03-16", "dept": "ЛКС (Линейно-кабельные сети)", "notes": ""},
    {"plate": "119GR02", "brand": "CHANGAN", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-02-26", "insp": "2027-03-17", "dept": "Северный", "notes": ""},
    {"plate": "122FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-20", "dept": "Юго-Запад", "notes": ""},
    {"plate": "123GP03", "brand": "Foton", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-03-10", "insp": "2027-03-26", "dept": "Каскелен", "notes": ""},
    {"plate": "124ЕА02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-09", "dept": "Северный", "notes": ""},
    {"plate": "125ЕА02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-19", "dept": "Юго-Запад", "notes": ""},
    {"plate": "126ЕА02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-23", "dept": "Иссык", "notes": ""},
    {"plate": "127EA02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-18", "dept": "Иссык", "notes": ""},
    {"plate": "127FA02", "brand": "CHANGAN SC1022SEAH6 бортовой", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-10", "insp": "2027-03-16", "dept": "ЛКС (Линейно-кабельные сети)", "notes": "Обслуживаем сами"},
    {"plate": "127LY02", "brand": "Hyundai Accent", "company": "ТОО «СвязьСервисКомплект»", "fuel": "АИ-92", "ins": "2027-04-12", "insp": None, "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "128ЕА02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-20", "dept": "Северный", "notes": ""},
    {"plate": "133GR02", "brand": "CHANGAN", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-02-26", "insp": "2027-03-16", "dept": "Иссык", "notes": ""},
    {"plate": "140GR02", "brand": "Foton", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-02-26", "insp": "2027-03-16", "dept": "Каскелен", "notes": ""},
    {"plate": "154GW02", "brand": "DFSK C 35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-04-03", "insp": "2027-03-16", "dept": "Северный", "notes": ""},
    {"plate": "156FJ02", "brand": "ГАЗель 330273", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-07-29", "dept": "ЛКС (Линейно-кабельные сети)", "notes": ""},
    {"plate": "156GW02", "brand": "DFSK C 35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-04-03", "insp": "2027-05-14", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "157GW02", "brand": "DFSK C 35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-04-03", "insp": "2027-03-20", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "161FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-23", "dept": "Каскелен", "notes": ""},
    {"plate": "170GW02", "brand": "DFSK C 35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-04-03", "insp": "2027-04-13", "dept": "Северный", "notes": ""},
    {"plate": "172GW02", "brand": "DFSK C 35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-04-03", "insp": "2027-05-08", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "173GW02", "brand": "DFSK C 35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-04-03", "insp": "2027-06-16", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "176GW02", "brand": "DFSK C 35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-04-03", "insp": "2027-05-22", "dept": "Юго-Восток", "notes": ""},
    {"plate": "183EX02", "brand": "ГАЗель 27057", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-07", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "183GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-02", "dept": "ОИС (Инженерные системы)", "notes": "GPS трекер Улан 30.06.26"},
    {"plate": "184GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-26", "dept": "Юго-Запад", "notes": ""},
    {"plate": "185GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-14", "dept": "Юго-Восток", "notes": ""},
    {"plate": "186GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-14", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": "Пришел 1 ключ всего"},
    {"plate": "187GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт № 5 от 22.07.26"},
    {"plate": "189GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Иссык", "notes": ""},
    {"plate": "190GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Юго-Восток", "notes": ""},
    {"plate": "191ЕА02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-19", "dept": "Каскелен", "notes": ""},
    {"plate": "192GY02", "brand": "DFSK Sokon C35", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-06-30", "insp": "2027-07-01", "dept": "Юго-Восток", "notes": ""},
    {"plate": "196EX02", "brand": "ГАЗель 27057", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-22", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "196FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "Юго-Восток", "notes": ""},
    {"plate": "203FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-16", "dept": "Начальник отдела", "notes": ""},
    {"plate": "210GI02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-28", "insp": "2026-11-17", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "211FC02", "brand": "JAC Sunray M209C", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-04-28", "insp": "2026-04-02", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "223CT02", "brand": "ГАЗель", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": None, "insp": None, "dept": "Иссык", "notes": "Аварийный списание Иссык документы в сейфе", "status": "WRITE_OFF"},
    {"plate": "227FC02", "brand": "JAC Sunray M209C", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-04-28", "insp": "2027-03-19", "dept": "Развозка автобус", "notes": "Техосмотр 1 раз в 6 месяцев", "interval": 6},
    {"plate": "233FC02", "brand": "JAC Sunray", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-04-28", "insp": "2026-04-02", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "234FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-18", "dept": "Северный", "notes": ""},
    {"plate": "235FR02", "brand": "JAC Sunray", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-02-08", "insp": "2027-02-24", "dept": "Развозка автобус", "notes": "Техосмотр 1 раз в 6 месяцев", "interval": 6},
    {"plate": "241FA02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "Юго-Запад", "notes": ""},
    {"plate": "247ЕО02", "brand": "Damas DLX", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-20", "dept": "Юго-Восток", "notes": ""},
    {"plate": "255ЕО02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №2 от 27.03.2026"},
    {"plate": "258FR02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-03", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "260ЕО02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "Юго-Запад", "notes": ""},
    {"plate": "262FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-19", "dept": "Юго-Восток", "notes": ""},
    {"plate": "265FR02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-05-25", "dept": "Северный", "notes": ""},
    {"plate": "270FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-26", "dept": "Юго-Запад", "notes": ""},
    {"plate": "277FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-18", "dept": "Каскелен", "notes": ""},
    {"plate": "284FG02", "brand": "JAC JS3", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-01", "dept": "Юго-Запад", "notes": ""},
    {"plate": "284FR02", "brand": "Isuzu (Автовышка)", "company": "ТОО «Elite ProBuilding»", "fuel": "ДТ", "ins": "2027-02-09", "insp": "2027-04-01", "dept": "ЛКС (Линейно-кабельные сети)", "notes": "Автовышка", "interval": 6},
    {"plate": "292FA02", "brand": "CHANGAN SC1022SEAH6 бортовой", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-16", "dept": "ЛКС (Линейно-кабельные сети)", "notes": "Обслуживаем сами"},
    {"plate": "304FA02", "brand": "CHANGAN SC1022SEAH6 бортовой", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-03", "dept": "ЛКС (Линейно-кабельные сети)", "notes": ""},
    {"plate": "305FA02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-12-31", "insp": "2027-02-20", "dept": "Иссык", "notes": ""},
    {"plate": "316FR02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-11", "dept": "Юго-Запад", "notes": ""},
    {"plate": "322СJ02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-04", "insp": "2026-09-12", "dept": "Юго-Запад", "notes": "Шымкент Акт №6 13.08.26"},
    {"plate": "341BQ02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-23", "dept": "Шымкент (Филиал)", "notes": "Шымкент 28.05.26"},
    {"plate": "342CJ02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-16", "dept": "Юго-Запад", "notes": ""},
    {"plate": "342EO02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "347CP02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-23", "dept": "Юго-Восток", "notes": ""},
    {"plate": "348BQ02", "brand": "Damas Chevrolet Van", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-07", "dept": "ВОЛС (Отдел развития)", "vin": "MXCCVABD0MK847500", "tech_passport": "AL0013871", "color": "Белый", "fuel_card": "96378", "notes": ""},
    {"plate": "349BQ02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-15", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "349СТ02", "brand": "Damas DLX", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": None, "insp": None, "dept": "Иссык", "notes": "Аварийный списание Иссык документы в сейфе", "status": "WRITE_OFF"},
    {"plate": "352FQ02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-04", "dept": "Юго-Восток", "notes": ""},
    {"plate": "358СР02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-12", "dept": "Юго-Восток", "notes": ""},
    {"plate": "361FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-31", "dept": "Юго-Восток", "notes": ""},
    {"plate": "362DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-09", "dept": "Северный", "notes": ""},
    {"plate": "366CJ02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-03", "insp": "2026-09-17", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "379DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-01", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №3 от 20.05.2026"},
    {"plate": "381СJ02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-03", "insp": "2027-09-07", "dept": "Капчагай", "notes": ""},
    {"plate": "382СJ02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-20", "insp": "2026-09-12", "dept": "Северный", "notes": "Шымкент 19.08.26"},
    {"plate": "384DI02", "brand": "Damas DLX", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-07-03", "insp": "2027-03-26", "dept": "Юго-Восток", "notes": ""},
    {"plate": "385DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №2 от 27.03.2026"},
    {"plate": "389FQ02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-18", "dept": "Юго-Запад", "notes": ""},
    {"plate": "391СР02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-16", "dept": "Каскелен", "notes": ""},
    {"plate": "401DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-18", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №5 от 22.07.26"},
    {"plate": "408FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-13", "dept": "Северный", "notes": ""},
    {"plate": "411FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-16", "dept": "Северный", "notes": ""},
    {"plate": "416FI02", "brand": "Dongfeng пикап", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-08-04", "dept": "ЛКС (Линейно-кабельные сети)", "notes": "Обслуживаем сами"},
    {"plate": "418FA02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-13", "dept": "Северный", "notes": ""},
    {"plate": "420DH02", "brand": "Нива Легенда LADA 4х4", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-03", "dept": "Юго-Запад", "notes": ""},
    {"plate": "421DH02", "brand": "Нива Легенда LADA 4х4", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-08-06", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "428FI02", "brand": "Dongfeng пикап", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-08-04", "dept": "ЛКС (Линейно-кабельные сети)", "notes": "Обслуживаем сами"},
    {"plate": "433GR02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-01-30", "insp": "2027-02-04", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "438GR02", "brand": "Dongfeng автобус", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-02-02", "insp": "2026-08-09", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №2 от 27.03.2026", "interval": 6},
    {"plate": "445FC02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-20", "dept": "Юго-Восток", "notes": ""},
    {"plate": "446FC02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-20", "dept": "Иссык", "notes": ""},
    {"plate": "448DF02", "brand": "Нива Легенда LADA 4х4", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-21", "dept": "Северный", "notes": ""},
    {"plate": "449DF02", "brand": "Нива Легенда LADA 4х4", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-20", "dept": "Юго-Восток", "notes": ""},
    {"plate": "451GR02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-01-30", "insp": "2027-02-03", "dept": "Иссык", "notes": ""},
    {"plate": "452GR02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-01-30", "insp": "2027-02-03", "dept": "Каскелен", "notes": ""},
    {"plate": "455FC02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-06-02", "dept": "Иссык", "notes": ""},
    {"plate": "459ЕО02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-15", "dept": "Капчагай", "notes": "Шымкент Акт №5"},
    {"plate": "460FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-12-28", "dept": "Каскелен", "notes": ""},
    {"plate": "462GR02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-01-30", "insp": "2027-02-03", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "463GR02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-01-30", "insp": "2027-02-03", "dept": "Юго-Восток", "notes": ""},
    {"plate": "465GR02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-01-30", "insp": "2027-02-03", "dept": "Северный", "notes": ""},
    {"plate": "469GR02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-01-30", "insp": "2027-02-03", "dept": "Юго-Восток", "notes": ""},
    {"plate": "474LE02", "brand": "ГАЗель 2705", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-13", "dept": "ЛКС (Линейно-кабельные сети)", "notes": ""},
    {"plate": "478GR02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-01-30", "insp": "2027-02-20", "dept": "Юго-Восток", "notes": ""},
    {"plate": "479FQ02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-03", "dept": "Иссык", "notes": ""},
    {"plate": "481AC02", "brand": "Damas DLX", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-21", "dept": "Северный", "notes": ""},
    {"plate": "486DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-26", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №2 от 27.03.2026"},
    {"plate": "492DF02", "brand": "Нива Легенда LADA 4х4", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-01", "dept": "Юго-Запад", "notes": ""},
    {"plate": "494FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-08-03", "dept": "Северный", "notes": ""},
    {"plate": "496FG02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-07-31", "dept": "Юго-Запад", "notes": ""},
    {"plate": "496GR02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-01-30", "insp": "2027-02-03", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "497GR02", "brand": "DFSK C 35", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-01-30", "insp": "2027-02-05", "dept": "Юго-Запад", "notes": ""},
    {"plate": "503FI02", "brand": "ГАЗель 27057", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-04", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "505GE02", "brand": "Chevrolet Cobalt", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-09-09", "insp": "2027-09-07", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "511GE02", "brand": "Chevrolet Cobalt", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-09-09", "insp": "2027-09-15", "dept": "Юго-Восток", "notes": ""},
    {"plate": "512GE02", "brand": "Chevrolet Cobalt", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-09-09", "insp": "2027-09-24", "dept": "Иссык", "notes": ""},
    {"plate": "519DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-09", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №6 13.08.26"},
    {"plate": "521AC02", "brand": "KIA RIO", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-09-22", "insp": "2027-03-30", "dept": "Закуп и Снабжение", "notes": "Почта"},
    {"plate": "526DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "532EU02", "brand": "Hyundai Porter 2", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "ДТ", "ins": "2026-12-17", "insp": "2027-08-24", "dept": "Автобаза (Емцова 11)", "notes": ""},
    {"plate": "534FQ02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-04", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "535GE02", "brand": "Chevrolet Cobalt", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2026-09-09", "insp": "2027-09-07", "dept": "Каскелен", "notes": ""},
    {"plate": "537FQ02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-04", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "549FQ02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-04", "dept": "Северный", "notes": ""},
    {"plate": "553CN02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-06", "dept": "Шымкент (Филиал)", "notes": "Шымкент 28.05.26"},
    {"plate": "560DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-12", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №2 от 27.03.2026"},
    {"plate": "576FQ02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-04", "dept": "Каскелен", "notes": ""},
    {"plate": "584AS02", "brand": "Цзефан", "company": "ТОО «СвязьСервисКомплект»", "fuel": "АИ-92", "ins": None, "insp": None, "dept": "Иссык", "notes": "Аварийный списание Иссык", "status": "WRITE_OFF"},
    {"plate": "584FQ02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-09", "dept": "Каскелен", "notes": ""},
    {"plate": "592DI02", "brand": "Damas DLX", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-09", "insp": "2027-09-10", "dept": "Капчагай", "notes": ""},
    {"plate": "601LZ02", "brand": "Damas DLX", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-18", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №3 от 20.05.2026"},
    {"plate": "605GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-02", "dept": "Каскелен", "notes": ""},
    {"plate": "625FI02", "brand": "Dongfeng пикап", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-08-05", "dept": "ЛКС (Линейно-кабельные сети)", "notes": "Обслуживаем сами"},
    {"plate": "644AG02", "brand": "JAC Sunray", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "ДТ", "ins": "2027-03-09", "insp": "2027-09-23", "dept": "ЛКС (Линейно-кабельные сети)", "notes": "", "interval": 6},
    {"plate": "644FA02", "brand": "ГАЗель 27057", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-20", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "650GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-02", "dept": "Каскелен", "notes": ""},
    {"plate": "663GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "664GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "667GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №6 13.08.26"},
    {"plate": "670GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Северный", "notes": ""},
    {"plate": "671GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Юго-Запад", "notes": ""},
    {"plate": "672GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "673GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-13", "dept": "Северный", "notes": "Эксплуатация ППР"},
    {"plate": "679GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Юго-Восток", "notes": ""},
    {"plate": "680GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Юго-Запад", "notes": ""},
    {"plate": "687GY02", "brand": "DFSK Sokon C35", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-06-29", "insp": "2027-07-01", "dept": "Юго-Запад", "notes": ""},
    {"plate": "689DM02", "brand": "Ларгус LADA", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-20", "dept": "Юго-Запад", "notes": ""},
    {"plate": "724FA02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-14", "dept": "Каскелен", "notes": ""},
    {"plate": "735FA02", "brand": "JAC JS3", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-11", "dept": "Юго-Запад", "notes": ""},
    {"plate": "743DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-18", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №3 от 20.05.2026"},
    {"plate": "745АС02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-31", "dept": "Шымкент (Филиал)", "notes": "Шымкент 28.05.26"},
    {"plate": "746АС02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-02", "dept": "Юго-Восток", "notes": ""},
    {"plate": "761AA02", "brand": "ГАЗель 330232 2288", "company": "ТОО «СвязьСервисКомплект»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-18", "dept": "ЛКС (Линейно-кабельные сети)", "notes": ""},
    {"plate": "762GR02", "brand": "CHANGAN", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-03-17", "insp": "2027-03-17", "dept": "Юго-Восток", "notes": ""},
    {"plate": "764FA02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "Иссык", "notes": ""},
    {"plate": "795GR02", "brand": "Foton", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-03-10", "insp": "2027-03-26", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "notes": ""},
    {"plate": "796DI02", "brand": "Damas DLX", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-10-09", "insp": "2027-09-05", "dept": "Юго-Запад", "notes": ""},
    {"plate": "804DI02", "brand": "Танк 500", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-95", "ins": "2027-03-09", "insp": "2026-09-12", "dept": "Автобаза (Емцова 11)", "notes": "Продан 11.08.26", "status": "SOLD"},
    {"plate": "811DG02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-21", "dept": "Юго-Восток", "notes": ""},
    {"plate": "813DG02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №2 от 27.03.2026"},
    {"plate": "813LS02", "brand": "LADA GRANTA FL", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-13", "insp": "2027-09-17", "dept": "Юго-Запад", "notes": ""},
    {"plate": "814DG02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": None, "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №3 от 20.05.2026"},
    {"plate": "816DG02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-12", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт № 5 от 22.07.26"},
    {"plate": "818DE02", "brand": "Ларгус LADA KS015L", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-04", "insp": "2027-07-16", "dept": "ВОЛС (Отдел развития)", "notes": ""},
    {"plate": "832DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-22", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №2 от 27.03.2026"},
    {"plate": "837DF02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-17", "dept": "Юго-Восток", "notes": ""},
    {"plate": "842DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-22", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "843DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-18", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "848FE02", "brand": "JAC JS3", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-03-19", "insp": "2027-03-19", "dept": "Иссык", "notes": ""},
    {"plate": "848GC02", "brand": "Toyota Land Cruiser", "company": "ТОО «Meganet»", "fuel": "АИ-95", "ins": "2027-08-12", "insp": "2027-08-20", "dept": "Служба безопасности (СБ)", "notes": ""},
    {"plate": "849DF02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-10-10", "dept": "Шымкент (Филиал)", "notes": "Шымкент 28.05.2026"},
    {"plate": "849DI02", "brand": "Damas DLX", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-10-10", "dept": "Автобаза (Емцова 11)", "notes": "Дежурка"},
    {"plate": "861FE02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-05-02", "dept": "Иссык", "notes": ""},
    {"plate": "869DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-22", "dept": "Юго-Запад", "notes": ""},
    {"plate": "871DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-10-06", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "872DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-15", "dept": "Северный", "notes": ""},
    {"plate": "874DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-17", "dept": "Шымкент (Филиал)", "notes": "Шымкент 13.08.26"},
    {"plate": "876DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-19", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "880DI02", "brand": "Damas DLX", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2026-09-17", "dept": "Шымкент (Филиал)", "notes": "Шымкент Акт №1 от 2026"},
    {"plate": "892CY02", "brand": "Нива Легенда LADA 4х4", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-09-10", "dept": "Каскелен", "notes": ""},
    {"plate": "921LK02", "brand": "Ларгус LADA", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-16", "dept": "Каскелен", "notes": ""},
    {"plate": "928LK02", "brand": "Ларгус LADA", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-10", "insp": "2027-03-30", "dept": "Юго-Восток", "notes": ""},
    {"plate": "932LK02", "brand": "Ларгус LADA", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-10", "insp": "2027-09-09", "dept": "Каскелен", "notes": ""},
    {"plate": "941ES02", "brand": "Dongfeng DFA5041XXY будка", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2026-11-07", "insp": "2027-09-24", "dept": "Закуп и Снабжение", "notes": "Обслуживаем сами"},
    {"plate": "941СI02", "brand": "Damas DLX", "company": "ТОО «Meganet»", "fuel": "АИ-92", "ins": "2027-09-22", "insp": "2027-09-17", "dept": "ОИС (Инженерные системы)", "notes": ""},
    {"plate": "947LK02", "brand": "Ларгус LADA", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-10", "dept": "Автобаза (Емцова 11)", "notes": "Ремонт замена двиг, кпп", "status": "REPAIR"},
    {"plate": "981EQ02", "brand": "CHANGAN EV Электричка", "company": "ТОО «Elite ProBuilding»", "fuel": "Электро", "ins": "2027-03-09", "insp": "2027-09-25", "dept": "Автобаза (Емцова 11)", "notes": "Директор Департамента Эксплуатации Умаганов Олег"},
    {"plate": "981FE02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-20", "dept": "Служба безопасности (СБ)", "notes": "ОВК"},
    {"plate": "983FQ02", "brand": "Нива LADA Тревел", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-02-09", "insp": "2027-03-03", "dept": "Северный", "notes": ""},
    {"plate": "988FE02", "brand": "JAC JS3", "company": "ТОО «Elite ProBuilding»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-04-14", "dept": "Юго-Восток", "notes": ""},
    {"plate": "990GK02", "brand": "Dongfeng автобус развозка", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "ДТ", "ins": "2027-02-07", "insp": "2027-08-09", "dept": "Развозка автобус", "notes": "Техосмотр 1 раз в 6 месяцев", "interval": 6},
    {"plate": "990LK02", "brand": "Ларгус LADA", "company": "ТОО «NLS KAZAKHSTAN»", "fuel": "АИ-92", "ins": "2027-03-09", "insp": "2027-03-26", "dept": "Юго-Запад", "notes": ""},
]

# Real driver names, positions, departments and phones from Excel
RAW_DRIVERS = [
    # Юго-Восток
    {"name": "Мұратов Жалғас Мұратұлы", "phone": "87076665088", "pos": "Инсталлятор", "dept": "Юго-Восток", "plate": "066GP02"},
    {"name": "Исмоилов Арман Исматуғли", "phone": "87073304098", "pos": "Инсталлятор", "dept": "Юго-Восток", "plate": "469GR02"},
    {"name": "Оксикбай Асет Нұржауұлы", "phone": "87076116383", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "262FG02"},
    {"name": "Маратов Ардақ Нурланұлы", "phone": "87001999181", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "811DG02"},
    {"name": "Әуесхан Асқар Бағдатұлы", "phone": "87086054750", "pos": "Инсталлятор", "dept": "Юго-Восток", "plate": "176GW02"},
    {"name": "Мажитов Самат Женисбекович", "phone": "87479099392", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "762GR02"},
    {"name": "Авдеев Сергей Сергеевич", "phone": "87777217931", "pos": "Инсталлятор", "dept": "Юго-Восток", "plate": "384DI02"},
    {"name": "Торешов Нурбол Серикович", "phone": "87478198809", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "247ЕО02"},
    {"name": "Сапаров Улугбек Нурсейт Угли", "phone": "87772441802", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "746АС02"},
    {"name": "Далжанов Ардақ Асанович", "phone": "87470401838", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "065GI02"},
    {"name": "Баймурзаев Нурбол", "phone": "87017279448", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "463GR02"},
    {"name": "Абдимажитов Бегарыс Сапаримбатулы", "phone": "87002318140", "pos": "Инсталлятор", "dept": "Юго-Восток", "plate": "401DI02"},
    {"name": "Дуйсенбаев Бахытжон Нурулла угли", "phone": "87716076767", "pos": "Инсталлятор", "dept": "Юго-Восток", "plate": "928LK02"},
    {"name": "Хусаинов Нижат Нигматович", "phone": "87084003152", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "511GE02"},
    {"name": "Карибаев Ринат Русланович", "phone": "87785020217", "pos": "Инсталлятор", "dept": "Юго-Восток", "plate": "196FG02"},
    {"name": "Сулейменов Станислав Рашитович", "phone": "87771106565", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "445FC02"},
    {"name": "Утекеев Шухрат", "phone": "87772777494", "pos": "Инсталлятор", "dept": "Юго-Восток", "plate": "449DF02"},
    {"name": "Жакупбеков Алимжан Каримханович", "phone": "87089661289", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "361FG02"},
    {"name": "Сызбаев Руслан Мухамадиевич", "phone": "87479693090", "pos": "Инсталлятор", "dept": "Юго-Восток", "plate": "352FQ02"},
    {"name": "Тютюкин Руслан Багдатович", "phone": "87781083298", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "988FE02"},
    {"name": "Касимов Ашимжан Дильмуратович", "phone": "87715537146", "pos": "Бригадир", "dept": "Юго-Восток", "plate": "478GR02"},
    {"name": "Эргашбаев Алмасхан Рихсибойуғли", "phone": "87765961313", "pos": "Инсталлятор", "dept": "Юго-Восток", "plate": "837DF02"},
    
    # Каскелен
    {"name": "Трошкин Александр", "phone": "87760075550", "pos": "Бригадир", "dept": "Каскелен", "plate": "460FG02"},
    {"name": "Утемисов Наурызбек", "phone": "87073110397", "pos": "Инсталлятор", "dept": "Каскелен", "plate": "161FG02"},
    {"name": "Беркинов Данияр", "phone": "87078277606", "pos": "Бригадир", "dept": "Каскелен", "plate": "277FG02"},
    {"name": "Арсланбаев Еркінбек", "phone": "87058773056", "pos": "Инсталлятор", "dept": "Каскелен", "plate": "724FA02"},
    {"name": "Құрман Әділет", "phone": "87470806469", "pos": "Инсталлятор", "dept": "Каскелен", "plate": "921LK02"},
    {"name": "Зайтенов Марат", "phone": "87084229018", "pos": "Инсталлятор", "dept": "Каскелен", "plate": "932LK02"},
    {"name": "Шадияров Аслан", "phone": "87781477931", "pos": "Инсталлятор", "dept": "Каскелен", "plate": "191ЕА02"},
    {"name": "Сапарбаев Бабур", "phone": "87079992961", "pos": "Инсталлятор", "dept": "Каскелен", "plate": "584FQ02"},
    {"name": "Досанов Нурполат", "phone": "87081011414", "pos": "Инсталлятор", "dept": "Каскелен", "plate": "576FQ02"},
    {"name": "Курман Даурен", "phone": "87471676634", "pos": "Бригадир", "dept": "Каскелен", "plate": "123GP03"},
    {"name": "Акимтай Әділет", "phone": "87056761303", "pos": "Инсталлятор", "dept": "Каскелен", "plate": "140GR02"},
    {"name": "Конысбаев Архар", "phone": "87021470122", "pos": "Инсталлятор", "dept": "Каскелен", "plate": "452GR02"},
    {"name": "Абжами Әділет", "phone": "87086726695", "pos": "Инсталлятор", "dept": "Каскелен", "plate": "535GE02"},

    # Юго-Запад
    {"name": "Медеов Талгат Русланович", "phone": "87772062926", "pos": "Водитель", "dept": "Юго-Запад", "plate": "316FR02"},
    {"name": "Гуламдунов Кадирдан Кудусжанович", "phone": "87715806341", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "270FG02"},
    {"name": "Султанов Мундаш Сирдашжанович", "phone": "87075859022", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "389FQ02"},
    {"name": "Абдувалиев Кадирдан Турсунжанович", "phone": "87072080662", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "505GE02"},
    {"name": "Алаев Халмурат Талгатович", "phone": "8708042408", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "064GI02"},
    {"name": "Гункин Андрей Ильич", "phone": "87714493059", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "284FG02"},
    {"name": "Кечин Никита Сергеевич", "phone": "87472422892", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "342CJ02"},
    {"name": "Бакытов Азамат Асетович", "phone": "87714176545", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "322СJ02"},
    {"name": "Ажибай Кайсар Талгатулы", "phone": "87074995404", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "027GP02"},
    {"name": "Шакен Алишер", "phone": "87070192203", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "497GR02"},
    {"name": "Ашимбаев Ернар", "phone": "87714930029", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "058GI02"},
    {"name": "Бейсенбай Аманжол Кенжетайулы", "phone": "87022166699", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "014GI02"},
    {"name": "Иманбердиев Карим Абдуганиевич", "phone": "87058745532", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "689DM02"},
    {"name": "Құрман Дәулет Абдылжанұлы", "phone": "87002623007", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "813LS02"},
    {"name": "Мамедов Рустам Маликович", "phone": "87076598687", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "122FG02"},
    {"name": "Елупахин Денис Андреевич", "phone": "87756158354", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "420DH02"},
    {"name": "Сериков Мадияр Ертайулы", "phone": "87478705467", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "526DI02"},
    {"name": "Сабырхан Мейрхан Еркімбекұлы", "phone": "87026660270", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "796DI02"},
    {"name": "Кисебаев Алмас", "phone": "87079127732", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "735FA02"},
    {"name": "Айкимбаев Нурлан", "phone": "87007430032", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "125ЕА02"},
    {"name": "Айманбетов Арман", "phone": "87085931338", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "038FG02"},
    {"name": "Толеугали Толеген", "phone": "87771005121", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "492DF02"},
    {"name": "Еркехан Бакыт", "phone": "87023304133", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "496FG02"},
    {"name": "Иманалы Багдат Муратулы", "phone": "87766714933", "pos": "Инсталлятор", "dept": "Юго-Запад", "plate": "241FA02"},

    # ОИС (Инженерные системы)
    {"name": "Ахметов Ермек Туруспекұлы", "phone": "87071792289", "pos": "Техник ОИС", "dept": "ОИС (Инженерные системы)", "plate": "941СI02"},
    {"name": "Калдибаев Акберди Амантаевич", "phone": "87066064332", "pos": "Техник ОИС", "dept": "ОИС (Инженерные системы)", "plate": "941СI02"},
    {"name": "Смольский Павел Владимирович", "phone": "87711020333", "pos": "Техник ОИС", "dept": "ОИС (Инженерные системы)", "plate": "260ЕО02"},
    {"name": "Акимов Бақытжан Ардақұлы", "phone": "87783203823", "pos": "Техник ОИС", "dept": "ОИС (Инженерные системы)", "plate": "260ЕО02"},
    {"name": "Тюлемисов Ербол Баянбекович", "phone": "87713067862", "pos": "Бригадир ОИС", "dept": "ОИС (Инженерные системы)", "plate": "106GW02"},
    {"name": "Джумадилов Ердос Сейдинович", "phone": "", "pos": "Техник ОИС", "dept": "ОИС (Инженерные системы)", "plate": "106GW02"},
    {"name": "Қабаргелді Нүркен Асхатұлы", "phone": "87089493632", "pos": "Бригадир ОИС", "dept": "ОИС (Инженерные системы)", "plate": "869DI02"},
    {"name": "Кудряшов Максим Викторович", "phone": "87073133230", "pos": "Техник ОИС", "dept": "ОИС (Инженерные системы)", "plate": "869DI02"},

    # Аварийно-оперативное реагирование (ОТЭ)
    {"name": "Толыбек Куаныш", "phone": "87776416007", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "087GI02"},
    {"name": "Кахарманов Кожабек", "phone": "87085324757", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "115GW02"},
    {"name": "Муширбеков Алмас", "phone": "87474533973", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "258FR02"},
    {"name": "Маликжанов Рафаэль", "phone": "87479289289", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "157GW02"},
    {"name": "Ашик Тоқтасын М.", "phone": "87055695696", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "537FQ02"},
    {"name": "Чекаленко Юрий", "phone": "87001562131", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "892CY02"},
    {"name": "Зейнелханов Серікбол", "phone": "87077763674", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "534FQ02"},
    {"name": "Кикимов Санжар", "phone": "87076470296", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "210GI02"},
    {"name": "Серик Рахат", "phone": "87074969698", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "097GI02"},
    {"name": "Гинько Александр", "phone": "87011454158", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "503FI02"},
    {"name": "Султанов Бауыржан", "phone": "87076246978", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "795GR02"},
    {"name": "Аденов Турсынбай Даулетханович", "phone": "87718598000", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "496GR02"},
    {"name": "Сембаев Диас", "phone": "877773595151", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "433GR02"},
    {"name": "Тургумбаев Алмас", "phone": "87011454158", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "462GR02"},
    {"name": "Казтурган Қосай", "phone": "87716190173", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "156GW02"},
    {"name": "Турлы Нурбол Мухаметжанұлы", "phone": "87055776847", "pos": "Водитель ОТЭ", "dept": "Аварийно-оперативное реагирование (ОТЭ/ООР)", "plate": "421DH02"},

    # Иссык
    {"name": "Шарипов Азиз", "phone": "87051134555", "pos": "Бригадир", "dept": "Иссык", "plate": "095GI02"},
    {"name": "Маханов Ринат Сергеевич", "phone": "87770152623", "pos": "Инсталлятор", "dept": "Иссык", "plate": "446FC02"},
    {"name": "Завадский Сергей Дмитриевич", "phone": "87471332272", "pos": "Бригадир", "dept": "Иссык", "plate": "052GI02"},
    {"name": "Тахтиев Акимжан Мажитович", "phone": "87475304682", "pos": "Бригадир", "dept": "Иссык", "plate": "092DH02"},
    {"name": "Кабылов Баглан Багдатович", "phone": "87074398314", "pos": "Бригадир", "dept": "Иссык", "plate": "479FQ02"},
    {"name": "Семятбакиев Расул Хамзатович", "phone": "87001585863", "pos": "Инсталлятор", "dept": "Иссык", "plate": "305FA02"},
    {"name": "Киса Улан", "phone": "87718519065", "pos": "Бригадир", "dept": "Иссык", "plate": "764FA02"},
    {"name": "Скак Данияр Берикович", "phone": "87084013294", "pos": "Бригадир", "dept": "Иссык", "plate": "126ЕА02"},
    {"name": "Аугамбаев Мадияр", "phone": "87471604712", "pos": "Инсталлятор", "dept": "Иссык", "plate": "067GI02"},
    {"name": "Максутов Арман Нариманович", "phone": "87786797880", "pos": "Бригадир", "dept": "Иссык", "plate": "451GR02"},
    {"name": "Несипбаев Ернар", "phone": "87073799282", "pos": "Бригадир", "dept": "Иссык", "plate": "861FE02"},
    {"name": "Жолдасбаев Темирбек Талғатұлы", "phone": "87074588762", "pos": "Бригадир", "dept": "Иссык", "plate": "512GE02"},
    {"name": "Отеген Женисбай Ташкентбайулы", "phone": "87767172520", "pos": "Инсталлятор", "dept": "Иссык", "plate": "127EA02"},
    {"name": "Чанов Кирилл Сергеевич", "phone": "87064155212", "pos": "Бригадир", "dept": "Иссык", "plate": "848FE02"},
    {"name": "Букеев Берик Мырзагельдиулы", "phone": "87051521363", "pos": "Бригадир", "dept": "Иссык", "plate": "133GR02"},
    {"name": "Табыл Ұшқын Әділжанұлы", "phone": "87716853724", "pos": "Бригадир", "dept": "Иссык", "plate": "067GI02"},

    # ВОЛС (Отдел развития)
    {"name": "Рашид Ернат Рашидұлы", "phone": "87475180494", "pos": "Помощник сварщика", "dept": "ВОЛС (Отдел развития)", "plate": "172GW02"},
    {"name": "Буташов Нұржас Сандикулұлы", "phone": "87089789596", "pos": "Сварщик ВОЛС", "dept": "ВОЛС (Отдел развития)", "plate": "105GW02"},
    {"name": "Абдулла Дәнебек Асқарұлы", "phone": "87020002069", "pos": "Помощник сварщика", "dept": "ВОЛС (Отдел развития)", "plate": "044GI02"},
    {"name": "Қоран Данияр Манасұлы", "phone": "87079194953", "pos": "Сварщик", "dept": "ВОЛС (Отдел развития)", "plate": "173GW02"},
    {"name": "Смагулов Мурзабек Сатокович", "phone": "87768055505", "pos": "Старший инженер", "dept": "ВОЛС (Отдел развития)", "plate": "078GI02"},
    {"name": "Сейпалиев Айтуған", "phone": "87473731050", "pos": "Помощник сварщика", "dept": "ВОЛС (Отдел развития)", "plate": "348BQ02"},
    {"name": "Сабырбаев Дулат Оразбайұлы", "phone": "87476872717", "pos": "Сварщик", "dept": "ВОЛС (Отдел развития)", "plate": "818DE02"},
    {"name": "Кунградбаев Жандос Нурлыбекулы", "phone": "87083435209", "pos": "Сварщик", "dept": "ВОЛС (Отдел развития)", "plate": "342EO02"},
    {"name": "Асан Нұркен Копжұрсінұлы", "phone": "87476226260", "pos": "Монтажник", "dept": "ВОЛС (Отдел развития)", "plate": "196EX02"},
    {"name": "Боскымбаев Азамат Ержанович", "phone": "87075291288", "pos": "Монтажник", "dept": "ВОЛС (Отдел развития)", "plate": "183EX02"},
    {"name": "Наурузбаев Болат Бизатович", "phone": "87058039563", "pos": "Монтажник", "dept": "ВОЛС (Отдел развития)", "plate": "644FA02"},
    {"name": "Чауке Бірлік Бауыржанұлы", "phone": "87057025809", "pos": "Монтажник", "dept": "ВОЛС (Отдел развития)", "plate": "874DI02"},

    # ЛКС (Линейно-кабельные сети)
    {"name": "Ахметжан Шухрат Махаметжанұлы", "phone": "87473849971", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "127FA02"},
    {"name": "Ашимов Махмутжан Касымович", "phone": "87088922686", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "118GR02"},
    {"name": "Елеу Жангірхан Нұрланұлы", "phone": "87071090944", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "428FI02"},
    {"name": "Қанатбай Нұржан Сакенұлы", "phone": "87473434243", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "416FI02"},
    {"name": "Муратбаев Асхат Амангелдыевич", "phone": "87473655899", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "428FI02"},
    {"name": "Реимбаев Кутлыбай Нурлыбай улы", "phone": "87058455434", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "284FR02"},
    {"name": "Стыбаев Даурен Асылбекович", "phone": "87066707488", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "156FJ02"},
    {"name": "Толебаев Турганбек Арманулы", "phone": "87079546088", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "644AG02"},
    {"name": "Нурахмет Жомарт Сағындықұлы", "phone": "87475630497", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "304FA02"},
    {"name": "Шынбергенов Мұратбай Қуандықұлы", "phone": "87772960516", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "625FI02"},
    {"name": "Нағашбек Мағжан Махажанұлы", "phone": "87766763168", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "474LE02"},
    {"name": "Айтуганов Бауыржан Орынбекович", "phone": "87777057833", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "625FI02"},
    {"name": "Алтай Медеу", "phone": "87006935796", "pos": "Водитель ЛКС", "dept": "ЛКС (Линейно-кабельные сети)", "plate": "292FA02"},
]

RAW_FINES = [
    {"plate": "014GI02", "notice": "267588230724583", "v_date": "2026-04-06", "acc_date": "2026-06-09", "notified": "2026-06-10", "paid": "2026-06-10", "driver": "Бейсенбай Аманжол Кенжетайулы", "status": "PAID"},
    {"plate": "014GI02", "notice": "267588231086795", "v_date": "2026-05-26", "acc_date": "2026-06-09", "notified": "2026-06-10", "paid": "2026-06-10", "driver": "Бейсенбай Аманжол Кенжетайулы", "status": "PAID"},
    {"plate": "014GI02", "notice": "267588231132513", "v_date": "2026-06-02", "acc_date": "2026-06-19", "notified": "2026-06-22", "paid": "2026-06-22", "driver": "Бейсенбай Аманжол Кенжетайулы", "status": "PAID"},
    {"plate": "044GI02", "notice": "267588230945271", "v_date": "2026-05-12", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": "2026-05-21", "driver": "Абдулла Дәнебек Асқарұлы", "status": "PAID"},
    {"plate": "061ЕО02", "notice": "267588230873068", "v_date": "2026-04-25", "acc_date": "2026-05-15", "notified": "2026-05-15", "paid": "2026-04-30", "driver": "", "status": "PAID"},
    {"plate": "087GI02", "notice": "267588230772624", "v_date": "2026-04-12", "acc_date": "2026-05-15", "notified": "2026-05-15", "paid": None, "driver": "Толыбек Куаныш", "status": "REFUSED", "memo": True, "notes": "Отказ от оплаты, передать в СБ"},
    {"plate": "097GI02", "notice": "261900030357730", "v_date": "2026-04-30", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": "2026-05-20", "driver": "Серик Рахат", "status": "PAID"},
    {"plate": "097GI02", "notice": "261900030513536", "v_date": "2026-06-10", "acc_date": "2026-06-19", "notified": "2026-06-19", "paid": "2026-06-19", "driver": "Серик Рахат", "status": "PAID"},
    {"plate": "097GI02", "notice": "261900030543325", "v_date": "2026-06-19", "acc_date": "2026-06-19", "notified": "2026-06-19", "paid": "2026-06-19", "driver": "Серик Рахат", "status": "PAID"},
    {"plate": "125ЕА02", "notice": "261900030402226", "v_date": "2026-05-13", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": "2026-05-20", "driver": "Айкимбаев Нурлан", "status": "PAID"},
    {"plate": "127FA02", "notice": "267588231039871", "v_date": "2026-05-20", "acc_date": "2026-05-25", "notified": "2026-05-25", "paid": "2026-06-04", "driver": "Султанов Елбек Зокирулы", "status": "PAID"},
    {"plate": "156GW02", "notice": "261900030534239", "v_date": "2026-06-16", "acc_date": "2026-06-19", "notified": "2026-06-19", "paid": "2026-06-22", "driver": "Казтурган Қосай", "status": "PAID"},
    {"plate": "235FR02", "notice": "Оплата штрафа 21625тг", "v_date": "2026-05-10", "acc_date": "2026-05-13", "notified": "2026-05-13", "paid": "2026-05-13", "amount": 21625.0, "driver": "Мусаев Шахназар", "status": "PAID"},
    {"plate": "247ЕО02", "notice": "267588230898372", "v_date": "2026-05-05", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": "2026-05-20", "driver": "Торешов Нурбол Серикович", "status": "PAID"},
    {"plate": "258FR02", "notice": "267500030052240", "v_date": "2026-04-07", "acc_date": "2026-05-15", "notified": "2026-05-15", "paid": "2026-03-02", "driver": "Муширбеков Алмас", "status": "PAID", "notes": "Чек найден 606104756931"},
    {"plate": "341BQ02", "notice": "261900030363510", "v_date": "2026-05-03", "acc_date": "2026-05-21", "notified": "2026-05-21", "paid": "2026-05-21", "driver": "Сейпалиев Айтуған", "status": "PAID"},
    {"plate": "352FQ02", "notice": "267588231056347", "v_date": "2026-05-23", "acc_date": "2026-06-19", "notified": "2026-06-19", "paid": "2026-07-26", "driver": "Сызбаев Руслан Мухамадиевич", "status": "DISPUTED", "is_not_our": True, "notes": "Задвоение, авто не нашей компании, оплачено сторонним лицом"},
    {"plate": "411FG02", "notice": "261900030406663", "v_date": "2026-05-14", "acc_date": "2026-05-21", "notified": "2026-05-21", "paid": "2026-05-21", "driver": "Рахан Аблай", "status": "PAID"},
    {"plate": "411FG02", "notice": "261900030410393", "v_date": "2026-05-16", "acc_date": "2026-05-21", "notified": "2026-05-21", "paid": "2026-05-21", "driver": "Рахан Аблай", "status": "PAID"},
    {"plate": "478GR02", "notice": "267588230924477", "v_date": "2026-05-07", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": "2026-05-20", "driver": "Касимов Ашимжан Дильмуратович", "status": "PAID"},
    {"plate": "503FI02", "notice": "261900030376281", "v_date": "2026-05-06", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": "2026-05-20", "driver": "Гинько Александр", "status": "PAID"},
    {"plate": "503FI02", "notice": "Акт изъятия ГРНЗ (ст. 334 КоАП РК - выбросы 100 МРП)", "v_date": "2026-06-24", "acc_date": "2026-06-25", "notified": "2026-06-25", "paid": None, "amount": 369200.0, "driver": "Жилкибаев Биржан", "status": "NOTIFIED", "notes": "Экология, изъяты номера"},
    {"plate": "576FQ02", "notice": "261900030346166", "v_date": "2026-05-01", "acc_date": "2026-05-15", "notified": "2026-05-15", "paid": "2026-05-15", "driver": "Досанов Нурполат", "status": "PAID"},
    {"plate": "644FA02", "notice": "267588230810436", "v_date": "2026-04-18", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": None, "driver": "Наурузбаев Болат Бизатович", "status": "REFUSED", "memo": True, "notes": "Жаксылык Газиз отказ от оплаты, не отвечает"},
    {"plate": "644FA02", "notice": "261900030544907", "v_date": "2026-06-19", "acc_date": "2026-06-25", "notified": "2026-06-25", "paid": None, "driver": "Наурузбаев Болат Бизатович", "status": "REFUSED", "memo": True, "notes": "Жаксылык Газиз отказ от оплаты"},
    {"plate": "762GR02", "notice": "267588230751590", "v_date": "2026-04-09", "acc_date": "2026-05-15", "notified": "2026-05-15", "paid": "2026-06-10", "driver": "Мажитов Самат Женисбекович", "status": "PAID"},
    {"plate": "762GR02", "notice": "267588230921352", "v_date": "2026-05-06", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": "2026-06-10", "driver": "Мажитов Самат Женисбекович", "status": "PAID"},
    {"plate": "762GR02", "notice": "267588230957914", "v_date": "2026-05-14", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": "2026-06-10", "driver": "Мажитов Самат Женисбекович", "status": "PAID"},
    {"plate": "762GR02", "notice": "267588231028074", "v_date": "2026-05-19", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": "2026-06-10", "driver": "Мажитов Самат Женисбекович", "status": "PAID"},
    {"plate": "764FA02", "notice": "261900030407993", "v_date": "2026-05-15", "acc_date": "2026-05-20", "notified": "2026-05-20", "paid": "2026-05-20", "driver": "Киса Улан", "status": "PAID"},
    {"plate": "848FE02", "notice": "Казавтожол № 615602873874 = 7014тг", "v_date": "2026-06-05", "acc_date": "2026-06-08", "notified": "2026-06-08", "paid": "2026-06-10", "amount": 7014.0, "driver": "Чанов Кирилл Сергеевич", "status": "PAID"},
    {"plate": "848GC02", "notice": "267588230891570", "v_date": "2026-05-04", "acc_date": "2026-05-21", "notified": "2026-05-21", "paid": "2026-05-21", "driver": "", "status": "PAID", "notes": "Михаил СБ"},
    {"plate": "869DI02", "notice": "267588230951401", "v_date": "2026-05-13", "acc_date": "2026-05-21", "notified": "2026-05-21", "paid": "2026-05-21", "driver": "Қабаргелді Нүркен Асхатұлы", "status": "PAID"},
    {"plate": "874DI02", "notice": "261900030457066", "v_date": "2026-05-28", "acc_date": "2026-06-10", "notified": "2026-06-10", "paid": None, "driver": "Чауке Бірлік Бауыржанұлы", "status": "REFUSED", "memo": True, "notes": "Отказ от оплаты, урезали бонусы нет денег"},
]

def init_db_data(db: Session):
    """Seed initial data if not already populated."""
    # 1. Create Default Users (Admin, Dispatcher, Viewer)
    if db.query(User).count() == 0:
        users = [
            User(
                username="admin",
                full_name="Администратор Системы",
                role="admin",
                hashed_password=get_password_hash("admin123")
            ),
            User(
                username="dispatcher",
                full_name="Диспетчер Транспортного Отдела",
                role="dispatcher",
                hashed_password=get_password_hash("disp123")
            ),
            User(
                username="viewer",
                full_name="Руководитель (Просмотр)",
                role="viewer",
                hashed_password=get_password_hash("view123")
            ),
        ]
        db.add_all(users)
        db.commit()

    # 2. Companies
    company_map = {}
    for c_data in COMPANIES_DATA:
        c = db.query(Company).filter(Company.name == c_data["name"]).first()
        if not c:
            c = Company(name=c_data["name"], code=c_data["code"])
            db.add(c)
            db.commit()
            db.refresh(c)
        company_map[c.name] = c.id
        if c.code:
            company_map[c.code] = c.id

    # 3. Departments
    dept_map = {}
    for d_data in DEPARTMENTS_DATA:
        d = db.query(Department).filter(Department.name == d_data["name"]).first()
        if not d:
            d = Department(
                name=d_data["name"],
                head_name=d_data.get("head_name"),
                head_phone=d_data.get("head_phone")
            )
            db.add(d)
            db.commit()
            db.refresh(d)
        dept_map[d.name] = d.id

    # 4. Vehicles
    vehicle_map = {}
    if db.query(Vehicle).count() == 0:
        for v in RAW_VEHICLES:
            norm_plate = normalize_plate(v["plate"])
            disp_plate = format_plate_display(v["plate"])
            
            # Match company
            comp_name = v.get("company", "")
            comp_id = None
            for c_key, c_id in company_map.items():
                if c_key in comp_name or comp_name in c_key:
                    comp_id = c_id
                    break

            # Match department
            dept_name = v.get("dept", "")
            dept_id = None
            for d_key, d_id in dept_map.items():
                if d_key in dept_name or dept_name in d_key:
                    dept_id = d_id
                    break
            
            new_v = Vehicle(
                plate_number=norm_plate,
                plate_display=disp_plate,
                brand_model=v.get("brand", "Не указана"),
                fuel_type=v.get("fuel", "АИ-92"),
                company_id=comp_id,
                department_id=dept_id,
                insurance_expiry=parse_date(v.get("ins")),
                inspection_expiry=parse_date(v.get("insp")),
                inspection_interval_months=v.get("interval", 12),
                vin=v.get("vin"),
                tech_passport_number=v.get("tech_passport"),
                color=v.get("color"),
                fuel_card_number=v.get("fuel_card"),
                status=v.get("status", "ACTIVE"),
                location_notes=v.get("notes") if "Шымкент" in str(v.get("notes")) or "Иссык" in str(v.get("notes")) else None,
                notes=v.get("notes")
            )
            db.add(new_v)
            db.commit()
            db.refresh(new_v)
            vehicle_map[norm_plate] = new_v.id
    else:
        for v in db.query(Vehicle).all():
            vehicle_map[v.plate_number] = v.id

    # 5. Drivers & Primary Assignments
    driver_map = {}
    if db.query(Driver).count() == 0:
        for d in RAW_DRIVERS:
            # Match department
            dept_name = d.get("dept", "")
            dept_id = None
            for d_key, d_id in dept_map.items():
                if d_key in dept_name or dept_name in d_key:
                    dept_id = d_id
                    break

            new_d = Driver(
                full_name=d["name"],
                phone=d.get("phone"),
                position=d.get("pos", "Водитель"),
                department_id=dept_id,
                status="ACTIVE"
            )
            db.add(new_d)
            db.commit()
            db.refresh(new_d)
            driver_map[d["name"]] = new_d.id

            # Create assignment to vehicle if plate is specified
            target_plate = normalize_plate(d.get("plate", ""))
            if target_plate in vehicle_map:
                v_id = vehicle_map[target_plate]
                assign = DriverAssignment(
                    vehicle_id=v_id,
                    driver_id=new_d.id,
                    start_date=date(2026, 1, 1),
                    assignment_type="PRIMARY",
                    reason="Закрепленный водитель по приказу",
                    is_active=True
                )
                db.add(assign)
                db.commit()
    else:
        for d in db.query(Driver).all():
            driver_map[d.full_name] = d.id

    # 6. Fines
    if db.query(Fine).count() == 0:
        for f in RAW_FINES:
            target_plate = normalize_plate(f["plate"])
            if target_plate not in vehicle_map:
                continue
            v_id = vehicle_map[target_plate]

            # Find driver ID if name matches or partial matches
            d_id = None
            driver_str = f.get("driver", "")
            if driver_str:
                for d_name, did in driver_map.items():
                    if d_name in driver_str or driver_str in d_name:
                        d_id = did
                        break

            new_fine = Fine(
                vehicle_id=v_id,
                driver_id=d_id,
                notice_number=f["notice"],
                violation_date=parse_date(f.get("v_date")),
                accounting_date=parse_date(f.get("acc_date")),
                driver_notified_date=parse_date(f.get("notified")),
                payment_date=parse_date(f.get("paid")),
                amount=f.get("amount", 0.0),
                status=f.get("status", "NEW"),
                is_not_our_car=f.get("is_not_our", False),
                in_official_memo=f.get("memo", False),
                notes=f.get("notes")
            )
            db.add(new_fine)
        db.commit()

    # 7. Initial Waybills Sample
    if db.query(Waybill).count() == 0:
        # Sample waybills for current month to demonstrate tracking
        sample_wb = [
            {"num": "ПЛ-0014", "plate": "014GI02", "driver": "Бейсенбай Аманжол Кенжетайулы", "odometer_start": 21102, "odometer_end": 22450, "month": "2026-10"},
            {"num": "ПЛ-0027", "plate": "027GP02", "driver": "Ажибай Кайсар Талгатулы", "odometer_start": 10956, "odometer_end": 11545, "month": "2026-10"},
            {"num": "ПЛ-0038", "plate": "038FG02", "driver": "Айманбетов Арман", "odometer_start": 27317, "odometer_end": 28400, "month": "2026-10"},
            {"num": "ПЛ-0078", "plate": "078GI02", "driver": "Смагулов Мурзабек Сатокович", "odometer_start": 18162, "odometer_end": 19500, "month": "2026-10"},
            {"num": "ПЛ-0095", "plate": "095GI02", "driver": "Шарипов Азиз", "odometer_start": 25191, "odometer_end": 25760, "month": "2026-10"},
            {"num": "ПЛ-0183", "plate": "183GY02", "driver": "Смольский Павел Владимирович", "odometer_start": 51030, "odometer_end": 52100, "month": "2026-10"},
        ]
        for wb in sample_wb:
            v_plate = normalize_plate(wb["plate"])
            if v_plate in vehicle_map:
                v_id = vehicle_map[v_plate]
                d_id = driver_map.get(wb["driver"])
                if not d_id and db.query(Driver).first():
                    d_id = db.query(Driver).first().id
                if d_id:
                    total_dist = wb["odometer_end"] - wb["odometer_start"]
                    w_obj = Waybill(
                        waybill_number=wb["num"],
                        vehicle_id=v_id,
                        driver_id=d_id,
                        period_month=wb["month"],
                        issue_date=date(2026, 10, 1),
                        valid_until=date(2026, 10, 31),
                        start_odometer=wb["odometer_start"],
                        end_odometer=wb["odometer_end"],
                        total_distance=total_dist,
                        status="RETURNED"
                    )
                    db.add(w_obj)
        db.commit()

    # 8. Sample Maintenance records from the Excel logs
    if db.query(MaintenanceRecord).count() == 0:
        sample_maint = [
            {"plate": "078GI02", "type": "SCHEDULED_TO", "desc": "ТО и замена масла (пробег 18162)", "req_date": "2026-05-18", "app_date": "2026-05-19", "mileage": 18162, "contractor": "СТО Хабаров", "status": "COMPLETED"},
            {"plate": "084FG02", "type": "SCHEDULED_TO", "desc": "ТО замена масла и фильтров", "req_date": "2026-05-19", "app_date": "2026-05-21", "mileage": 27317, "contractor": "СТО Хабаров", "status": "COMPLETED"},
            {"plate": "125ЕА02", "type": "TOW_TRUCK", "desc": "Эвакуатор до Емцова 11 (ЕРП №5700 от 09.06.26)", "req_date": "2026-06-05", "contractor": "ИП Мухраев", "status": "COMPLETED", "doc": "ЕРП №5700"},
            {"plate": "342CJ02", "type": "TOW_TRUCK", "desc": "Эвакуатор до Емцова 11 (ЕРП №5699 от 09.06.26)", "req_date": "2026-05-29", "contractor": "ИП Мухраев", "status": "COMPLETED", "doc": "ЕРП №5699"},
            {"plate": "347CP02", "type": "REPAIR", "desc": "Бензонасос, карбюратор (эвакуатор ЕРП №5364)", "req_date": "2026-05-13", "contractor": "ИП Мухраев", "status": "COMPLETED", "doc": "ЕРП №5364"},
            {"plate": "401DI02", "type": "TOW_TRUCK", "desc": "Эвакуатор до Емцова 11 (ЕРП №5363 от 20.05.26)", "req_date": "2026-05-05", "contractor": "ИП Мухраев", "status": "COMPLETED", "doc": "ЕРП №5363"},
            {"plate": "503FI02", "type": "REPAIR", "desc": "Лопнул патрубок антифриза, эвакуация до базы Емцова 11", "req_date": "2026-06-30", "contractor": "ИП Мухраев", "status": "COMPLETED"},
            {"plate": "667GY02", "type": "WHEEL_ALIGNMENT", "desc": "Геометрия и развал-схождение колес", "req_date": "2026-07-28", "contractor": "СТО Хабаров", "status": "COMPLETED"},
            {"plate": "848FE02", "type": "WINDSHIELD", "desc": "Замена лобового стекла", "req_date": "2026-06-29", "contractor": "СТО Хабаров", "status": "COMPLETED"},
        ]
        for m in sample_maint:
            v_plate = normalize_plate(m["plate"])
            if v_plate in vehicle_map:
                v_id = vehicle_map[v_plate]
                m_obj = MaintenanceRecord(
                    vehicle_id=v_id,
                    request_date=parse_date(m.get("req_date")) or date.today(),
                    appointment_date=parse_date(m.get("app_date")),
                    mileage_at_service=m.get("mileage", 0),
                    service_type=m["type"],
                    contractor=m.get("contractor"),
                    document_number=m.get("doc"),
                    description=m["desc"],
                    status=m["status"]
                )
                db.add(m_obj)
        db.commit()
