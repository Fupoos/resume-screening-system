/** API服务封装 */
import axios, { AxiosError } from 'axios';
import type { Job, JobCreate, JobUpdate, MatchRequest, MatchResult } from '../types';

// 创建axios实例
const api = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1') + '/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error: AxiosError) => {
    // 处理401未授权错误
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('userInfo');
      window.location.href = '/login';
    }
    // 统一错误处理
    const data = error.response?.data as any;
    const message = data?.detail || error.message || '请求失败';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

// ==================== 认证相关API ====================

interface UserInfo {
  id: string;
  username: string;
  role: string;
  job_categories: string[];
  is_active: boolean;
}

interface UserCreate {
  username: string;
  password: string;
  role?: string;
  job_categories?: string[];
}

interface UserUpdate {
  password?: string;
  role?: string;
  job_categories?: string[];
  is_active?: boolean;
}

/** 获取当前用户信息 */
export const getCurrentUser = async (): Promise<UserInfo> => {
  return api.get('/auth/me');
};

/** 获取用户列表（仅管理员） */
export const getUsers = async (): Promise<any[]> => {
  return api.get('/auth/users');
};

/** 创建用户（仅管理员） */
export const createUser = async (data: UserCreate): Promise<any> => {
  return api.post('/auth/users', data);
};

/** 更新用户（仅管理员） */
export const updateUser = async (id: string, data: UserUpdate): Promise<any> => {
  return api.put(`/auth/users/${id}`, data);
};

/** 删除用户（仅管理员） */
export const deleteUser = async (id: string): Promise<{ message: string }> => {
  return api.delete(`/auth/users/${id}`);
};

/** 获取可用的岗位类别列表（仅管理员） */
export const getAvailableJobCategories = async (): Promise<string[]> => {
  return api.get('/auth/job-categories');
};

// ==================== 岗位相关API ====================

/** 获取岗位列表 */
export const getJobs = async (): Promise<Job[]> => {
  return api.get('/jobs/');
};

/** 获取岗位详情 */
export const getJob = async (id: string): Promise<Job> => {
  return api.get(`/jobs/${id}`);
};

/** 创建岗位 */
export const createJob = async (data: JobCreate): Promise<Job> => {
  return api.post('/jobs/', data);
};

/** 更新岗位 */
export const updateJob = async (id: string, data: JobUpdate): Promise<Job> => {
  return api.put(`/jobs/${id}`, data);
};

/** 删除岗位 */
export const deleteJob = async (id: string): Promise<{ message: string }> => {
  return api.delete(`/jobs/${id}`);
};

// ==================== 筛选相关API ====================

/** 简历匹配 */
export const matchResume = async (data: MatchRequest): Promise<MatchResult> => {
  return api.post('/screening/match', data);
};

/** 获取筛选结果列表 */
export const getScreeningResults = async (params?: {
  job_id?: string;
  result?: string;
  skip?: number;
  limit?: number;
  time_range?: string;  // 时间范围: today/this_week/this_month
  screening_status?: string;  // 筛选状态: pending/不合格/待定/可以发offer/已面试
  search?: string;  // 搜索候选人姓名
}): Promise<any> => {
  return api.get('/screening/results', { params });
};

/** 获取筛选结果详情 */
export const getScreeningResult = async (id: string): Promise<any> => {
  return api.get(`/screening/result/${id}`);
};

// ==================== 简历相关API ====================

/** 获取简历列表 */
export const getResumes = async (params?: {
  status?: string;
  screening_status?: string;  // 筛选状态: pending/不合格/待定/可以发offer/已面试
  skip?: number;
  limit?: number;
  file_type?: string;
  has_pdf_and_content?: boolean;  // 只返回既有PDF又有正文的简历
  agent_evaluated?: boolean;  // 只返回已通过Agent评估的简历
  min_score?: number;  // 最低Agent评分
  exclude_needs_review?: boolean;  // 排除需要人工审核的简历(raw_text少于100字符)
  needs_review_only?: boolean;  // 只返回需要人工审核的简历
  time_range?: string;  // 时间范围: today/this_week/this_month
  search?: string;  // 搜索候选人姓名
}): Promise<{ total: number; items: any[]; page?: number; page_size?: number }> => {
  return api.get('/resumes/', { params });
};

