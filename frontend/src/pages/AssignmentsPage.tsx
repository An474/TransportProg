import React, { useEffect, useState } from 'react';
import {
  Table, Card, Button, Input, Select, Tag, Space, Modal, Form,
  Row, Col, DatePicker, message, Typography, Switch
} from 'antd';
import {
  SwapOutlined, PlusOutlined, CarOutlined, UserOutlined, StopOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { apiClient } from '../api/client';
import { Assignment, Vehicle, Driver } from '../types';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

export const AssignmentsPage: React.FC = () => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeOnly, setActiveOnly] = useState(false);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | undefined>();
  const [form] = Form.useForm();
  const { hasRole } = useAuth();

  const loadData = async () => {
    setLoading(true);
    try {
      const [aList, vList, dList] = await Promise.all([
        apiClient.getAssignments({ active_only: activeOnly }),
        apiClient.getVehicles(),
        apiClient.getDrivers(),
      ]);
      setAssignments(aList);
      setVehicles(vList);
      setDrivers(dList);
    } catch {
      message.error('Ошибка загрузки журнала пересадок');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeOnly]);

  const handleOpenModal = () => {
    form.resetFields();
    form.setFieldsValue({
      assignment_type: 'TEMPORARY',
      start_date: dayjs(),
      reason: 'Временная замена (пересадка)'
    });
    setSelectedVehicleId(undefined);
    setIsModalOpen(true);
  };

  const handleVehicleChange = (vId: number) => {
    setSelectedVehicleId(vId);
    const vehicle = vehicles.find(v => v.id === vId);
    if (vehicle && vehicle.current_driver_name) {
      form.setFieldsValue({ notes: `Предыдущий водитель: ${vehicle.current_driver_name}` });
    }
  };

  const handleSave = async (values: any) => {
    try {
      await apiClient.createAssignment({
        ...values,
        start_date: values.start_date.format('YYYY-MM-DD'),
        end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : null,
      });
      message.success('Пересадка успешно сохранена и вступила в силу');
      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка сохранения пересадки');
    }
  };

  const handleDeactivate = async (id: number) => {
    try {
      await apiClient.deactivateAssignment(id);
      message.success('Закрепление/пересадка завершена');
      loadData();
    } catch {
      message.error('Ошибка завершения');
    }
  };

  const columns = [
    {
      title: 'Автомобиль',
      dataIndex: 'plate_number',
      key: 'plate_number',
      render: (t: string) => <Tag color="blue" icon={<CarOutlined />} style={{ fontSize: 13, padding: '2px 8px' }}>{t}</Tag>,
    },
    {
      title: 'Водитель',
      dataIndex: 'driver_name',
      key: 'driver_name',
      render: (name: string, r: Assignment) => (
        <div>
          <Text strong>{name}</Text>
          {r.driver_phone && <div style={{ fontSize: 11, color: '#8c8c8c' }}>{r.driver_phone}</div>}
        </div>
      ),
    },
    {
      title: 'Тип назначения',
      dataIndex: 'assignment_type',
      key: 'assignment_type',
      render: (type: string) => {
        if (type === 'PRIMARY') return <Tag color="green">Основной</Tag>;
        if (type === 'TEMPORARY') return <Tag color="orange">Временная пересадка</Tag>;
        return <Tag color="purple">Сменный</Tag>;
      },
    },
    {
      title: 'Период',
      key: 'period',
      render: (_: any, r: Assignment) => (
        <span>
          с {dayjs(r.start_date).format('DD.MM.YYYY')} по {r.end_date ? dayjs(r.end_date).format('DD.MM.YYYY') : <Tag color="cyan">Настоящее время</Tag>}
        </span>
      ),
    },
    {
      title: 'Причина пересадки',
      dataIndex: 'reason',
      key: 'reason',
      render: (t: string) => t || <Text type="secondary">—</Text>,
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        active ? <Tag color="success">Действует</Tag> : <Tag color="default">Завершено</Tag>
      ),
    },
    {
      title: 'Действие',
      key: 'action',
      render: (_: any, r: Assignment) => (
        hasRole(['admin', 'dispatcher']) && r.is_active && (
          <Button size="small" icon={<StopOutlined />} onClick={() => handleDeactivate(r.id)}>
            Завершить
          </Button>
        )
      ),
    },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>Журнал пересадок и закреплений авто</Title>
            <Text type="secondary">История всех смен водителей, временных замен на время отпусков и ремонтов</Text>
          </div>
          <Space>
            <span>
              Только действующие: <Switch checked={activeOnly} onChange={setActiveOnly} />
            </span>
            {hasRole(['admin', 'dispatcher']) && (
              <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenModal}>
                Оформить пересадку
              </Button>
            )}
          </Space>
        </div>
      </Card>

      <Card>
        <Table
          dataSource={assignments}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* Transfer Modal */}
      <Modal
        title="Оформление пересадки / смены водителя"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        okText="Зафиксировать пересадку"
        cancelText="Отмена"
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Form.Item name="vehicle_id" label="Автомобиль" rules={[{ required: true, message: 'Выберите автомобиль' }]}>
            <Select showSearch placeholder="Выберите ТС" optionFilterProp="children" onChange={handleVehicleChange}>
              {vehicles.map((v) => (
                <Option key={v.id} value={v.id}>
                  {v.plate_display} ({v.brand_model}) - текущий водитель: {v.current_driver_name || 'нет'}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="driver_id" label="Назначаемый водитель" rules={[{ required: true, message: 'Выберите водителя' }]}>
            <Select showSearch placeholder="Выберите нового водителя" optionFilterProp="children">
              {drivers.map((d) => (
                <Option key={d.id} value={d.id}>
                  {d.full_name} ({d.position}) {d.phone ? `- ${d.phone}` : ''}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="assignment_type" label="Тип закрепления" rules={[{ required: true }]}>
                <Select>
                  <Option value="TEMPORARY">Временная замена (пересадка)</Option>
                  <Option value="PRIMARY">Новый постоянный водитель</Option>
                  <Option value="SHIFT">Сменный водитель</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="start_date" label="Дата передачи" rules={[{ required: true }]}>
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="end_date" label="Дата возврата (если временная замена)">
            <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} placeholder="Не обязательно" />
          </Form.Item>

          <Form.Item name="reason" label="Причина смены/пересадки">
            <Input placeholder="Отпуск основного водителя, поломка/ремонт авто, больничный..." />
          </Form.Item>

          <Form.Item name="notes" label="Дополнительные отметки">
            <Input.TextArea rows={2} placeholder="Переданы ключи, состояние кузова, топливо в баке..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
