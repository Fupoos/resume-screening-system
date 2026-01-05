/** 筛选相关类型定义 */

export interface MatchRequest {
  candidate_name: string;
  phone?: string;
  email?: string;
  education?: string;
  work_years?: number;
  skills: string[];
  job_id: string;
}

export interface MatchResult {
  candidate_name: string;
  job_name: string;
  screening_result: 'PASS' | 'REVIEW' | 'REJECT';
  agent_score: number;
  matched_points: string[];
  unmatched_points: string[];
  suggestion: string;
}

export interface ScreeningResult {
  id: string;
  resume_id: string;
  job_id: string;
  agent_score: number | null;
  screening_result: 'PASS' | 'REVIEW' | 'REJECT';
  matched_points: string[];
  unmatched_points: string[];
  suggestion?: string;
  created_at: string;
}

// 筛选结果显示名称映射
export const SCREENING_RESULT_LABELS: Record<MatchResult['screening_result'], string> = {
  PASS: '通过',
  REVIEW: '待定',
  REJECT: '拒绝'
};

// 筛选结果颜色映射
export const SCREENING_RESULT_COLORS: Record<MatchResult['screening_result'], string> = {
  PASS: 'success',
  REVIEW: 'warning',
  REJECT: 'error'
};
