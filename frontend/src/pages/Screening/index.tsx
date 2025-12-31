/** 筛选结果页面 - 显示所有简历的匹配结果 */
import { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, message, Tooltip } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { JOB_CATEGORY_LABELS, JOB_CATEGORY_COLORS } from '../../types';

interface ScreeningResult {
  id: string;
  resume_id: string;
  candidate_name: string;
  job_id: string;
  job_name: string;
  job_category: string;
  match_score: number;
  skill_score: number;
  experience_score: number;
  education_score: number;
  screening_result: 'PASS' | 'REVIEW' | 'REJECT';
  matched_points: string[];
  unmatched_points: string[];
  suggestion: string;
  created_at: string;
}

const ScreeningPage = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ScreeningResult[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });

  // 加载筛选结果
  useEffect(() => {
    loadResults();
  }, []);

  const loadResults = async (page: number = 1, pageSize: number = 50) => {
    setLoading(true);
    try {
      const skip = (page - 1) * pageSize;
      // 调用后端API获取筛选结果，传递分页参数
      const response = await fetch(`http://localhost:8000/api/v1/screening/results?skip=${skip}&limit=${pageSize}`);
      if (!response.ok) {
        throw new Error('获取筛选结果失败');
      }
      const data = await response.json();
      setResults(data.results || []);
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
    loadResults(pagination.current, pagination.pageSize);
  };

  // 获取筛选结果标签颜色
  const getResultColor = (result: string) => {
    switch (result) {
      case 'PASS':
        return 'success';
      case 'REVIEW':
        return 'warning';
      case 'REJECT':
        return 'error';
      default:
        return 'default';
    }
  };

  // 获取筛选结果文本
  const getResultText = (result: string) => {
    switch (result) {
      case 'PASS':
        return '通过';
      case 'REVIEW':
        return '待定';
      case 'REJECT':
        return '拒绝';
      default:
        return result;
    }
  };

  // 获取分数颜色
  const getScoreColor = (score: number) => {
    if (score >= 70) return '#52c41a';
    if (score >= 50) return '#faad14';
    return '#f5222d';
  };

  const columns: ColumnsType<ScreeningResult> = [
    {
      title: '候选人',
      dataIndex: 'candidate_name',
      key: 'candidate_name',
      width: 120,
      fixed: 'left' as const,
    },
    {
      title: '应聘岗位',
      key: 'job',
      width: 200,
      render: (_: any, record: ScreeningResult) => (
        <div>
          <div>
            <Tag color={JOB_CATEGORY_COLORS[record.job_category as keyof typeof JOB_CATEGORY_COLORS]} style={{ marginRight: 4 }}>
              {JOB_CATEGORY_LABELS[record.job_category as keyof typeof JOB_CATEGORY_LABELS]}
            </Tag>
            <span style={{ fontWeight: 500 }}>{record.job_name}</span>
          </div>
        </div>
      ),
    },
    {
      title: '匹配分数',
      key: 'scores',
      width: 280,
      render: (_: any, record: ScreeningResult) => (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
            <span style={{ fontSize: 12, color: '#999', width: 60 }}>总分：</span>
            <span style={{ fontSize: 18, fontWeight: 'bold', color: getScoreColor(record.match_score) }}>
              {record.match_score}分
            </span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            <span style={{ fontSize: 11, color: '#999' }}>
              技能: <span style={{ color: getScoreColor(record.skill_score) }}>{record.skill_score}</span>
            </span>
            <span style={{ fontSize: 11, color: '#999' }}>
              经验: <span style={{ color: getScoreColor(record.experience_score) }}>{record.experience_score}</span>
            </span>
            <span style={{ fontSize: 11, color: '#999' }}>
              学历: <span style={{ color: getScoreColor(record.education_score) }}>{record.education_score}</span>
            </span>
          </div>
        </div>
      ),
    },
    {
      title: '筛选结果',
      dataIndex: 'screening_result',
      key: 'screening_result',
      width: 100,
      render: (result: string) => (
        <Tag color={getResultColor(result)} style={{ fontSize: 12 }}>
          {getResultText(result)}
        </Tag>
      ),
    },
    {
      title: '匹配信息',
      key: 'match_points',
      width: 400,
      render: (_: any, record: ScreeningResult) => (
        <div>
          {/* 匹配的要点 */}
          {record.matched_points && record.matched_points.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 11, color: '#52c41a', fontWeight: 'bold', marginBottom: 4 }}>
                ✓ 匹配项 ({record.matched_points.length})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {record.matched_points.slice(0, 5).map((point, index) => (
                  <Tag key={index} color="success" style={{ fontSize: 11, margin: 0 }}>
                    {point}
                  </Tag>
                ))}
                {record.matched_points.length > 5 && (
                  <Tooltip title={record.matched_points.slice(5).join(', ')}>
                    <Tag style={{ fontSize: 11, margin: 0 }}>+{record.matched_points.length - 5}</Tag>
                  </Tooltip>
                )}
              </div>
            </div>
          )}

          {/* 未匹配的要点 */}
          {record.unmatched_points && record.unmatched_points.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: '#f5222d', fontWeight: 'bold', marginBottom: 4 }}>
                ✗ 未匹配项 ({record.unmatched_points.length})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {record.unmatched_points.slice(0, 5).map((point, index) => (
                  <Tag key={index} color="error" style={{ fontSize: 11, margin: 0 }}>
                    {point}
                  </Tag>
                ))}
                {record.unmatched_points.length > 5 && (
                  <Tooltip title={record.unmatched_points.slice(5).join(', ')}>
                    <Tag style={{ fontSize: 11, margin: 0 }}>+{record.unmatched_points.length - 5}</Tag>
                  </Tooltip>
                )}
              </div>
            </div>
          )}

          {/* 如果没有任何匹配信息 */}
          {(!record.matched_points || record.matched_points.length === 0) &&
           (!record.unmatched_points || record.unmatched_points.length === 0) && (
            <span style={{ fontSize: 12, color: '#999' }}>无匹配详情</span>
          )}
        </div>
      ),
    },
    {
      title: '建议',
      dataIndex: 'suggestion',
      key: 'suggestion',
      width: 350,
      render: (text: string) => (
        <Tooltip title={text} placement="topLeft">
          <div style={{
            fontSize: 12,
            color: '#666',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            maxHeight: 100,
            overflow: 'auto',
            lineHeight: 1.6
          }}>
            {text}
          </div>
        </Tooltip>
      ),
    },
    {
      title: '匹配时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => {
        if (!date) return '-';
        const d = new Date(date);
        return d.toLocaleString('zh-CN');
      },
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>筛选结果</h2>
        <Button
          type="default"
          icon={<ReloadOutlined />}
          onClick={() => loadResults(pagination.current, pagination.pageSize)}
          loading={loading}
        >
          刷新
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={results}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            pageSizeOptions: ['20', '50', '100', '200'],
            showTotal: (total) => `共 ${total} 条筛选结果`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1500 }}
        />
      </Card>
    </div>
  );
};

export default ScreeningPage;
