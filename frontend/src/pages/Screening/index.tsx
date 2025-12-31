/** 筛选结果页面 - 显示通过Agent评估的简历（绿色和黄色） */
import { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, message, Tooltip } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { JOB_CATEGORY_COLORS } from '../../types';
import { getResumes } from '../../services/api';

interface AgentEvaluatedResume {
  id: string;
  candidate_name: string | null;
  phone: string | null;
  email: string | null;
  education: string | null;
  education_level: string | null;
  work_years: number | null;
  job_category: string | null;
  agent_score: number | null;
  agent_evaluation_id: string | null;
  screening_status: string | null;
  agent_evaluated_at: string | null;
  skills: string[];
  city: string | null;
}

const ScreeningPage = () => {
  const [loading, setLoading] = useState(false);
  const [resumes, setResumes] = useState<AgentEvaluatedResume[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });

  // 加载通过Agent评估的简历
  useEffect(() => {
    loadResumes();

    // 设置自动刷新，每30秒刷新一次
    const interval = setInterval(() => {
      loadResumes(pagination.current, pagination.pageSize);
    }, 30000); // 30秒

    return () => clearInterval(interval); // 清理定时器
  }, []);

  const loadResumes = async (page: number = 1, pageSize: number = 50) => {
    setLoading(true);
    try {
      const skip = (page - 1) * pageSize;
      // 只获取已评估且分数 >= 40（绿色和黄色）的简历
      const data = await getResumes({
        agent_evaluated: true,
        min_score: 40,
        skip,
        limit: pageSize,
      });

      // 过滤：只显示已评估的简历
      const filteredResumes = (data.items || []).filter(
        (r: AgentEvaluatedResume) => r.agent_score !== null && r.agent_score >= 40
      );

      setResumes(filteredResumes);
      setPagination({
        current: page,
        pageSize: pageSize,
        total: data.total || 0,
      });
    } catch (error) {
      message.error('加载简历列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (pagination: any) => {
    loadResumes(pagination.current, pagination.pageSize);
  };

  // 获取筛选状态标签颜色
  const getStatusColor = (_status: string | null, score: number | null) => {
    if (score === null) return 'default';
    if (score >= 70) return 'success';  // 绿色 - 可以发offer
    if (score >= 40) return 'warning';  // 黄色 - 待定
    return 'error';  // 红色 - 不合格
  };

  // 获取筛选状态文本
  const getStatusText = (_status: string | null, score: number | null) => {
    if (score === null) return '未评估';
    if (score >= 70) return '可以发offer';
    if (score >= 40) return '待定';
    return '不合格';
  };

  // 获取分数颜色
  const getScoreColor = (score: number | null) => {
    if (score === null) return '#999';
    if (score >= 70) return '#52c41a';  // 绿色
    if (score >= 40) return '#faad14';  // 黄色
    return '#f5222d';  // 红色
  };

  // 获取学历等级颜色
  const getEducationLevelColor = (level: string | null) => {
    if (!level) return 'default';
    const colorMap: Record<string, string> = {
      '985': 'red',
      '211': 'orange',
      'QS前50': 'purple',
      'QS前100': 'blue',
      'QS前200': 'cyan',
      '双非': 'default',
    };
    return colorMap[level] || 'default';
  };

  const columns: ColumnsType<AgentEvaluatedResume> = [
    {
      title: '候选人',
      dataIndex: 'candidate_name',
      key: 'candidate_name',
      width: 150,
      fixed: 'left' as const,
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
            <Tag color={JOB_CATEGORY_COLORS[record.job_category as keyof typeof JOB_CATEGORY_COLORS]} style={{ fontSize: 12 }}>
              {record.job_category}
            </Tag>
          ) : (
            <span style={{ color: '#999' }}>未分类</span>
          )}
          {record.city && (
            <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
              {record.city}
            </div>
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
            {record.education || '-'}
            {record.education_level && (
              <Tag color={getEducationLevelColor(record.education_level)} style={{ marginLeft: 4, fontSize: 11 }}>
                {record.education_level}
              </Tag>
            )}
          </div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {record.work_years || 0} 年工作经验
          </div>
        </div>
      ),
    },
    {
      title: '技能标签',
      dataIndex: 'skills',
      key: 'skills',
      width: 250,
      render: (skills: string[] = []) => {
        const displaySkills = skills.slice(0, 4);
        const remainingCount = skills.length - 4;
        return (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {displaySkills.map((skill, index) => (
              <Tag key={index} color="blue" style={{ fontSize: 11, marginBottom: 2 }}>
                {skill}
              </Tag>
            ))}
            {remainingCount > 0 && (
              <Tooltip title={skills.slice(4).join(', ')}>
                <Tag style={{ fontSize: 11, marginBottom: 2 }}>+{remainingCount}</Tag>
              </Tooltip>
            )}
          </div>
        );
      },
    },
    {
      title: 'Agent评分',
      key: 'agent_score',
      width: 120,
      render: (_: any, record: AgentEvaluatedResume) => (
        <div>
          {record.agent_score !== null ? (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{
                fontSize: 24,
                fontWeight: 'bold',
                color: getScoreColor(record.agent_score)
              }}>
                {record.agent_score}
              </span>
              <span style={{ fontSize: 14, color: '#999', marginLeft: 4 }}>分</span>
            </div>
          ) : (
            <span style={{ color: '#999' }}>未评估</span>
          )}
        </div>
      ),
    },
    {
      title: '筛选结果',
      key: 'screening_status',
      width: 120,
      render: (_: any, record: AgentEvaluatedResume) => {
        const score = record.agent_score;
        const status = record.screening_status;

        if (score === null) {
          return <Tag style={{ fontSize: 12 }}>未评估</Tag>;
        }

        return (
          <Tag color={getStatusColor(status, score)} style={{ fontSize: 13, fontWeight: 500 }}>
            {getStatusText(status, score)}
          </Tag>
        );
      },
    },
    {
      title: '评估时间',
      dataIndex: 'agent_evaluated_at',
      key: 'agent_evaluated_at',
      width: 160,
      render: (date: string | null) => {
        if (!date) return '-';
        const d = new Date(date);
        return d.toLocaleString('zh-CN');
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: AgentEvaluatedResume) => (
        <Button
          type="link"
          size="small"
          onClick={() => handleViewPdf(record.id)}
        >
          查看PDF
        </Button>
      ),
    },
  ];

  const handleViewPdf = (resumeId: string) => {
    // 在新窗口打开PDF
    window.open(`http://localhost:8000/api/v1/pdfs/${resumeId}`, '_blank');
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h2 style={{ margin: 0 }}>筛选结果</h2>
          <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
            只显示通过FastGPT Agent评估的简历（绿色和黄色）
          </div>
        </div>
        <Button
          type="default"
          icon={<ReloadOutlined />}
          onClick={() => loadResumes(pagination.current, pagination.pageSize)}
          loading={loading}
        >
          刷新
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={resumes}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            pageSizeOptions: ['20', '50', '100', '200'],
            showTotal: (total, range) =>
              `显示 ${range[0]}-${range[1]} 条，共 ${total} 条通过评估的简历`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          rowClassName={(record) => {
            const score = record.agent_score;
            if (score === null) return '';
            if (score >= 70) return 'row-pass';
            if (score >= 40) return 'row-review';
            return 'row-reject';
          }}
        />
      </Card>

      <style>{`
        .row-pass:hover {
          background-color: #f6ffed !important;
        }
        .row-review:hover {
          background-color: #fffbe6 !important;
        }
        .row-reject:hover {
          background-color: #fff1f0 !important;
        }
      `}</style>
    </div>
  );
};

export default ScreeningPage;
