"""技能数据库 - 最小化版本

根据CLAUDE.md核心原则：
- 本地不进行技能评分
- 所有技能评估通过外部Agent完成
- 此文件仅用于提取技能关键词（不用于评分）
"""

# 通用技能列表（仅用于关键词提取，不用于评分）
SKILLS_DATABASE = {
    "programming": [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust",
        "C++", "C#", "PHP", "Ruby", "Swift", "Kotlin", "Dart",
        "HTML", "CSS", "SQL", "NoSQL", "Shell", "Bash"
    ],
    "frameworks": [
        "Django", "Flask", "FastAPI", "Spring", "Spring Boot",
        "React", "Vue", "Angular", "Node.js", "Express",
        "MyBatis", "Hibernate", "Entity Framework"
    ],
    "databases": [
        "MySQL", "PostgreSQL", "Oracle", "SQL Server", "MongoDB",
        "Redis", "Elasticsearch", "Memcached", "Cassandra"
    ],
    "tools": [
        "Git", "Docker", "Kubernetes", "Jenkins", "GitLab CI",
        "Linux", "Nginx", "Apache", "Tomcat", "IIS"
    ],
    "data_science": [
        "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas",
        "NumPy", "Matplotlib", "Jupyter", "R", "Tableau"
    ],
    "office": [
        "Excel", "Word", "PowerPoint", "Outlook", "Visio",
        "Photoshop", "Illustrator", "Premiere"
    ],
    "management": [
        "Scrum", "Agile", "项目管理", "团队管理", "产品管理",
        "需求分析", "系统设计", "架构设计"
    ]
}

# 技能同义词映射（简化版）
SKILL_SYNONYMS = {
    "js": "JavaScript",
    "ts": "TypeScript",
    "py": "Python",
    "gitlab": "GitLab",
    "github": "Git",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "redis": "Redis",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "nginx": "Nginx"
}
