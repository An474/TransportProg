import React, { useEffect, useState } from 'react';
import { Table, Card, Tag, Typography, message, Select, Row, Col, Space } from 'antd';
import { HistoryOutlined, UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { apiClient } from '../api/client';
import { AuditLog } from '../types';

const { Title, Text } = Typography;
const { Option } = Select;

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<string | undefined>();
  const [selectedAction, setSelectedAction] = useState<string | undefined>();

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getAuditLogs({
        entity_name: selectedEntity,
        action: selectedAction,
        limit: 150,
      });
      setLogs(data);
    } catch {
      message.error('Ошибка загрузки журнала аудита');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedEntity, selectedAction]);

  const actionColorMap: Record<string, string> = {
    CREATE: 'green',
    UPDATE: 'blue',
    DELETE: 'red',
    DEACTIVATE: 'orange',
  };

  const columns = [
    {
      title: 'Время',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (t: string) => dayjs(t).format('DD.MM.YYYY HH:mm:ss'),
    },
    {
      title: 'Сотрудник',
      dataIndex: 'username',
      key: 'username',
      width: 150,
      render: (u: string) => (
        <Space>
          <UserOutlined />
          <Text strong>{u}</Text>
        </Space>
      ),
    },
    {
      title: 'Действие',
      dataIndex: 'action',
      key: 'action',
      width: 130,
      render: (act: string) => <Tag color={actionColorMap[act] || 'default'}>{act}</Tag>,
    },
    {
      title: 'Раздел',
      dataIndex: 'entity_name',
      key: 'entity_name',
      width: 140,
      render: (e: string) => <Tag>{e}</Tag>,
    },
    {
      title: 'Детализация изменений',
      dataIndex: 'changes_json',
      key: 'changes_json',
      render: (raw: string) => {
        if (!raw) return <Text type="secondary">—</Text>;
        try {
          const parsed = JSON.parse(raw);
          return (
            <pre style={{ margin: 0, fontSize: 11, background: '#f5f5f5', padding: 6, borderRadius: 4, maxWidth: 500, overflowX: 'auto' }}>
              {JSON.stringify(parsed, null, 2)}
            </pre>
          );
        } catch {
          return raw;
        }
      },
    },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={12}>
            <Title level={4} style={{ margin: 0 }}>Журнал действий и аудита системы</Title>
            <Text type="secondary">Фиксация всех созданий, правок и удалений с указанием автора и времени</Text>
          </Col>
          <Col xs={12} md={6}>
            <Select
              placeholder="Фильтр по разделу"
              style={{ width: '100%' }}
              allowClear
              value={selectedEntity}
              onChange={setSelectedEntity}
            >
              <Option value="VEHICLE">Автомобили (VEHICLE)</Option>
              <Option value="DRIVER">Водители (DRIVER)</Option>
              <Option value="WAYBILL">Путевые листы (WAYBILL)</Option>
              <Option value="FINE">Штрафы (FINE)</Option>
              <Option value="ASSIGNMENT">Пересадки (ASSIGNMENT)</Option>
              <Option value="MAINTENANCE">Ремонты (MAINTENANCE)</Option>
              <Option value="USER">Пользователи (USER)</Option>
            </Select>
          </Col>
          <Col xs={12} md={6}>
            <Select
              placeholder="Фильтр по действию"
              style={{ width: '100%' }}
              allowClear
              value={selectedAction}
              onChange={setSelectedAction}
            >
              <Option value="CREATE">Создание (CREATE)</Option>
              <Option value="UPDATE">Редактирование (UPDATE)</Option>
              <Option value="DELETE">Удаление (DELETE)</Option>
              <Option value="DEACTIVATE">Деактивация</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          dataSource={logs}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 25 }}
        />
      </Card>
    </div>
  );
};
