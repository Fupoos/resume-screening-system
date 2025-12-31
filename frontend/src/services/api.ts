/** API服务封装 */
import axios, { AxiosError } from 'axios';
import type { Job, JobCreate, JobUpdate, MatchRequest, MatchResult } from '../types';

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
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
    // 统一错误处理
    const data = error.response?.data as any;
    const message = data?.detail || error.message || '请求失败';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

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
  skip?: number;
  limit?: number;
  has_pdf_and_content?: boolean;  // 只返回既有PDF又有正文的简历
}): Promise<{ total: number; items: any[]; page?: number; page_size?: number }> => {
  return api.get('/resumes/', { params });
};

/** 获取简历详情 */
export const getResume = async (id: string): Promise<any> => {
  return api.get(`/resumes/${id}`);
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
