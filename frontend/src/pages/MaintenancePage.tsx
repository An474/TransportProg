import React, { useEffect, useState } from 'react';
import {
  Table, Card, Button, Input, Select, Tag, Space, Modal, Form,
  Row, Col, DatePicker, message, Typography, Tooltip, Popconfirm
} from 'antd';
import {
  ToolOutlined, PlusOutlined, SearchOutlined, CheckCircleOutlined, CarOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { apiClient } from '../api/client';
import { MaintenanceRecord, Vehicle, Driver } from '../types';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

export const MaintenancePage: React.FC = () => {
  const [records, setRecords] = useState<MaintenanceRecord[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string | undefined>();
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>();

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<MaintenanceRecord | null>(null);

  const [form] = Form.useForm();
  const { hasRole } = useAuth();

  const loadData = async () => {
    setLoading(true);
    try {
      const [mList, vList, dList] = await Promise.all([
        apiClient.getMaintenance({
          query: searchQuery,
          service_type: selectedType,
          status: selectedStatus,
        }),
        apiClient.getVehicles(),
        apiClient.getDrivers(),
      ]);
      setRecords(mList);
      setVehicles(vList);
      setDrivers(dList);
    } catch {
      message.error('Ошибка загрузки записей ТО и ремонтов');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedType, selectedStatus]);

  const handleSearch = () => {
    loadData();
  };

  const handleOpenModal = (r?: MaintenanceRecord) => {
    if (r) {
      setEditingRecord(r);
      form.setFieldsValue({
        ...r,
        request_date: dayjs(r.request_date),
        appointment_date: r.appointment_date ? dayjs(r.appointment_date) : null,
        completion_date: r.completion_date ? dayjs(r.completion_date) : null,
      });
    } else {
      setEditingRecord(null);
      form.resetFields();
      form.setFieldsValue({
        request_date: dayjs(),
        service_type: 'SCHEDULED_TO',
        status: 'REQUESTED',
        contractor: 'СТО Хабаров',
      });
    }
    setIsModalOpen(true);
  };

  const handleSave = async (values: any) => {
    try {
      const payload = {
        ...values,
        request_date: values.request_date.format('YYYY-MM-DD'),
        appointment_date: values.appointment_date ? values.appointment_date.format('YYYY-MM-DD') : null,
        completion_date: values.completion_date ? values.completion_date.format('YYYY-MM-DD') : null,
      };

      if (editingRecord) {
        await apiClient.updateMaintenance(editingRecord.id, payload);
        message.success('Запись обновлена');
      } else {
        await apiClient.createMaintenance(payload);
        message.success('Заявка на ТО/ремонт зарегистрирована');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const handleComplete = async (r: MaintenanceRecord) => {
    try {
      await apiClient.updateMaintenance(r.id, {
        status: 'COMPLETED',
        completion_date: dayjs().format('YYYY-MM-DD')
      });
      message.success('Ремонт завершен, статус автомобиля восстановлен');
      loadData();
    } catch {
      message.error('Ошибка');
    }
  };

  const serviceTypeMap: Record<string, { label: string; color: string }> = {
    SCHEDULED_TO: { label: 'Плановое ТО', color: 'blue' },
    BODY_DAMAGE: { label: 'Кузовной дефект', color: 'volcano' },
    TOW_TRUCK: { label: 'Эвакуатор', color: 'purple' },
    WINDSHIELD: { label: 'Лобовое стекло', color: 'cyan' },
    WHEEL_ALIGNMENT: { label: 'Геометрия колес', color: 'geekblue' },
    REPAIR: { label: 'Слесарный ремонт', color: 'orange' },
    OTHER: { label: 'Прочее', color: 'default' },
  };

  const columns = [
    {
      title: 'Автомобиль',
      dataIndex: 'plate_number',
      key: 'plate_number',
      render: (t: string) => <Tag color="blue" icon={<CarOutlined />}>{t}</Tag>,
    },
    {
      title: 'Вид работ',
      dataIndex: 'service_type',
      key: 'service_type',
      render: (type: string) => {
        const item = serviceTypeMap[type] || { label: type, color: 'default' };
        return <Tag color={item.color}>{item.label}</Tag>;
      },
    },
    {
      title: 'Описание / Причина',
      dataIndex: 'description',
      key: 'description',
      render: (d: string) => <Text strong>{d}</Text>,
    },
    {
      title: 'Дата заявки',
      dataIndex: 'request_date',
      key: 'request_date',
      render: (d: string) => dayjs(d).format('DD.MM.YYYY'),
    },
    {
      title: 'Запись на',
      dataIndex: 'appointment_date',
      key: 'appointment_date',
      render: (d: string) => d ? dayjs(d).format('DD.MM.YYYY') : <Text type="secondary">—</Text>,
    },
    {
      title: 'Пробег (км)',
      dataIndex: 'mileage_at_service',
      key: 'mileage_at_service',
      render: (m: number) => m > 0 ? `${m.toLocaleString()} км` : <Text type="secondary">—</Text>,
    },
    {
      title: 'Подрядчик / СТО',
      dataIndex: 'contractor',
      key: 'contractor',
      render: (c: string) => c || <Text type="secondary">—</Text>,
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      render: (st: string) => {
        const map: Record<string, { label: string; color: string }> = {
          REQUESTED: { label: 'Заявка', color: 'orange' },
          SCHEDULED: { label: 'Записан', color: 'blue' },
          IN_PROGRESS: { label: 'В ремонте', color: 'red' },
          COMPLETED: { label: 'Завершено', color: 'green' },
          CANCELLED: { label: 'Отменено', color: 'default' },
        };
        const item = map[st] || { label: st, color: 'default' };
        return <Tag color={item.color}>{item.label}</Tag>;
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, r: MaintenanceRecord) => (
        <Space size="small">
          {hasRole(['admin', 'dispatcher']) && (
            <>
              <Button size="small" onClick={() => handleOpenModal(r)}>Ред.</Button>
              {r.status !== 'COMPLETED' && (
                <Button size="small" type="primary" onClick={() => handleComplete(r)}>
                  Готово
                </Button>
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
              placeholder="Поиск по авто, описанию, СТО, ЕРП..."
              prefix={<SearchOutlined />}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={12} sm={6} md={5}>
            <Select
              placeholder="Вид обслуживания"
              style={{ width: '100%' }}
              allowClear
              value={selectedType}
              onChange={setSelectedType}
            >
              <Option value="SCHEDULED_TO">Плановое ТО</Option>
              <Option value="TOW_TRUCK">Эвакуатор</Option>
              <Option value="REPAIR">Ремонт</Option>
              <Option value="WINDSHIELD">Замена лобового</Option>
              <Option value="WHEEL_ALIGNMENT">Геометрия</Option>
              <Option value="BODY_DAMAGE">Кузовной дефект</Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="Статус"
              style={{ width: '100%' }}
              allowClear
              value={selectedStatus}
              onChange={setSelectedStatus}
            >
              <Option value="REQUESTED">Заявка</Option>
              <Option value="SCHEDULED">Записан</Option>
              <Option value="IN_PROGRESS">В ремонте</Option>
              <Option value="COMPLETED">Завершено</Option>
            </Select>
          </Col>
          <Col xs={24} sm={8} md={7} style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={handleSearch} type="primary">Применить</Button>
              {hasRole(['admin', 'dispatcher']) && (
                <Button icon={<PlusOutlined />} type="primary" onClick={() => handleOpenModal()}>
                  Заявка на ТО / Ремонт
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          dataSource={records}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* Modal */}
      <Modal
        title={editingRecord ? 'Редактирование записи ТО / Ремонта' : 'Заявка на ТО / Ремонт / Эвакуацию'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        okText="Сохранить"
        cancelText="Отмена"
        width={650}
      >
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="vehicle_id" label="Автомобиль" rules={[{ required: true, message: 'Выберите автомобиль' }]}>
                <Select showSearch placeholder="Выберите ТС" optionFilterProp="children">
                  {vehicles.map((v) => (
                    <Option key={v.id} value={v.id}>
                      {v.plate_display} ({v.brand_model})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="service_type" label="Вид работ" rules={[{ required: true }]}>
                <Select>
                  <Option value="SCHEDULED_TO">Плановое ТО (замена масла, фильтра)</Option>
                  <Option value="TOW_TRUCK">Эвакуатор</Option>
                  <Option value="REPAIR">Слесарный ремонт (сцепление, ходовая...)</Option>
                  <Option value="WINDSHIELD">Замена лобового стекла</Option>
                  <Option value="WHEEL_ALIGNMENT">Геометрия колес (развал-схождение)</Option>
                  <Option value="BODY_DAMAGE">Кузовное повреждение / дефект</Option>
                  <Option value="OTHER">Прочее</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="Описание работ / Неисправность" rules={[{ required: true, message: 'Укажите описание' }]}>
            <Input placeholder="Замена масла, лопнул патрубок, замена колодок..." />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="request_date" label="Дата запроса" rules={[{ required: true }]}>
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="appointment_date" label="Дата записи на СТО">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="mileage_at_service" label="Пробег ТС (км)">
                <Input type="number" placeholder="27317" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="contractor" label="Подрядчик / СТО">
                <Input placeholder="СТО Хабаров, ИП Мухраев..." />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="status" label="Статус">
                <Select>
                  <Option value="REQUESTED">Заявка</Option>
                  <Option value="SCHEDULED">Записан</Option>
                  <Option value="IN_PROGRESS">В ремонте</Option>
                  <Option value="COMPLETED">Завершено</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="document_number" label="Номер документа (ЕРП / Договор / Акт)">
                <Input placeholder="ЕРП №5700, Акт №1..." />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="cost" label="Стоимость работ (₸)">
                <Input type="number" placeholder="0" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="Примечания">
            <Input.TextArea rows={2} placeholder="Приемщик, комментарии..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
