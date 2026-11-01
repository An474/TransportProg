import React, { useState } from 'react';
import { Card, Form, Input, Button, Alert, Typography } from 'antd';
import { UserOutlined, LockOutlined, CarOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;

export const LoginPage: React.FC = () => {
  const [form] = Form.useForm();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (values: any) => {
    setError(null);
    setLoading(true);
    try {
      await login(values.username, values.password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка авторизации. Проверьте логин и пароль.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #0b1f3a 0%, #173865 50%, #205081 100%)',
      padding: 16
    }}>
      <Card style={{ width: 440, boxShadow: '0 12px 32px rgba(0,0,0,0.3)', borderRadius: 12 }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: '#e6f4ff',
            color: '#1677ff',
            fontSize: 32,
            marginBottom: 12
          }}>
            <CarOutlined />
          </div>
          <Title level={3} style={{ margin: 0, color: '#1f1f1f' }}>Транспортный отдел</Title>
          <Text type="secondary">Единая информационная система учета автопарка</Text>
        </div>

        {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 20 }} />}

        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="username"
            label="Имя пользователя (Логин)"
            rules={[{ required: true, message: 'Введите логин' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="Введите логин" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            label="Пароль"
            rules={[{ required: true, message: 'Введите пароль' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Введите пароль" size="large" />
          </Form.Item>

          <Form.Item style={{ marginTop: 28, marginBottom: 8 }}>
            <Button type="primary" htmlType="submit" size="large" block loading={loading} style={{ height: 44, fontWeight: 600 }}>
              Войти в систему
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};
