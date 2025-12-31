/** 岗位类型定义 */

export interface Job {
  id: string;
  name: string;
  category: 'hr' | 'software' | 'finance' | 'sales';
  description?: string;
  required_skills: string[];
  preferred_skills: string[];
  min_work_years: number;
  min_education: string;
  skill_weight: number;
  experience_weight: number;
  education_weight: number;
  pass_threshold: number;
  review_threshold: number;
  is_active: boolean;
}

export interface JobCreate {
  name: string;
  category: 'hr' | 'software' | 'finance' | 'sales';
  description?: string;
  required_skills: string[];
  preferred_skills: string[];
  min_work_years: number;
  min_education: string;
  skill_weight?: number;
  experience_weight?: number;
  education_weight?: number;
  pass_threshold?: number;
  review_threshold?: number;
}

export interface JobUpdate {
  name?: string;
  category?: 'hr' | 'software' | 'finance' | 'sales';
  description?: string;
  required_skills?: string[];
  preferred_skills?: string[];
  min_work_years?: number;
  min_education?: string;
  skill_weight?: number;
  experience_weight?: number;
  education_weight?: number;
  pass_threshold?: number;
  review_threshold?: number;
  is_active?: boolean;
}

// 岗位类别显示名称映射
export const JOB_CATEGORY_LABELS: Record<Job['category'], string> = {
  hr: 'HR岗位',
  software: '软件开发',
  finance: '财务岗位',
  sales: '销售岗位'
};

// 岗位类别颜色映射
export const JOB_CATEGORY_COLORS: Record<Job['category'], string> = {
  hr: 'purple',
  software: 'blue',
  finance: 'green',
  sales: 'orange'
};
