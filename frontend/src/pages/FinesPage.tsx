import React, { useEffect, useState } from 'react';
import {
  Table, Card, Button, Input, Select, Tag, Space, Modal, Form,
  Row, Col, DatePicker, message, Typography, Tooltip, Popconfirm, Switch, Alert, Divider
} from 'antd';
import {
  WarningOutlined, PlusOutlined, SearchOutlined, DownloadOutlined,
  DollarOutlined, CheckCircleOutlined, UserOutlined, RobotOutlined, CarOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { apiClient } from '../api/client';
import { Fine, Vehicle, Driver } from '../types';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

export const FinesPage: React.FC = () => {
  const [fines, setFines] = useState<Fine[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>();
  const [onlyMemo, setOnlyMemo] = useState(false);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingFine, setEditingFine] = useState<Fine | null>(null);
  const [detectedDriverInfo, setDetectedDriverInfo] = useState<string | null>(null);
  const [exportingMemo, setExportingMemo] = useState(false);

  const [form] = Form.useForm();
  const { hasRole } = useAuth();

  const handleExportMemo = async () => {
    setExportingMemo(true);
    try {
      await apiClient.downloadFile('/reports/export/memo', `Sluzhebnaya_Zapiska_${dayjs().format('YYYYMMDD')}.xlsx`);
      message.success('Служебная записка успешно выгружена');
    } catch {
      message.error('Ошибка выгрузки файла');
    } finally {
      setExportingMemo(false);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [fList, vList, dList] = await Promise.all([
        apiClient.getFines({
          query: searchQuery,
          status: selectedStatus,
          in_official_memo: onlyMemo ? true : undefined,
        }),
        apiClient.getVehicles(),
        apiClient.getDrivers(),
      ]);
      setFines(fList);
      setVehicles(vList);
      setDrivers(dList);
    } catch {
      message.error('Ошибка загрузки штрафов');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedStatus, onlyMemo]);

  const handleSearch = () => {
    loadData();
  };

  const handleOpenModal = (f?: Fine) => {
    setDetectedDriverInfo(null);
    if (f) {
      setEditingFine(f);
      form.setFieldsValue({
        ...f,
        violation_date: f.violation_date ? dayjs(f.violation_date) : null,
        accounting_date: f.accounting_date ? dayjs(f.accounting_date) : null,
        driver_notified_date: f.driver_notified_date ? dayjs(f.driver_notified_date) : null,
        payment_date: f.payment_date ? dayjs(f.payment_date) : null,
      });
    } else {
      setEditingFine(null);
      form.resetFields();
      form.setFieldsValue({
        status: 'NEW',
        accounting_date: dayjs(),
        amount: 0,
        is_not_our_car: false,
        in_official_memo: false,
      });
    }
    setIsModalOpen(true);
  };

  const handleAutoDetect = async () => {
    const vId = form.getFieldValue('vehicle_id');
    const vDate = form.getFieldValue('violation_date');
    if (!vId || !vDate) {
      message.warning('Сначала выберите автомобиль и укажите дату нарушения');
      return;
    }

    try {
      const res = await apiClient.autoDetectDriver(vId, vDate.format('YYYY-MM-DD'));
      if (res.driver_id) {
        form.setFieldsValue({ driver_id: res.driver_id });
        setDetectedDriverInfo(`Определен водитель: ${res.driver_name} (Источник: ${res.source})`);
        message.success(`Определен: ${res.driver_name}`);
      } else {
        setDetectedDriverInfo('Не удалось найти закрепление или путевой на эту дату');
        message.info('Водитель не найден в истории пересадок на эту дату');
      }
    } catch {
      message.error('Ошибка автоопределения');
    }
  };

  const handleSaveFine = async (values: any) => {
    try {
      const payload = {
        ...values,
        violation_date: values.violation_date ? values.violation_date.format('YYYY-MM-DD') : null,
        accounting_date: values.accounting_date ? values.accounting_date.format('YYYY-MM-DD') : null,
        driver_notified_date: values.driver_notified_date ? values.driver_notified_date.format('YYYY-MM-DD') : null,
        payment_date: values.payment_date ? values.payment_date.format('YYYY-MM-DD') : null,
      };

      if (editingFine) {
        await apiClient.updateFine(editingFine.id, payload);
        message.success('Штраф обновлен');
      } else {
        await apiClient.createFine(payload);
        message.success('Штраф успешно внесен в систему');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const handleDeleteFine = async (id: number) => {
    try {
      await apiClient.deleteFine(id);
      message.success('Штраф удален');
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const handleToggleMemo = async (f: Fine) => {
    try {
      await apiClient.updateFine(f.id, { in_official_memo: !f.in_official_memo });
      message.success(!f.in_official_memo ? 'Включен в служебку СБ' : 'Исключен из служебки СБ');
      loadData();
    } catch {
      message.error('Ошибка');
    }
  };

  const columns = [
    {
      title: 'Гос. номер',
      dataIndex: 'plate_number',
      key: 'plate_number',
      width: 120,
      render: (t: string) => <Tag color="blue" icon={<CarOutlined />}>{t}</Tag>,
    },
    {
      title: '№ Постановления / Протокола',
      dataIndex: 'notice_number',
      key: 'notice_number',
      render: (num: string, r: Fine) => (
        <div>
          <Text strong>{num}</Text>
          {r.is_not_our_car && (
            <div><Tag color="volcano" style={{ fontSize: 10 }}>Ошибочный (не наше авто)</Tag></div>
          )}
        </div>
      ),
    },
    {
      title: 'Дата нарушения',
      dataIndex: 'violation_date',
      key: 'violation_date',
      width: 120,
      render: (d: string) => d ? dayjs(d).format('DD.MM.YYYY') : <Text type="secondary">—</Text>,
    },
    {
      title: 'Водитель на дату нарушения',
      key: 'driver',
      width: 220,
      render: (_: any, r: Fine) => (
        <div>
          <Text>{r.driver_name || <Text type="secondary">Не определен</Text>}</Text>
          {r.driver_phone && <div style={{ fontSize: 11, color: '#8c8c8c' }}>{r.driver_phone}</div>}
        </div>
      ),
    },
    {
      title: 'Сумма (₸)',
      dataIndex: 'amount',
      key: 'amount',
      width: 110,
      render: (amt: number) => amt > 0 ? <b>{amt.toLocaleString()} ₸</b> : <Text type="secondary">—</Text>,
    },
    {
      title: 'Движение дат',
      key: 'dates',
      render: (_: any, r: Fine) => (
        <div style={{ fontSize: 11 }}>
          <div>Бухг: {r.accounting_date ? dayjs(r.accounting_date).format('DD.MM.YY') : '—'}</div>
          <div>Оповещен: {r.driver_notified_date ? dayjs(r.driver_notified_date).format('DD.MM.YY') : '—'}</div>
          <div>Оплата: {r.payment_date ? dayjs(r.payment_date).format('DD.MM.YY') : <span style={{ color: '#f5222d' }}>нет</span>}</div>
        </div>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (st: string, r: Fine) => {
        const map: Record<string, { label: string; color: string }> = {
          NEW: { label: 'Новый', color: 'orange' },
          NOTIFIED: { label: 'Оповещен', color: 'gold' },
          PAID: { label: 'Оплачен', color: 'green' },
          REFUSED: { label: 'Отказ оплаты', color: 'red' },
          DISPUTED: { label: 'Оспаривается', color: 'purple' },
        };
        const item = map[st] || { label: st, color: 'default' };
        return (
          <Space direction="vertical" size={2}>
            <Tag color={item.color}>{item.label}</Tag>
            {r.in_official_memo && <Tag color="magenta">В служебке СБ</Tag>}
          </Space>
        );
      },
    },
    {
      title: 'Примечания',
      dataIndex: 'notes',
      key: 'notes',
      render: (n: string) => n || <Text type="secondary">—</Text>,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      render: (_: any, r: Fine) => (
        <Space size="small">
          {hasRole(['admin', 'dispatcher']) && (
            <>
              <Button size="small" onClick={() => handleOpenModal(r)}>Ред.</Button>
              <Tooltip title={r.in_official_memo ? 'Убрать из служебки' : 'Включить в служебку СБ'}>
                <Button
                  size="small"
                  type={r.in_official_memo ? 'primary' : 'default'}
                  danger={!r.in_official_memo}
                  onClick={() => handleToggleMemo(r)}
                >
                  СБ
                </Button>
              </Tooltip>
            </>
          )}
          {hasRole(['admin']) && (
            <Popconfirm title="Удалить штраф?" onConfirm={() => handleDeleteFine(r.id)} okText="Да" cancelText="Нет">
              <Button size="small" danger>X</Button>
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
          <Col xs={24} sm={10} md={7}>
            <Input
              placeholder="Поиск по № протокола, авто, водителю..."
              prefix={<SearchOutlined />}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={12} sm={6} md={5}>
            <Select
              placeholder="Статус оплаты"
              style={{ width: '100%' }}
              allowClear
              value={selectedStatus}
              onChange={setSelectedStatus}
            >
              <Option value="NEW">Новый</Option>
              <Option value="NOTIFIED">Оповещен</Option>
              <Option value="PAID">Оплачен</Option>
              <Option value="REFUSED">Отказ оплаты</Option>
              <Option value="DISPUTED">Оспаривается</Option>
            </Select>
          </Col>
          <Col xs={12} sm={8} md={5}>
            <Space>
              <Text>Только для СБ:</Text>
              <Switch checked={onlyMemo} onChange={setOnlyMemo} />
            </Space>
          </Col>
          <Col xs={24} sm={12} md={7} style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={handleSearch} type="primary">Применить</Button>
              {hasRole(['admin', 'dispatcher']) && (
                <Button icon={<PlusOutlined />} type="primary" onClick={() => handleOpenModal()}>
                  Внести штраф
                </Button>
              )}
              <Button
                icon={<DownloadOutlined />}
                danger
                loading={exportingMemo}
                onClick={handleExportMemo}
              >
                Служебка в СБ (Excel)
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between' }}>
          <Text strong>Всего штрафов в выборке: {fines.length}</Text>
          <Text type="secondary">При внесении штрафа водитель на дату нарушения определяется автоматически</Text>
        </div>
        <Table
          dataSource={fines}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 25 }}
        />
      </Card>

      {/* Fine Modal */}
      <Modal
        title={editingFine ? `Редактирование штрафа: ${editingFine.notice_number}` : 'Внесение нового штрафа ПДД'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        okText="Сохранить"
        cancelText="Отмена"
        width={680}
      >
        <Form form={form} layout="vertical" onFinish={handleSaveFine}>
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
              <Form.Item name="notice_number" label="№ Протокола / Постановления" rules={[{ required: true, message: 'Введите номер' }]}>
                <Input placeholder="№ 267588231086795" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="violation_date" label="Дата нарушения">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12} style={{ display: 'flex', alignItems: 'center', paddingTop: 8 }}>
              <Button icon={<RobotOutlined />} onClick={handleAutoDetect} type="dashed" style={{ width: '100%' }}>
                Автоопределение водителя
              </Button>
            </Col>
          </Row>

          {detectedDriverInfo && (
            <Alert message={detectedDriverInfo} type="info" showIcon style={{ marginBottom: 16 }} />
          )}

          <Form.Item name="driver_id" label="Ответственный водитель">
            <Select showSearch placeholder="Выберите водителя (или используйте автоопределение)" optionFilterProp="children" allowClear>
              {drivers.map((d) => (
                <Option key={d.id} value={d.id}>
                  {d.full_name} ({d.position}) {d.phone ? `- ${d.phone}` : ''}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="amount" label="Сумма штрафа (₸)">
                <Input type="number" placeholder="21625" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="status" label="Статус">
                <Select>
                  <Option value="NEW">Новый</Option>
                  <Option value="NOTIFIED">Оповещен</Option>
                  <Option value="PAID">Оплачен</Option>
                  <Option value="REFUSED">Отказ оплаты</Option>
                  <Option value="DISPUTED">Оспаривается</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="payment_date" label="Дата оплаты">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="accounting_date" label="Дата получения от бухгалтерии">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="driver_notified_date" label="Дата оповещения водителя">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="in_official_memo" valuePropName="checked">
                <Switch /> <span style={{ marginLeft: 8 }}>Включить в служебную записку для СБ</span>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_not_our_car" valuePropName="checked">
                <Switch /> <span style={{ marginLeft: 8 }}>Ошибочный (не наше авто)</span>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="Примечания диспетчера">
            <Input.TextArea rows={2} placeholder="Отказ от оплаты, не выходит в Kaspi, передан чек..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
