import React, { useEffect, useState } from 'react';
import {
  Card,
  Button,
  Table,
  Typography,
  Space,
  message,
  Alert,
  Tag,
  Input,
  Switch,
  Divider,
  Modal,
  Collapse,
  Spin,
  notification
} from 'antd';
import {
  CloudDownloadOutlined,
  PlusOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  CloudUploadOutlined,
  SyncOutlined,
  GithubOutlined,
  CopyOutlined,
  SafetyCertificateOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { apiClient } from '../api/client';

const { Title, Text, Paragraph } = Typography;

const GOOGLE_APPS_SCRIPT_TEMPLATE = `// ============================================================
// Google Apps Script для приема резервных копий Транспортного отдела
// ============================================================

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var filename = data.filename || ("backup_" + Utilities.formatDate(new Date(), "GMT+5", "yyyy-MM-dd_HH-mm-ss") + ".zip");
    var base64Content = data.content;
    
    if (!base64Content) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error", 
        message: "No content provided"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // Декодируем файл из base64
    var decoded = Utilities.base64Decode(base64Content);
    var blob = Utilities.newBlob(decoded, "application/zip", filename);
    
    // Ищем или создаем папку "Резервные копии Транспорт" на Google Диске
    var folderName = "Резервные копии Транспорт";
    var folders = DriveApp.getFoldersByName(folderName);
    var targetFolder;
    
    if (folders.hasNext()) {
      targetFolder = folders.next();
    } else {
      targetFolder = DriveApp.createFolder(folderName);
    }
    
    // Сохраняем файл на ваш личный Google Диск
    var file = targetFolder.createFile(blob);
    
    // Храним последние 30 копий (старые автоматически отправляются в корзину)
    var allFiles = targetFolder.getFiles();
    var fileList = [];
    while (allFiles.hasNext()) {
      fileList.push(allFiles.next());
    }
    fileList.sort(function(a, b) {
      return b.getDateCreated().getTime() - a.getDateCreated().getTime();
    });
    if (fileList.length > 30) {
      for (var i = 30; i < fileList.length; i++) {
        fileList[i].setTrashed(true);
      }
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "ok",
      fileId: file.getId(),
      fileName: file.getName(),
      fileSize: file.getSize(),
      url: file.getUrl()
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}`;

export const BackupsPage: React.FC = () => {
  const [backups, setBackups] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  // Google Drive Settings
  const [gdriveUrl, setGdriveUrl] = useState('');
  const [gdriveEnabled, setGdriveEnabled] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const [testingGdrive, setTestingGdrive] = useState(false);
  const [lastGdriveStatus, setLastGdriveStatus] = useState<string | null>(null);

  // GitHub Update State
  const [checkingUpdate, setCheckingUpdate] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<any>(null);
  const [applyingUpdate, setApplyingUpdate] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getBackups();
      setBackups(data);

      const settings = await apiClient.getBackupSettings();
      setGdriveUrl(settings.google_drive_webhook_url || '');
      setGdriveEnabled(Boolean(settings.google_drive_enabled));
      if (settings.last_google_drive_status) {
        setLastGdriveStatus(`${settings.last_google_drive_backup || ''}: ${settings.last_google_drive_status}`);
      }
    } catch {
      message.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    checkForUpdatesQuietly();
  }, []);

  const checkForUpdatesQuietly = async () => {
    try {
      const res = await apiClient.checkUpdates();
      setUpdateInfo(res);
    } catch {
      // Quiet fail on auto-check
    }
  };

  const handleManualCheckUpdates = async () => {
    setCheckingUpdate(true);
    try {
      const res = await apiClient.checkUpdates();
      setUpdateInfo(res);
      if (res.has_update) {
        message.info(`Доступна новая версия: v${res.latest_version}`);
      } else {
        message.success('У вас установлена самая актуальная версия программы!');
      }
    } catch (e: any) {
      message.error('Не удалось связаться с GitHub для проверки обновлений');
    } finally {
      setCheckingUpdate(false);
    }
  };

  const handleApplyUpdate = () => {
    Modal.confirm({
      title: 'Подтверждение обновления программы',
      icon: <SafetyCertificateOutlined style={{ color: '#52c41a' }} />,
      content: (
        <div>
          <Paragraph>
            Система скачает релиз <b>v{updateInfo?.latest_version}</b> с репозитория <code>An474/TransportProg</code>.
          </Paragraph>
          <Paragraph type="success">
            <b>Гарантия безопасности:</b> Перед обновлением система автоматически создаст резервную копию базы данных. База данных и все введенные автомобили и штрафы останутся нетронутыми!
          </Paragraph>
        </div>
      ),
      okText: 'Обновить сейчас',
      cancelText: 'Отмена',
      onOk: async () => {
        setApplyingUpdate(true);
        try {
          const res = await apiClient.applyUpdate({ download_url: updateInfo?.download_url });
          notification.success({
            message: 'Обновление успешно установлено!',
            description: 'Файлы программы обновлены. Страница перезагрузится через 3 секунды...',
            duration: 4
          });
          setTimeout(() => {
            window.location.reload();
          }, 3000);
        } catch (e: any) {
          message.error(e.response?.data?.detail || 'Ошибка при обновлении программы');
        } finally {
          setApplyingUpdate(false);
        }
      }
    });
  };

  const handleCreateBackup = async () => {
    setCreating(true);
    try {
      const res = await apiClient.createBackup();
      message.success(res.message || 'Резервная копия успешно создана!');
      if (res.google_drive?.status === 'ok') {
        message.success('Копия также успешно отправлена на ваш Google Диск!');
      }
      loadData();
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка создания резервной копии');
    } finally {
      setCreating(false);
    }
  };

  const handleSaveGdriveSettings = async () => {
    setSavingSettings(true);
    try {
      await apiClient.saveBackupSettings({
        google_drive_webhook_url: gdriveUrl.trim(),
        google_drive_enabled: gdriveEnabled
      });
      message.success('Настройки Google Диска сохранены');
    } catch {
      message.error('Не удалось сохранить настройки');
    } finally {
      setSavingSettings(false);
    }
  };

  const handleTestGoogleDrive = async () => {
    if (!gdriveUrl) {
      message.warning('Сначала укажите URL Webhook Google Apps Script');
      return;
    }
    setTestingGdrive(true);
    try {
      await handleSaveGdriveSettings();
      const res = await apiClient.testGoogleDrive();
      message.success(res.message);
      loadData();
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка отправки на Google Диск');
    } finally {
      setTestingGdrive(false);
    }
  };

  const copyScriptToClipboard = () => {
    navigator.clipboard.writeText(GOOGLE_APPS_SCRIPT_TEMPLATE);
    message.success('Код скрипта скопирован в буфер обмена!');
  };

  const columns = [
    {
      title: 'Имя архивного файла',
      dataIndex: 'filename',
      key: 'filename',
      render: (name: string) => (
        <Space>
          <DatabaseOutlined style={{ color: '#1677ff' }} />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: 'Размер',
      dataIndex: 'size_kb',
      key: 'size_kb',
      render: (size: number) => <Tag color="blue">{size} КБ</Tag>,
    },
    {
      title: 'Дата и время создания',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (d: string) => d,
    },
    {
      title: 'Статус архива',
      key: 'status',
      render: () => <Tag color="success" icon={<CheckCircleOutlined />}>Локально сохранен</Tag>,
    },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      {/* 1. Header Card */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>Резервное копирование и Обновление системы</Title>
            <Text type="secondary">Гарантия сохранности данных автопарка и обновление программы в 1 клик</Text>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            loading={creating}
            onClick={handleCreateBackup}
            size="large"
          >
            Создать резервную копию сейчас
          </Button>
        </div>
      </Card>

      {/* 2. GitHub 1-Click Update Card */}
      <Card
        style={{ marginBottom: 16, borderColor: updateInfo?.has_update ? '#52c41a' : '#d9d9d9' }}
        title={
          <Space>
            <GithubOutlined style={{ fontSize: 20 }} />
            <span>Обновление программы через GitHub</span>
            <Tag color="cyan">Репозиторий: An474/TransportProg</Tag>
          </Space>
        }
        extra={
          <Button
            icon={<SyncOutlined spin={checkingUpdate} />}
            onClick={handleManualCheckUpdates}
            loading={checkingUpdate}
          >
            Проверить обновления
          </Button>
        }
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Space direction="vertical" size={4}>
              <div>
                <Text>Текущая версия: </Text>
                <Tag color="blue" style={{ fontSize: 13, fontWeight: 600 }}>v{updateInfo?.current_version || '1.0.0'}</Tag>
                {updateInfo?.latest_version && (
                  <>
                    <Text style={{ marginLeft: 16 }}>Версия на GitHub: </Text>
                    <Tag color={updateInfo?.has_update ? 'success' : 'default'} style={{ fontSize: 13, fontWeight: 600 }}>
                      v{updateInfo?.latest_version}
                    </Tag>
                  </>
                )}
              </div>
              <Text type="secondary">
                {updateInfo?.has_update
                  ? 'Доступно свежее обновление с исправлениями и новыми возможностями.'
                  : 'У вас установлена последняя доступная версия программы.'}
              </Text>
            </Space>
          </div>

          {updateInfo?.has_update && (
            <Button
              type="primary"
              size="large"
              style={{ background: '#52c41a', borderColor: '#52c41a', height: 44, fontWeight: 600 }}
              icon={<CloudDownloadOutlined />}
              loading={applyingUpdate}
              onClick={handleApplyUpdate}
            >
              Обновить всю программу до v{updateInfo?.latest_version}
            </Button>
          )}
        </div>

        {updateInfo?.has_update && updateInfo?.release_notes && (
          <Alert
            message={`Что нового в версии v${updateInfo?.latest_version}:`}
            description={<div style={{ whiteSpace: 'pre-wrap' }}>{updateInfo?.release_notes}</div>}
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Card>

      {/* 3. Google Drive Integration Card */}
      <Card
        style={{ marginBottom: 16 }}
        title={
          <Space>
            <CloudUploadOutlined style={{ fontSize: 20, color: '#1677ff' }} />
            <span>Выгрузка резервных копий на ваш личный Google Диск</span>
            {gdriveEnabled && gdriveUrl ? (
              <Tag color="success">Активно</Tag>
            ) : (
              <Tag color="default">Отключено</Tag>
            )}
          </Space>
        }
      >
        <Paragraph type="secondary">
          Система может автоматически отправлять каждый созданный бэкап в отдельную папку <b>«Резервные копии Транспорт»</b> на ваш личный Google Диск. На компьютере мамы ничего настраивать не нужно.
        </Paragraph>

        <div style={{ marginBottom: 16 }}>
          <Space align="center" style={{ marginBottom: 12 }}>
            <Switch
              checked={gdriveEnabled}
              onChange={(checked) => setGdriveEnabled(checked)}
            />
            <Text strong>Включить автоматическую отправку на Google Диск</Text>
          </Space>

          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <Input
              placeholder="https://script.google.com/macros/s/AKfycb.../exec"
              value={gdriveUrl}
              onChange={(e) => setGdriveUrl(e.target.value)}
              prefix={<CloudUploadOutlined />}
              style={{ flex: 1 }}
            />
            <Button
              onClick={handleSaveGdriveSettings}
              loading={savingSettings}
            >
              Сохранить URL
            </Button>
            <Button
              type="primary"
              onClick={handleTestGoogleDrive}
              loading={testingGdrive}
              disabled={!gdriveUrl}
            >
              Проверить отправку на Google Диск
            </Button>
          </div>
        </div>

        {lastGdriveStatus && (
          <Alert
            message="Статус последней выгрузки на Google Диск"
            description={lastGdriveStatus}
            type={lastGdriveStatus.includes('Успешно') ? 'success' : 'info'}
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Instructions Accordion */}
        <Collapse
          items={[
            {
              key: 'instructions',
              label: (
                <Space>
                  <InfoCircleOutlined style={{ color: '#1677ff' }} />
                  <Text strong>Инструкция: как подключить свой Google Диск за 2 минуты (бесплатно)</Text>
                </Space>
              ),
              children: (
                <div>
                  <ol style={{ paddingLeft: 20, lineHeight: 1.8 }}>
                    <li>
                      Откройте в браузере сайт <b><a href="https://script.google.com/home/start" target="_blank" rel="noreferrer">script.google.com</a></b> (под своим личным Google-аккаунтом).
                    </li>
                    <li>
                      Нажмите кнопку <b>«Новый проект»</b> (синяя кнопка слева вверху).
                    </li>
                    <li>
                      Сотрите всё в редакторе и вставьте готовый код (нажмите кнопку ниже):
                      <div style={{ margin: '8px 0' }}>
                        <Button
                          icon={<CopyOutlined />}
                          onClick={copyScriptToClipboard}
                          size="small"
                        >
                          Скопировать код Google Apps Script
                        </Button>
                      </div>
                    </li>
                    <li>
                      В правом верхнем углу нажмите синюю кнопку <b>«Начать развертывание»</b> (Deploy) → <b>«Новое развертывание»</b> (New deployment).
                    </li>
                    <li>
                      Нажмите на иконку шестеренки слева от «Выберите тип» → выберите <b>«Веб-приложение»</b> (Web app).
                    </li>
                    <li>
                      В настройках укажите:
                      <ul>
                        <li><b>Запуск от имени:</b> <i>«Я (ваш_email@gmail.com)»</i></li>
                        <li><b>У кого есть доступ:</b> <i>«Все» (Anyone)</i></li>
                      </ul>
                    </li>
                    <li>
                      Нажмите <b>«Развернуть»</b>, разрешите доступ к Google Диску и <b>скопируйте полученный URL веб-приложения</b> (заканчивается на <code>/exec</code>).
                    </li>
                    <li>
                      Вставьте скопированный URL в поле выше и нажмите <b>«Проверить отправку на Google Диск»</b>. В вашем Google Диске моментально появится папка <i>«Резервные копии Транспорт»</i> со свежим бэкапом!
                    </li>
                  </ol>
                </div>
              )
            }
          ]}
        />
      </Card>

      {/* 4. Local Backups List */}
      <Card
        title={
          <Space>
            <DatabaseOutlined style={{ color: '#1677ff' }} />
            <span>Локальные резервные копии на этом компьютере ({backups.length})</span>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={backups}
          rowKey="filename"
          loading={loading}
          pagination={{ pageSize: 8 }}
        />
      </Card>
    </div>
  );
};
