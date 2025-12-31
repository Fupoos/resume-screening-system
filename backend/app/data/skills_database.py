"""技能数据库 - 按分类组织"""

SKILLS_DATABASE = {
    'programming': [  # 编程语言
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
        'PHP', 'Ruby', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl',
        'Shell', 'Bash', 'PowerShell', 'Lua', 'Dart', 'Flutter',
        # 同义词映射
        'python', 'py', 'python3',
        'js',
        'ts',
        'golang',
        'go语言',
        'c++',
        'c#',
        'csharp',
    ],
    'frontend': [  # 前端框架
        'React', 'Vue', 'Angular', 'Svelte', 'Next.js', 'Nuxt.js',
        'jQuery', 'Bootstrap', 'Tailwind', 'Ant Design', 'Element UI',
        # 同义词
        'reactjs', 'react.js', 'vuejs', 'vue.js', 'angularjs', 'angular.js',
        'nextjs', 'next.js', 'nuxtjs', 'nuxt.js',
    ],
    'backend': [  # 后端框架
        'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Express', 'Koa',
        'Laravel', 'Ruby on Rails', 'ASP.NET', 'Node.js', 'NestJS',
    ],
    'database': [  # 数据库
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle',
        'SQL Server', 'SQLite', 'Elasticsearch', 'ClickHouse',
        # 同义词
        'pg', 'postgres', 'postgressql',
        'mongo',
        'mysql',
        'ms sql', 'mssql',
        'es', 'elastic',
    ],
    'devops': [  # DevOps工具
        'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitLab', 'GitHub',
        'CI/CD', 'Terraform', 'Ansible', 'Linux', 'Nginx',
        # 同义词
        'k8s', 'kubes',
        'docker compose',
        'cicd', 'ci/cd',
    ],
    'cloud': [  # 新增：云平台
        'AWS', 'Azure', 'GCP', 'Google Cloud', '阿里云', '腾讯云', '华为云',
        'EC2', 'S3', 'Lambda', 'DynamoDB', 'RDS', 'EKS', 'ECS',
        'Azure Functions', 'Blob Storage', 'Cosmos DB', 'AKS',
        'Google Compute Engine', 'Cloud Functions', 'BigQuery',
        'Cloudflare', 'Linode', 'DigitalOcean',
        # 同义词
        'aws', 'amazon web services', 'aw',
        'azure',
        'gcp', 'gc', 'google cloud',
    ],
    'bigdata': [  # 新增：大数据
        'Hadoop', 'Spark', 'Flink', 'Kafka', 'Hive', 'HBase',
        'Presto', 'Impala', 'Cassandra', 'Elasticsearch', 'Logstash', 'Kibana',
        'Snowflake', 'Databricks', 'Airflow', 'dbt', 'Hudi', 'Iceberg',
        # 同义词
        'spark streaming', 'structured streaming',
        'elk', 'elk stack',
    ],
    'aiml': [  # 新增：AI/ML
        'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'XGBoost',
        'LightGBM', 'CatBoost', 'OpenCV', 'NLTK', 'SpaCy',
        'Transformers', 'BERT', 'GPT', 'LangChain',
        'Pandas', 'NumPy', 'Matplotlib', 'Seaborn',
        'Jupyter', 'Colab', 'Kaggle',
        # 同义词
        'tensorflow', 'tf',
        'pytorch',
        'keras',
        'sklearn', 'scikit-learn',
        'xgboost',
        'lightgbm',
        'catboost',
        'opencv', 'cv',
        'nlp',
        'spacy',
    ],
    'mobile': [  # 新增：移动开发
        'iOS', 'Android', 'React Native', 'Flutter', 'Swift', 'Kotlin',
        'SwiftUI', 'Jetpack Compose', 'Xamarin', 'Cordova', 'Ionic',
        # 同义词
        'reactnative', 'react native',
    ],
    'microservices': [  # 新增：微服务与架构
        'Microservices', 'gRPC', 'GraphQL', 'REST API', 'SOAP',
        'Message Queue', 'RabbitMQ', 'Kafka', 'ActiveMQ',
        'Service Mesh', 'Istio', 'Linkerd',
        # 同义词
        'rest', 'graphql', 'grpc', 'microservice',
    ],
    'monitoring': [  # 新增：监控与可观测性
        'Prometheus', 'Grafana', 'ELK', 'Elastic Stack', 'Splunk',
        'Datadog', 'New Relic', 'AppDynamics', 'Jaeger', 'Zipkin',
        'Sentry', 'PagerDuty',
    ],
    'office': [  # 办公软件
        'Excel', 'Word', 'PowerPoint', 'Outlook', 'PPT',
        'SAP', 'OA', 'ERP', 'CRM',
        # 同义词
        'ppt', 'ppoint',
    ],
    'finance': [  # 财务相关
        '财务', '会计', '审计', '税务', '成本核算',
        '财务报表', '预算管理', '财务分析',
    ],
    'hr': [  # 人力资源
        '招聘', '培训', '绩效管理', '薪酬福利', '员工关系',
        'HRBP', '人才盘点', '组织发展',
    ],
    'management': [  # 管理技能
        '项目管理', '团队管理', '沟通协调', '谈判', '领导力',
        'PMP', 'Scrum', 'Agile', '瀑布模型',
        # 同义词
        'pm', 'scrum', 'agile',
    ],
    'language': [  # 语言技能
        '英语', '英语六级', 'CET-6', 'CET6', '英语四级', 'CET-4', 'CET4',
        '德语', '法语', '日语', '韩语', '西班牙语', '俄语', '阿拉伯语',
        '普通话', '粤语',
        # 同义词
        'english', '英语能力',
        'german', '德语能力',
        'french', '法语能力',
        'japanese', '日语能力',
    ],
    'ai_platform': [  # AI平台和工具
        'Coze', 'Coze应用', '豆包', '文心一言', '讯飞星火', '通义千问',
        'ChatGPT', 'GPT', 'GPT-4', 'Claude', 'Gemini',
        'Midjourney', 'Stable Diffusion', 'DALL-E',
        'LangChain', 'Hugging Face', 'AutoGPT',
        # 同义词
        'coze', 'chatgpt', 'gpt-4', 'langchain',
    ],
}

