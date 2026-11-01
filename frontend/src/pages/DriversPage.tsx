import React, { useEffect, useState } from 'react';
import {
  Table, Card, Button, Input, Select, Tag, Space, Modal, Form,
  Row, Col, message, Typography, Tooltip, Popconfirm, DatePicker
} from 'antd';
import {
  TeamOutlined, PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, SwapOutlined, CarOutlined
} from '@ant-design/icons';
import { apiClient } from '../api/client';
import { Driver, Department, Vehicle } from '../types';
import { useAuth } from '../context/AuthContext';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

export const DriversPage: React.FC = () => {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDept, setSelectedDept] = useState<number | undefined>();
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>();

  // Driver Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDriver, setEditingDriver] = useState<Driver | null>(null);

  // Assignment Modal
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [assignTargetDriver, setAssignTargetDriver] = useState<Driver | null>(null);

  const [form] = Form.useForm();
  const [assignForm] = Form.useForm();
  const { hasRole } = useAuth();

  const loadData = async () => {
    setLoading(true);
    try {
      const [drList, dList, vList] = await Promise.all([
        apiClient.getDrivers({
          query: searchQuery,
          department_id: selectedDept,
          status: selectedStatus,
        }),
        apiClient.getDepartments(),
        apiClient.getVehicles(),
      ]);
      setDrivers(drList);
      setDepartments(dList);
      setVehicles(vList);
    } catch {
      message.error('Ошибка загрузки списка водителей');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedDept, selectedStatus]);

  const handleSearch = () => {
    loadData();
  };

  const handleOpenModal = (d?: Driver) => {
    if (d) {
      setEditingDriver(d);
      form.setFieldsValue(d);
    } else {
      setEditingDriver(null);
      form.resetFields();
      form.setFieldsValue({ status: 'ACTIVE', position: 'Инсталлятор' });
    }
    setIsModalOpen(true);
  };

  const handleSaveDriver = async (values: any) => {
    try {
      if (editingDriver) {
        await apiClient.updateDriver(editingDriver.id, values);
        message.success('Данные сотрудника обновлены');
      } else {
        await apiClient.createDriver(values);
        message.success('Сотрудник добавлен в базу');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const handleDeleteDriver = async (id: number) => {
    try {
      await apiClient.deleteDriver(id);
      message.success('Сотрудник удален');
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const handleOpenAssignModal = (d: Driver) => {
    setAssignTargetDriver(d);
    assignForm.resetFields();
    assignForm.setFieldsValue({
      driver_id: d.id,
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
      message.success('Автомобиль успешно закреплен за сотрудником');
      setIsAssignModalOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка закрепления');
    }
  };

  const columns = [
    {
      title: 'ФИО сотрудника',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'Телефон',
      dataIndex: 'phone',
      key: 'phone',
      render: (t: string) => t || <Text type="secondary">—</Text>,
    },
    {
      title: 'Должность',
      dataIndex: 'position',
      key: 'position',
      render: (pos: string) => <Tag color="blue">{pos || 'Водитель'}</Tag>,
    },
    {
      title: 'Подразделение',
      dataIndex: 'department_name',
      key: 'department_name',
      render: (d: string) => d || <Text type="secondary">—</Text>,
    },
    {
      title: 'Закрепленный автомобиль',
      key: 'vehicle',
      render: (_: any, r: Driver) => (
        <div>
          {r.current_vehicle_plate ? (
            <Tag color="cyan" icon={<CarOutlined />}>{r.current_vehicle_plate}</Tag>
          ) : (
            <Text type="secondary">Нет автомобиля</Text>
          )}
        </div>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      render: (st: string) => {
        const map: Record<string, { label: string; color: string }> = {
          ACTIVE: { label: 'Работает', color: 'green' },
          VACATION: { label: 'В отпуске', color: 'gold' },
          SICK_LEAVE: { label: 'Больничный', color: 'volcano' },
          DISMISSED: { label: 'Уволен', color: 'red' },
          SUSPENDED: { label: 'Отстранен', color: 'default' },
        };
        const item = map[st] || { label: st, color: 'default' };
        return <Tag color={item.color}>{item.label}</Tag>;
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 140,
      render: (_: any, r: Driver) => (
        <Space size="small">
          {hasRole(['admin', 'dispatcher']) && (
            <>
              <Tooltip title="Закрепить за автомобилем">
                <Button size="small" icon={<SwapOutlined />} onClick={() => handleOpenAssignModal(r)} />
              </Tooltip>
              <Tooltip title="Редактировать">
                <Button size="small" icon={<EditOutlined />} onClick={() => handleOpenModal(r)} />
              </Tooltip>
            </>
          )}
          {hasRole(['admin']) && (
            <Popconfirm title="Удалить сотрудника?" onConfirm={() => handleDeleteDriver(r.id)} okText="Да" cancelText="Нет">
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
          <Col xs={24} sm={10} md={8}>
            <Input
              placeholder="Поиск по ФИО, телефону, должности..."
              prefix={<SearchOutlined />}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={12} sm={6} md={5}>
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
          <Col xs={12} sm={4} md={4}>
            <Select
              placeholder="Статус"
              style={{ width: '100%' }}
              allowClear
              value={selectedStatus}
              onChange={setSelectedStatus}
            >
              <Option value="ACTIVE">Работает</Option>
              <Option value="VACATION">В отпуске</Option>
              <Option value="SICK_LEAVE">Больничный</Option>
              <Option value="DISMISSED">Уволен</Option>
            </Select>
          </Col>
          <Col xs={24} sm={4} md={7} style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={handleSearch} type="primary">Применить</Button>
              {hasRole(['admin', 'dispatcher']) && (
                <Button icon={<PlusOutlined />} type="primary" onClick={() => handleOpenModal()}>
                  Добавить водителя
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <div style={{ marginBottom: 12 }}>
          <Text strong>Всего сотрудников в реестре: {drivers.length}</Text>
        </div>
        <Table
          dataSource={drivers}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 25, showSizeChanger: true }}
        />
      </Card>

      {/* Driver Form Modal */}
      <Modal
        title={editingDriver ? `Редактирование: ${editingDriver.full_name}` : 'Новый водитель / сотрудник'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" onFinish={handleSaveDriver}>
          <Form.Item name="full_name" label="ФИО сотрудника" rules={[{ required: true, message: 'Введите ФИО' }]}>
            <Input placeholder="Иванов Иван Иванович (поддерживаются казахские символы)" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="phone" label="Номер телефона">
                <Input placeholder="87071234567" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="position" label="Должность">
                <Select>
                  <Option value="Водитель">Водитель</Option>
                  <Option value="Бригадир">Бригадир</Option>
                  <Option value="Инсталлятор">Инсталлятор</Option>
                  <Option value="Сварщик ВОЛС">Сварщик ВОЛС</Option>
                  <Option value="Помощник сварщика">Помощник сварщика</Option>
                  <Option value="Монтажник">Монтажник</Option>
                  <Option value="Техник ОИС">Техник ОИС</Option>
                  <Option value="Старший инженер">Старший инженер</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="department_id" label="Подразделение">
                <Select placeholder="Выберите подразделение" allowClear>
                  {departments.map((d) => (
                    <Option key={d.id} value={d.id}>{d.name}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="Статус">
                <Select>
                  <Option value="ACTIVE">Работает</Option>
                  <Option value="VACATION">В отпуске</Option>
                  <Option value="SICK_LEAVE">Больничный</Option>
                  <Option value="DISMISSED">Уволен</Option>
                  <Option value="SUSPENDED">Отстранен</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="Примечания">
            <Input.TextArea rows={2} placeholder="Номер удостоверения, права, комментарии..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* Assign Vehicle Modal */}
      <Modal
        title={`Закрепить автомобиль за: ${assignTargetDriver?.full_name}`}
        open={isAssignModalOpen}
        onCancel={() => setIsAssignModalOpen(false)}
        onOk={() => assignForm.submit()}
        okText="Закрепить"
        cancelText="Отмена"
      >
        <Form form={assignForm} layout="vertical" onFinish={handleSaveAssignment}>
          <Form.Item name="driver_id" hidden>
            <Input />
          </Form.Item>

          <Form.Item name="vehicle_id" label="Выберите автомобиль" rules={[{ required: true, message: 'Выберите автомобиль' }]}>
            <Select showSearch placeholder="Поиск по гос. номеру или марке" optionFilterProp="children">
              {vehicles.map((v) => (
                <Option key={v.id} value={v.id}>
                  {v.plate_display} ({v.brand_model}) - {v.department_name || 'Без отдела'}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="assignment_type" label="Тип закрепления">
                <Select>
                  <Option value="PRIMARY">Основное закрепление</Option>
                  <Option value="TEMPORARY">Временная замена</Option>
                  <Option value="SHIFT">Сменный водитель</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="start_date" label="Дата начала">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="reason" label="Причина">
            <Input placeholder="Плановое закрепление / замена..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
