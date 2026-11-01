import React, { useEffect, useState } from 'react';
import {
  Table, Card, Button, Input, Select, Tag, Space, Modal, Form,
  Row, Col, DatePicker, message, Typography, Tooltip, Drawer, Tabs, Descriptions, Popconfirm
} from 'antd';
import {
  CarOutlined, PlusOutlined, SearchOutlined, DownloadOutlined,
  EditOutlined, DeleteOutlined, InfoCircleOutlined, SwapOutlined, WarningOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { apiClient } from '../api/client';
import { Vehicle, Company, Department, Driver } from '../types';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

export const VehiclesPage: React.FC = () => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCompany, setSelectedCompany] = useState<number | undefined>();
  const [selectedDept, setSelectedDept] = useState<number | undefined>();
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>();
  const [selectedInsState, setSelectedInsState] = useState<string | undefined>();
  const [selectedInspState, setSelectedInspState] = useState<string | undefined>();

  // Modals & Details
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [drawerVehicleId, setDrawerVehicleId] = useState<number | null>(null);
  const [vehicleHistory, setVehicleHistory] = useState<any | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Quick assignment modal
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [assignTargetVehicle, setAssignTargetVehicle] = useState<Vehicle | null>(null);
  const [exporting, setExporting] = useState(false);

  const [form] = Form.useForm();
  const [assignForm] = Form.useForm();
  const { hasRole } = useAuth();

  const loadData = async () => {
    setLoading(true);
    try {
      const [vList, cList, dList, drList] = await Promise.all([
        apiClient.getVehicles({
          query: searchQuery,
          company_id: selectedCompany,
          department_id: selectedDept,
          status: selectedStatus,
          insurance_state: selectedInsState,
          inspection_state: selectedInspState,
        }),
        apiClient.getCompanies(),
        apiClient.getDepartments(),
        apiClient.getDrivers(),
      ]);
      setVehicles(vList);
      setCompanies(cList);
      setDepartments(dList);
      setDrivers(drList);
    } catch (err: any) {
      message.error('Ошибка загрузки данных автопарка');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCompany, selectedDept, selectedStatus, selectedInsState, selectedInspState]);

  const handleSearch = () => {
    loadData();
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      await apiClient.downloadFile('/reports/export/vehicles', `Vehicles_Registry_${dayjs().format('YYYYMMDD')}.xlsx`);
      message.success('Реестр автопарка успешно выгружен в Excel');
    } catch {
      message.error('Ошибка выгрузки файла');
    } finally {
      setExporting(false);
    }
  };

  const handleOpenModal = (v?: Vehicle) => {
    if (v) {
      setEditingVehicle(v);
      form.setFieldsValue({
        ...v,
        insurance_expiry: v.insurance_expiry ? dayjs(v.insurance_expiry) : null,
        inspection_expiry: v.inspection_expiry ? dayjs(v.inspection_expiry) : null,
        tech_passport_date: v.tech_passport_date ? dayjs(v.tech_passport_date) : null,
      });
    } else {
      setEditingVehicle(null);
      form.resetFields();
      form.setFieldsValue({
        status: 'ACTIVE',
        fuel_type: 'АИ-92',
        inspection_interval_months: 12,
        has_gps: false,
        has_branding: false,
      });
    }
    setIsModalOpen(true);
  };

  const handleSaveVehicle = async (values: any) => {
    try {
      const payload = {
        ...values,
        insurance_expiry: values.insurance_expiry ? values.insurance_expiry.format('YYYY-MM-DD') : null,
        inspection_expiry: values.inspection_expiry ? values.inspection_expiry.format('YYYY-MM-DD') : null,
        tech_passport_date: values.tech_passport_date ? values.tech_passport_date.format('YYYY-MM-DD') : null,
      };

      if (editingVehicle) {
        await apiClient.updateVehicle(editingVehicle.id, payload);
        message.success('Данные автомобиля успешно обновлены');
      } else {
        await apiClient.createVehicle(payload);
        message.success('Автомобиль успешно добавлен в базу');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const handleDeleteVehicle = async (id: number) => {
    try {
      await apiClient.deleteVehicle(id);
      message.success('Автомобиль удален');
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const handleOpenDrawer = async (vehicleId: number) => {
    setDrawerVehicleId(vehicleId);
    setHistoryLoading(true);
    try {
      const data = await apiClient.getVehicleHistory(vehicleId);
      setVehicleHistory(data);
    } catch {
      message.error('Ошибка загрузки карточки ТС');
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleOpenAssignModal = (v: Vehicle) => {
    setAssignTargetVehicle(v);
    assignForm.resetFields();
    assignForm.setFieldsValue({
      vehicle_id: v.id,
      assignment_type: 'PRIMARY',
      start_date: dayjs(),
      reason: 'Плановое закрепление'
    });
    setIsAssignModalOpen(true);
  };

  const handleSaveAssignment = async (values: any) => {
    try {
      await apiClient.createAssignment({
        ...values,
        start_date: values.start_date.format('YYYY-MM-DD'),
        end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : null,
      });
      message.success('Пересадка успешно зафиксирована');
      setIsAssignModalOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка фиксации пересадки');
    }
  };

  const columns = [
    {
      title: 'Гос. номер',
      dataIndex: 'plate_display',
      key: 'plate_display',
      fixed: 'left' as const,
      width: 130,
      render: (text: string, r: Vehicle) => (
        <a onClick={() => handleOpenDrawer(r.id)} style={{ fontWeight: 600, color: '#1677ff' }}>
          {text}
        </a>
      ),
    },
    {
      title: 'Марка / Модель',
      dataIndex: 'brand_model',
      key: 'brand_model',
      width: 170,
    },
    {
      title: 'Компания',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 160,
      render: (t: string) => t || <Text type="secondary">—</Text>,
    },
    {
      title: 'Подразделение',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 150,
      render: (t: string) => t || <Text type="secondary">—</Text>,
    },
    {
      title: 'Закрепленный водитель',
      key: 'driver',
      width: 220,
      render: (_: any, r: Vehicle) => (
        <div>
          {r.current_driver_name ? (
            <div>
              <Text strong style={{ fontSize: 13 }}>{r.current_driver_name}</Text>
              {r.current_driver_phone && (
                <div style={{ fontSize: 11, color: '#8c8c8c' }}>{r.current_driver_phone}</div>
              )}
            </div>
          ) : (
            <Tag color="default">Не закреплен</Tag>
          )}
        </div>
      ),
    },
    {
      title: 'Страховка (ОГПО)',
      key: 'insurance',
      width: 140,
      render: (_: any, r: Vehicle) => {
        if (!r.insurance_expiry) return <Tag>Нет даты</Tag>;
        if (r.insurance_state === 'EXPIRED') {
          return <Tag color="error">Истекла ({r.days_to_insurance} дн)</Tag>;
        }
        if (r.insurance_state === 'WARNING') {
          return <Tag color="warning">Осталось {r.days_to_insurance} дн</Tag>;
        }
        return <Tag color="success">до {dayjs(r.insurance_expiry).format('DD.MM.YY')}</Tag>;
      },
    },
    {
      title: 'Техосмотр',
      key: 'inspection',
      width: 140,
      render: (_: any, r: Vehicle) => {
        if (!r.inspection_expiry) return <Tag>Нет даты</Tag>;
        if (r.inspection_state === 'EXPIRED') {
          return <Tag color="error">Истек ({r.days_to_inspection} дн)</Tag>;
        }
        if (r.inspection_state === 'WARNING') {
          return <Tag color="warning">Осталось {r.days_to_inspection} дн</Tag>;
        }
        return <Tag color="success">до {dayjs(r.inspection_expiry).format('DD.MM.YY')}</Tag>;
      },
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (st: string) => {
        const map: Record<string, { label: string; color: string }> = {
          ACTIVE: { label: 'В строю', color: 'green' },
          REPAIR: { label: 'В ремонте', color: 'orange' },
          RESERVE: { label: 'Резерв', color: 'blue' },
          WRITE_OFF: { label: 'Списание', color: 'red' },
          SOLD: { label: 'Продан', color: 'default' },
        };
        const item = map[st] || { label: st, color: 'default' };
        return <Tag color={item.color}>{item.label}</Tag>;
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      fixed: 'right' as const,
      width: 150,
      render: (_: any, r: Vehicle) => (
        <Space size="small">
          <Tooltip title="Карточка ТС">
            <Button size="small" icon={<InfoCircleOutlined />} onClick={() => handleOpenDrawer(r.id)} />
          </Tooltip>
          {hasRole(['admin', 'dispatcher']) && (
            <>
              <Tooltip title="Пересадить водителя">
                <Button size="small" icon={<SwapOutlined />} onClick={() => handleOpenAssignModal(r)} />
              </Tooltip>
              <Tooltip title="Редактировать">
                <Button size="small" icon={<EditOutlined />} onClick={() => handleOpenModal(r)} />
              </Tooltip>
            </>
          )}
          {hasRole(['admin']) && (
            <Popconfirm title="Удалить автомобиль?" onConfirm={() => handleDeleteVehicle(r.id)} okText="Да" cancelText="Нет">
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <Input
              placeholder="Поиск по номеру, марке, VIN..."
              prefix={<SearchOutlined />}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="Компания"
              style={{ width: '100%' }}
              allowClear
              value={selectedCompany}
              onChange={setSelectedCompany}
            >
              {companies.map((c) => (
                <Option key={c.id} value={c.id}>{c.name}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="Подразделение"
              style={{ width: '100%' }}
              allowClear
              value={selectedDept}
              onChange={setSelectedDept}
            >
              {departments.map((d) => (
                <Option key={d.id} value={d.id}>{d.name}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Select
              placeholder="Статус ТС"
              style={{ width: '100%' }}
              allowClear
              value={selectedStatus}
              onChange={setSelectedStatus}
            >
              <Option value="ACTIVE">В строю</Option>
              <Option value="REPAIR">В ремонте</Option>
              <Option value="RESERVE">Резерв</Option>
              <Option value="WRITE_OFF">Списание</Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Select
              placeholder="Техосмотр"
              style={{ width: '100%' }}
              allowClear
              value={selectedInspState}
              onChange={setSelectedInspState}
            >
              <Option value="EXPIRED">Просрочен</Option>
              <Option value="WARNING">Скоро (&lt;30 дн)</Option>
              <Option value="OK">В норме</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4} style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={handleSearch} type="primary">Применить</Button>
              {hasRole(['admin', 'dispatcher']) && (
                <Button icon={<PlusOutlined />} type="primary" onClick={() => handleOpenModal()}>
                  Добавить
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
          <Text strong>Найдено автомобилей: {vehicles.length}</Text>
          <Button icon={<DownloadOutlined />} loading={exporting} onClick={handleExport}>
            Выгрузить в Excel
          </Button>
        </div>

        <Table
          dataSource={vehicles}
          columns={columns}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1250 }}
          pagination={{ pageSize: 25, showSizeChanger: true, pageSizeOptions: ['15', '25', '50', '100'] }}
        />
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        title={editingVehicle ? `Редактирование: ${editingVehicle.plate_display}` : 'Новый автомобиль'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        width={700}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" onFinish={handleSaveVehicle}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="plate_number" label="Гос. номер" rules={[{ required: true, message: 'Введите гос. номер' }]}>
                <Input placeholder="014GI02" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="brand_model" label="Марка / Модель" rules={[{ required: true, message: 'Введите марку' }]}>
                <Input placeholder="DFSK C 35" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="company_id" label="Компания-владелец">
                <Select placeholder="Выберите компанию" allowClear>
                  {companies.map((c) => (
                    <Option key={c.id} value={c.id}>{c.name}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="department_id" label="Подразделение">
                <Select placeholder="Выберите подразделение" allowClear>
                  {departments.map((d) => (
                    <Option key={d.id} value={d.id}>{d.name}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="fuel_type" label="Вид топлива">
                <Select>
                  <Option value="АИ-92">АИ-92</Option>
                  <Option value="АИ-95">АИ-95</Option>
                  <Option value="ДТ">ДТ (Дизель)</Option>
                  <Option value="Электро">Электро</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="fuel_card_number" label="Номер карты ГСМ">
                <Input placeholder="96378" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="status" label="Статус ТС">
                <Select>
                  <Option value="ACTIVE">В строю</Option>
                  <Option value="REPAIR">В ремонте</Option>
                  <Option value="RESERVE">В резерве</Option>
                  <Option value="WRITE_OFF">Списание</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="insurance_expiry" label="Страховка до">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="inspection_expiry" label="Техосмотр до">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="current_mileage" label="Текущий пробег (км)">
                <Input type="number" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="color" label="Цвет">
                <Input placeholder="Белый" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="vin" label="VIN номер">
                <Input placeholder="MXCCVABD..." />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="Примечания и комментарии">
            <Input.TextArea rows={2} placeholder="Акты передачи, примечания..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* Driver Transfer / Assignment Modal */}
      <Modal
        title={`Пересадка / Закрепление водителя: ${assignTargetVehicle?.plate_display}`}
        open={isAssignModalOpen}
        onCancel={() => setIsAssignModalOpen(false)}
        onOk={() => assignForm.submit()}
        okText="Закрепить водителя"
        cancelText="Отмена"
      >
        <Form form={assignForm} layout="vertical" onFinish={handleSaveAssignment}>
          <Form.Item name="vehicle_id" hidden>
            <Input />
          </Form.Item>

          <Form.Item name="driver_id" label="Выберите водителя" rules={[{ required: true, message: 'Выберите водителя' }]}>
            <Select showSearch placeholder="Поиск по ФИО водителя" optionFilterProp="children">
              {drivers.map((d) => (
                <Option key={d.id} value={d.id}>
                  {d.full_name} ({d.position}) {d.phone ? `- ${d.phone}` : ''}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="assignment_type" label="Тип закрепления">
                <Select>
                  <Option value="PRIMARY">Основное закрепление</Option>
                  <Option value="TEMPORARY">Временная замена (Пересадка)</Option>
                  <Option value="SHIFT">Сменный водитель</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="start_date" label="Дата передачи">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="reason" label="Причина передачи">
            <Input placeholder="Отпуск основного водителя, ремонт его авто, служебное задание..." />
          </Form.Item>

          <Form.Item name="notes" label="Примечание к передаче">
            <Input placeholder="Переданы ключи, акт приема, техпаспорт..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* Vehicle Full History Drawer */}
      <Drawer
        title={`Карточка автомобиля: ${vehicleHistory?.vehicle?.plate_display || ''}`}
        placement="right"
        width={750}
        onClose={() => setDrawerVehicleId(null)}
        open={drawerVehicleId !== null}
      >
        {historyLoading || !vehicleHistory ? (
          <div style={{ textAlign: 'center', padding: 40 }}><Text type="secondary">Загрузка...</Text></div>
        ) : (
          <Tabs defaultActiveKey="info" items={[
            {
              key: 'info',
              label: 'Общая информация',
              children: (
                <div>
                  <Descriptions bordered column={2} size="small">
                    <Descriptions.Item label="Гос. номер">{vehicleHistory.vehicle.plate_display}</Descriptions.Item>
                    <Descriptions.Item label="Марка">{vehicleHistory.vehicle.brand_model}</Descriptions.Item>
                    <Descriptions.Item label="Компания">{vehicleHistory.vehicle.company_name || '—'}</Descriptions.Item>
                    <Descriptions.Item label="Подразделение">{vehicleHistory.vehicle.department_name || '—'}</Descriptions.Item>
                    <Descriptions.Item label="Топливо">{vehicleHistory.vehicle.fuel_type}</Descriptions.Item>
                    <Descriptions.Item label="Карта ГСМ">{vehicleHistory.vehicle.fuel_card_number || '—'}</Descriptions.Item>
                    <Descriptions.Item label="Страховка до">
                      {vehicleHistory.vehicle.insurance_expiry || '—'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Техосмотр до">
                      {vehicleHistory.vehicle.inspection_expiry || '—'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Текущий пробег">{vehicleHistory.vehicle.current_mileage} км</Descriptions.Item>
                    <Descriptions.Item label="Статус">{vehicleHistory.vehicle.status}</Descriptions.Item>
                    <Descriptions.Item label="VIN">{vehicleHistory.vehicle.vin || '—'}</Descriptions.Item>
                    <Descriptions.Item label="Цвет">{vehicleHistory.vehicle.color || '—'}</Descriptions.Item>
                  </Descriptions>
                  {vehicleHistory.vehicle.notes && (
                    <div style={{ marginTop: 16 }}>
                      <Text strong>Примечания: </Text>
                      <Text>{vehicleHistory.vehicle.notes}</Text>
                    </div>
                  )}
                </div>
              )
            },
            {
              key: 'drivers',
              label: `Пересадки (${vehicleHistory.assignments.length})`,
              children: (
                <Table
                  dataSource={vehicleHistory.assignments}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  columns={[
                    { title: 'Водитель', dataIndex: 'driver_name' },
                    { title: 'Тип', dataIndex: 'assignment_type', render: (t) => t === 'PRIMARY' ? <Tag color="blue">Основной</Tag> : <Tag color="orange">Замена</Tag> },
                    { title: 'С', dataIndex: 'start_date' },
                    { title: 'По', dataIndex: 'end_date', render: (t) => t || 'По наст. время' },
                    { title: 'Причина', dataIndex: 'reason' },
                  ]}
                />
              )
            },
            {
              key: 'fines',
              label: `Штрафы (${vehicleHistory.fines.length})`,
              children: (
                <Table
                  dataSource={vehicleHistory.fines}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  columns={[
                    { title: '№ Протокола', dataIndex: 'notice_number' },
                    { title: 'Дата', dataIndex: 'violation_date' },
                    { title: 'Водитель', dataIndex: 'driver_name' },
                    { title: 'Сумма', dataIndex: 'amount' },
                    { title: 'Статус', dataIndex: 'status', render: (st) => st === 'PAID' ? <Tag color="green">Оплачен</Tag> : <Tag color="red">Не оплачен</Tag> },
                  ]}
                />
              )
            },
            {
              key: 'maintenance',
              label: `ТО и Ремонт (${vehicleHistory.maintenance.length})`,
              children: (
                <Table
                  dataSource={vehicleHistory.maintenance}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  columns={[
                    { title: 'Дата', dataIndex: 'request_date' },
                    { title: 'Тип', dataIndex: 'service_type' },
                    { title: 'Описание', dataIndex: 'description' },
                    { title: 'СТО', dataIndex: 'contractor' },
                    { title: 'Статус', dataIndex: 'status', render: (st) => <Tag>{st}</Tag> },
                  ]}
                />
              )
            }
          ]} />
        )}
      </Drawer>
    </div>
  );
};
