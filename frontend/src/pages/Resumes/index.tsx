/** 简历列表页面 - 显示所有导入的简历及其最佳匹配 - v2 */
import { useState, useEffect } from 'react';
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
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  InboxOutlined,
  SyncOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { getResumes, deleteResume } from '../../services/api';
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
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [rawTextExpanded, setRawTextExpanded] = useState(false);

  // 加载简历列表
  useEffect(() => {
    handleRefresh();
  }, []);

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

  const loadResumes = async (page = 1, pageSize = 100) => {
    setLoading(true);
    try {
      // 计算跳过数量
      const skip = (page - 1) * pageSize;
      // 只获取PDF类型的简历
      const data = await getResumes({ limit: pageSize, skip: skip, file_type: 'pdf' });
      setResumes(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      message.error('加载简历列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (page: number, pageSize: number) => {
    loadResumes(page, pageSize);
  };

  const handleRefresh = () => {
    loadResumes(1, 50);
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

  const columns = [
    {
      title: '候选人',
      dataIndex: 'candidate_name',
      key: 'candidate_name',
      width: 120,
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
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const statusMap: Record<string, { text: string; color: string }> = {
          pending: { text: '待处理', color: 'default' },
          parsed: { text: '已解析', color: 'processing' },
          processed: { text: '已完成', color: 'success' },
        };
        const info = statusMap[status] || { text: status, color: 'default' };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
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
              <SyncOutlined spin /> 自动刷新中... (每5秒更新一次)
            </div>
          )}
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
          dataSource={resumes}
          rowKey="id"
          loading={loading}
          pagination={{
            total: total,
            pageSize: 50,
            showSizeChanger: true,
            pageSizeOptions: ['20', '50', '100', '200', '500'],
            showTotal: (total) => `共 ${total} 份简历`,
            onChange: handleTableChange,
          }}
          scroll={{ x: 1200 }}
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
        }}
        footer={null}
        width={800}
      >
        {selectedResume && (
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

            {(selectedResume as any).raw_text && (
              <div style={{ marginTop: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <h4 style={{ margin: 0 }}>
                    原始文本
                    {selectedResume.file_type === 'email_body' && (
                      <Tag color="blue" style={{ marginLeft: 8 }}>邮件正文</Tag>
                    )}
                    {selectedResume.file_type && selectedResume.file_type !== 'email_body' && (
                      <Tag color="green" style={{ marginLeft: 8 }}>
                        {selectedResume.file_type.toUpperCase()}文件
                      </Tag>
                    )}
                  </h4>
                  <Space>
                    <span style={{ fontSize: 12, color: '#999' }}>
                      {(selectedResume as any).raw_text?.length || 0} 字符
                    </span>
                    <Button
                      type="link"
                      size="small"
                      onClick={() => setRawTextExpanded(!rawTextExpanded)}
                    >
                      {rawTextExpanded ? '收起' : '展开全部'}
                    </Button>
                  </Space>
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
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ResumesPage;
