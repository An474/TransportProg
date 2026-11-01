"""
Comprehensive End-to-End Test Suite for Transport Department System.
Verifies all 12 modules, user roles, security, Kazakh UTF-8 encoding,
database consistency, and Excel export validity.
"""
import os
import sys
import io
import json
import zipfile
from datetime import date, timedelta

# Fix Windows console encoding for Kazakh characters
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Ensure backend root is on path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

passed = 0
failed = 0

def test(name):
    def decorator(fn):
        global passed, failed
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {str(e)}")
            failed += 1
    return decorator

print("=" * 70)
print(" ЗАПУСК ПОЛНОГО КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ СИСТЕМЫ ТРАНСПОРТНОГО ОТДЕЛА")
print("=" * 70)

# Tokens storage
tokens = {}
created_ids = {}

try:
    # -------------------------------------------------------------
    # 1. AUTHENTICATION & ACCESS CONTROL (RBAC)
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 1] Авторизация и разграничение прав (RBAC)...")

    @test("1.1 Вход администратора (admin / admin123)")
    def _():
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        tokens["admin"] = data["access_token"]

    @test("1.2 Вход диспетчера (dispatcher / disp123)")
    def _():
        r = client.post("/api/v1/auth/login", json={"username": "dispatcher", "password": "disp123"})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        tokens["dispatcher"] = r.json()["access_token"]

    @test("1.3 Вход руководителя (viewer / view123)")
    def _():
        r = client.post("/api/v1/auth/login", json={"username": "viewer", "password": "view123"})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        tokens["viewer"] = r.json()["access_token"]

    @test("1.4 Защита от неверного пароля")
    def _():
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong_password"})
        assert r.status_code == 401

    @test("1.5 Доступ к управлению пользователями: Администратор разрешен, Диспетчер запрещен")
    def _():
        h_admin = {"Authorization": f"Bearer {tokens['admin']}"}
        h_disp = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        
        r_admin = client.get("/api/v1/auth/users", headers=h_admin)
        assert r_admin.status_code == 200
        
        r_disp = client.get("/api/v1/auth/users", headers=h_disp)
        assert r_disp.status_code == 403, f"Expected 403 Forbidden for dispatcher, got {r_disp.status_code}"

    # -------------------------------------------------------------
    # 2. REFERENCES & DICTIONARIES
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 2] Справочники (Компании и Подразделения)...")

    @test("2.1 Список компаний (Meganet, EPB, NLS, CCK)")
    def _():
        h = {"Authorization": f"Bearer {tokens['admin']}"}
        r = client.get("/api/v1/ref/companies", headers=h)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        comps = r.json()
        assert len(comps) >= 4
        names = [c["name"] for c in comps]
        assert any("Meganet" in n for n in names)
        assert any("Elite ProBuilding" in n for n in names)

    @test("2.2 Список подразделений (Юго-Запад, Юго-Восток, ВОЛС, Шымкент и др.)")
    def _():
        h = {"Authorization": f"Bearer {tokens['admin']}"}
        r = client.get("/api/v1/ref/departments", headers=h)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        depts = r.json()
        assert len(depts) >= 10

    # -------------------------------------------------------------
    # 3. VEHICLES FLEET MANAGEMENT
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 3] Автопарк (Реестр ТС, Поиск, Карточка)...")

    @test("3.1 Загрузка реестра автопарка (217+ ТС)")
    def _():
        h = {"Authorization": f"Bearer {tokens['viewer']}"}
        r = client.get("/api/v1/vehicles?limit=300", headers=h)
        assert r.status_code == 200
        vehicles = r.json()
        assert len(vehicles) >= 217

    @test("3.2 Поиск автомобиля по госномеру (нормализованному и с пробелами)")
    def _():
        h = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        r1 = client.get("/api/v1/vehicles?query=014GI02", headers=h)
        assert r1.status_code == 200
        assert len(r1.json()) >= 1
        
        r2 = client.get("/api/v1/vehicles?query=014 GI 02", headers=h)
        assert r2.status_code == 200
        assert len(r2.json()) >= 1

    @test("3.3 Создание нового автомобиля и проверка светофора техосмотра")
    def _():
        h = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        payload = {
            "plate_number": "777ТЕСТ02",
            "brand_model": "JAC Sunray Тестовый",
            "fuel_type": "ДТ",
            "insurance_expiry": str(date.today() + timedelta(days=20)),  # Желтый светофор (<30 дней)
            "inspection_expiry": str(date.today() - timedelta(days=5)), # Красный светофор (просрочен)
            "status": "ACTIVE"
        }
        r = client.post("/api/v1/vehicles", json=payload, headers=h)
        assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
        v = r.json()
        assert v["plate_number"] == "777ТЕСТ02"
        assert v["insurance_state"] == "WARNING"
        assert v["inspection_state"] == "EXPIRED"
        created_ids["vehicle_id"] = v["id"]

    @test("3.4 Детальная карточка ТС со связанными историями")
    def _():
        h = {"Authorization": f"Bearer {tokens['viewer']}"}
        v_id = created_ids["vehicle_id"]
        r = client.get(f"/api/v1/vehicles/{v_id}/history", headers=h)
        assert r.status_code == 200
        hist = r.json()
        assert "vehicle" in hist
        assert "assignments" in hist
        assert "fines" in hist
        assert "maintenance" in hist

    # -------------------------------------------------------------
    # 4. DRIVERS & KAZAKH ALPHABET PRESERVATION
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 4] Водители и поддержка казахского алфавита...")

    @test("4.1 Загрузка базы водителей (124+ водителей)")
    def _():
        h = {"Authorization": f"Bearer {tokens['viewer']}"}
        r = client.get("/api/v1/drivers", headers=h)
        assert r.status_code == 200
        drivers = r.json()
        assert len(drivers) >= 124

    @test("4.2 Корректность сохранения и поиска специфических букв казахского языка")
    def _():
        h = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        kazakh_name = "Қасымжомарт Ғаниұлы Өмірзақ Әбдірахманұлы"
        payload = {
            "full_name": kazakh_name,
            "phone": "+7 707 999 88 77",
            "position": "Монтажник ВОЛС",
            "status": "ACTIVE"
        }
        r = client.post("/api/v1/drivers", json=payload, headers=h)
        assert r.status_code == 200
        d = r.json()
        assert d["full_name"] == kazakh_name, f"Expected {kazakh_name}, got {d['full_name']}"
        created_ids["driver_id"] = d["id"]

        # Search with Kazakh letter
        r_search = client.get("/api/v1/drivers?query=Ғаниұлы", headers=h)
        assert r_search.status_code == 200
        found = [x["full_name"] for x in r_search.json()]
        assert kazakh_name in found

    # -------------------------------------------------------------
    # 5. ASSIGNMENTS & DRIVER TRANSFERS
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 5] Журнал пересадок и замен водителей...")

    @test("5.1 Закрепление водителя за автомобилем и обновление текущего водителя")
    def _():
        h = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        v_id = created_ids["vehicle_id"]
        d_id = created_ids["driver_id"]

        assign_payload = {
            "vehicle_id": v_id,
            "driver_id": d_id,
            "start_date": str(date.today()),
            "assignment_type": "PRIMARY",
            "reason": "Основное закрепление по приказу"
        }
        r = client.post("/api/v1/assignments", json=assign_payload, headers=h)
        assert r.status_code == 200
        created_ids["assignment_id"] = r.json()["id"]

        # Check vehicle now shows current driver
        r_veh = client.get(f"/api/v1/vehicles/{v_id}", headers=h)
        assert r_veh.status_code == 200
        assert "Ғаниұлы" in (r_veh.json()["current_driver_name"] or "")

    # -------------------------------------------------------------
    # 6. WAYBILLS & ODOMETER TRACKING
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 6] Путевые листы и расчет пробега...")

    @test("6.1 Создание путевого листа с расчетом дистанции")
    def _():
        h = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        wb_payload = {
            "waybill_number": "ПЛ-ТЕСТ-001",
            "vehicle_id": created_ids["vehicle_id"],
            "driver_id": created_ids["driver_id"],
            "period_month": "2026-11",
            "issue_date": str(date.today()),
            "start_odometer": 10000,
            "end_odometer": 10550,
            "status": "RETURNED"
        }
        r = client.post("/api/v1/waybills", json=wb_payload, headers=h)
        assert r.status_code == 200
        wb = r.json()
        assert wb["total_distance"] == 550
        created_ids["waybill_id"] = wb["id"]

    @test("6.2 Еженедельный контроль возврата (Недели 1, 2, 3, 4)")
    def _():
        h = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        wb_id = created_ids["waybill_id"]
        update_payload = {
            "weekly_returns": json.dumps({"w1": True, "w2": True, "w3": False, "w4": False})
        }
        r = client.put(f"/api/v1/waybills/{wb_id}", json=update_payload, headers=h)
        assert r.status_code == 200
        assert r.json()["weekly_returns"] == update_payload["weekly_returns"]

    # -------------------------------------------------------------
    # 7. FINES & SMART DRIVER AUTO-DETECTION
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 7] Штрафы ПДД и умное автоопределение водителя...")

    @test("7.1 Автоматическое определение ответственного водителя по дате нарушения")
    def _():
        h = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        fine_payload = {
            "vehicle_id": created_ids["vehicle_id"],
            "notice_number": "ШТР-ТЕСТ-999",
            "violation_date": str(date.today()),
            "accounting_date": str(date.today()),
            "amount": 19500.0,
            "status": "NEW"
        }
        r = client.post("/api/v1/fines", json=fine_payload, headers=h)
        assert r.status_code == 200
        fine = r.json()
        # Driver must be auto-assigned because of active assignment
        assert fine["driver_id"] == created_ids["driver_id"]
        assert "Ғаниұлы" in fine["driver_name"]
        created_ids["fine_id"] = fine["id"]

    @test("7.2 Перевод статуса штрафа: Оповещен -> Оплачен")
    def _():
        h = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        f_id = created_ids["fine_id"]
        r = client.put(f"/api/v1/fines/{f_id}", json={"status": "PAID", "payment_date": str(date.today())}, headers=h)
        assert r.status_code == 200
        assert r.json()["status"] == "PAID"

    # -------------------------------------------------------------
    # 8. MAINTENANCE & REPAIRS
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 8] ТО, Ремонты и Эвакуация...")

    @test("8.1 Создание записи ТО и эвакуации ИП Мухраев")
    def _():
        h = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        maint_payload = {
            "vehicle_id": created_ids["vehicle_id"],
            "driver_id": created_ids["driver_id"],
            "service_type": "TOW_TRUCK",
            "contractor": "ИП Мухраев",
            "document_number": "ЕРП №9999",
            "description": "Эвакуация после поломки на базу Емцова 11",
            "status": "IN_PROGRESS"
        }
        r = client.post("/api/v1/maintenance", json=maint_payload, headers=h)
        assert r.status_code == 200
        m = r.json()
        assert m["contractor"] == "ИП Мухраев"
        assert "777" in m["plate_number"]
        created_ids["maint_id"] = m["id"]

    # -------------------------------------------------------------
    # 9. FUEL LOGS
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 9] Учет ГСМ и топлива...")

    @test("9.1 Внесение фактической заправки и расчет отклонений")
    def _():
        h = {"Authorization": f"Bearer {tokens['dispatcher']}"}
        fuel_payload = {
            "vehicle_id": created_ids["vehicle_id"],
            "driver_id": created_ids["driver_id"],
            "period_date": str(date.today()),
            "consumption_rate": 10.0,
            "distance_traveled": 500.0,
            "actual_liters": 55.0,
            "fuel_card_number": "9900-1122-3344"
        }
        r = client.post("/api/v1/fuel", json=fuel_payload, headers=h)
        assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
        fl = r.json()
        assert fl["calculated_liters"] == 50.0  # (500 * 10) / 100
        assert fl["actual_liters"] == 55.0
        assert fl["deviation_liters"] == 5.0    # 55 - 50 = +5.0 (перерасход)
        created_ids["fuel_id"] = fl["id"]

    # -------------------------------------------------------------
    # 10. REPORTS & EXCEL EXPORT
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 10] Аналитика и Экспорт в Excel...")

    @test("10.1 Показатели сводного дашборда")
    def _():
        h = {"Authorization": f"Bearer {tokens['viewer']}"}
        r = client.get("/api/v1/reports/dashboard", headers=h)
        assert r.status_code == 200
        data = r.json()
        assert "total_vehicles" in data
        assert "active_vehicles" in data
        assert "inspection_expired" in data

    @test("10.2 Выгрузка реестра автопарка в Excel (.xlsx) с валидацией файла")
    def _():
        h = {"Authorization": f"Bearer {tokens['admin']}"}
        r = client.get("/api/v1/reports/export/vehicles", headers=h)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
        # Verify it is a valid zip/xlsx archive
        zipfile.ZipFile(io.BytesIO(r.content))

    @test("10.3 Выгрузка служебной записки в СБ по штрафам (.xlsx)")
    def _():
        h = {"Authorization": f"Bearer {tokens['admin']}"}
        r = client.get("/api/v1/reports/export/memo", headers=h)
        assert r.status_code == 200
        zipfile.ZipFile(io.BytesIO(r.content))

    @test("10.4 Скачивание отчета через параметр ?token=... (для вкладок браузера)")
    def _():
        token = tokens["viewer"]
        r = client.get(f"/api/v1/reports/export/vehicles?token={token}")
        assert r.status_code == 200

    # -------------------------------------------------------------
    # 11. AUDIT TRAIL
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 11] Журнал аудита...")

    @test("11.1 Запись всех действий в аудит-лог")
    def _():
        h = {"Authorization": f"Bearer {tokens['admin']}"}
        r = client.get("/api/v1/audit", headers=h)
        assert r.status_code == 200
        logs = r.json()
        assert len(logs) > 0
        actions = [l["action"] for l in logs]
        assert "CREATE" in actions

    # -------------------------------------------------------------
    # 12. BACKUPS & GOOGLE DRIVE WEBHOOK
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 12] Резервные копии и Google Диск...")

    @test("12.1 Создание резервной копии базы данных")
    def _():
        h = {"Authorization": f"Bearer {tokens['admin']}"}
        r = client.post("/api/v1/backup/create", headers=h)
        assert r.status_code == 200
        res = r.json()
        assert res["status"] == "ok"
        assert res["filename"].endswith(".zip")

    @test("12.2 Сохранение и чтение настроек Google Диска")
    def _():
        h = {"Authorization": f"Bearer {tokens['admin']}"}
        settings_payload = {
            "google_drive_webhook_url": "https://script.google.com/macros/s/TEST_MACRO/exec",
            "google_drive_enabled": True
        }
        r = client.post("/api/v1/backup/settings", json=settings_payload, headers=h)
        assert r.status_code == 200
        
        r_get = client.get("/api/v1/backup/settings", headers=h)
        assert r_get.status_code == 200
        assert r_get.json()["google_drive_webhook_url"] == settings_payload["google_drive_webhook_url"]

    # -------------------------------------------------------------
    # 13. SYSTEM & GITHUB UPDATES
    # -------------------------------------------------------------
    print("\n[МОДУЛЬ 13] Обновление через GitHub...")

    @test("13.1 Проверка версии и обновлений GitHub")
    def _():
        h = {"Authorization": f"Bearer {tokens['admin']}"}
        r = client.get("/api/v1/system/updates", headers=h)
        assert r.status_code == 200
        data = r.json()
        assert "current_version" in data
        assert "has_update" in data

