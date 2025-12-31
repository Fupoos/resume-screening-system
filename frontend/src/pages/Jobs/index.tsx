/** 岗位管理页面 */
import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, Tag, InputNumber, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getJobs, createJob, updateJob, deleteJob } from '../../services/api';
import type { Job } from '../../types';
import { JOB_CATEGORY_LABELS, JOB_CATEGORY_COLORS } from '../../types';

const { Option } = Select;

const JobsPage = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [form] = Form.useForm();

  // 加载岗位列表
  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await getJobs();
      setJobs(data);
    } catch (error) {
      message.error('加载岗位列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  // 打开新增/编辑模态框
  const handleOpenModal = (job?: Job) => {
    if (job) {
      setEditingJob(job);
      form.setFieldsValue(job);
    } else {
      setEditingJob(null);
      form.resetFields();
    }
    setModalVisible(true);
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (editingJob) {
        // 编辑
        await updateJob(editingJob.id, values);
        message.success('岗位更新成功');
      } else {
        // 新增
        await createJob(values);
        message.success('岗位创建成功');
      }

      setModalVisible(false);
      loadJobs();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 删除岗位
  const handleDelete = async (id: string) => {
    try {
      await deleteJob(id);
      message.success('岗位删除成功');
      loadJobs();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 表格列定义
  const columns: ColumnsType<Job> = [
    {
      title: '岗位名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: Job['category']) => (
        <Tag color={JOB_CATEGORY_COLORS[category]}>
          {JOB_CATEGORY_LABELS[category]}
        </Tag>
      ),
    },
    {
      title: '必备技能',
      dataIndex: 'required_skills',
      key: 'required_skills',
      render: (skills: string[]) => (
        <>
          {skills.map((skill) => (
            <Tag key={skill}>{skill}</Tag>
          ))}
        </>
      ),
    },
    {
      title: '最低学历',
      dataIndex: 'min_education',
      key: 'min_education',
      width: 100,
    },
    {
      title: '最低年限',
      dataIndex: 'min_work_years',
      key: 'min_work_years',
      width: 100,
      render: (years: number) => `${years}年`,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'default'}>
          {active ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除?"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>岗位管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
          新增岗位
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={jobs}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
        scroll={{ x: 1200 }}
      />

      <Modal
        title={editingJob ? '编辑岗位' : '新增岗位'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
        okText="确认"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="岗位名称"
            name="name"
            rules={[{ required: true, message: '请输入岗位名称' }]}
          >
            <Input placeholder="例如：Python后端工程师" />
          </Form.Item>

          <Form.Item
            label="岗位类别"
            name="category"
            rules={[{ required: true, message: '请选择岗位类别' }]}
          >
            <Select placeholder="请选择">
              <Option value="hr">HR岗位</Option>
              <Option value="software">软件开发</Option>
              <Option value="finance">财务岗位</Option>
              <Option value="sales">销售岗位</Option>
            </Select>
          </Form.Item>

          <Form.Item label="岗位描述" name="description">
            <Input.TextArea rows={3} placeholder="请输入岗位描述" />
          </Form.Item>

          <Form.Item
            label="必备技能"
            name="required_skills"
            rules={[{ required: true, message: '请输入必备技能' }]}
            tooltip="多个技能用逗号分隔"
          >
            <Select
              mode="tags"
              placeholder="请输入必备技能，按回车添加"
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item label="加分技能" name="preferred_skills">
            <Select
              mode="tags"
              placeholder="请输入加分技能，按回车添加"
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item label="最低学历" name="min_education" initialValue="大专">
            <Select>
              <Option value="博士">博士</Option>
              <Option value="硕士">硕士</Option>
              <Option value="本科">本科</Option>
              <Option value="大专">大专</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="最低工作年限"
            name="min_work_years"
            initialValue={0}
          >
            <InputNumber min={0} max={30} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default JobsPage;