# 同义词映射表
SKILL_SYNONYMS = {
    # ========== 编程语言 ==========
    'python': 'Python',
    'py': 'Python',
    'python3': 'Python',

    'javascript': 'JavaScript',
    'js': 'JavaScript',

    'typescript': 'TypeScript',
    'ts': 'TypeScript',

    'golang': 'Go',
    'go语言': 'Go',

    'c++': 'C++',
    'c#': 'C#',
    'csharp': 'C#',

    # ========== 前端框架 ==========
    'react': 'React',
    'reactjs': 'React',
    'react.js': 'React',

    'vue': 'Vue',
    'vuejs': 'Vue',
    'vue.js': 'Vue',

    'angular': 'Angular',
    'angularjs': 'Angular',
    'angular.js': 'Angular',

    'next.js': 'Next.js',
    'nextjs': 'Next.js',

    'nuxt.js': 'Nuxt.js',
    'nuxtjs': 'Nuxt.js',

    # ========== 后端框架 ==========
    'django': 'Django',
    'flask': 'Flask',
    'fastapi': 'FastAPI',
    'express': 'Express',
    'koa': 'Koa',
    'spring': 'Spring Boot',
    'springboot': 'Spring Boot',
    'laravel': 'Laravel',
    'asp.net': 'ASP.NET',
    'nodejs': 'Node.js',
    'node': 'Node.js',

    # ========== 数据库 ==========
    'mysql': 'MySQL',
    'postgresql': 'PostgreSQL',
    'postgres': 'PostgreSQL',
    'postgressql': 'PostgreSQL',
    'pg': 'PostgreSQL',

    'mongodb': 'MongoDB',
    'mongo': 'MongoDB',

    'redis': 'Redis',
    'oracle': 'Oracle',
    'sqlite': 'SQLite',
    'elasticsearch': 'Elasticsearch',
    'elastic': 'Elasticsearch',
    'es': 'Elasticsearch',

    'ms sql': 'SQL Server',
    'mssql': 'SQL Server',

    # ========== DevOps ==========
    'docker': 'Docker',
    'kubernetes': 'Kubernetes',
    'k8s': 'Kubernetes',
    'kubes': 'Kubernetes',
    'jenkins': 'Jenkins',
    'git': 'Git',
    'github': 'GitHub',
    'gitlab': 'GitLab',
    'nginx': 'Nginx',
    'linux': 'Linux',

    'ci/cd': 'CI/CD',
    'cicd': 'CI/CD',

    # ========== 云平台 ==========
    'aws': 'AWS',
    'amazon web services': 'AWS',
    'aw': 'AWS',

    'azure': 'Azure',

    'gcp': 'GCP',
    'gc': 'GCP',
    'google cloud': 'GCP',

    # ========== 大数据 ==========
    'spark streaming': 'Spark',
    'structured streaming': 'Spark',
    'elk': 'Elasticsearch',
    'elk stack': 'Elasticsearch',

    # ========== AI/ML ==========
    'tensorflow': 'TensorFlow',
    'tf': 'TensorFlow',

    'pytorch': 'PyTorch',

    'keras': 'Keras',

    'sklearn': 'Scikit-learn',
    'scikit-learn': 'Scikit-learn',

    'xgboost': 'XGBoost',
    'lightgbm': 'LightGBM',
    'catboost': 'CatBoost',

    'opencv': 'OpenCV',
    'cv': 'OpenCV',

    'nlp': 'NLTK',

    'spacy': 'SpaCy',

    # ========== 移动开发 ==========
    'reactnative': 'React Native',
    'react native': 'React Native',

    # ========== 微服务 ==========
    'rest': 'REST API',
    'graphql': 'GraphQL',
    'grpc': 'gRPC',
    'microservice': 'Microservices',

    # ========== 办公软件 ==========
    'excel': 'Excel',
    'word': 'Word',
    'powerpoint': 'PowerPoint',
    'ppt': 'PowerPoint',
    'ppoint': 'PowerPoint',
    'outlook': 'Outlook',
    'sap': 'SAP',
    'oa': 'OA',
    'erp': 'ERP',
    'crm': 'CRM',

    # ========== 财务相关 ==========
    '审计': '审计',
    '税务': '税务',

    # ========== HR相关 ==========
    'hrbp': 'HRBP',

    # ========== 管理技能 ==========
    'pm': 'PMP',
    'pmp': 'PMP',
    'scrum': 'Scrum',
    'agile': 'Agile',

    # ========== 语言技能 ==========
    'english': '英语',
    'cet-6': '英语六级',
    'cet6': '英语六级',
    'cet-4': '英语四级',
    'cet4': '英语四级',
    'german': '德语',
    'french': '法语',
    'japanese': '日语',

    # ========== AI平台 ==========
    'coze': 'Coze',
    'chatgpt': 'ChatGPT',
    'gpt': 'ChatGPT',
    'gpt-4': 'GPT-4',
    'langchain': 'LangChain',
}

# 常见错别字映射
SKILL_TYPOS = {
    # 编程语言错���字
    'javascirpt': 'JavaScript',
    'javscript': 'JavaScript',
    'tyepscript': 'TypeScript',
    'typesript': 'TypeScript',
    'phyton': 'Python',
    'pyton': 'Python',

    # 前端框架错别字
    'reactjs': 'React',
    'vuejs': 'Vue',

    # 数据库错别字
    'postgre': 'PostgreSQL',
    'postgressql': 'PostgreSQL',
    'monogdb': 'MongoDB',
    'mongdb': 'MongoDB',

    # 云平台错别字
    'amazone web services': 'AWS',
    'amazonservices': 'AWS',

    # 框架错别字
    'djanggo': 'Django',
    'flaslk': 'Flask',
    'fastapii': 'FastAPI',
    'springboot': 'Spring Boot',
}
