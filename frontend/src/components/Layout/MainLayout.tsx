/** 主布局组件 */
import { Outlet } from 'react-router-dom';
import { Layout, Menu, Dropdown, Avatar, Button } from 'antd';
import {
  HomeOutlined,
  TeamOutlined,
  InboxOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import type { MenuProps } from 'antd';
import './MainLayout.css';

const { Header, Sider, Content } = Layout;

const MainLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAdmin } = useAuth();

  const baseMenuItems = [
    {
      key: '/dashboard',
      icon: <HomeOutlined />,
      label: '仪表盘',
      onClick: () => navigate('/dashboard'),
    },
    {
      key: '/jobs',
      icon: <TeamOutlined />,
      label: '岗位管理',
      onClick: () => navigate('/jobs'),
    },
    {
      key: '/resumes',
      icon: <InboxOutlined />,
      label: '简历列表',
      onClick: () => navigate('/resumes'),
    },
    {
      key: '/manual-review',
      icon: <CheckCircleOutlined />,
      label: '人工审核',
      onClick: () => navigate('/manual-review'),
    },
    {
      key: '/screening',
      icon: <FileTextOutlined />,
      label: '筛选结果',
      onClick: () => navigate('/screening'),
    },
  ];

  // 管理员额外菜单
  const adminMenuItems = [...baseMenuItems,
    {
      key: '/users',
      icon: <SettingOutlined />,
      label: '用户管理',
      onClick: () => navigate('/users'),
    },
  ];

  const menuItems = isAdmin ? adminMenuItems : baseMenuItems;

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240} theme="light">
        <div className="logo">
          <h2>📄 简历初筛系统</h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h1 style={{ fontSize: 20, margin: 0 }}>简历智能初筛系统</h1>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Button type="text" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar size="small" icon={<UserOutlined />} />
              <span>{user?.username}</span>
              <span style={{ fontSize: 12, color: '#999' }}>
                {isAdmin ? '管理员' : 'HR用户'}
              </span>
            </Button>
          </Dropdown>
        </Header>
        <Content style={{ margin: '24px', background: '#fff', padding: '24px', borderRadius: '8px' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
