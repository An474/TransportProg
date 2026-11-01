export interface User {
  id: number;
  username: string;
  full_name: string;
  role: 'admin' | 'dispatcher' | 'viewer';
  is_active: boolean;
  created_at: string;
}

export interface Company {
  id: number;
  name: string;
  code?: string;
  is_active: boolean;
}

export interface Department {
  id: number;
  name: string;
  head_name?: string;
  head_phone?: string;
  is_active: boolean;
}

export interface Vehicle {
  id: number;
  plate_number: string;
  plate_display: string;
  brand_model: string;
  fuel_type: string;
  company_id?: number;
  company_name?: string;
  department_id?: number;
  department_name?: string;
  vin?: string;
  tech_passport_number?: string;
  tech_passport_date?: string;
  color?: string;
  fuel_card_number?: string;
  lease_contract?: string;
  insurance_expiry?: string;
  inspection_expiry?: string;
  inspection_interval_months: number;
  has_gps: boolean;
  has_branding: boolean;
  status: 'ACTIVE' | 'REPAIR' | 'WRITE_OFF' | 'RESERVE' | 'SOLD';
  current_mileage: number;
  location_notes?: string;
  notes?: string;
  current_driver_name?: string;
  current_driver_phone?: string;
  days_to_insurance?: number;
  days_to_inspection?: number;
  insurance_state: 'OK' | 'WARNING' | 'EXPIRED' | 'UNSET';
  inspection_state: 'OK' | 'WARNING' | 'EXPIRED' | 'UNSET';
  created_at: string;
}

export interface Driver {
  id: number;
  full_name: string;
  phone?: string;
  position: string;
  department_id?: number;
  department_name?: string;
  status: 'ACTIVE' | 'VACATION' | 'SICK_LEAVE' | 'DISMISSED' | 'SUSPENDED';
  notes?: string;
  current_vehicle_plate?: string;
  created_at: string;
}

export interface Assignment {
  id: number;
  vehicle_id: number;
  driver_id: number;
  driver_name: string;
  driver_phone?: string;
  plate_number: string;
  start_date: string;
  end_date?: string;
  assignment_type: 'PRIMARY' | 'TEMPORARY' | 'SHIFT';
  reason?: string;
  is_active: boolean;
  notes?: string;
  created_at: string;
}

export interface Waybill {
  id: number;
  waybill_number: string;
  vehicle_id: number;
  plate_number: string;
  driver_id: number;
  driver_name: string;
  driver_phone?: string;
  period_month?: string;
  issue_date: string;
  valid_until?: string;
  start_odometer: number;
  end_odometer: number;
  total_distance: number;
  is_lost: boolean;
  weekly_returns: string;
  status: 'ISSUED' | 'RETURNED' | 'OVERDUE' | 'LOST';
  notes?: string;
  created_at: string;
}

export interface Fine {
  id: number;
  vehicle_id: number;
  plate_number: string;
  company_name?: string;
  department_name?: string;
  driver_id?: number;
  driver_name?: string;
  driver_phone?: string;
  notice_number: string;
  violation_date?: string;
  accounting_date?: string;
  driver_notified_date?: string;
  payment_date?: string;
  amount: number;
  status: 'NEW' | 'NOTIFIED' | 'PAID' | 'REFUSED' | 'DISPUTED';
  is_not_our_car: boolean;
  in_official_memo: boolean;
  notes?: string;
  created_at: string;
}

export interface MaintenanceRecord {
  id: number;
  vehicle_id: number;
  plate_number: string;
  driver_id?: number;
  driver_name?: string;
  request_date: string;
  appointment_date?: string;
  completion_date?: string;
  mileage_at_service: number;
  service_type: 'SCHEDULED_TO' | 'BODY_DAMAGE' | 'TOW_TRUCK' | 'WINDSHIELD' | 'WHEEL_ALIGNMENT' | 'REPAIR' | 'OTHER';
  contractor?: string;
  cost: number;
  document_number?: string;
  status: 'REQUESTED' | 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  description?: string;
  notes?: string;
  created_at: string;
}

export interface FuelLog {
  id: number;
  vehicle_id: number;
  plate_number: string;
  driver_id?: number;
  driver_name?: string;
  period_date: string;
  consumption_rate: number;
  distance_traveled: number;
  calculated_liters: number;
  actual_liters: number;
  deviation_liters: number;
  fuel_card_number?: string;
  notes?: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user_id?: number;
  username: string;
  entity_name: string;
  entity_id?: number;
  action: string;
  changes_json?: string;
  created_at: string;
}

export interface DashboardStats {
  total_vehicles: number;
  active_vehicles: number;
  repair_vehicles: number;
  reserve_vehicles: number;
  insurance_expired: number;
  insurance_warning: number;
  inspection_expired: number;
  inspection_warning: number;
  total_fines: number;
  unpaid_fines: number;
  active_drivers: number;
  active_waybills: number;
}
