/** 筛选结果页面 - 只显示已配置FastGPT Agent的岗位类别（目前只有实施顾问） */
import { useState, useEffect, useMemo } from 'react';
import { Card, Table, Tag, Button, message, Tooltip, Radio, Space } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getScreeningResults, markInterviewed } from '../../services/api';

interface AgentEvaluatedResume {
  id: string | null;
  resume_id: string;
  candidate_name: string | null;
  candidate_email: string | null;
  candidate_phone: string | null;
  candidate_education: string | null;
  education_level?: string | null;
  job_id: string | null;
  job_name: string;
  job_category: string;
  agent_score: number | null;
  screening_result: string;
  matched_points: string[];
  unmatched_points: string[];
  suggestion: string;
  evaluated: boolean;
  created_at: string;
  phone?: string | null;
  email?: string | null;
  work_years?: number | null;
  skills?: string[];
  city?: string | null;
  screening_status?: string | null;
  agent_evaluated_at?: string | null;
}

const ScreeningPage = () => {
  const [loading, setLoading] = useState(false);
  const [resumes, setResumes] = useState<AgentEvaluatedResume[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });
  const [timeRange, setTimeRange] = useState<string>('all');
  const [timeStats, setTimeStats] = useState({ today: 0, thisWeek: 0, thisMonth: 0, all: 0 });
  const [screeningStatus, setScreeningStatus] = useState<string>('all'); // 'all' | 'interviewed' | 'pass' | 'pending' | 'fail'
  const [sortField, setSortField] = useState<string>('agent_evaluated_at');
  const [sortOrder, setSortOrder] = useState<'ascend' | 'descend' | null>('descend');

  // 加载简历
  useEffect(() => {
    loadResumes();
    const interval = setInterval(() => {
      loadResumes(pagination.current, pagination.pageSize);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // 监听时间范围变化
  useEffect(() => {
    loadResumes(1, pagination.pageSize);
  }, [timeRange]);

  const loadResumes = async (page: number = 1, pageSize: number = 50) => {
    setLoading(true);
    try {
      const skip = (page - 1) * pageSize;
      const params: any = { skip, limit: pageSize };
      if (timeRange !== 'all') {
        params.time_range = timeRange;
      }
      const data = await getScreeningResults(params);

      const results = data.results || [];
      fetchTimeStats();

      const adaptedResults = results.map((item: any) => ({
        ...item,
        phone: item.candidate_phone,
        email: item.candidate_email,
        screening_status: item.screening_status || item.screening_result,
        agent_evaluated_at: item.created_at,
      }));

      setResumes(adaptedResults);
      setPagination({
        current: page,
        pageSize: pageSize,
        total: data.total || 0,
      });
    } catch (error) {
      message.error('加载筛选结果失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (newPagination: any, _filters: any, sorter: any) => {
    if (sorter && !Array.isArray(sorter)) {
      setSortField(sorter.field);
      setSortOrder(sorter.order as 'ascend' | 'descend' | null);
    }
    const pageChanged = newPagination.current !== pagination.current;
    const pageSizeChanged = newPagination.pageSize !== pagination.pageSize;
    if (pageChanged || pageSizeChanged) {
      loadResumes(newPagination.current, newPagination.pageSize);
    }
  };

  const handleTimeRangeChange = (e: any) => {
    setTimeRange(e.target.value);
  };

  const handleMarkInterviewed = async (resumeId: string, name: string) => {
    try {
      const result = await markInterviewed(resumeId);
      message.success(result.message || `已将"${name}"标记为已面试`);
      loadResumes(pagination.current, pagination.pageSize);
    } catch (error) {
      message.error('操作失败');
    }
  };

  const getTimeLabel = (createdAt: string | null | undefined) => {
    if (!createdAt) return { text: '-', color: 'default' };
    const date = new Date(createdAt);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const thisWeekStart = new Date(today);
    thisWeekStart.setDate(today.getDate() - today.getDay());
    const thisMonthStart = new Date(now.getFullYear(), now.getMonth(), 1);

    if (date >= today) return { text: '今天', color: 'red' };
    else if (date >= thisWeekStart) return { text: '本周', color: 'gold' };
    else if (date >= thisMonthStart) return { text: '本月', color: 'blue' };
    else return { text: `${date.getMonth() + 1}-${date.getDate()}`, color: 'default' };
  };

  const formatDateTime = (dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
  };

  const fetchTimeStats = async () => {
    try {
      const allData = await getScreeningResults({ limit: 1 });
      const todayData = await getScreeningResults({ limit: 1, time_range: 'today' });
      const weekData = await getScreeningResults({ limit: 1, time_range: 'this_week' });
      const monthData = await getScreeningResults({ limit: 1, time_range: 'this_month' });
      setTimeStats({
        all: allData.total || 0,
        today: todayData.total || 0,
        thisWeek: weekData.total || 0,
        thisMonth: monthData.total || 0,
      });
    } catch (error) {
      console.error('获取统计数据失败:', error);
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return '#999';
    if (score >= 70) return '#52c41a';
    if (score >= 40) return '#faad14';
    return '#f5222d';
  };

  const sortedResumes = useMemo(() => {
    let sorted = [...resumes];

    // 前端按状态筛选
    if (screeningStatus !== 'all') {
      sorted = sorted.filter((item) => {
        const score = item.agent_score;

        if (screeningStatus === 'interviewed') {
          // 已面试
          return item.screening_status === '已面试';
        } else if (screeningStatus === 'pass') {
          // 可以进行面试：agent_score >= 70
          return score !== null && score >= 70;
        } else if (screeningStatus === 'pending') {
          // 待定：40 <= agent_score < 70
          return score !== null && score >= 40 && score < 70;
        } else if (screeningStatus === 'fail') {
          // 不合格：agent_score < 40
          return score !== null && score < 40;
        }
        return true;
      });
    }

    // 排序
    if (sortField && sortOrder) {
      sorted.sort((a, b) => {
        let compareResult = 0;
        switch (sortField) {
          case 'candidate_name':
            const nameA = a.candidate_name || '';
            const nameB = b.candidate_name || '';
            compareResult = nameA.localeCompare(nameB, 'zh-CN');
            break;
          case 'agent_score':
            const scoreA = a.agent_score ?? -1;
            const scoreB = b.agent_score ?? -1;
            compareResult = scoreA - scoreB;
            break;
          case 'agent_evaluated_at':
            const timeA = a.agent_evaluated_at ? new Date(a.agent_evaluated_at).getTime() : 0;
            const timeB = b.agent_evaluated_at ? new Date(b.agent_evaluated_at).getTime() : 0;
            compareResult = timeA - timeB;
            break;
          default:
            break;
        }
        return sortOrder === 'ascend' ? compareResult : -compareResult;
      });
    }
    return sorted;
  }, [resumes, sortField, sortOrder, screeningStatus]);

  // 计算筛选后的总数（用于分页显示）
  const filteredTotal = screeningStatus === 'all' ? pagination.total : sortedResumes.length;

  const columns: ColumnsType<AgentEvaluatedResume> = [
    {
      title: '候选人',
      dataIndex: 'candidate_name',
      key: 'candidate_name',
      width: 150,
      fixed: 'left' as const,
      sorter: (a: AgentEvaluatedResume, b: AgentEvaluatedResume) => {
        const nameA = a.candidate_name || '';
        const nameB = b.candidate_name || '';
        return nameA.localeCompare(nameB, 'zh-CN');
      },
      sortOrder: sortField === 'candidate_name' ? sortOrder : null,
      render: (name: string | null, record: AgentEvaluatedResume) => (
        <div>
          <div style={{ fontWeight: 'bold', fontSize: 14 }}>{name || '未命名'}</div>
          <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>
            {record.phone && <div>{record.phone}</div>}
            {record.email && <div style={{ fontSize: 11 }}>{record.email}</div>}
          </div>
        </div>
      ),
    },
    {
      title: '职位',
      key: 'job',
      width: 150,
      render: (_: any, record: AgentEvaluatedResume) => (
        <div>
          {record.job_category ? (
            <Tag color="blue" style={{ fontSize: 12 }}>{record.job_category}</Tag>
          ) : (
            <span style={{ color: '#999' }}>未分类</span>
          )}
          {record.city && (
            <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>{record.city}</div>
          )}
        </div>
      ),
    },
    {
      title: '学历与经验',
      key: 'education',
      width: 180,
      render: (_: any, record: AgentEvaluatedResume) => (
        <div>
          <div style={{ marginBottom: 4 }}>
            {record.candidate_education && record.education_level ? (
              <>{record.candidate_education}/{record.education_level}</>
            ) : record.candidate_education || '-'}
          </div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {record.work_years != null ? `${record.work_years}年工作经验` : '-'}
          </div>
        </div>
      ),
    },
    {
      title: '技能标签',
      dataIndex: 'skills',
      key: 'skills',
      width: 200,
      render: (skills: string[] = []) => {
        const displaySkills = skills.slice(0, 3);
        const remainingCount = skills.length - 3;
        return (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {displaySkills.map((skill, index) => (
              <Tag key={index} color="blue" style={{ fontSize: 11, marginBottom: 2 }}>
                {skill}
              </Tag>
            ))}
            {remainingCount > 0 && (
              <Tooltip title={skills.slice(3).join(', ')}>
                <Tag style={{ fontSize: 11, marginBottom: 2 }}>+{remainingCount}</Tag>
              </Tooltip>
            )}
          </div>
        );
      },
    },
    {
      title: 'Agent评分',
      dataIndex: 'agent_score',
      key: 'agent_score',
      width: 120,
      sorter: (a: AgentEvaluatedResume, b: AgentEvaluatedResume) => {
        const scoreA = a.agent_score ?? -1;
        const scoreB = b.agent_score ?? -1;
        return scoreA - scoreB;
      },
      sortOrder: sortField === 'agent_score' ? sortOrder : null,
      render: (_: any, record: AgentEvaluatedResume) => (
        <div>
          {record.agent_score !== null && record.agent_score !== undefined ? (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ fontSize: 24, fontWeight: 'bold', color: getScoreColor(record.agent_score) }}>
                {record.agent_score}
              </span>
              <span style={{ fontSize: 14, color: '#999', marginLeft: 4 }}>分</span>
            </div>
          ) : (
            <span style={{ color: '#999' }}>待评估</span>
          )}
        </div>
      ),
    },
    {
      title: '筛选结果',
      key: 'screening_status',
      width: 140,
      render: (_: any, record: AgentEvaluatedResume) => {
        const score = record.agent_score;
        if (score === null || score === undefined) return <Tag style={{ fontSize: 12 }}>待评估</Tag>;
        if (score >= 70) return <Tag color="success" style={{ fontSize: 13, fontWeight: 500 }}>可以进入面试</Tag>;
        if (score >= 40) return <Tag color="warning" style={{ fontSize: 13, fontWeight: 500 }}>待定</Tag>;
        return <Tag color="error" style={{ fontSize: 13, fontWeight: 500 }}>不合格</Tag>;
      },
    },
    {
      title: '评估时间',
      dataIndex: 'agent_evaluated_at',
      key: 'agent_evaluated_at',
      width: 120,
      sorter: (a: AgentEvaluatedResume, b: AgentEvaluatedResume) => {
        const timeA = a.agent_evaluated_at ? new Date(a.agent_evaluated_at).getTime() : 0;
        const timeB = b.agent_evaluated_at ? new Date(b.agent_evaluated_at).getTime() : 0;
        return timeA - timeB;
      },
      defaultSortOrder: 'descend' as const,
      sortOrder: sortField === 'agent_evaluated_at' ? sortOrder : null,
      render: (date: string | null | undefined) => {
        const label = getTimeLabel(date);
        return (
          <Tooltip title={formatDateTime(date)}>
            <Tag color={label.color}>{label.text}</Tag>
          </Tooltip>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: AgentEvaluatedResume) => (
        <Space size="small">
          <Button type="link" size="small" onClick={() => window.open(`http://localhost:8000/api/v1/pdfs/${record.resume_id}`, '_blank')}>
            查看PDF
          </Button>
          <Button type="link" size="small" onClick={() => {
            const resumeId = record.resume_id;
            const name = record.candidate_name || '未命名';
            if (resumeId) handleMarkInterviewed(resumeId, name);
          }}>
            {record.screening_status === '已面试' ? '取消面试' : '已面试'}
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0 }}>筛选结果</h2>
          <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
            只显示已配置FastGPT Agent的岗位类别（目前：实施顾问）
          </div>
          <div style={{ marginTop: 12 }}>
            <Radio.Group value={timeRange} onChange={handleTimeRangeChange} buttonStyle="solid">
              <Radio.Button value="all">全部 ({timeStats.all})</Radio.Button>
              <Radio.Button value="today">今天 ({timeStats.today})</Radio.Button>
              <Radio.Button value="this_week">本周 ({timeStats.thisWeek})</Radio.Button>
              <Radio.Button value="this_month">本月 ({timeStats.thisMonth})</Radio.Button>
            </Radio.Group>
          </div>
          <div style={{ marginTop: 8 }}>
            <Radio.Group value={screeningStatus} onChange={(e) => setScreeningStatus(e.target.value)} buttonStyle="solid">
              <Radio.Button value="all">全部</Radio.Button>
              <Radio.Button value="interviewed">已面试</Radio.Button>
              <Radio.Button value="pass">可以进行面试</Radio.Button>
              <Radio.Button value="pending">待定</Radio.Button>
              <Radio.Button value="fail">不合格</Radio.Button>
            </Radio.Group>
          </div>
        </div>
        <Button type="default" icon={<ReloadOutlined />} onClick={() => loadResumes(pagination.current, pagination.pageSize)} loading={loading}>
          刷新
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={sortedResumes}
          rowKey="id"
          loading={loading}
          pagination={{
            current: screeningStatus !== 'all' ? 1 : pagination.current,
            pageSize: pagination.pageSize,
            total: filteredTotal,
            showSizeChanger: screeningStatus === 'all',
            pageSizeOptions: ['20', '50', '100', '200'],
            showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条简历`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          rowClassName={(record) => {
            if (record.screening_status === '已面试') return 'row-interviewed';
            const score = record.agent_score;
            if (score === null || score === undefined) return '';
            if (score >= 70) return 'row-pass';
            if (score >= 40) return 'row-review';
            return 'row-reject';
          }}
        />
      </Card>

      <style>{`
        .row-pass:hover { background-color: #f6ffed !important; }
        .row-review:hover { background-color: #fffbe6 !important; }
        .row-reject:hover { background-color: #fff1f0 !important; }
        .row-interviewed { background-color: #f5f5f5 !important; color: #999 !important; }
        .row-interviewed td { background-color: #f5f5f5 !important; color: #999 !important; }
      `}</style>
    </div>
  );
};

export default ScreeningPage;
