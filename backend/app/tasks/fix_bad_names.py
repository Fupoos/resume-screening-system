"""修复错误的姓名"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser

def fix_bad_names():
    """修复错误的姓名"""
    db = SessionLocal()
    parser = ResumeParser()
    
    try:
        # 查找姓名有问题的简历
        bad_names = ['双一流', '未命名', None, '']
        
        resumes = db.query(Resume).filter(
            Resume.candidate_name.in_(bad_names)
        ).all()
        
        print(f"找到 {len(resumes)} 份姓名有问题的简历")
        
        for resume in resumes:
            print(f"\n处理简历ID: {resume.id}")
            print(f"当前姓名: {resume.candidate_name}")
            print(f"文件路径: {resume.file_path}")
            
            # 重新提取姓名
            if resume.raw_text:
                # 尝试从邮件主题提取
                if resume.source_email_subject:
                    name = parser._extract_name_from_email_subject(resume.source_email_subject)
                    if name:
                        print(f"✓ 从邮件主题提取到姓名: {name}")
                        resume.candidate_name = name
                        db.commit()
                        continue
                
                # 尝试从文件名提取
                if resume.file_path:
                    filename = os.path.basename(resume.file_path)
                    name = parser._extract_name_from_filename(filename)
                    if name:
                        print(f"✓ 从文件名提取到姓名: {name}")
                        resume.candidate_name = name
                        db.commit()
                        continue
                
                # 尝试从raw_text重新提取
                name = parser._extract_name(resume.raw_text)
                if name:
                    print(f"✓ 从文本重新提取到姓名: {name}")
                    resume.candidate_name = name
                    db.commit()
                    continue
                
                # 如果都提取不到，尝试从邮箱前缀提取
                if resume.email:
                    # 提取邮箱前缀作为姓名
                    email_prefix = resume.email.split('@')[0]
                    # 去除数字和特殊字符
                    import re
                    name = re.sub(r'[0-9._-]', '', email_prefix)
                    if len(name) >= 2 and len(name) <= 4:
                        print(f"✓ 从邮箱提取到姓名: {name}")
                        resume.candidate_name = name
                        db.commit()
                        continue
                
                print(f"✗ 无法提取姓名，保持原样")
        
        print("\n" + "=" * 80)
        print("修复完成！")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_bad_names()
