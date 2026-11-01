import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Tag, Typography, Button, Space, Spin, Alert } from 'antd';
import {
  CarOutlined,
  CheckCircleOutlined,
  ToolOutlined,
  WarningOutlined,
  SafetyCertificateOutlined,
  DollarOutlined,
  TeamOutlined,
  FileTextOutlined,
  SwapOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { DashboardStats, Vehicle, Fine } from '../types';

const { Title, Text } = Typography;

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [urgentVehicles, setUrgentVehicles] = useState<Vehicle[]>([]);
  const [unpaidFines, setUnpaidFines] = useState<Fine[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const navigate = useNavigate();

  const handleExport = async () => {
    setExporting(true);
    try {
      await apiClient.downloadFile('/reports/export/vehicles', `Vehicles_Registry.xlsx`);
    } finally {
      setExporting(false);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [dashStats, vehiclesData, finesData] = await Promise.all([
        apiClient.getDashboardStats(),
        apiClient.getVehicles(),
        apiClient.getFines()
      ]);
      setStats(dashStats);

      // Filter critical vehicles (expired or expiring in <= 15 days)
      const urgent = vehiclesData.filter(
        v => v.insurance_state === 'EXPIRED' || v.inspection_state === 'EXPIRED' ||
             (v.days_to_insurance !== undefined && v.days_to_insurance <= 15) ||
             (v.days_to_inspection !== undefined && v.days_to_inspection <= 15)
      ).slice(0, 8);
      setUrgentVehicles(urgent);

      // Top unpaid / refused fines
      const criticalFines = finesData.filter(
        f => f.status === 'REFUSED' || f.status === 'NOTIFIED' || f.status === 'NEW'
      ).slice(0, 8);
      setUnpaidFines(criticalFines);

    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading || !stats) {
    return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>Панель управления автопарком</Title>
          <Text type="secondary">Оперативная сводка на текущую дату</Text>
        </div>
        <Space>
          <Button icon={<FileTextOutlined />} onClick={() => navigate('/waybills')}>Выписать путевой</Button>
          <Button icon={<SwapOutlined />} onClick={() => navigate('/assignments')}>Оформить пересадку</Button>
          <Button icon={<WarningOutlined />} danger onClick={() => navigate('/fines')}>Внести штраф</Button>
          <Button icon={<DownloadOutlined />} type="primary" loading={exporting} onClick={handleExport}>
            Экспорт в Excel
          </Button>
        </Space>
      </div>

      {/* Summary KPI Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => navigate('/vehicles')} style={{ borderLeft: '4px solid #1890ff' }}>
            <Statistic
              title="Всего автопарка"
              value={stats.total_vehicles}
              prefix={<CarOutlined style={{ color: '#1890ff' }} />}
              suffix={<Text type="secondary" style={{ fontSize: 13 }}>ед.</Text>}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
              В строю: <span style={{ color: '#52c41a', fontWeight: 600 }}>{stats.active_vehicles}</span> | В ремонте: <span style={{ color: '#fa8c16', fontWeight: 600 }}>{stats.repair_vehicles}</span>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => navigate('/vehicles?inspection_state=EXPIRED')} style={{ borderLeft: '4px solid #f5222d' }}>
            <Statistic
              title="Просрочен техосмотр"
              value={stats.inspection_expired}
              valueStyle={{ color: '#cf1322' }}
              prefix={<WarningOutlined style={{ color: '#f5222d' }} />}
              suffix={<Text type="secondary" style={{ fontSize: 13 }}>авто</Text>}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
              Требуют внимания (&lt;30 дн): <span style={{ color: '#faad14', fontWeight: 600 }}>{stats.inspection_warning}</span>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => navigate('/vehicles?insurance_state=EXPIRED')} style={{ borderLeft: '4px solid #fa8c16' }}>
            <Statistic
              title="Просрочена страховка"
              value={stats.insurance_expired}
              valueStyle={{ color: '#d46b08' }}
              prefix={<SafetyCertificateOutlined style={{ color: '#fa8c16' }} />}
              suffix={<Text type="secondary" style={{ fontSize: 13 }}>авто</Text>}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
              Истекает (&lt;30 дн): <span style={{ color: '#faad14', fontWeight: 600 }}>{stats.insurance_warning}</span>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => navigate('/fines?status=REFUSED')} style={{ borderLeft: '4px solid #722ed1' }}>
            <Statistic
              title="Неоплаченные штрафы"
              value={stats.unpaid_fines}
              valueStyle={{ color: stats.unpaid_fines > 0 ? '#cf1322' : '#52c41a' }}
              prefix={<DollarOutlined style={{ color: '#722ed1' }} />}
              suffix={<Text type="secondary" style={{ fontSize: 13 }}>протоколов</Text>}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
              Всего зарегистрировано: <b>{stats.total_fines}</b>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Critical Lists */}
      <Row gutter={[16, 16]} style={{ marginTop: 20 }}>
        <Col xs={24} lg={14}>
          <Card
            title={
              <Space>
                <WarningOutlined style={{ color: '#faad14' }} />
                <span>Срочный контроль: Страховки и Техосмотры</span>
              </Space>
            }
            extra={<Button type="link" onClick={() => navigate('/vehicles')}>Все автомобили</Button>}
          >
            <Table
              dataSource={urgentVehicles}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                {
                  title: 'Гос. номер',
                  dataIndex: 'plate_display',
                  render: (text) => <Text strong>{text}</Text>,
                },
                {
                  title: 'Марка',
                  dataIndex: 'brand_model',
                },
                {
                  title: 'Водитель',
                  dataIndex: 'current_driver_name',
                  render: (t, r) => t || <Text type="secondary">Не назначен</Text>,
                },
                {
                  title: 'Техосмотр',
                  dataIndex: 'inspection_expiry',
                  render: (val, r) => {
                    if (!val) return <Tag>Нет данных</Tag>;
                    if (r.inspection_state === 'EXPIRED') return <Tag color="error">Просрочен ({r.days_to_inspection} дн)</Tag>;
                    if (r.inspection_state === 'WARNING') return <Tag color="warning">{r.days_to_inspection} дн</Tag>;
                    return <Tag color="success">до {val}</Tag>;
                  }
                },
                {
                  title: 'Страховка',
                  dataIndex: 'insurance_expiry',
                  render: (val, r) => {
                    if (!val) return <Tag>Нет данных</Tag>;
                    if (r.insurance_state === 'EXPIRED') return <Tag color="error">Просрочена ({r.days_to_insurance} дн)</Tag>;
                    if (r.insurance_state === 'WARNING') return <Tag color="warning">{r.days_to_insurance} дн</Tag>;
                    return <Tag color="success">до {val}</Tag>;
                  }
                },
              ]}
            />
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Card
            title={
              <Space>
                <DollarOutlined style={{ color: '#f5222d' }} />
                <span>Штрафы, требующие внимания</span>
              </Space>
            }
            extra={<Button type="link" onClick={() => navigate('/fines')}>Реестр штрафов</Button>}
          >
            <Table
              dataSource={unpaidFines}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                {
                  title: 'Гос. номер',
                  dataIndex: 'plate_number',
                  render: (t) => <Tag color="blue">{t}</Tag>,
                },
                {
                  title: '№ Протокола',
                  dataIndex: 'notice_number',
                  render: (t) => <Text style={{ fontSize: 12 }}>{t}</Text>
                },
                {
                  title: 'Водитель',
                  dataIndex: 'driver_name',
                  render: (t) => t || <Text type="secondary">Не определен</Text>
                },
                {
                  title: 'Статус',
                  dataIndex: 'status',
                  render: (st, r) => {
                    if (r.in_official_memo) return <Tag color="magenta">В служебке СБ</Tag>;
                    if (st === 'REFUSED') return <Tag color="error">Отказ оплаты</Tag>;
                    if (st === 'NOTIFIED') return <Tag color="warning">Оповещен</Tag>;
                    return <Tag color="orange">Новый</Tag>;
                  }
                }
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
