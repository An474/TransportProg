import React, { useEffect, useState } from 'react';
import {
  Table, Card, Button, Input, Select, Tag, Space, Modal, Form,
  Row, Col, DatePicker, message, Typography, Checkbox, Tooltip, Popconfirm
} from 'antd';
import {
  FileTextOutlined, PlusOutlined, SearchOutlined, WarningOutlined,
  CheckCircleOutlined, CloseCircleOutlined, CarOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { apiClient } from '../api/client';
import { Waybill, Vehicle, Driver } from '../types';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

export const WaybillsPage: React.FC = () => {
  const [waybills, setWaybills] = useState<Waybill[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>();

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingWaybill, setEditingWaybill] = useState<Waybill | null>(null);

  const [form] = Form.useForm();
  const { hasRole } = useAuth();

  const loadData = async () => {
    setLoading(true);
    try {
      const [wList, vList, dList] = await Promise.all([
        apiClient.getWaybills({ query: searchQuery, status: selectedStatus }),
        apiClient.getVehicles(),
        apiClient.getDrivers(),
      ]);
      setWaybills(wList);
      setVehicles(vList);
      setDrivers(dList);
    } catch {
      message.error('Ошибка загрузки путевых листов');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedStatus]);

  const handleSearch = () => {
    loadData();
  };

  const handleOpenModal = (w?: Waybill) => {
    if (w) {
      setEditingWaybill(w);
      form.setFieldsValue({
        ...w,
        issue_date: dayjs(w.issue_date),
        valid_until: w.valid_until ? dayjs(w.valid_until) : null,
      });
    } else {
      setEditingWaybill(null);
      form.resetFields();
      form.setFieldsValue({
        issue_date: dayjs(),
        valid_until: dayjs().endOf('month'),
        period_month: dayjs().format('YYYY-MM'),
        status: 'ISSUED',
        is_lost: false,
      });
    }
    setIsModalOpen(true);
  };

  const handleVehicleSelect = (vId: number) => {
    const v = vehicles.find((item) => item.id === vId);
    if (v) {
      form.setFieldsValue({ start_odometer: v.current_mileage });
      // Find driver assigned to this vehicle
      const d = drivers.find((driver) => driver.full_name === v.current_driver_name);
      if (d) {
        form.setFieldsValue({ driver_id: d.id });
      }
    }
  };

  const handleSaveWaybill = async (values: any) => {
    try {
      const payload = {
        ...values,
        issue_date: values.issue_date.format('YYYY-MM-DD'),
        valid_until: values.valid_until ? values.valid_until.format('YYYY-MM-DD') : null,
      };

      if (editingWaybill) {
        await apiClient.updateWaybill(editingWaybill.id, payload);
        message.success('Путевой лист обновлен');
      } else {
        await apiClient.createWaybill(payload);
        message.success('Путевой лист успешно выписан');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const handleToggleWeek = async (w: Waybill, weekKey: 'w1' | 'w2' | 'w3' | 'w4') => {
    try {
      let state = { w1: false, w2: false, w3: false, w4: false };
      try {
        state = JSON.parse(w.weekly_returns);
      } catch {}

      state[weekKey] = !state[weekKey];
      await apiClient.updateWaybill(w.id, {
        weekly_returns: JSON.stringify(state)
      });
      loadData();
    } catch {
      message.error('Ошибка сохранения статуса недели');
    }
  };

  const handleMarkLost = async (w: Waybill) => {
    try {
      await apiClient.updateWaybill(w.id, { is_lost: true, status: 'LOST' });
      message.warning(`Путевой лист №${w.waybill_number} помечен как утерянный`);
      loadData();
    } catch {
      message.error('Ошибка');
    }
  };

  const columns = [
    {
      title: '№ Путевки',
      dataIndex: 'waybill_number',
      key: 'waybill_number',
      render: (t: string, r: Waybill) => (
        <Space>
          <Text strong>{t}</Text>
          {r.is_lost && <Tag color="error">Утеряна</Tag>}
        </Space>
      ),
    },
    {
      title: 'Автомобиль',
      dataIndex: 'plate_number',
      key: 'plate_number',
      render: (t: string) => <Tag color="blue" icon={<CarOutlined />}>{t}</Tag>,
    },
    {
      title: 'Водитель',
      dataIndex: 'driver_name',
      key: 'driver_name',
      render: (name: string, r: Waybill) => (
        <div>
          <Text>{name}</Text>
          {r.driver_phone && <div style={{ fontSize: 11, color: '#8c8c8c' }}>{r.driver_phone}</div>}
        </div>
      ),
    },
    {
      title: 'Период',
      key: 'period',
      render: (_: any, r: Waybill) => (
        <span>{dayjs(r.issue_date).format('DD.MM.YY')} – {r.valid_until ? dayjs(r.valid_until).format('DD.MM.YY') : '—'}</span>
      ),
    },
    {
      title: 'Одометр (км)',
      key: 'odometer',
      render: (_: any, r: Waybill) => (
        <span style={{ fontSize: 12 }}>
          Старт: {r.start_odometer} | Кон: {r.end_odometer || '—'} {r.total_distance > 0 && <b style={{ color: '#1677ff' }}>({r.total_distance} км)</b>}
        </span>
      ),
    },
    {
      title: 'Сдача маршрутных листов (1-4 нед)',
      key: 'weeks',
      render: (_: any, r: Waybill) => {
        let state = { w1: false, w2: false, w3: false, w4: false };
        try {
          state = JSON.parse(r.weekly_returns);
        } catch {}
        return (
          <Space orientation="horizontal" size="small">
            <Checkbox checked={state.w1} onChange={() => handleToggleWeek(r, 'w1')}>1н</Checkbox>
            <Checkbox checked={state.w2} onChange={() => handleToggleWeek(r, 'w2')}>2н</Checkbox>
            <Checkbox checked={state.w3} onChange={() => handleToggleWeek(r, 'w3')}>3н</Checkbox>
            <Checkbox checked={state.w4} onChange={() => handleToggleWeek(r, 'w4')}>4н</Checkbox>
          </Space>
        );
      },
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      render: (st: string) => {
        const map: Record<string, { label: string; color: string }> = {
          ISSUED: { label: 'На руках', color: 'processing' },
          RETURNED: { label: 'Сдан', color: 'success' },
          OVERDUE: { label: 'Просрочен', color: 'error' },
          LOST: { label: 'Утерян', color: 'default' },
        };
        const item = map[st] || { label: st, color: 'default' };
        return <Tag color={item.color}>{item.label}</Tag>;
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, r: Waybill) => (
        <Space size="small">
          {hasRole(['admin', 'dispatcher']) && (
            <>
              <Button size="small" onClick={() => handleOpenModal(r)}>Ред.</Button>
              {!r.is_lost && (
                <Popconfirm title="Отметить как утерянную?" onConfirm={() => handleMarkLost(r)} okText="Да" cancelText="Нет">
                  <Button size="small" danger>Утеря</Button>
                </Popconfirm>
              )}
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={10} md={8}>
            <Input
              placeholder="Поиск по номеру путевки, авто, водителю..."
              prefix={<SearchOutlined />}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={12} sm={6} md={5}>
            <Select
              placeholder="Статус путевого"
              style={{ width: '100%' }}
              allowClear
              value={selectedStatus}
              onChange={setSelectedStatus}
            >
              <Option value="ISSUED">На руках</Option>
              <Option value="RETURNED">Сдан</Option>
              <Option value="LOST">Утерян</Option>
              <Option value="OVERDUE">Просрочен</Option>
            </Select>
          </Col>
          <Col xs={24} sm={8} md={11} style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={handleSearch} type="primary">Применить</Button>
              {hasRole(['admin', 'dispatcher']) && (
                <Button icon={<PlusOutlined />} type="primary" onClick={() => handleOpenModal()}>
                  Выписать путевой лист
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          dataSource={waybills}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* Waybill Modal */}
      <Modal
        title={editingWaybill ? `Редактирование путевого листа: ${editingWaybill.waybill_number}` : 'Выписка путевого листа'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        okText="Сохранить"
        cancelText="Отмена"
        width={650}
      >
        <Form form={form} layout="vertical" onFinish={handleSaveWaybill}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="waybill_number" label="Номер путевого листа" rules={[{ required: true, message: 'Введите номер' }]}>
                <Input placeholder="ПЛ-1025" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="period_month" label="Месяц учета">
                <Input placeholder="2026-10" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="vehicle_id" label="Автомобиль" rules={[{ required: true, message: 'Выберите автомобиль' }]}>
                <Select showSearch placeholder="Выберите ТС" optionFilterProp="children" onChange={handleVehicleSelect}>
                  {vehicles.map((v) => (
                    <Option key={v.id} value={v.id}>
                      {v.plate_display} ({v.brand_model}) - пробег: {v.current_mileage} км
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="driver_id" label="Водитель" rules={[{ required: true, message: 'Выберите водителя' }]}>
                <Select showSearch placeholder="Выберите водителя" optionFilterProp="children">
                  {drivers.map((d) => (
                    <Option key={d.id} value={d.id}>
                      {d.full_name} ({d.position})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="issue_date" label="Дата выдачи" rules={[{ required: true }]}>
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="valid_until" label="Действителен до">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="start_odometer" label="Спидометр выезд (км)">
                <Input type="number" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="end_odometer" label="Спидометр возврат (км)">
                <Input type="number" placeholder="При возврате" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="status" label="Статус">
                <Select>
                  <Option value="ISSUED">На руках</Option>
                  <Option value="RETURNED">Сдан</Option>
                  <Option value="OVERDUE">Просрочен</Option>
                  <Option value="LOST">Утерян</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="Примечания">
            <Input.TextArea rows={2} placeholder="Причины задержки, отметки..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
