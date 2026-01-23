/** 人工审核页面 - 处理无法自动解析的简历（加密PDF/扫描件/图片简历） */
import { useState, useEffect, useRef } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  message,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Descriptions,
  Tooltip,
  Alert,
  Spin,
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { getResumes, deleteResume, updateResume, getResume } from '../../services/api';
import type { Resume } from '../../types';
import { SkillsDisplay } from '../../components/SkillsDisplay';
import { renderAsync } from 'docx-preview';

const { TextArea } = Input;

const ManualReviewPage = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentResume, setCurrentResume] = useState<Resume | null>(null);
  const [editForm] = Form.useForm();
  const [docxLoading, setDocxLoading] = useState(false);
  const docxContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadResumes();
  }, []);

  // 加载DOCX预览
  useEffect(() => {
    const loadDocxPreview = async () => {
      if (!detailModalVisible || !currentResume) {
        // 清空容器
        if (docxContainerRef.current) {
          docxContainerRef.current.innerHTML = '';
        }
        return;
      }

      // 只处理DOCX文件
      if ((currentResume as any).file_type === 'docx' || (currentResume as any).file_type === 'doc') {
        const container = docxContainerRef.current;
        if (!container) return;

        setDocxLoading(true);
        try {
          // 获取DOCX文件
          const response = await fetch(`http://localhost:8000/api/v1/pdfs/${currentResume.id}`);
          if (!response.ok) {
            throw new Error('无法获取文件');
          }

          const arrayBuffer = await response.arrayBuffer();

          // 渲染DOCX
          await renderAsync(arrayBuffer, container, undefined, {
            className: 'docx-preview',
            inWrapper: true,
          });

          // 添加样式优化
          const style = document.createElement('style');
          style.textContent = `
            .docx-preview { padding: 20px; }
            .docx-wrapper { background: white; }
            section.docx { margin-bottom: 0; box-shadow: none; }
          `;
          container.appendChild(style);
        } catch (error) {
          console.error('DOCX预览失败:', error);
          container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999;">预览失败，请下载后查看</div>';
        } finally {
          setDocxLoading(false);
        }
      }
    };

    loadDocxPreview();
  }, [detailModalVisible, currentResume]);

  const loadResumes = async (page = 1, pageSize = 50) => {
    setLoading(true);
    try {
      const skip = (page - 1) * pageSize;
      const data = await getResumes({
        limit: pageSize,
        skip: skip,
        needs_review_only: true
      });
      setResumes(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      message.error('加载待审核简历失败');
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

  // 查看详情
  const handleViewDetail = async (resume: Resume) => {
    try {
      const detailData = await getResume(resume.id);
      setCurrentResume(detailData);
      setDetailModalVisible(true);
    } catch (error) {
      message.error('获取简历详情失败');
      setCurrentResume(resume);
      setDetailModalVisible(true);
    }
  };

  // 编辑简历
  const handleEdit = async (resume: Resume) => {
    try {
      const detailData = await getResume(resume.id);
      setCurrentResume(detailData);
      editForm.setFieldsValue({
        candidate_name: detailData.candidate_name || '',
        phone: detailData.phone || '',
        email: detailData.email || '',
        education: detailData.education || '',
        work_years: detailData.work_years || 0,
        skills: (detailData.skills || []).join(', '),
      });
      setEditModalVisible(true);
    } catch (error) {
      message.error('获取简历信息失败');
    }
  };

  // 保存编辑
  const handleSaveEdit = async () => {
    try {
      const values = await editForm.validateFields();
      const skills = values.skills
        ? values.skills.split(',').map((s: string) => s.trim()).filter(Boolean)
        : [];

      await updateResume(currentResume!.id, {
        candidate_name: values.candidate_name,
        phone: values.phone,
        email: values.email,
        education: values.education,
        work_years: values.work_years,
        skills,
      });

      message.success('简历更新成功');
      setEditModalVisible(false);
      handleRefresh();
    } catch (error) {
      message.error('保存失败');
    }
  };

  // 删除简历
  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这份简历吗？删除后无法恢复。',
      icon: <ExclamationCircleOutlined />,
      okText: '确定',
      cancelText: '取消',
      okButtonProps: { danger: true },
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
            {(record as any).file_type?.toUpperCase() || '未知'}
          </div>
        </div>
      ),
    },
    {
      title: '文本长度',
      key: 'text_length',
      width: 100,
      render: (_: any, record: Resume) => {
        const length = (record as any).raw_text_length || 0;
        const color = length === 0 ? 'red' : length < 100 ? 'orange' : 'green';
        return <Tag color={color}>{length} 字符</Tag>;
      },
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
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => (
        <div style={{ fontSize: 12 }}>
          {date ? new Date(date).toLocaleString('zh-CN') : '-'}
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 240,
      fixed: 'right' as const,
      render: (_: any, record: Resume) => (
        <Space size="small">
          {(record as any).file_type === 'pdf' && (
            <Tooltip title="查看PDF">
              <Button
                type="link"
                size="small"
                onClick={() => window.open(`http://localhost:8000/api/v1/pdfs/${record.id}#zoom=175`, '_blank')}
              >
                查看PDF
              </Button>
            </Tooltip>
          )}
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="编辑信息">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
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
      <Alert
        message="人工审核"
        description="此处显示无法自动解析的简历（如加密PDF、扫描件、图片格式等）。请查看原始文件后手动补充候选人信息。"
        type="info"
        showIcon
        closable
        style={{ marginBottom: 16 }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h2 style={{ margin: 0 }}>人工审核</h2>
          <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
            共 {total} 份简历需要人工处理
          </div>
        </div>
        <Space>
          <Button
            type="default"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
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
            pageSizeOptions: ['20', '50', '100'],
            showTotal: (total) => `共 ${total} 份简历`,
            onChange: handleTableChange,
          }}
          scroll={{ x: 1100 }}
        />
      </Card>

      {/* 编辑弹窗 */}
      <Modal
        title="编辑简历信息"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        onOk={handleSaveEdit}
        okText="保存"
        cancelText="取消"
        width={600}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item
            label="姓名"
            name="candidate_name"
            rules={[{ required: true, message: '请输入候选人姓名' }]}
          >
            <Input placeholder="请输入候选人姓名" />
          </Form.Item>

          <Form.Item label="手机号" name="phone">
            <Input placeholder="请输入手机号" />
          </Form.Item>

          <Form.Item label="邮箱" name="email">
            <Input placeholder="请输入邮箱" />
          </Form.Item>

          <Form.Item label="学历" name="education">
            <Select placeholder="请选择学历" allowClear>
              <Select.Option value="博士">博士</Select.Option>
              <Select.Option value="硕士">硕士</Select.Option>
              <Select.Option value="本科">本科</Select.Option>
              <Select.Option value="大专">大专</Select.Option>
              <Select.Option value="高中">高中</Select.Option>
              <Select.Option value="其他">其他</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="工作年限" name="work_years">
            <InputNumber min={0} max={50} style={{ width: '100%' }} placeholder="请输入工作年限" />
          </Form.Item>

          <Form.Item label="技能标签" name="skills">
            <TextArea
              rows={3}
              placeholder="请输入技能标签，用逗号分隔（如：Java, Python, Spring）"
            />
          </Form.Item>
        </Form>

        {currentResume && (currentResume as any).raw_text_length !== undefined && (
          <Alert
            message={`提示：原始文本仅 ${(currentResume as any).raw_text_length} 字符，可能是加密文件或扫描件`}
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Modal>

      {/* 详情弹窗 */}
      <Modal
        title="简历详情"
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          // 清空DOCX容器
          if (docxContainerRef.current) {
            docxContainerRef.current.innerHTML = '';
          }
        }}
        footer={[
          <Button key="close" onClick={() => {
            setDetailModalVisible(false);
            // 清空DOCX容器
            if (docxContainerRef.current) {
              docxContainerRef.current.innerHTML = '';
            }
          }}>
            关闭
          </Button>,
          <Button
            key="edit"
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              setDetailModalVisible(false);
              handleEdit(currentResume!);
            }}
          >
            编辑信息
          </Button>,
        ]}
        width={1000}
        style={{ top: 20 }}
      >
        {currentResume && (
          <div>
            <Descriptions title="基本信息" column={2} bordered size="small">
              <Descriptions.Item label="姓名">{currentResume.candidate_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="文件类型">
                <Tag>{(currentResume as any).file_type?.toUpperCase() || '未知'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="手机">{currentResume.phone || '-'}</Descriptions.Item>
              <Descriptions.Item label="邮箱">{currentResume.email || '-'}</Descriptions.Item>
              <Descriptions.Item label="学历">{currentResume.education || '-'}</Descriptions.Item>
              <Descriptions.Item label="工作年限">{currentResume.work_years || 0}年</Descriptions.Item>
            </Descriptions>

            {/* PDF/DOCX 预览区域 */}
            {(currentResume as any).file_type === 'pdf' && (
              <div style={{ marginTop: 16 }}>
                <h4>原始文件预览</h4>
                <div
                  style={{
                    height: 'calc(100vh - 250px)',
                    minHeight: 750,
                    border: '1px solid #e8e8e8',
                    borderRadius: 8,
                    overflow: 'hidden',
                    backgroundColor: '#f5f5f5'
                  }}
                >
                  <iframe
                    src={`http://localhost:8000/api/v1/pdfs/${currentResume.id}#zoom=175`}
                    style={{ width: '100%', height: '100%', border: 'none' }}
                    title="简历PDF预览"
                  />
                </div>
              </div>
            )}

            {(currentResume as any).file_type === 'docx' && (
              <div style={{ marginTop: 16 }}>
                <h4>原始文件预览</h4>
                <div
                  style={{
                    height: 'calc(100vh - 250px)',
                    minHeight: 750,
                    border: '1px solid #e8e8e8',
                    borderRadius: 8,
                    overflow: 'auto',
                    backgroundColor: '#fff'
                  }}
                >
                  {docxLoading ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                      <Spin tip="正在加载DOCX预览..." />
                    </div>
                  ) : (
                    <div
                      ref={docxContainerRef}
                      style={{ width: '100%', height: '100%' }}
                    />
                  )}
                </div>
              </div>
            )}

            <div style={{ marginTop: 16 }}>
              <h4>技能标签</h4>
              <SkillsDisplay skills={currentResume.skills || []} maxDisplay={50} />
            </div>

            {(currentResume as any).raw_text && (currentResume as any).raw_text.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>原始文本 ({(currentResume as any).raw_text?.length || 0} 字符)</h4>
                <div
                  style={{
                    background: '#f5f5f5',
                    padding: 12,
                    borderRadius: 6,
                    maxHeight: 200,
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    fontSize: 12,
                    border: '1px solid #e8e8e8'
                  }}
                >
                  {(currentResume as any).raw_text}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ManualReviewPage;
