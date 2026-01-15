/** 简历列表页面 - 显示所有导入的简历及其最佳匹配 - v2 */
import { useState, useEffect, useMemo } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Upload,
  message,
  Modal,
  Descriptions,
  Spin,
  Tooltip,
  Tabs,
  Radio,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  InboxOutlined,
  SyncOutlined,
  ReloadOutlined,
  CloudDownloadOutlined,
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { getResumes, deleteResume, importHistoricalEmails, markResumeForReview } from '../../services/api';
import type { Resume } from '../../types';
import { SkillsDisplay } from '../../components/SkillsDisplay';

const { Dragger } = Upload;

const ResumesPage = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [checkingEmail, setCheckingEmail] = useState(false);
  const [polling, setPolling] = useState(false);
  const [importingHistorical, setImportingHistorical] = useState(false);
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [rawTextExpanded, setRawTextExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState('parsed'); // 'parsed' | 'pdf' | 'raw'
  const [timeRange, setTimeRange] = useState<string>('all'); // 'all' | 'today' | 'this_week' | 'this_month'
  const [timeStats, setTimeStats] = useState({ today: 0, thisWeek: 0, thisMonth: 0, all: 0 });
  const [sortField, setSortField] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<'ascend' | 'descend' | null>('descend');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  // 加载简历列表
  useEffect(() => {
    handleRefresh();
  }, []);

  // 监听时间范围变化
  useEffect(() => {
    loadResumes(1, 50);
  }, [timeRange]);

  // 学历等级颜色映射
  const getEducationLevelColor = (level: string) => {
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

  // 时间标签函数
  const getTimeLabel = (createdAt: string) => {
    if (!createdAt) return { text: '-', color: 'default' };

    const date = new Date(createdAt);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const thisWeekStart = new Date(today);
    thisWeekStart.setDate(today.getDate() - today.getDay()); // 周日作为本周开始
    const thisMonthStart = new Date(now.getFullYear(), now.getMonth(), 1);

    if (date >= today) {
      return { text: '今天', color: 'red' };
    } else if (date >= thisWeekStart) {
      return { text: '本周', color: 'gold' };
    } else if (date >= thisMonthStart) {
      return { text: '本月', color: 'blue' };
    } else {
      // 显示具体日期
      return {
        text: `${date.getMonth() + 1}-${date.getDate()}`,
        color: 'default'
      };
    }
  };

  // 格式化完整时间
  const formatDateTime = (dateStr: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
  };

  // 获取各时间范围的统计数据
  const fetchTimeStats = async () => {
    try {
      // 获取全部数量
      const allData = await getResumes({ limit: 1, exclude_needs_review: true });
      const allTotal = allData.total || 0;

      // 获取今天的数量
      const todayData = await getResumes({ limit: 1, time_range: 'today', exclude_needs_review: true });
      const todayTotal = todayData.total || 0;

      // 获取本周的数量
      const weekData = await getResumes({ limit: 1, time_range: 'this_week', exclude_needs_review: true });
      const weekTotal = weekData.total || 0;

      // 获取本月的数量
      const monthData = await getResumes({ limit: 1, time_range: 'this_month', exclude_needs_review: true });
      const monthTotal = monthData.total || 0;

      setTimeStats({
        all: allTotal,
        today: todayTotal,
        thisWeek: weekTotal,
        thisMonth: monthTotal
      });
    } catch (error) {
      console.error('获取统计数据失败:', error);
    }
  };

  const loadResumes = async (page = 1, pageSize = 100) => {
    setLoading(true);
    try {
      // 计算跳过数量
      const skip = (page - 1) * pageSize;
      // 获取可解析的简历（排除需要人工审核的，即文本少于100字符的）
      const params: any = { limit: pageSize, skip: skip, exclude_needs_review: true };
      // 添加时间范围筛选
      if (timeRange !== 'all') {
        params.time_range = timeRange;
      }
      const data = await getResumes(params);
      setResumes(data.items || []);
      setTotal(data.total || 0);

      // 同时更新统计数据
      fetchTimeStats();
    } catch (error) {
      message.error('加载简历列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (page: number, size: number) => {
    setCurrentPage(page);
    setPageSize(size);
    loadResumes(page, size);
  };

  // 对数据进行排序
  const sortedResumes = useMemo(() => {
    const sorted = [...resumes];
    if (sortField && sortOrder) {
      sorted.sort((a, b) => {
        let compareResult = 0;
        switch (sortField) {
          case 'candidate_name':
            const nameA = a.candidate_name || '';
            const nameB = b.candidate_name || '';
            compareResult = nameA.localeCompare(nameB, 'zh-CN');
            break;
          case 'created_at':
            const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
            const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
            compareResult = timeA - timeB;
            break;
          default:
            break;
        }
        return sortOrder === 'ascend' ? compareResult : -compareResult;
      });
    }
    return sorted;
  }, [resumes, sortField, sortOrder]);

  const handleRefresh = () => {
    loadResumes(1, 50);
  };

  // 时间范围变化处理
  const handleTimeRangeChange = (e: any) => {
    setTimeRange(e.target.value);
  };

  // 导入历史邮件
  const handleImportHistorical = async () => {
    setImportingHistorical(true);
    try {
      const result = await importHistoricalEmails(1000);
      message.success(result.message || '历史邮件导入已启动');

      // 启动轮询刷新机制（每10秒刷新一次，持续5分钟）
      setPolling(true);
      let pollCount = 0;
      const maxPolls = 30; // 30次 * 10秒 = 5分钟

      const pollInterval = setInterval(async () => {
        pollCount++;
        await handleRefresh();

        if (pollCount >= maxPolls) {
          clearInterval(pollInterval);
          setPolling(false);
          message.info('自动刷新结束');
        }
      }, 10000);

    } catch (error) {
      message.error('导入历史邮件失败');
      setPolling(false);
    } finally {
      setImportingHistorical(false);
    }
  };

  const handleCheckEmail = async () => {
    setCheckingEmail(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/email/trigger-check', {
        method: 'POST',
      });
      const result = await response.json();
      message.success(result.message || '邮箱检查已启动');

      // 启动轮询刷新机制（每5秒刷新一次，持续60秒）
      setPolling(true);
      let pollCount = 0;
      const maxPolls = 12; // 12次 * 5秒 = 60秒

      const pollInterval = setInterval(async () => {
        pollCount++;
        await handleRefresh();

        if (pollCount >= maxPolls) {
          clearInterval(pollInterval);
          setPolling(false);
          message.info('自动刷新结束');
        }
      }, 5000);

      // 立即刷新一次
      setTimeout(() => {
        message.info('正在刷新简历列表...');
        handleRefresh();
      }, 3000);

    } catch (error) {
      message.error('触发邮箱检查失败');
      setPolling(false);
    } finally {
      setCheckingEmail(false);
    }
  };

  // 上传简历
  const handleUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options;
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file as File);
      formData.append('auto_match', 'true');

      // 直接调用API
      const response = await fetch('http://localhost:8000/api/v1/resumes/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('上传失败');
      }

      const result = await response.json();

      message.success('简历上传成功！');
      onSuccess?.(result);
      setUploadModalVisible(false);
      handleRefresh();
    } catch (error) {
      message.error('上传简历失败');
      onError?.(error as Error);
    } finally {
      setUploading(false);
    }
  };

  // 删除简历
  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这份简历吗？删除后无法恢复。',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteResume(id);
          message.success('删除成功');
          handleRefresh();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  // 查看详情
  const handleViewDetail = async (resume: Resume) => {
    try {
      // 通过API获取完整的简历详情（包含raw_text）
      const response = await fetch(`http://localhost:8000/api/v1/resumes/${resume.id}`);
      if (!response.ok) {
        throw new Error('获取简历详情失败');
      }
      const detailData = await response.json();
      setSelectedResume(detailData);
      setDetailVisible(true);
    } catch (error) {
      message.error('获取简历详情失败');
      // 如果获取失败，使用列表中的数据
      setSelectedResume(resume);
      setDetailVisible(true);
    }
  };

  // 标记为需要人工审核
  const handleMarkForReview = async (id: string, name: string) => {
    try {
      await markResumeForReview(id);
      message.success(`已将"${name}"标记为需要人工审核`);
      handleRefresh();
    } catch (error) {
      message.error('标记失败');
    }
  };

  const columns = [
    {
      title: '候选人',
      dataIndex: 'candidate_name',
      key: 'candidate_name',
      width: 120,
      sorter: (a: Resume, b: Resume) => {
        const nameA = a.candidate_name || '';
        const nameB = b.candidate_name || '';
        return nameA.localeCompare(nameB, 'zh-CN');
      },
      sortOrder: sortField === 'candidate_name' ? sortOrder : null,
      render: (name: string, record: Resume) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{name || '未命名'}</div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {record.education}
            {(record as any).education_level && (
              <Tag color={getEducationLevelColor((record as any).education_level)} style={{ marginLeft: 4, fontSize: 11 }}>
                {(record as any).education_level}
              </Tag>
            )}
            · {record.work_years || 0}年
          </div>
        </div>
      ),
    },
    {
      title: '联系方式',
      key: 'contact',
      width: 180,
      render: (_: any, record: Resume) => (
        <div>
          <div>{record.phone || '-'}</div>
          <div style={{ fontSize: 12, color: '#999' }}>{record.email || '-'}</div>
        </div>
      ),
    },
    {
      title: '技能标签',
      dataIndex: 'skills',
      key: 'skills',
      width: 300,
      render: (skills: string[]) => (
        <SkillsDisplay skills={skills || []} maxDisplay={4} />
      ),
    },
    {
      title: '接收时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 100,
      sorter: (a: Resume, b: Resume) => {
        const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return timeA - timeB;
      },
      sortOrder: sortField === 'created_at' ? sortOrder : null,
      render: (createdAt: string) => {
        const label = getTimeLabel(createdAt);
        return (
          <Tooltip title={formatDateTime(createdAt)}>
            <Tag color={label.color}>{label.text}</Tag>
          </Tooltip>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      fixed: 'right' as const,
      render: (_: any, record: Resume) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="标记待审核">
            <Button
              type="link"
              size="small"
              onClick={() => handleMarkForReview(record.id, record.candidate_name || '未命名')}
            >
              标记待审核
            </Button>
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h2 style={{ margin: 0 }}>简历管理</h2>
          {polling && (
            <div style={{ fontSize: 12, color: '#1890ff', marginTop: 4 }}>
              <SyncOutlined spin /> 自动刷新中...
            </div>
          )}
          {/* 时间筛选器 */}
          <div style={{ marginTop: 12 }}>
            <Space size="middle">
              <span style={{ color: '#666' }}>筛选:</span>
              <Radio.Group value={timeRange} onChange={handleTimeRangeChange} buttonStyle="solid">
                <Radio.Button value="all">全部 <span style={{ color: '#1890ff' }}>({timeStats.all})</span></Radio.Button>
                <Radio.Button value="today">今天 <span style={{ color: '#ff4d4f' }}>({timeStats.today})</span></Radio.Button>
                <Radio.Button value="this_week">本周 <span style={{ color: '#faad14' }}>({timeStats.thisWeek})</span></Radio.Button>
                <Radio.Button value="this_month">本月 <span style={{ color: '#1890ff' }}>({timeStats.thisMonth})</span></Radio.Button>
              </Radio.Group>
            </Space>
          </div>
        </div>
        <Space>
          <Button
            type="default"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          >
            刷新列表
          </Button>
          <Button
            type="default"
            icon={<SyncOutlined />}
            onClick={handleCheckEmail}
            loading={checkingEmail}
          >
            检查邮箱
          </Button>
          <Button
            type="default"
            icon={<CloudDownloadOutlined />}
            onClick={handleImportHistorical}
            loading={importingHistorical}
          >
            导入历史邮件
          </Button>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setUploadModalVisible(true)}
          >
            导入简历
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={sortedResumes}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            pageSizeOptions: ['20', '50', '100', '200', '500'],
            showTotal: (total) => `共 ${total} 份简历`,
          }}
          onChange={(newPagination, _filters, sorter) => {
            // 处理排序（前端排序）
            if (sorter && !Array.isArray(sorter)) {
              setSortField(sorter.field as string);
              setSortOrder((sorter.order as 'ascend' | 'descend' | null));
            }
            // 只在分页变化时重新加载数据
            const pageChanged = newPagination.current !== currentPage;
            const pageSizeChanged = newPagination.pageSize !== pageSize;
            if (pageChanged || pageSizeChanged) {
              handleTableChange(newPagination.current || 1, newPagination.pageSize || 50);
            }
          }}
        />
      </Card>

      {/* 上传简历弹窗 */}
      <Modal
        title="导入简历"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <Dragger
          name="file"
          multiple={false}
          accept=".pdf,.docx,.doc"
          customRequest={handleUpload}
          disabled={uploading}
          showUploadList={false}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持 PDF 和 DOCX 格式，上传后将自动解析并匹配所有岗位
          </p>
        </Dragger>

        {uploading && (
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <Spin tip="正在解析简历并自动匹配..." />
          </div>
        )}
      </Modal>

      {/* 简历详情弹窗 */}
      <Modal
        title="简历详情"
        open={detailVisible}
        onCancel={() => {
          setDetailVisible(false);
          setRawTextExpanded(false); // 重置展开状态
          setActiveTab('parsed'); // 重置Tab
        }}
        footer={null}
        width={1400}
      >
        {selectedResume && (
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'parsed',
                label: '解析信息',
                children: (
                  <div>
                    <Descriptions title="基本信息" column={2} bordered size="small">
                      <Descriptions.Item label="姓名">{selectedResume.candidate_name || '-'}</Descriptions.Item>
                      <Descriptions.Item label="性别">-</Descriptions.Item>
                      <Descriptions.Item label="手机">{selectedResume.phone || '-'}</Descriptions.Item>
                      <Descriptions.Item label="邮箱">{selectedResume.email || '-'}</Descriptions.Item>
                      <Descriptions.Item label="学历">
                        <Space>
                          {selectedResume.education || '-'}
                          {(selectedResume as any).education_level && (
                            <Tag color={getEducationLevelColor((selectedResume as any).education_level)}>
                              {(selectedResume as any).education_level}
                            </Tag>
                          )}
                        </Space>
                      </Descriptions.Item>
                      <Descriptions.Item label="工作年限">{selectedResume.work_years || 0}年</Descriptions.Item>
                    </Descriptions>

                    {(selectedResume.source_email_subject || selectedResume.source_sender) && (
                      <Descriptions title="邮件来源" column={1} bordered size="small" style={{ marginTop: 16 }}>
                        {selectedResume.source_email_subject && (
                          <Descriptions.Item label="邮件主题">
                            {selectedResume.source_email_subject}
                          </Descriptions.Item>
                        )}
                        {selectedResume.source_sender && (
                          <Descriptions.Item label="发件人">
                            {selectedResume.source_sender}
                          </Descriptions.Item>
                        )}
                      </Descriptions>
                    )}

                    <div style={{ marginTop: 16 }}>
                      <h4>技能标签</h4>
                      <SkillsDisplay skills={selectedResume.skills || []} maxDisplay={50} />
                    </div>
                  </div>
                ),
              },
              {
                key: 'pdf',
                label: '原始文件',
                children: (
                  <div style={{ height: '800px', border: '1px solid #e8e8e8', borderRadius: 8, overflow: 'hidden' }}>
                    {selectedResume.file_type === 'pdf' ? (
                      // PDF直接预览，宽度100%自适应
                      <iframe
                        src={`http://localhost:8000/api/v1/pdfs/${selectedResume.id}#view=FitH`}
                        style={{ width: '100%', height: '100%', border: 'none' }}
                        title="简历PDF"
                      />
                    ) : selectedResume.file_type === 'docx' || selectedResume.file_type === 'doc' ? (
                      // DOCX使用后端preview端点预览
                      <iframe
                        src={`http://localhost:8000/api/v1/pdfs/${selectedResume.id}/preview`}
                        style={{ width: '100%', height: '100%', border: 'none' }}
                        title="简历DOCX"
                      />
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#999' }}>
                        暂不支持预览此文件类型
                      </div>
                    )}
                  </div>
                ),
              },
              {
                key: 'raw',
                label: '原始文本',
                children: (selectedResume as any).raw_text ? (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <Space>
                        {selectedResume.file_type === 'email_body' && (
                          <Tag color="blue">邮件正文</Tag>
                        )}
                        {selectedResume.file_type && selectedResume.file_type !== 'email_body' && (
                          <Tag color="green">
                            {selectedResume.file_type.toUpperCase()}文件
                          </Tag>
                        )}
                        <span style={{ fontSize: 12, color: '#999' }}>
                          {(selectedResume as any).raw_text?.length || 0} 字符
                        </span>
                      </Space>
                      <Button
                        type="link"
                        size="small"
                        onClick={() => setRawTextExpanded(!rawTextExpanded)}
                      >
                        {rawTextExpanded ? '收起' : '展开全部'}
                      </Button>
                    </div>
                    <div
                      style={{
                        background: '#f5f5f5',
                        padding: 16,
                        borderRadius: 8,
                        maxHeight: rawTextExpanded ? 800 : 400,
                        overflow: 'auto',
                        whiteSpace: 'pre-wrap',
                        fontSize: 13,
                        lineHeight: 1.8,
                        fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                        border: '1px solid #e8e8e8'
                      }}
                    >
                      {(selectedResume as any).raw_text}
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>暂无原始文本</div>
                ),
              },
            ]}
          />
        )}
      </Modal>
    </div>
  );
};

export default ResumesPage;
