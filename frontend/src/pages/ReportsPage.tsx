import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Button, Typography, Space, Table, Tag, message } from 'antd';
import {
  DownloadOutlined, FileExcelOutlined, WarningOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { apiClient } from '../api/client';
import { Vehicle } from '../types';

const { Title, Text, Paragraph } = Typography;

export const ReportsPage: React.FC = () => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [downloadingVehicles, setDownloadingVehicles] = useState(false);
  const [downloadingMemo, setDownloadingMemo] = useState(false);

  useEffect(() => {
    apiClient.getVehicles().then((res) => {
      setVehicles(res);
    });
  }, []);

  const handleDownloadVehicles = async () => {
    setDownloadingVehicles(true);
    try {
      await apiClient.downloadFile('/reports/export/vehicles', `Vehicles_Registry_${dayjs().format('YYYYMMDD')}.xlsx`);
      message.success('Реестр автопарка успешно выгружен');
    } catch {
      message.error('Ошибка скачивания файла');
    } finally {
      setDownloadingVehicles(false);
    }
  };

  const handleDownloadMemo = async () => {
    setDownloadingMemo(true);
    try {
      await apiClient.downloadFile('/reports/export/memo', `Sluzhebnaya_Zapiska_${dayjs().format('YYYYMMDD')}.xlsx`);
      message.success('Служебная записка успешно выгружена');
    } catch {
      message.error('Ошибка скачивания файла');
    } finally {
      setDownloadingMemo(false);
    }
  };

  // Compute breakdowns
  const companyCounts: Record<string, number> = {};
  const deptCounts: Record<string, number> = {};
  const fuelCounts: Record<string, number> = {};

  vehicles.forEach((v) => {
    const comp = v.company_name || 'Не указана';
    companyCounts[comp] = (companyCounts[comp] || 0) + 1;

    const dept = v.department_name || 'Без подразделения';
    deptCounts[dept] = (deptCounts[dept] || 0) + 1;

    const fuel = v.fuel_type || 'АИ-92';
    fuelCounts[fuel] = (fuelCounts[fuel] || 0) + 1;
  });

  const companyData = Object.entries(companyCounts).map(([name, count]) => ({
    name, count, percent: Math.round((count / (vehicles.length || 1)) * 100)
  }));

  const deptData = Object.entries(deptCounts).map(([name, count]) => ({
    name, count, percent: Math.round((count / (vehicles.length || 1)) * 100)
  })).sort((a, b) => b.count - a.count);

  const fuelData = Object.entries(fuelCounts).map(([name, count]) => ({
    name, count, percent: Math.round((count / (vehicles.length || 1)) * 100)
  }));

  return (
    <div>
      <Card style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0 }}>Центр отчетов и экспорта данных</Title>
        <Text type="secondary">Генерация официальных отчетов, реестров и служебных записок в Excel</Text>
      </Card>

      {/* Download Action Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <FileExcelOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                <span>Полный реестр автопарка</span>
              </Space>
            }
            extra={
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                loading={downloadingVehicles}
                onClick={handleDownloadVehicles}
              >
                Скачать Excel (.xlsx)
              </Button>
            }
          >
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              Выгружает актуальный срез всех 217+ автомобилей компании со всеми реквизитами: госномера, марки,
              компании-владельцы, подразделения, закрепленные водители, сроки техосмотра, страховки, номера карт ГСМ,
              цветовой светофор и пробег.
            </Paragraph>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <WarningOutlined style={{ color: '#f5222d', fontSize: 20 }} />
                <span>Служебная записка в СБ по штрафам</span>
              </Space>
            }
            extra={
              <Button
                danger
                type="primary"
                icon={<DownloadOutlined />}
                loading={downloadingMemo}
                onClick={handleDownloadMemo}
              >
                Служебная записка (.xlsx)
              </Button>
            }
          >
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              Автоматически генерирует официальную форму служебной записки в адрес руководства и Службы безопасности
              со списком сотрудников, отказавшихся добровольно оплачивать штрафы ПДД по эксплуатируемым автомобилям.
            </Paragraph>
          </Card>
        </Col>
      </Row>

      {/* Analytics Breakdown Tables */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card title="Распределение по компаниям" size="small">
            <Table
              dataSource={companyData}
              rowKey="name"
              pagination={false}
              size="small"
              columns={[
                { title: 'Компания', dataIndex: 'name', render: (t) => <Text strong>{t}</Text> },
                { title: 'Авто', dataIndex: 'count', align: 'right', render: (c) => <Tag color="blue">{c}</Tag> },
                { title: 'Доля', dataIndex: 'percent', align: 'right', render: (p) => `${p}%` },
              ]}
            />
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card title="Распределение по видам топлива" size="small">
            <Table
              dataSource={fuelData}
              rowKey="name"
              pagination={false}
              size="small"
              columns={[
                { title: 'Топливо', dataIndex: 'name', render: (t) => <Tag color="orange">{t}</Tag> },
                { title: 'Авто', dataIndex: 'count', align: 'right', render: (c) => <b>{c}</b> },
                { title: 'Доля', dataIndex: 'percent', align: 'right', render: (p) => `${p}%` },
              ]}
            />
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card title="Распределение по подразделениям" size="small">
            <Table
              dataSource={deptData}
              rowKey="name"
              pagination={{ pageSize: 6 }}
              size="small"
              columns={[
                { title: 'Участок', dataIndex: 'name', render: (t) => <Text>{t}</Text> },
                { title: 'Авто', dataIndex: 'count', align: 'right', render: (c) => <Tag color="cyan">{c}</Tag> },
                { title: '%', dataIndex: 'percent', align: 'right', render: (p) => `${p}%` },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
