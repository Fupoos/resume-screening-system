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

### **原则2：只保留有正文+PDF附件的简历**

**原则说明：**
- 系统**只接受**同时满足以下两个条件的简历：
  1. 有PDF附件（`file_type='pdf'` 且 `pdf_path` 不为空）
  2. 有正文内容（`raw_text` 不为空且不为None）
- **不符合条件的简历必须立即删除**
- **完全不考虑保留**：邮件正文简历、无正文简历、无PDF简历等

**保留条件（必须同时满足）：**
```python
file_type == 'pdf'
AND pdf_path IS NOT NULL
AND pdf_path != ''
AND raw_text IS NOT NULL
AND raw_text != ''
```

**删除条件（任一满足即删除）：**
```python
-- 无PDF附件
file_type != 'pdf' OR pdf_path IS NULL

-- 无正文内容
raw_text IS NULL OR raw_text == ''

-- 邮件正文类型
file_type == 'email_body'
```

**执行方式：**
- 定期清理：删除所有不符合条件的简历
- 导入时过滤：导入时直接丢弃不符合条件的简历
- 前端显示：只显示符合条件的简历

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
   - 例如：保留无正文、无PDF、邮件正文类型的简历

5. **修改此文档**
   - 任何试图修改上述核心原则的行为都需要先获得用户明确同意

---

## 📋 当前系统架构

### 外部Agent集成
- **FastGPT Agent**: 唯一允许的评分和判断来源
- **文件位置**: `backend/app/services/agent_client.py`
- **调用方式**: `AgentClient.evaluate_resume()`

### 已删除的本地评分模块
以下模块违反核心原则，已删除：

1. `backend/app/services/job_matcher.py` - 岗位匹配服务
2. `backend/app/services/screening_classifier.py` - 筛选分类器
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
- "保留无正文/无PDF的简历"
- "保留邮件正文类型的简历"

**您必须：**
1. 立即停止
2. 提醒用户此请求违反核心原则
3. 建议符合原则的实现方式
4. 如果用户坚持，必须获得明确确认后再执行

---

## 📅 创建与更新日期

**创建日期：2025-12-31**
**更新日期：2025-12-31** - 添加简历保留规则

由用户明确要求创建，此文档具有最高优先级，任何代码修改都不得违反此原则。
