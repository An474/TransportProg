import axios from 'axios';
import {
  User, Company, Department, Vehicle, Driver, Assignment,
  Waybill, Fine, MaintenanceRecord, FuelLog, AuditLog, DashboardStats
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (window.location.pathname !== '/login') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const apiClient = {
  // Auth
  login: async (username: string, password: string) => {
    const res = await api.post('/auth/login', { username, password });
    return res.data;
  },
  getMe: async (): Promise<User> => {
    const res = await api.get('/auth/me');
    return res.data;
  },
  getUsers: async (): Promise<User[]> => {
    const res = await api.get('/auth/users');
    return res.data;
  },
  createUser: async (data: any): Promise<User> => {
    const res = await api.post('/auth/users', data);
    return res.data;
  },
  updateUser: async (id: number, data: any): Promise<User> => {
    const res = await api.put(`/auth/users/${id}`, data);
    return res.data;
  },
  deleteUser: async (id: number) => {
    const res = await api.delete(`/auth/users/${id}`);
    return res.data;
  },

  // References
  getCompanies: async (): Promise<Company[]> => {
    const res = await api.get('/ref/companies');
    return res.data;
  },
  getDepartments: async (): Promise<Department[]> => {
    const res = await api.get('/ref/departments');
    return res.data;
  },

  // Vehicles
  getVehicles: async (params?: any): Promise<Vehicle[]> => {
    const res = await api.get('/vehicles', { params });
    return res.data;
  },
  getVehicle: async (id: number): Promise<Vehicle> => {
    const res = await api.get(`/vehicles/${id}`);
    return res.data;
  },
  getVehicleHistory: async (id: number): Promise<any> => {
    const res = await api.get(`/vehicles/${id}/history`);
    return res.data;
  },
  createVehicle: async (data: any): Promise<Vehicle> => {
    const res = await api.post('/vehicles', data);
    return res.data;
  },
  updateVehicle: async (id: number, data: any): Promise<Vehicle> => {
    const res = await api.put(`/vehicles/${id}`, data);
    return res.data;
  },
  deleteVehicle: async (id: number) => {
    const res = await api.delete(`/vehicles/${id}`);
    return res.data;
  },

  // Drivers
  getDrivers: async (params?: any): Promise<Driver[]> => {
    const res = await api.get('/drivers', { params });
    return res.data;
  },
  createDriver: async (data: any): Promise<Driver> => {
    const res = await api.post('/drivers', data);
    return res.data;
  },
  updateDriver: async (id: number, data: any): Promise<Driver> => {
    const res = await api.put(`/drivers/${id}`, data);
    return res.data;
  },
  deleteDriver: async (id: number) => {
    const res = await api.delete(`/drivers/${id}`);
    return res.data;
  },

  // Assignments
  getAssignments: async (params?: any): Promise<Assignment[]> => {
    const res = await api.get('/assignments', { params });
    return res.data;
  },
  createAssignment: async (data: any): Promise<Assignment> => {
    const res = await api.post('/assignments', data);
    return res.data;
  },
  deactivateAssignment: async (id: number) => {
    const res = await api.put(`/assignments/${id}/deactivate`);
    return res.data;
  },

  // Waybills
  getWaybills: async (params?: any): Promise<Waybill[]> => {
    const res = await api.get('/waybills', { params });
    return res.data;
  },
  createWaybill: async (data: any): Promise<Waybill> => {
    const res = await api.post('/waybills', data);
    return res.data;
  },
  updateWaybill: async (id: number, data: any): Promise<Waybill> => {
    const res = await api.put(`/waybills/${id}`, data);
    return res.data;
  },
  deleteWaybill: async (id: number) => {
    const res = await api.delete(`/waybills/${id}`);
    return res.data;
  },

  // Fines
  getFines: async (params?: any): Promise<Fine[]> => {
    const res = await api.get('/fines', { params });
    return res.data;
  },
  autoDetectDriver: async (vehicleId: number, violationDate: string) => {
    const res = await api.get('/fines/auto-detect-driver', {
      params: { vehicle_id: vehicleId, violation_date: violationDate },
    });
    return res.data;
  },
  createFine: async (data: any): Promise<Fine> => {
    const res = await api.post('/fines', data);
    return res.data;
  },
  updateFine: async (id: number, data: any): Promise<Fine> => {
    const res = await api.put(`/fines/${id}`, data);
    return res.data;
  },
  deleteFine: async (id: number) => {
    const res = await api.delete(`/fines/${id}`);
    return res.data;
  },
  getMemoCandidates: async (): Promise<Fine[]> => {
    const res = await api.get('/fines/memo-candidates');
    return res.data;
  },

  // Maintenance
  getMaintenance: async (params?: any): Promise<MaintenanceRecord[]> => {
    const res = await api.get('/maintenance', { params });
    return res.data;
  },
  createMaintenance: async (data: any): Promise<MaintenanceRecord> => {
    const res = await api.post('/maintenance', data);
    return res.data;
  },
  updateMaintenance: async (id: number, data: any): Promise<MaintenanceRecord> => {
    const res = await api.put(`/maintenance/${id}`, data);
    return res.data;
  },
  deleteMaintenance: async (id: number) => {
    const res = await api.delete(`/maintenance/${id}`);
    return res.data;
  },

  // Fuel
  getFuelLogs: async (params?: any): Promise<FuelLog[]> => {
    const res = await api.get('/fuel', { params });
    return res.data;
  },
  createFuelLog: async (data: any): Promise<FuelLog> => {
    const res = await api.post('/fuel', data);
    return res.data;
  },
  deleteFuelLog: async (id: number) => {
    const res = await api.delete(`/fuel/${id}`);
    return res.data;
  },

  // Reports
  getDashboardStats: async (): Promise<DashboardStats> => {
    const res = await api.get('/reports/dashboard');
    return res.data;
  },
  getAuditLogs: async (params?: any): Promise<AuditLog[]> => {
    const res = await api.get('/audit', { params });
    return res.data;
  },
  getBackups: async (): Promise<any[]> => {
    const res = await api.get('/backup');
    return res.data;
  },
  createBackup: async () => {
    const res = await api.post('/backup/create');
    return res.data;
  },
  getBackupSettings: async () => {
    const res = await api.get('/backup/settings');
    return res.data;
  },
  saveBackupSettings: async (data: any) => {
    const res = await api.post('/backup/settings', data);
    return res.data;
  },
  testGoogleDrive: async () => {
    const res = await api.post('/backup/test-google-drive');
    return res.data;
  },
  checkUpdates: async () => {
    const res = await api.get('/system/updates');
    return res.data;
  },
  applyUpdate: async (data?: any) => {
    const res = await api.post('/system/update', data || {});
    return res.data;
  },
  downloadFile: async (url: string, filename: string) => {
    const res = await api.get(url, { responseType: 'blob' });
    const blobUrl = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  },
};
