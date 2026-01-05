/** 筛选结果页面 - 只显示已配置FastGPT Agent的岗位类别（目前只有实施顾问） */
import { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, message, Tooltip } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { JOB_CATEGORY_COLORS } from '../../types';
import { getScreeningResults } from '../../services/api';

interface AgentEvaluatedResume {
  id: string | null;
  resume_id: string;
  candidate_name: string | null;
  candidate_email: string | null;
  candidate_phone: string | null;
  candidate_education: string | null;
  education_level?: string | null;  // 🔴 新增：学历等级（985/211/QS前50等）
  job_id: string | null;
  job_name: string;
  job_category: string;
  agent_score: number | null;  // Agent评分
  screening_result: string;  // "CAN_HIRE" | "PENDING" | "REJECTED" | "PENDING_REVIEW"
  matched_points: string[];
  unmatched_points: string[];
  suggestion: string;
  evaluated: boolean;  // 是否已评估
  created_at: string;
  // 为了兼容旧代码，添加字段映射
  phone?: string | null;
  email?: string | null;
  work_years?: number | null;
  skills?: string[];
  city?: string | null;
  screening_status?: string | null;  // 映射到screening_result
  agent_evaluated_at?: string | null;  // 映射到created_at
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
      // 🔴 修改：调用筛选结果API，只显示已配置FastGPT Agent的岗位类别（目前只有实施顾问）
      const data = await getScreeningResults({
        skip,
        limit: pageSize,
      });

      // 适配数据格式：results -> items
      const results = data.results || [];

      // 为了兼容旧代码，添加字段映射
      const adaptedResults = results.map((item: any) => ({
        ...item,
        phone: item.candidate_phone,
        email: item.candidate_email,
        screening_status: item.screening_result,  // 用screening_result作为screening_status
        agent_evaluated_at: item.created_at,  // 用created_at作为agent_evaluated_at
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
    if (score === null) return '待评估';
    if (score >= 70) return '可以进入面试';  // 🔴 修改：从"可以发offer"改为"可以进入面试"
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
            {record.candidate_education && record.education_level ? (
              <>
                {record.candidate_education}/{record.education_level}
              </>
            ) : record.candidate_education || '-'}
          </div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {record.work_years !== undefined ? record.work_years : 0} 年工作经验
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
      key: 'agent_score',
      width: 120,
      render: (_: any, record: AgentEvaluatedResume) => (
        <div>
          {record.agent_score !== null && record.agent_score !== undefined ? (
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
            <span style={{ color: '#999' }}>待评估</span>
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

        if (score === null || score === undefined) {
          return <Tag style={{ fontSize: 12 }}>待评估</Tag>;
        }

        return (
          <Tag color={getStatusColor(status || null, score)} style={{ fontSize: 13, fontWeight: 500 }}>
            {getStatusText(status || null, score)}
          </Tag>
        );
      },
    },
    {
      title: '评估时间',
      dataIndex: 'agent_evaluated_at',
      key: 'agent_evaluated_at',
      width: 160,
      render: (date: string | null | undefined) => {
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
          onClick={() => {
            // 🔴 修复：必须使用resume_id，而不是id（id是screening_result的ID）
            const resumeId = record.resume_id;
            if (resumeId) {
              handleViewPdf(resumeId);
            }
          }}
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
            只显示已配置FastGPT Agent的岗位类别（目前：实施顾问）
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
              `显示 ${range[0]}-${range[1]} 条，共 ${total} 条简历`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          rowClassName={(record) => {
            const score = record.agent_score;
            if (score === null || score === undefined) return '';
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
