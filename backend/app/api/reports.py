import io
from datetime import date
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.core.database import get_db
from app.models.models import Vehicle, Driver, Fine, Waybill, MaintenanceRecord, User
from app.schemas.schemas import DashboardStats
from app.api.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["Отчеты и Аналитика"])

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()

    total_vehicles = db.query(Vehicle).count()
    active_vehicles = db.query(Vehicle).filter(Vehicle.status == "ACTIVE").count()
    repair_vehicles = db.query(Vehicle).filter(Vehicle.status == "REPAIR").count()
    reserve_vehicles = db.query(Vehicle).filter(Vehicle.status == "RESERVE").count()

    all_vehicles = db.query(Vehicle).all()
    ins_expired = 0
    ins_warning = 0
    insp_expired = 0
    insp_warning = 0

    for v in all_vehicles:
        if v.insurance_expiry:
            days = (v.insurance_expiry - today).days
            if days < 0:
                ins_expired += 1
            elif days <= 30:
                ins_warning += 1
        
        if v.inspection_expiry:
            days = (v.inspection_expiry - today).days
            if days < 0:
                insp_expired += 1
            elif days <= 30:
                insp_warning += 1

    total_fines = db.query(Fine).count()
    unpaid_fines = db.query(Fine).filter(Fine.status.in_(["NEW", "NOTIFIED", "REFUSED"])).count()

    active_drivers = db.query(Driver).filter(Driver.status == "ACTIVE").count()
    active_waybills = db.query(Waybill).filter(Waybill.status == "ISSUED").count()

    return {
        "total_vehicles": total_vehicles,
        "active_vehicles": active_vehicles,
        "repair_vehicles": repair_vehicles,
        "reserve_vehicles": reserve_vehicles,
        "insurance_expired": ins_expired,
        "insurance_warning": ins_warning,
        "inspection_expired": insp_expired,
        "inspection_warning": insp_warning,
        "total_fines": total_fines,
        "unpaid_fines": unpaid_fines,
        "active_drivers": active_drivers,
        "active_waybills": active_waybills
    }

@router.get("/export/vehicles")
def export_vehicles_excel(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    vehicles = db.query(Vehicle).order_by(Vehicle.plate_number).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Реестр автопарка"

    # Header styling
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='D3D3D3'),
        right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'),
        bottom=Side(style='thin', color='D3D3D3')
    )

    headers = [
        "№", "Гос. номер", "Марка/Модель", "Компания", "Подразделение", "ГСМ",
        "Страховка до", "Техосмотр до", "Статус", "Пробег (км)", "Карта ГСМ", "VIN", "Примечания"
    ]
    ws.append(headers)

    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    row_num = 2
    for idx, v in enumerate(vehicles, 1):
        ws.append([
            idx,
            v.plate_display,
            v.brand_model,
            v.company.name if v.company else "",
            v.department.name if v.department else "",
            v.fuel_type,
            v.insurance_expiry.strftime("%d.%m.%Y") if v.insurance_expiry else "",
            v.inspection_expiry.strftime("%d.%m.%Y") if v.inspection_expiry else "",
            v.status,
            v.current_mileage,
            v.fuel_card_number or "",
            v.vin or "",
            v.notes or ""
        ])
        
        # Border
        for col_idx in range(1, len(headers) + 1):
            ws.cell(row=row_num, column=col_idx).border = thin_border

        row_num += 1

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Vehicles_Registry_{date.today().strftime('%Y%m%d')}.xlsx"
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/memo")
@router.get("/export/memo-security")
def export_memo_excel(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Exports the official debt/fine memo to Security Service."""
    fines = db.query(Fine).filter(
        (Fine.status == "REFUSED") | (Fine.in_official_memo == True)
    ).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Служебная записка"

    # Title
    ws["A1"] = "СЛУЖЕБНАЯ ЗАПИСКА"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    ws["A2"] = "В службу безопасности и руководству компании"
    ws["A3"] = f"Дата формирования: {date.today().strftime('%d.%m.%Y')}"
    ws["A5"] = "В ходе проверки установлено наличие задолженности по административным штрафам по транспортным средствам, указанным в приложении."

    headers = ["№", "Компания авто", "Гос. номер", "№ Уведомления/Штрафа", "ФИО водителя", "Подразделение", "Сумма (тг)", "Статус / Примечание"]
    ws.append([])
    ws.append(headers)
    
    header_row = 7
    header_fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.fill = header_fill
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    curr_row = 8
    for idx, f in enumerate(fines, 1):
        ws.append([
            idx,
            f.vehicle.company.name if f.vehicle and f.vehicle.company else "",
            f.vehicle.plate_display if f.vehicle else "",
            f.notice_number,
            f.driver.full_name if f.driver else "Не определен",
            f.vehicle.department.name if f.vehicle and f.vehicle.department else "",
            f.amount,
            f.notes or "Отказ от оплаты в добровольном порядке"
        ])
        curr_row += 1

    ws.cell(row=curr_row + 2, column=1, value="Указанные сотрудники были проинформированы о необходимости погашения имеющейся задолженности.")
    ws.cell(row=curr_row + 3, column=1, value="Прошу рассмотреть данный вопрос и принять соответствующие меры в рамках действующих процедур.")

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Sluzhebnaya_Zapiska_{date.today().strftime('%Y%m%d')}.xlsx"
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
