/** 简历相关类型定义 */

export interface SkillsByLevel {
  expert?: string[];
  proficient?: string[];
  familiar?: string[];
  mentioned?: string[];
}

export interface Resume {
  id: string;
  candidate_name: string | null;
  phone: string | null;
  email: string | null;
  education: string | null;
  work_years: number | null;
  skills: string[];
  skills_by_level?: SkillsByLevel;
  status: string;
  file_type: string | null;
  file_path?: string | null;
  raw_text?: string | null;
  source_email_id?: string | null;
  source_email_subject?: string | null;
  source_sender?: string | null;
  created_at: string;
  updated_at: string;
  top_matches?: TopMatch[];
}

export interface TopMatch {
  job_id: string;
  job_name: string;
  job_category: string;
  match_score: number;
  skill_score: number;
  experience_score: number;
  education_score: number;
  screening_result: 'PASS' | 'REVIEW' | 'REJECT';
  matched_points: string[];
  unmatched_points: string[];
  suggestion: string;
  created_at: string;
}
