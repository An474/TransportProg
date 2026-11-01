import React, { useState } from 'react';
import { Layout, Menu, Button, Typography, Space, Tag, theme, Dropdown } from 'antd';
import {
  DashboardOutlined,
  CarOutlined,
  TeamOutlined,
  SwapOutlined,
  FileTextOutlined,
  WarningOutlined,
  ToolOutlined,
  FireOutlined,
  BarChartOutlined,
  HistoryOutlined,
  CloudDownloadOutlined,
  LogoutOutlined,
  UserOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const { Header, Sider, Content } = Layout;
const { Text, Title } = Typography;

export const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Дашборд',
    },
    {
      key: '/vehicles',
      icon: <CarOutlined />,
      label: 'Автопарк',
    },
    {
      key: '/drivers',
      icon: <TeamOutlined />,
      label: 'Водители',
    },
    {
      key: '/assignments',
      icon: <SwapOutlined />,
      label: 'Пересадки и замены',
    },
    {
      key: '/waybills',
      icon: <FileTextOutlined />,
      label: 'Путевые листы',
    },
    {
      key: '/fines',
      icon: <WarningOutlined />,
      label: 'Штрафы и Служебки',
    },
    {
      key: '/maintenance',
      icon: <ToolOutlined />,
      label: 'ТО, Ремонты, Эвакуация',
    },
    {
      key: '/fuel',
      icon: <FireOutlined />,
      label: 'Учет ГСМ',
    },
    {
      key: '/reports',
      icon: <BarChartOutlined />,
      label: 'Отчеты и Выгрузка',
    },
    ...(hasRole(['admin'])
      ? [
          {
            key: '/users',
            icon: <UserOutlined />,
            label: 'Пользователи',
          },
          {
            key: '/audit',
            icon: <HistoryOutlined />,
            label: 'Журнал аудита',
          },
          {
            key: '/backups',
            icon: <CloudDownloadOutlined />,
            label: 'Резервные копии',
          },
        ]
      : []),
  ];

  const roleColorMap: Record<string, string> = {
    admin: 'red',
    dispatcher: 'blue',
    viewer: 'green',
  };

  const roleNameMap: Record<string, string> = {
    admin: 'Администратор',
    dispatcher: 'Диспетчер',
    viewer: 'Руководитель',
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        width={250}
        style={{
          background: '#001529',
          boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
        }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: '0 20px',
          background: '#002140',
          color: '#fff',
          overflow: 'hidden'
        }}>
          <CarOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: collapsed ? 0 : 12 }} />
          {!collapsed && (
            <div>
              <div style={{ fontWeight: 'bold', fontSize: 16, lineHeight: 1.2 }}>ТРАНСПОРТ</div>
              <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.6)' }}>Отдел логистики</div>
            </div>
          )}
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8 }}
        />
      </Sider>

      <Layout>
        <Header style={{
          padding: '0 24px',
          background: token.colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0',
          position: 'sticky',
          top: 0,
          zIndex: 10,
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16, width: 48, height: 48 }}
          />

          <Space size="middle">
            <Tag color={roleColorMap[user?.role || ''] || 'default'} style={{ padding: '4px 10px', fontSize: 13 }}>
              {roleNameMap[user?.role || ''] || user?.role}
            </Tag>
            <Space>
              <UserOutlined />
              <Text strong>{user?.full_name}</Text>
            </Space>
            <Button icon={<LogoutOutlined />} danger type="text" onClick={logout}>
              Выйти
            </Button>
          </Space>
        </Header>

        <Content style={{ margin: '20px 24px 0', overflow: 'initial' }}>
          <Outlet />
        </Content>

        <Layout.Footer style={{ textAlign: 'center', color: '#8c8c8c', fontSize: 12 }}>
          Информационная система транспортного отдела © 2026. Поддержка многопользовательской работы.
        </Layout.Footer>
      </Layout>
    </Layout>
  );
};
