import React, { useEffect, useState } from 'react';
import {
  Table, Card, Button, Input, Select, Tag, Space, Modal, Form,
  Row, Col, Switch, message, Typography, Tooltip, Popconfirm
} from 'antd';
import {
  UserOutlined, PlusOutlined, EditOutlined, DeleteOutlined,
  LockOutlined, SafetyCertificateOutlined, CheckCircleOutlined, StopOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { apiClient } from '../api/client';
import { User } from '../types';
import { useAuth } from '../context/AuthContext';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

export const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  const [form] = Form.useForm();
  const { user: currentUser } = useAuth();

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getUsers();
      setUsers(data);
    } catch {
      message.error('Ошибка загрузки списка пользователей');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenModal = (u?: User) => {
    if (u) {
      setEditingUser(u);
      form.setFieldsValue({
        username: u.username,
        full_name: u.full_name,
        role: u.role,
        is_active: u.is_active,
        password: '',
      });
    } else {
      setEditingUser(null);
      form.resetFields();
      form.setFieldsValue({
        role: 'dispatcher',
        is_active: true,
      });
    }
    setIsModalOpen(true);
  };

  const handleSaveUser = async (values: any) => {
    try {
      if (editingUser) {
        const payload: any = {
          full_name: values.full_name,
          role: values.role,
          is_active: values.is_active,
        };
        if (values.password) {
          payload.password = values.password;
        }
        await apiClient.updateUser(editingUser.id, payload);
        message.success(`Пользователь ${editingUser.username} обновлен`);
      } else {
        await apiClient.createUser(values);
        message.success(`Пользователь ${values.username} успешно создан`);
      }
      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка сохранения пользователя');
    }
  };

  const handleToggleActive = async (u: User) => {
    if (u.id === currentUser?.id) {
      message.warning('Нельзя заблокировать собственную учетную запись');
      return;
    }
    try {
      await apiClient.updateUser(u.id, { is_active: !u.is_active });
      message.success(u.is_active ? `Пользователь ${u.username} заблокирован` : `Пользователь ${u.username} активирован`);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка изменения статуса');
    }
  };

  const handleDeleteUser = async (id: number) => {
    try {
      await apiClient.deleteUser(id);
      message.success('Пользователь удален');
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const roleTagMap: Record<string, { label: string; color: string }> = {
    admin: { label: 'Администратор', color: 'red' },
    dispatcher: { label: 'Диспетчер', color: 'blue' },
    viewer: { label: 'Руководитель (Просмотр)', color: 'green' },
  };

  const columns = [
    {
      title: 'Логин',
      dataIndex: 'username',
      key: 'username',
      render: (u: string, r: User) => (
        <Space>
          <UserOutlined style={{ color: '#1677ff' }} />
          <Text strong>{u}</Text>
          {r.id === currentUser?.id && <Tag color="purple">Вы</Tag>}
        </Space>
      ),
    },
    {
      title: 'ФИО сотрудника',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (t: string) => <Text>{t}</Text>,
    },
    {
      title: 'Роль в системе',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const item = roleTagMap[role] || { label: role, color: 'default' };
        return <Tag color={item.color} style={{ fontSize: 13, padding: '2px 8px' }}>{item.label}</Tag>;
      },
    },
    {
      title: 'Статус аккаунта',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        active ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>Активен</Tag>
        ) : (
          <Tag color="error" icon={<StopOutlined />}>Заблокирован</Tag>
        )
      ),
    },
    {
      title: 'Дата регистрации',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (d: string) => dayjs(d).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 170,
      render: (_: any, r: User) => (
        <Space size="small">
          <Tooltip title="Редактировать">
            <Button size="small" icon={<EditOutlined />} onClick={() => handleOpenModal(r)} />
          </Tooltip>
          {r.id !== currentUser?.id && (
            <>
              <Tooltip title={r.is_active ? 'Заблокировать' : 'Разблокировать'}>
                <Button
                  size="small"
                  type={r.is_active ? 'default' : 'primary'}
                  danger={r.is_active}
                  icon={r.is_active ? <StopOutlined /> : <CheckCircleOutlined />}
                  onClick={() => handleToggleActive(r)}
                />
              </Tooltip>
              <Popconfirm
                title="Удалить пользователя?"
                description={`Вы уверены, что хотите безвозвратно удалить аккаунт ${r.username}?`}
                onConfirm={() => handleDeleteUser(r.id)}
                okText="Да, удалить"
                cancelText="Отмена"
              >
                <Button size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>Управление пользователями и правами доступа</Title>
            <Text type="secondary">Раздел доступен только администратору системы</Text>
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()} size="large">
            Создать пользователя
          </Button>
        </div>
      </Card>

      <Card>
        <Table
          dataSource={users}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* User Create / Edit Modal */}
      <Modal
        title={editingUser ? `Редактирование: ${editingUser.username}` : 'Создание нового пользователя'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        okText="Сохранить"
        cancelText="Отмена"
        width={550}
      >
        <Form form={form} layout="vertical" onFinish={handleSaveUser}>
          <Form.Item
            name="username"
            label="Имя пользователя (Логин)"
            rules={[{ required: true, message: 'Введите логин' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="ivanov" disabled={!!editingUser} />
          </Form.Item>

          <Form.Item
            name="full_name"
            label="ФИО сотрудника"
            rules={[{ required: true, message: 'Введите ФИО' }]}
          >
            <Input placeholder="Иванов Иван Иванович" />
          </Form.Item>

          <Form.Item
            name="role"
            label="Роль и уровень доступа"
            rules={[{ required: true, message: 'Выберите роль' }]}
          >
            <Select>
              <Option value="admin">Администратор (Полный доступ, управление правами, бэкапы)</Option>
              <Option value="dispatcher">Диспетчер (Внесение ТС, путевых, штрафов, пересадок, ТО)</Option>
              <Option value="viewer">Руководитель (Только просмотр и выгрузка отчетов)</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="password"
            label={editingUser ? 'Новый пароль (оставьте пустым, чтобы не менять)' : 'Пароль'}
            rules={editingUser ? [] : [{ required: true, message: 'Введите пароль' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder={editingUser ? '••••••••' : 'Введите пароль'} />
          </Form.Item>

          <Form.Item name="is_active" label="Статус учетной записи" valuePropName="checked">
            <Switch checkedChildren="Активен" unCheckedChildren="Заблокирован" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
