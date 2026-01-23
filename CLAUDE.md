# 简历筛选系统 - Claude AI 开发原则

## 🔴 核心原则（不可更改）

### **原则1：所有简历打分和判断必须通过外部Agent完成**

**原则说明：**
- 本系统禁止使用任何本地逻辑进行简历打分、筛选、判断
- 所有评分（score、evaluation）必须通过外部Agent（如FastGPT）完成
- 任何试图引入或恢复本地评分逻辑的行为都被视为违反核心原则

**适用范围：**
- 简历评分（0-100分）
- 职位分类判断
- 技能匹配评分
- 经验评估
- 学历评估
- 筛选结果分类（可以发offer/待定/不合格）
- 任何其他形式的简历判断或打分

**允许的本地逻辑：**
- ✅ 数据解析（PDF解析、邮件解析）
- ✅ 数据提取（提取姓名、电话、技能列表等）
- ✅ 数据存储（保存到数据库）
- ✅ 数据展示（前端展示）
- ✅ 调用外部Agent的代码
- ✅ 简单的字符串匹配（非评分用途，如从邮件标题提取职位名称）

**禁止的本地逻辑：**
- ❌ 计算分数（任何形式的score计算）
- ❌ 匹配评分（基于技能、经验、学历的打分）
- ❌ 筛选分类（基于分数的can_hire/pending_review/rejected判断）
- ❌ 智能判断（基于规则的职位推断、技能推断等需要评分/判断的逻辑）
- ❌ 任何本地形式的简历质量评估

---

### **原则2：只保留PDF或DOCX附件的简历**

**原则说明：**
- 系统**接受** PDF 和 DOCX 两种格式的简历附件
- 接受情况：1) PDF+正文 2) DOCX+正文 3) 只有PDF 4) 只有DOCX
- **不符合条件的简历必须立即删除**：纯邮件正文简历、无附件简历等

**保留条件：**
```python
-- PDF格式
file_type == 'pdf'
AND pdf_path IS NOT NULL
AND pdf_path != ''

-- DOCX格式
file_type == 'docx'
AND pdf_path IS NOT NULL
AND pdf_path != ''
```

**删除条件（任一满足即删除）：**
```python
-- 无有效附件
file_type NOT IN ('pdf', 'docx')

-- 邮件正文类型（纯文本，无附件）
file_type == 'email_body'
```

**执行方式：**
- 定期清理：删除所有不符合条件的简历
- 导入时过滤：导入时直接丢弃不符合条件的简历
- 前端显示：只显示符合条件的简历
- 预览功能：PDF可直接预览，DOCX需要下载后查看

---

## ⚠️ 违反原则的行为

以下行为被视为违反核心原则，**必须先与用户确认**：

1. **引入新的本地评分逻辑**
   - 例如：创建新的评分函数、算法或规则

2. **恢复已删除的本地评分代码**
   - 例如：重新引入JobMatcher、ScreeningClassifier等

3. **绕过外部Agent进行简历判断**
   - 例如：使用本地规则决定简历是否合格

4. **保留不符合条件的简历**
   - 例如：保留无附件、纯邮件正文类型的简历

5. **修改此文档**
   - 任何试图修改上述核心原则的行为都需要先获得用户明确同意

---

## 📋 当前系统架构

### 外部Agent集成
- **FastGPT Agent**: 唯一允许的评分和判断来源
- **文件位置**: `backend/app/services/agent_client.py`
- **调用方式**: `AgentClient.evaluate_resume()`

### 数据模型
- **ScreeningResult 模型**：只保留 `agent_score`（Agent评分 0-100）
- **已删除字段**：`match_score`, `rule_score`, `similarity_score`, `skill_score`, `experience_score`, `education_score`
- **Job 模型**：已删除权重字段 `skill_weight`, `experience_weight`, `education_weight`, `pass_threshold`, `review_threshold`

### 已删除的本地评分模块
以下模块违反核心原则，已删除：

1. `backend/app/services/job_matcher.py` - 岗位匹配服务
2. `backend/app/services/screening_classifier.py` - 筛选分类器（已从测试文件中移除引用）
3. `backend/app/services/skill_matcher.py` - 技能匹配器
4. `backend/app/services/school_classifier.py` - 学校分类器
5. `backend/app/data/job_titles.py` - 职位数据库（用于本地判断）
6. `backend/app/data/skills_database.py` - 技能数据库
7. `backend/app/data/chinese_universities.py` - 中国大学数据库
8. `backend/app/data/foreign_universities.py` - 外国大学数据库
9. `backend/app/data/skill_similarity.py` - 技能相似度矩阵

---

## 🚨 紧急提醒

**如果您（Claude AI）收到以下类型的请求：**
- "优化评分算法"
- "改进匹配逻辑"
- "添加智能判断功能"
- "实现本地筛选功能"
- "保留无附件的简历"
- "保留纯邮件正文类型的简历"

**您必须：**
1. 立即停止
2. 提醒用户此请求违反核心原则
3. 建议符合原则的实现方式
4. 如果用户坚持，必须获得明确确认后再执行

---

## 📅 创建与更新日期

**创建日期：2025-12-31**
**更新日期：2026-01-15** - 允许 DOCX 格式简历，系统接受 PDF 和 DOCX 两种格式

由用户明确要求创建，此文档具有最高优先级，任何代码修改都不得违反此原则。
