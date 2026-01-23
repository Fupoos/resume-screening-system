/**
 * 多来源批量上传简历弹窗组件
 * 支持：本地文件上传、URL下载、ZIP压缩包上传
 * 最大支持1000个文件
 */
import { useState } from 'react';
import { Modal, Upload, Button, Tabs, Input, message, Progress, Alert, Tag, Divider } from 'antd';
import { InboxOutlined, UploadOutlined, LinkOutlined, FileZipOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { multiSourceUploadResumes } from '../services/api';

const { Dragger } = Upload;
const { TextArea } = Input;

interface MultiSourceUploadModalProps {
  visible: boolean;
  onClose: () => void;
  onComplete: () => void;
}

export const MultiSourceUploadModal = ({ visible, onClose, onComplete }: MultiSourceUploadModalProps) => {
  const [uploading, setUploading] = useState(false);
  const [localFiles, setLocalFiles] = useState<File[]>([]);
  const [urls, setUrls] = useState('');
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);

  // 重置状态
  const resetState = () => {
    setLocalFiles([]);
    setUrls('');
    setZipFile(null);
    setUploadResult(null);
    setUploading(false);
  };

  const handleClose = () => {
    if (!uploading) {
      resetState();
      onClose();
    }
  };

  // 处理本地文件选择
  const handleLocalFileChange: UploadProps['onChange'] = ({ fileList }) => {
    const validFiles = fileList
      .filter(file => file.status !== 'removed')
      .map(file => file.originFileObj as File)
      .filter(file => {
        const ext = file.name.split('.').pop()?.toLowerCase();
        return ext === 'pdf' || ext === 'docx' || ext === 'doc';
      });

    // 限制1000个文件
    if (validFiles.length > 1000) {
      message.warning('最多支持上传1000个文件');
      setLocalFiles(validFiles.slice(0, 1000));
    } else {
      setLocalFiles(validFiles);
    }
  };

  // 处理ZIP文件选择
  const handleZipFileChange: UploadProps['onChange'] = ({ file }) => {
    const f = file.originFileObj as File;
    if (f) {
      const ext = f.name.split('.').pop()?.toLowerCase();
      if (ext === 'zip') {
        setZipFile(f);
      } else {
        message.error('只支持ZIP压缩包格式');
      }
    }
  };

  // 上传处理
  const handleUpload = async () => {
    if (localFiles.length === 0 && !urls.trim() && !zipFile) {
      message.warning('请选择至少一种上传方式');
      return;
    }

    // 检查总数
    let estimatedTotal = localFiles.length;
    if (urls.trim()) {
      try {
        const urlList = JSON.parse(urls);
        estimatedTotal += urlList.length;
      } catch {
        message.error('URL格式错误，请输入JSON数组格式');
        return;
      }
    }
    if (zipFile) {
      message.info('ZIP文件将自动解压，解压后的文件会计入总数限制');
    }

    if (estimatedTotal === 0) {
      message.warning('请选择要上传的文件');
      return;
    }

    if (estimatedTotal > 1000) {
      message.warning(`预计上传${estimatedTotal}个文件，超过1000个限制`);
      return;
    }

    setUploading(true);

    try {
      const urlList = urls.trim() ? JSON.parse(urls) : null;

      const result = await multiSourceUploadResumes({
        files: localFiles.length > 0 ? localFiles : undefined,
        urls: urlList,
        zipFile: zipFile || undefined,
      });

      setUploadResult(result);

      if (result.results?.overall?.exceeded) {
        message.error(`文件总数超过限制: ${result.results.overall.total}`);
      } else {
        const totalSuccess = result.results?.overall?.success || 0;
        const totalFailed = result.results?.overall?.failed || 0;

        if (totalFailed === 0) {
          message.success(`上传完成！成功处理 ${totalSuccess} 个文件`);
        } else {
          message.warning(`上传完成！成功 ${totalSuccess} 个，失败 ${totalFailed} 个`);
        }

        // 3秒后关闭弹窗并刷新列表
        setTimeout(() => {
          handleClose();
          onComplete();
        }, 3000);
      }
    } catch (error: any) {
      message.error(`上传失败: ${error.message || '未知错误'}`);
    } finally {
      setUploading(false);
    }
  };

  // 渲染上传结果
  const renderResult = () => {
    if (!uploadResult) return null;

    const { results } = uploadResult;
    const overall = results?.overall || {};

    return (
      <Alert
        message="上传结果"
        description={
          <div>
            <p>总文件数: {overall.total || 0}</p>
            <p>成功: <Tag color="green">{overall.success || 0}</Tag></p>
            <p>失败: <Tag color="red">{overall.failed || 0}</Tag></p>

            {results?.local_files && (
              <div style={{ marginTop: 8 }}>
                <Divider style={{ margin: '8px 0' }}>本地文件</Divider>
                <p>总数: {results.local_files.total} | 成功: {results.local_files.success} | 失败: {results.local_files.failed}</p>
                {results.local_files.errors.length > 0 && (
                  <div style={{ fontSize: 12, color: '#ff4d4f' }}>
                    {results.local_files.errors.map((e: any, i: number) => (
                      <div key={i}>{e.file}: {e.error}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {results?.urls && results.urls.total > 0 && (
              <div style={{ marginTop: 8 }}>
                <Divider style={{ margin: '8px 0' }}>URL下载</Divider>
                <p>总数: {results.urls.total} | 成功: {results.urls.success} | 失败: {results.urls.failed}</p>
              </div>
            )}

            {results?.zip && results.zip.total > 0 && (
              <div style={{ marginTop: 8 }}>
                <Divider style={{ margin: '8px 0' }}>ZIP解压</Divider>
                <p>总数: {results.zip.total} | 成功: {results.zip.success} | 跳过: {results.zip.skipped}</p>
              </div>
            )}
          </div>
        }
        type={overall.failed === 0 ? 'success' : 'warning'}
        showIcon
      />
    );
  };

  return (
    <Modal
      title="批量上传简历"
      open={visible}
      onCancel={handleClose}
      width={700}
      footer={
        uploadResult ? null : [
          <Button key="cancel" onClick={handleClose} disabled={uploading}>
            取消
          </Button>,
          <Button
            key="upload"
            type="primary"
            onClick={handleUpload}
            loading={uploading}
            disabled={localFiles.length === 0 && !urls.trim() && !zipFile}
          >
            开始上传
          </Button>,
        ]
      }
    >
      {uploadResult ? (
        renderResult()
      ) : (
        <>
          <Tabs
            defaultActiveKey="local"
            items={[
              {
                key: 'local',
                label: (
                  <span>
                    <UploadOutlined /> 本地文件
                    {localFiles.length > 0 && (
                      <Tag style={{ marginLeft: 8 }}>{localFiles.length}</Tag>
                    )}
                  </span>
                ),
                children: (
                  <div>
                    <Dragger
                      multiple
                      accept=".pdf,.docx,.doc"
                      onChange={handleLocalFileChange}
                      disabled={uploading}
                      showUploadList={true}
                      fileList={localFiles.map((file, index) => ({
                        uid: `${index}`,
                        name: file.name,
                        status: 'done' as const,
                        originFileObj: file as any,
                      }))}
                      onRemove={(file) => {
                        const index = localFiles.findIndex(f => f.name === file.name);
                        if (index > -1) {
                          const newFiles = [...localFiles];
                          newFiles.splice(index, 1);
                          setLocalFiles(newFiles);
                        }
                        return true;
                      }}
                      customRequest={({ onSuccess }) => setTimeout(() => onSuccess?.('ok'), 0)}
                    >
                      <p className="ant-upload-drag-icon">
                        <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                      </p>
                      <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                      <p className="ant-upload-hint">
                        支持 PDF 和 DOCX 格式，最多1000个文件
                      </p>
                    </Dragger>
                  </div>
                ),
              },
              {
                key: 'url',
                label: (
                  <span>
                    <LinkOutlined /> URL下载
                    {urls.trim() && (
                      <Tag style={{ marginLeft: 8 }}>{urls.split('\n').filter(Boolean).length}</Tag>
                    )}
                  </span>
                ),
                children: (
                  <div>
                    <p style={{ color: '#666', marginBottom: 8 }}>
                      输入简历下载链接，每行一个，支持JSON数组格式
                    </p>
                    <TextArea
                      rows={6}
                      placeholder='["http://example.com/resume1.pdf", "http://example.com/resume2.pdf"]'
                      value={urls}
                      onChange={(e) => setUrls(e.target.value)}
                      disabled={uploading}
                    />
                    <p style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
                      支持PDF和DOCX格式的直链
                    </p>
                  </div>
                ),
              },
              {
                key: 'zip',
                label: (
                  <span>
                    <FileZipOutlined /> ZIP压缩包
                    {zipFile && <Tag style={{ marginLeft: 8 }}>1</Tag>}
                  </span>
                ),
                children: (
                  <div>
                    <Dragger
                      accept=".zip"
                      maxCount={1}
                      onChange={(info) => {
                        if (info.fileList.length > 0) {
                          handleZipFileChange(info);
                        }
                      }}
                      disabled={uploading}
                      onRemove={() => setZipFile(null)}
                      customRequest={({ onSuccess }) => setTimeout(() => onSuccess?.('ok'), 0)}
                    >
                      <p className="ant-upload-drag-icon">
                        <FileZipOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                      </p>
                      <p className="ant-upload-text">点击或拖拽ZIP文件到此区域</p>
                      <p className="ant-upload-hint">
                        自动解压并处理其中的PDF/DOCX文件
                      </p>
                    </Dragger>
                    {zipFile && (
                      <p style={{ marginTop: 8, color: '#52c41a' }}>
                        ✓ 已选择: {zipFile.name}
                      </p>
                    )}
                  </div>
                ),
              },
            ]}
          />

          {uploading && (
            <div style={{ marginTop: 16 }}>
              <Progress
                percent={100}
                status="active"
                format={() => '正在上传和处理...'}
              />
            </div>
          )}

          <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <p style={{ margin: 0, fontSize: 12 }}>
              <strong>提示：</strong>
              <br />
              • 本地文件：最多1000个
              <br />
              • URL下载：支持批量下载直链
              <br />
              • ZIP压缩包：自动解压处理
              <br />
              • 总文件数（含解压）限制：1500个
            </p>
          </div>
        </>
      )}
    </Modal>
  );
};
