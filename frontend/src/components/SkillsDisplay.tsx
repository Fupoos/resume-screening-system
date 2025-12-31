import React from 'react';
import { Tag, Space, Tooltip } from 'antd';
import {
  CodeOutlined,
  DatabaseOutlined,
  CloudOutlined,
  FileTextOutlined,
  DollarOutlined,
  TeamOutlined,
  ToolOutlined,
  GlobalOutlined,
  RobotOutlined,
} from '@ant-design/icons';

interface SkillsDisplayProps {
  skills: string[];
  maxDisplay?: number;
}

// 技能分类映射
const SKILL_CATEGORIES: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  // 编程语言
  Python: { icon: <CodeOutlined />, color: 'blue', label: '后端开发' },
  Java: { icon: <CodeOutlined />, color: 'red', label: '后端开发' },
  JavaScript: { icon: <CodeOutlined />, color: 'gold', label: '前端开发' },
  TypeScript: { icon: <CodeOutlined />, color: 'blue', label: '前端开发' },
  Go: { icon: <CodeOutlined />, color: 'cyan', label: '后端开发' },
  'C++': { icon: <CodeOutlined />, color: 'blue', label: '后端开发' },
  'C#': { icon: <CodeOutlined />, color: 'purple', label: '后端开发' },
  Rust: { icon: <CodeOutlined />, color: 'orange', label: '后端开发' },
  PHP: { icon: <CodeOutlined />, color: 'indigo', label: '后端开发' },
  Ruby: { icon: <CodeOutlined />, color: 'red', label: '后端开发' },
  Swift: { icon: <CodeOutlined />, color: 'orange', label: '移动开发' },
  Kotlin: { icon: <CodeOutlined />, color: 'purple', label: '移动开发' },
  Scala: { icon: <CodeOutlined />, color: 'red', label: '后端开发' },
  R: { icon: <CodeOutlined />, color: 'blue', label: '数据科学' },
  MATLAB: { icon: <CodeOutlined />, color: 'orange', label: '数据科学' },

  // 前端框架
  React: { icon: <CodeOutlined />, color: 'cyan', label: '前端框架' },
  Vue: { icon: <CodeOutlined />, color: 'green', label: '前端框架' },
  Angular: { icon: <CodeOutlined />, color: 'red', label: '前端框架' },
  Svelte: { icon: <CodeOutlined />, color: 'orange', label: '前端框架' },
  'Next.js': { icon: <CodeOutlined />, color: 'black', label: '前端框架' },
  'Nuxt.js': { icon: <CodeOutlined />, color: 'green', label: '前端框架' },
  jQuery: { icon: <CodeOutlined />, color: 'blue', label: '前端框架' },
  Bootstrap: { icon: <CodeOutlined />, color: 'purple', label: 'UI框架' },
  Tailwind: { icon: <CodeOutlined />, color: 'cyan', label: 'UI框架' },
  'Ant Design': { icon: <CodeOutlined />, color: 'red', label: 'UI框架' },
  'Element UI': { icon: <CodeOutlined />, color: 'green', label: 'UI框架' },

  // 后端框架
  Django: { icon: <CodeOutlined />, color: 'green', label: '后端框架' },
  Flask: { icon: <CodeOutlined />, color: 'white', label: '后端框架' },
  FastAPI: { icon: <CodeOutlined />, color: 'teal', label: '后端框架' },
  'Spring Boot': { icon: <CodeOutlined />, color: 'green', label: '后端框架' },
  Express: { icon: <CodeOutlined />, color: 'gray', label: '后端框架' },
  Koa: { icon: <CodeOutlined />, color: 'blue', label: '后端框架' },
  Laravel: { icon: <CodeOutlined />, color: 'red', label: '后端框架' },
  'Ruby on Rails': { icon: <CodeOutlined />, color: 'red', label: '后端框架' },
  'ASP.NET': { icon: <CodeOutlined />, color: 'purple', label: '后端框架' },
  'Node.js': { icon: <CodeOutlined />, color: 'green', label: '后端框架' },
  NestJS: { icon: <CodeOutlined />, color: 'red', label: '后端框架' },

  // 数据库
  MySQL: { icon: <DatabaseOutlined />, color: 'orange', label: '数据库' },
  PostgreSQL: { icon: <DatabaseOutlined />, color: 'blue', label: '数据库' },
  MongoDB: { icon: <DatabaseOutlined />, color: 'green', label: '数据库' },
  Redis: { icon: <DatabaseOutlined />, color: 'red', label: '数据库' },
  Oracle: { icon: <DatabaseOutlined />, color: 'orange', label: '数据库' },
  'SQL Server': { icon: <DatabaseOutlined />, color: 'blue', label: '数据库' },
  SQLite: { icon: <DatabaseOutlined />, color: 'blue', label: '数据库' },
  Elasticsearch: { icon: <DatabaseOutlined />, color: 'yellow', label: '搜索引擎' },
  ClickHouse: { icon: <DatabaseOutlined />, color: 'orange', label: '数据库' },

  // DevOps工具
  Docker: { icon: <CloudOutlined />, color: 'blue', label: 'DevOps' },
  Kubernetes: { icon: <CloudOutlined />, color: 'blue', label: 'DevOps' },
  Jenkins: { icon: <CloudOutlined />, color: 'red', label: 'DevOps' },
  Git: { icon: <ToolOutlined />, color: 'purple', label: '版本控制' },
  GitHub: { icon: <ToolOutlined />, color: 'black', label: '代码托管' },
  GitLab: { icon: <ToolOutlined />, color: 'orange', label: '代码托管' },
  'CI/CD': { icon: <CloudOutlined />, color: 'blue', label: 'DevOps' },
  Terraform: { icon: <CloudOutlined />, color: 'purple', label: '基础设施' },
  Ansible: { icon: <CloudOutlined />, color: 'red', label: '自动化' },
  Linux: { icon: <CloudOutlined />, color: 'gold', label: '操作系统' },
  Nginx: { icon: <CloudOutlined />, color: 'green', label: 'Web服务器' },

  // 办公软件
  Excel: { icon: <FileTextOutlined />, color: 'green', label: '办公软件' },
  Word: { icon: <FileTextOutlined />, color: 'blue', label: '办公软件' },
  PowerPoint: { icon: <FileTextOutlined />, color: 'orange', label: '办公软件' },
  Outlook: { icon: <FileTextOutlined />, color: 'blue', label: '办公软件' },
  SAP: { icon: <FileTextOutlined />, color: 'blue', label: '企业软件' },
  OA: { icon: <FileTextOutlined />, color: 'cyan', label: '办公系统' },
  ERP: { icon: <FileTextOutlined />, color: 'purple', label: '企业软件' },
  CRM: { icon: <FileTextOutlined />, color: 'orange', label: '企业软件' },

  // 财务相关
  财务: { icon: <DollarOutlined />, color: 'gold', label: '财务技能' },
  会计: { icon: <DollarOutlined />, color: 'gold', label: '财务技能' },
  审计: { icon: <DollarOutlined />, color: 'orange', label: '财务技能' },
  税务: { icon: <DollarOutlined />, color: 'blue', label: '财务技能' },
  成本核算: { icon: <DollarOutlined />, color: 'purple', label: '财务技能' },
  财务报表: { icon: <DollarOutlined />, color: 'green', label: '财务技能' },
  预算管理: { icon: <DollarOutlined />, color: 'cyan', label: '财务技能' },
  财务分析: { icon: <DollarOutlined />, color: 'blue', label: '财务技能' },

  // HR相关
  招聘: { icon: <TeamOutlined />, color: 'purple', label: 'HR技能' },
  培训: { icon: <TeamOutlined />, color: 'blue', label: 'HR技能' },
  绩效管理: { icon: <TeamOutlined />, color: 'green', label: 'HR技能' },
  薪酬福利: { icon: <TeamOutlined />, color: 'orange', label: 'HR技能' },
  员工关系: { icon: <TeamOutlined />, color: 'cyan', label: 'HR技能' },
  HRBP: { icon: <TeamOutlined />, color: 'red', label: 'HR技能' },
  人才盘点: { icon: <TeamOutlined />, color: 'purple', label: 'HR技能' },
  组织发展: { icon: <TeamOutlined />, color: 'blue', label: 'HR技能' },

  // 管理技能
  项目管理: { icon: <TeamOutlined />, color: 'blue', label: '管理技能' },
  团队管理: { icon: <TeamOutlined />, color: 'green', label: '管理技能' },
  沟通协调: { icon: <TeamOutlined />, color: 'orange', label: '软技能' },
  谈判: { icon: <TeamOutlined />, color: 'purple', label: '软技能' },
  领导力: { icon: <TeamOutlined />, color: 'red', label: '软技能' },
  PMP: { icon: <TeamOutlined />, color: 'blue', label: '管理认证' },
  Scrum: { icon: <TeamOutlined />, color: 'orange', label: '敏捷开发' },
  Agile: { icon: <TeamOutlined />, color: 'green', label: '敏捷开发' },
  瀑布模型: { icon: <TeamOutlined />, color: 'blue', label: '开发方法' },

  // 语言技能
  英语: { icon: <GlobalOutlined />, color: 'blue', label: '语言能力' },
  英语六级: { icon: <GlobalOutlined />, color: 'blue', label: '语言能力' },
  CET6: { icon: <GlobalOutlined />, color: 'blue', label: '语言能力' },
  CET-6: { icon: <GlobalOutlined />, color: 'blue', label: '语言能力' },
  德语: { icon: <GlobalOutlined />, color: 'cyan', label: '语言能力' },
  法语: { icon: <GlobalOutlined />, color: 'purple', label: '语言能力' },
  日语: { icon: <GlobalOutlined />, color: 'pink', label: '语言能力' },
  韩语: { icon: <GlobalOutlined />, color: 'orange', label: '语言能力' },
  西班牙语: { icon: <GlobalOutlined />, color: 'yellow', label: '语言能力' },
  俄语: { icon: <GlobalOutlined />, color: 'red', label: '语言能力' },
  普通话: { icon: <GlobalOutlined />, color: 'geekblue', label: '语言能力' },

  // AI平台
  Coze: { icon: <RobotOutlined />, color: 'purple', label: 'AI平台' },
  Coze应用: { icon: <RobotOutlined />, color: 'purple', label: 'AI平台' },
  豆包: { icon: <RobotOutlined />, color: 'cyan', label: 'AI平台' },
  文心一言: { icon: <RobotOutlined />, color: 'green', label: 'AI平台' },
  讯飞星火: { icon: <RobotOutlined />, color: 'blue', label: 'AI平台' },
  通义千问: { icon: <RobotOutlined />, color: 'orange', label: 'AI平台' },
  ChatGPT: { icon: <RobotOutlined />, color: 'green', label: 'AI平台' },
  GPT: { icon: <RobotOutlined />, color: 'green', label: 'AI平台' },
  'GPT-4': { icon: <RobotOutlined />, color: 'green', label: 'AI平台' },
  Claude: { icon: <RobotOutlined />, color: 'orange', label: 'AI平台' },
  Gemini: { icon: <RobotOutlined />, color: 'blue', label: 'AI平台' },
  Midjourney: { icon: <RobotOutlined />, color: 'purple', label: 'AI绘画' },
  'Stable Diffusion': { icon: <RobotOutlined />, color: 'pink', label: 'AI绘画' },
  LangChain: { icon: <RobotOutlined />, color: 'cyan', label: 'AI框架' },
};

// 默认分类
const DEFAULT_CATEGORY = { icon: <ToolOutlined />, color: 'default', label: '其他技能' };

export const SkillsDisplay: React.FC<SkillsDisplayProps> = ({
  skills,
  maxDisplay = 10
}) => {
  if (!skills || skills.length === 0) {
    return <span style={{ color: '#999' }}>无技能信息</span>;
  }

  const displaySkills = skills.slice(0, maxDisplay);
  const remainingSkills = skills.slice(maxDisplay);

  return (
    <Space size={[4, 4]} wrap>
      {displaySkills.map((skill, index) => {
        const category = SKILL_CATEGORIES[skill] || DEFAULT_CATEGORY;
        const { icon, color, label } = category;

        return (
          <Tooltip key={index} title={label}>
            <Tag color={color} style={{ fontSize: 12 }}>
              {icon} {skill}
            </Tag>
          </Tooltip>
        );
      })}
      {remainingSkills.length > 0 && (
        <Tooltip title={remainingSkills.join(', ')}>
          <Tag style={{ fontSize: 12 }}>+{remainingSkills.length}</Tag>
        </Tooltip>
      )}
    </Space>
  );
};

export default SkillsDisplay;