/** 获取简历详情 */
export const getResume = async (id: string): Promise<any> => {
  return api.get(`/resumes/${id}`);
};

/** 更新简历信息（人工审核时手动补充） */
export const updateResume = async (id: string, data: {
  candidate_name?: string;
  phone?: string;
  email?: string;
  education?: string;
  work_years?: number;
  skills?: string[];
  work_experience?: any[];
  project_experience?: any[];
  education_history?: any[];
}): Promise<{ resume_id: string; message: string }> => {
  return api.put(`/resumes/${id}`, data);
};

/** 上传简历 */
export const uploadResume = async (file: File, autoMatch: boolean = true): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('auto_match', String(autoMatch));

  return api.post('/resumes/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

/** 删除简历 */
export const deleteResume = async (id: string): Promise<{ message: string }> => {
  return api.delete(`/resumes/${id}`);
};

/** 标记简历为需要人工审核 */
export const markResumeForReview = async (id: string): Promise<{
  resume_id: string;
  message: string;
}> => {
  return api.post(`/resumes/${id}/mark-for-review`);
};

/** 标记简历为已面试 */
export const markInterviewed = async (id: string): Promise<{
  resume_id: string;
  message: string;
}> => {
  return api.post(`/resumes/${id}/mark-interviewed`);
};

// ==================== 批量上传API ====================

/** 多来源混合上传简历（本地文件 + URL + ZIP） */
export const multiSourceUploadResumes = async (params: {
  files?: File[];
  urls?: string[];
  zipFile?: File;
}): Promise<{
  message: string;
  results: {
    local_files: {
      total: number;
      success: number;
      failed: number;
      errors: Array<{ file: string; error: string }>;
      file_paths: string[];
    };
    urls: {
      total: number;
      success: number;
      failed: number;
      errors: Array<{ url: string; error: string }>;
      file_paths: string[];
    };
    zip: {
      total: number;
      success: number;
      skipped: number;
      failed: number;
      errors: Array<{ file: string; error: string }>;
      file_paths: string[];
    };
    overall: {
      total: number;
      success: number;
      failed: number;
      exceeded?: boolean;
    };
  };
}> => {
  const formData = new FormData();

  // 添加本地文件
  if (params.files && params.files.length > 0) {
    params.files.forEach(file => {
      formData.append('files', file);
    });
  }

  // 添加URL列表
  if (params.urls && params.urls.length > 0) {
    formData.append('urls', JSON.stringify(params.urls));
  }

  // 添加ZIP文件
  if (params.zipFile) {
    formData.append('zip_file', params.zipFile);
  }

  return api.post('/upload/multi-source-upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 300000, // 5分钟超时（支持URL下载和ZIP解压）
  });
};

// ==================== 邮箱相关API ====================
// 邮箱相关功能（检查邮箱、导入历史邮件）已移除

/** 获取简历的筛选结果（前2个最佳匹配） */
export const getResumeScreenings = async (id: string): Promise<any> => {
  return api.get(`/resumes/${id}/screenings`);
};

// ==================== 统计相关API ====================

/** 获取Dashboard综合统计数据 */
export const getDashboardStatistics = async (): Promise<{
  overview: {
    total_resumes: number;
    pass_count: number;
    review_count: number;
    reject_count: number;
    pass_rate: number;
    avg_score: number;
  };
}> => {
  return api.get('/statistics/dashboard');
};

/** 按城市统计 */
export const getStatisticsByCity = async (): Promise<Record<string, {
  total: number;
  pass: number;
  review: number;
  reject: number;
  avg_score: number;
  pass_rate: number;
}>> => {
  return api.get('/statistics/by-city');
};

/** 按职位统计 */
export const getStatisticsByJob = async (): Promise<Record<string, {
  total: number;
  pass: number;
  review: number;
  reject: number;
  avg_score: number;
}>> => {
  return api.get('/statistics/by-job');
};

/** 按时间段统计 */
export const getStatisticsByTime = async (params: {
  start: string;
  end: string;
  group_by?: 'day' | 'week' | 'month';
}): Promise<Record<string, {
  total: number;
  pass: number;
  review: number;
  reject: number;
  avg_score: number;
}>> => {
  return api.get('/statistics/by-time', { params });
};

export default api;
