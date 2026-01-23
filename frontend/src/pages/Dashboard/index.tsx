/** 仪表盘页面 */
import { useEffect, useState, useRef } from 'react';
import { Card, Row, Col, Statistic, Table, Spin, Alert, Typography, Button, Space, Tag } from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  TrophyOutlined,
  ReloadOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import {
  getDashboardStatistics,
  getStatisticsByCity,
  getStatisticsByJob,
} from '../../services/api';
import type { ColumnsType } from 'antd/es/table';

const { Title } = Typography;

const AUTO_REFRESH_INTERVAL = 30000; // 30秒自动刷新

const DashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [cityData, setCityData] = useState<Record<string, any>>({});
  const [jobData, setJobData] = useState<Record<string, any>>({});
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchAllData = async (showRefreshLoading = false) => {
    if (showRefreshLoading) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      // 并发请求所有数据
      const [dashboard, city, job] = await Promise.all([
        getDashboardStatistics(),
        getStatisticsByCity(),
        getStatisticsByJob(),
      ]);

      setDashboardData(dashboard);
      setCityData(city);
      setJobData(job);
      setLastUpdateTime(new Date());
    } catch (err: any) {
      setError(err.message || '加载数据失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // 设置自动刷新
  const setupAutoRefresh = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    if (autoRefreshEnabled) {
      intervalRef.current = setInterval(() => {
        fetchAllData(false); // 后台刷新，不显示loading
      }, AUTO_REFRESH_INTERVAL);
    }
  };

  // 手动刷新
  const handleManualRefresh = () => {
    fetchAllData(true);
    // 重置定时器
    setupAutoRefresh();
  };

  // 初始化和自动刷新
  useEffect(() => {
    fetchAllData();
    setupAutoRefresh();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefreshEnabled]);

  // 城市统计表格列
  const cityColumns: ColumnsType<any> = [
    {
      title: '城市',
      dataIndex: 'city',
      key: 'city',
      sorter: (a, b) => a.total - b.total,
      defaultSortOrder: 'descend',
    },
    {
      title: '总数',
      dataIndex: 'total',
      key: 'total',
      render: (value: number) => <span style={{ fontWeight: 'bold' }}>{value}</span>,
    },
    {
      title: '可以发offer',
      dataIndex: 'pass',
      key: 'pass',
      render: (value: number, record: any) => (
        <span style={{ color: '#52c41a' }}>
          {value} ({((value / record.total) * 100).toFixed(1)}%)
        </span>
      ),
    },
    {
      title: '待定',
      dataIndex: 'review',
      key: 'review',
      render: (value: number, record: any) => (
        <span style={{ color: '#faad14' }}>
          {value} ({((value / record.total) * 100).toFixed(1)}%)
        </span>
      ),
    },
    {
      title: '不合格',
      dataIndex: 'reject',
      key: 'reject',
      render: (value: number, record: any) => (
        <span style={{ color: '#ff4d4f' }}>
          {value} ({((value / record.total) * 100).toFixed(1)}%)
        </span>
      ),
    },
    {
      title: '平均分',
      dataIndex: 'avg_score',
      key: 'avg_score',
      render: (value: number) => <span style={{ fontWeight: 'bold' }}>{value}</span>,
      sorter: (a, b) => a.avg_score - b.avg_score,
    },
  ];

  // 职位统计表格列
  const jobColumns: ColumnsType<any> = [
    {
      title: '职位',
      dataIndex: 'job',
      key: 'job',
      sorter: (a, b) => a.total - b.total,
      defaultSortOrder: 'descend',
    },
    {
      title: '总数',
      dataIndex: 'total',
      key: 'total',
      render: (value: number) => <span style={{ fontWeight: 'bold' }}>{value}</span>,
    },
    {
      title: '可以发offer',
      dataIndex: 'pass',
      key: 'pass',
      render: (value: number, record: any) => (
        <span style={{ color: '#52c41a' }}>
          {value} ({((value / record.total) * 100).toFixed(1)}%)
        </span>
      ),
    },
    {
      title: '待定',
      dataIndex: 'review',
      key: 'review',
      render: (value: number, record: any) => (
        <span style={{ color: '#faad14' }}>
          {value} ({((value / record.total) * 100).toFixed(1)}%)
        </span>
      ),
    },
    {
      title: '不合格',
      dataIndex: 'reject',
      key: 'reject',
      render: (value: number, record: any) => (
        <span style={{ color: '#ff4d4f' }}>
          {value} ({((value / record.total) * 100).toFixed(1)}%)
        </span>
      ),
    },
    {
      title: '平均分',
      dataIndex: 'avg_score',
      key: 'avg_score',
      render: (value: number) => <span style={{ fontWeight: 'bold' }}>{value}</span>,
      sorter: (a, b) => a.avg_score - b.avg_score,
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载统计数据..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="加载失败"
        description={error}
        type="error"
        showIcon
        style={{ margin: 24 }}
      />
    );
  }

  // 转换城市数据为表格格式
  const cityTableData = Object.entries(cityData).map(([city, data]: [string, any]) => ({
    key: city,
    city,
    ...data,
  }));

  // 转换职位数据为表格格式
  const jobTableData = Object.entries(jobData).map(([job, data]: [string, any]) => ({
    key: job,
    job,
    ...data,
  }));

  const overview = dashboardData?.overview || {
    total_resumes: 0,
    pass_count: 0,
    review_count: 0,
    reject_count: 0,
    pass_rate: 0,
    avg_score: 0,
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>仪表盘</Title>
        <Space>
          {refreshing && (
            <Tag color="processing" icon={<SyncOutlined spin />}>
              刷新中...
            </Tag>
          )}
          {lastUpdateTime && !loading && (
            <span style={{ color: '#999', fontSize: 12, marginRight: 8 }}>
              最后更新: {lastUpdateTime.toLocaleTimeString()}
            </span>
          )}
          <Button
            icon={<ReloadOutlined />}
            onClick={handleManualRefresh}
            loading={refreshing}
            size="small"
          >
            刷新
          </Button>
          <Tag
            color={autoRefreshEnabled ? 'success' : 'default'}
            style={{ cursor: 'pointer' }}
            onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
          >
            {autoRefreshEnabled ? '自动刷新: 开' : '自动刷新: 关'}
          </Tag>
        </Space>
      </div>

      {/* 综合统计卡片 */}
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={4}>
          <Card>
            <Statistic
              title="总简历数"
              value={overview.total_resumes}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title="可以发offer"
              value={overview.pass_count}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={`/ ${overview.total_resumes}`}
            />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title="待定"
              value={overview.review_count}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
              suffix={`/ ${overview.total_resumes}`}
            />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title="不合格"
              value={overview.reject_count}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
              suffix={`/ ${overview.total_resumes}`}
            />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title="平均分"
              value={overview.avg_score}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#722ed1' }}
              suffix="分"
              precision={1}
            />
          </Card>
        </Col>
      </Row>

      {/* 通过率展示 */}
      <Card style={{ marginTop: 24 }}>
        <Statistic
          title="通过率"
          value={overview.pass_rate * 100}
          precision={1}
          suffix="%"
          valueStyle={{
            color: overview.pass_rate >= 0.5 ? '#52c41a' : overview.pass_rate >= 0.3 ? '#faad14' : '#ff4d4f',
          }}
        />
      </Card>

      {/* 按城市统计 */}
      <Card
        title={<Title level={4}>按城市统计</Title>}
        style={{ marginTop: 24 }}
      >
        <Table
          columns={cityColumns}
          dataSource={cityTableData}
          pagination={{ pageSize: 10 }}
          size="middle"
        />
      </Card>

      {/* 按职位统计 */}
      <Card
        title={<Title level={4}>按职位统计</Title>}
        style={{ marginTop: 24 }}
      >
        <Table
          columns={jobColumns}
          dataSource={jobTableData}
          pagination={{ pageSize: 10 }}
          size="middle"
        />
      </Card>

      {/* 系统功能说明 */}
      <Card title="系统功能" style={{ marginTop: 24 }}>
        <p>当前系统已集成以下功能：</p>
        <ul>
          <li>📋 <strong>职位管理</strong>：支持Java开发、销售总监、自动化测试、市场运营、前端开发、产品经理、实施顾问</li>
          <li>🏙️ <strong>城市提取</strong>：从邮件标题、正文、简历内容中自动提取城市信息</li>
          <li>🎯 <strong>职位判断</strong>：基于三级优先级（邮件标题 {'>'} PDF内容 {'>'} 技能推断）自动判断应聘职位</li>
          <li>🤖 <strong>Agent评分</strong>：根据职位和城市路由到外部Agent进行智能评分（0-100分）</li>
          <li>📊 <strong>结果分类</strong>：
            <ul>
              <li>70-100分：可以发offer</li>
              <li>40-70分：待定（需人工复核）</li>
              <li>0-40分：不合格</li>
            </ul>
          </li>
          <li>📈 <strong>统计分析</strong>：按城市、职位、时间段进行多维度统计分析</li>
          <li>📧 <strong>邮箱监听</strong>：自动监听企业邮箱，解析简历附件并筛选</li>
        </ul>
      </Card>
    </div>
  );
};

export default DashboardPage;
