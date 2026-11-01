import React, { useEffect, useState } from 'react';
import {
  Table, Card, Button, Input, Select, Tag, Space, Modal, Form,
  Row, Col, DatePicker, message, Typography, Popconfirm
} from 'antd';
import {
  FireOutlined, PlusOutlined, DeleteOutlined, CarOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { apiClient } from '../api/client';
import { FuelLog, Vehicle, Driver } from '../types';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

export const FuelPage: React.FC = () => {
  const [logs, setLogs] = useState<FuelLog[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(false);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();
  const { hasRole } = useAuth();

  const loadData = async () => {
    setLoading(true);
    try {
      const [fList, vList, dList] = await Promise.all([
        apiClient.getFuelLogs(),
        apiClient.getVehicles(),
        apiClient.getDrivers(),
      ]);
      setLogs(fList);
      setVehicles(vList);
      setDrivers(dList);
    } catch {
      message.error('Ошибка загрузки данных ГСМ');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenModal = () => {
    form.resetFields();
    form.setFieldsValue({
      period_date: dayjs(),
      consumption_rate: 8.5,
      distance_traveled: 0,
      actual_liters: 0,
    });
    setIsModalOpen(true);
  };

  const handleVehicleSelect = (vId: number) => {
    const v = vehicles.find((item) => item.id === vId);
    if (v) {
      form.setFieldsValue({
        fuel_card_number: v.fuel_card_number || '',
      });
      // Suggest driver
      const d = drivers.find((dr) => dr.full_name === v.current_driver_name);
      if (d) {
        form.setFieldsValue({ driver_id: d.id });
      }
    }
  };

  const handleSave = async (values: any) => {
    try {
      await apiClient.createFuelLog({
        ...values,
        period_date: values.period_date.format('YYYY-MM-DD'),
      });
      message.success('Запись по ГСМ сохранена');
      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiClient.deleteFuelLog(id);
      message.success('Запись удалена');
      loadData();
    } catch {
      message.error('Ошибка');
    }
  };

  const columns = [
    {
      title: 'Дата',
      dataIndex: 'period_date',
      key: 'period_date',
      render: (d: string) => dayjs(d).format('DD.MM.YYYY'),
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
      render: (t: string) => t || <Text type="secondary">—</Text>,
    },
    {
      title: 'Карта ГСМ',
      dataIndex: 'fuel_card_number',
      key: 'fuel_card_number',
      render: (c: string) => c ? <Tag color="cyan">№ {c}</Tag> : <Text type="secondary">—</Text>,
    },
    {
      title: 'Норма (л/100км)',
      dataIndex: 'consumption_rate',
      key: 'consumption_rate',
      render: (r: number) => `${r} л`,
    },
    {
      title: 'Пробег (км)',
      dataIndex: 'distance_traveled',
      key: 'distance_traveled',
      render: (d: number) => `${d.toLocaleString()} км`,
    },
    {
      title: 'Расчет норма (л)',
      dataIndex: 'calculated_liters',
      key: 'calculated_liters',
      render: (l: number) => `${l} л`,
    },
    {
      title: 'Факт заправки (л)',
      dataIndex: 'actual_liters',
      key: 'actual_liters',
      render: (l: number) => <b>{l} л</b>,
    },
    {
      title: 'Отклонение (л)',
      dataIndex: 'deviation_liters',
      key: 'deviation_liters',
      render: (dev: number) => {
        if (dev > 0) return <Tag color="error">+{dev} л (перерасход)</Tag>;
        if (dev < 0) return <Tag color="success">{dev} л (экономия)</Tag>;
        return <Tag color="default">0 л</Tag>;
      },
    },
    {
      title: 'Примечания',
      dataIndex: 'notes',
      key: 'notes',
      render: (n: string) => n || <Text type="secondary">—</Text>,
    },
    {
      title: 'Действие',
      key: 'action',
      render: (_: any, r: FuelLog) => (
        hasRole(['admin']) && (
          <Popconfirm title="Удалить запись?" onConfirm={() => handleDelete(r.id)} okText="Да" cancelText="Нет">
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        )
      ),
    },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>Учет расхода топлива и карт ГСМ</Title>
            <Text type="secondary">Контроль фактических заправок, расчетного расхода по пробегу и отклонений</Text>
          </div>
          {hasRole(['admin', 'dispatcher']) && (
            <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenModal}>
              Внести заправку / расчет
            </Button>
          )}
        </div>
      </Card>

      <Card>
        <Table
          dataSource={logs}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* Modal */}
      <Modal
        title="Внесение данных по расходу топлива / заправке"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        okText="Сохранить"
        cancelText="Отмена"
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="vehicle_id" label="Автомобиль" rules={[{ required: true, message: 'Выберите автомобиль' }]}>
                <Select showSearch placeholder="Выберите ТС" optionFilterProp="children" onChange={handleVehicleSelect}>
                  {vehicles.map((v) => (
                    <Option key={v.id} value={v.id}>
                      {v.plate_display} ({v.brand_model}) - Карта: {v.fuel_card_number || 'нет'}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="driver_id" label="Водитель">
                <Select showSearch placeholder="Выберите водителя" optionFilterProp="children" allowClear>
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
              <Form.Item name="period_date" label="Дата" rules={[{ required: true }]}>
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="fuel_card_number" label="Номер карты ГСМ">
                <Input placeholder="96378" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="consumption_rate" label="Норма л/100км" rules={[{ required: true }]}>
                <Input type="number" step="0.1" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="distance_traveled" label="Пробег (км)" rules={[{ required: true }]}>
                <Input type="number" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="actual_liters" label="Факт залито (л)" rules={[{ required: true }]}>
                <Input type="number" step="0.1" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="Примечание">
            <Input placeholder="Отклонение рассчитывается автоматически при сохранении..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
