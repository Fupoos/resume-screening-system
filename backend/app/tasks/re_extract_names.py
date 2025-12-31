"""重新提取简历姓名"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser

def re_extract_names():
    """重新提取所有"候选人XXX"格式简历的姓名"""
    db = SessionLocal()
    parser = ResumeParser()
    
    try:
        # 查找所有"候选人XXX"格式的简历
        resumes = db.query(Resume).filter(
            Resume.candidate_name.like('候选人%')
        ).all()
        
        print(f"找到 {len(resumes)} 份\"候选人XXX\"格式的简历\n")
        
        fixed_count = 0
        for resume in resumes:
            print(f"处理简历ID: {resume.id}")
            print(f"  当前姓名: {resume.candidate_name}")
            
            if resume.raw_text:
                # 重新提取姓名
                new_name = parser._extract_name(resume.raw_text)
                
                if new_name and new_name != resume.candidate_name:
                    print(f"  ✓ 提取到新姓名: {new_name}")
                    resume.candidate_name = new_name
                    fixed_count += 1
                else:
                    print(f"  ✗ 未能提取到姓名，保持原样")
            else:
                print(f"  ✗ 无原始文本，无法提取")
            print()
        
        db.commit()
        
        print("=" * 80)
        print(f"修复完成！成功修复 {fixed_count} 份简历")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    re_extract_names()