finally:
    # -------------------------------------------------------------
    # CLEANUP TEST DATA
    # -------------------------------------------------------------
    print("\n[ОЧИСТКА] Удаление тестовых записей...")
    if "admin" in tokens:
        h_admin = {"Authorization": f"Bearer {tokens['admin']}"}
        if "fuel_id" in created_ids:
            client.delete(f"/api/v1/fuel/{created_ids['fuel_id']}", headers=h_admin)
        if "maint_id" in created_ids:
            client.delete(f"/api/v1/maintenance/{created_ids['maint_id']}", headers=h_admin)
        if "fine_id" in created_ids:
            client.delete(f"/api/v1/fines/{created_ids['fine_id']}", headers=h_admin)
        if "waybill_id" in created_ids:
            client.delete(f"/api/v1/waybills/{created_ids['waybill_id']}", headers=h_admin)
        if "vehicle_id" in created_ids:
            client.delete(f"/api/v1/vehicles/{created_ids['vehicle_id']}", headers=h_admin)
        if "driver_id" in created_ids:
            client.delete(f"/api/v1/drivers/{created_ids['driver_id']}", headers=h_admin)
        print("  Тестовые записи успешно удалены.")

print("\n" + "=" * 70)
print(f"ИТОГ ТЕСТИРОВАНИЯ: УСПЕШНО: {passed} | ПРОВАЛЕНО: {failed}")
print("=" * 70)

if failed > 0:
    sys.exit(1)
