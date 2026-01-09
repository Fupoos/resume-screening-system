"""大学等级数据库

用于分类大学为985/211/QS前50/100/200/双非

数据来源：
- 985工程大学名单（39所）
- 211工程大学名单（115所，含39所985）
- QS世界大学排名前200（含中国和外国大学）
"""

# ============== 中国大学数据 ==============

# 985工程大学（39所）
UNIVERSITIES_985 = [
    "清华大学", "北京大学", "厦门大学", "复旦大学", "南开大学",
    "武汉大学", "中山大学", "华南理工大学", "西安交通大学", "中国科学技术大学",
    "南京大学", "哈尔滨工业大学", "浙江大学", "天津大学", "山东大学",
    "华中科技大学", "东南大学", "四川大学", "吉林大学", "同济大学",
    "北京航空航天大学", "北京师范大学", "中国人民大学", "大连理工大学", "西北工业大学",
    "华东师范大学", "北京理工大学", "重庆大学", "湖南大学", "兰州大学",
    "东北大学", "中国海洋大学", "中南大学", "电子科技大学", "西北农林科技大学",
    "中央民族大学", "国防科学技术大学", "华东理工大学", "中国农业大学",
]

# 211工程大学（不含985，共76所）
UNIVERSITIES_211_ONLY = [
    "上海外国语大学", "上海财经大学", "北京外国语大学", "对外经济贸易大学",
    "北京邮电大学", "中国政法大学", "中央财经大学", "中国传媒大学",
    "北京交通大学", "北京科技大学", "北京化工大学", "北京工业大学",
    "北京林业大学", "北京中医药大学", "中国石油大学(华东)", "中国石油大学(北京)",
    "中国地质大学(武汉)", "中国地质大学(北京)", "中国矿业大学(北京)", "中国矿业大学(徐州)",
    "哈尔滨工程大学", "东北林业大学", "东北农业大学", "东北师范大学",
    "延边大学", "辽宁大学", "大连海事大学", "吉林大学",
    "东华大学", "华东理工大学", "上海大学",
    "苏州大学", "南京师范大学", "中国药科大学", "河海大学",
    "南京航空航天大学", "江南大学", "南京农业大学",
    "安徽大学", "合肥工业大学", "福州大学",
    "南昌大学", "郑州大学", "武汉理工大学", "华中师范大学",
    "华中农业大学", "中南财经政法大学", "湖南师范大学", "华南师范大学",
    "广西大学", "海南大学", "四川农业大学", "西南交通大学",
    "西南大学", "西南财经大学", "贵州大学",
    "云南大学", "西藏大学", "西北大学", "西安电子科技大学",
    "长安大学", "陕西师范大学", "青海大学", "宁夏大学",
    "新疆大学", "内蒙古大学", "石河子大学",
]

# QS世界大学排名（中国大学，2024/2025）
UNIVERSITIES_QS_TOP_50_CHINA = [
    "北京大学", "清华大学", "复旦大学", "上海交通大学", "浙江大学",
    "中国科学技术大学", "南京大学", "同济大学", "武汉大学",
]

UNIVERSITIES_QS_51_100_CHINA = [
    "哈尔滨工业大学", "西安交通大学", "中山大学", "南开大学",
    "北京师范大学", "华中科技大学", "天津大学", "东南大学",
]

UNIVERSITIES_QS_101_200_CHINA = [
    "北京航空航天大学", "厦门大学", "四川大学", "华南理工大学",
    "华东师范大学", "大连理工大学", "山东大学", "中南大学",
    "吉林大学", "湖南大学", "华东理工大学", "北京理工大学",
    "重庆大学", "北京科技大学", "北京工业大学", "中国农业大学",
    "北京外国语大学", "南京航空航天大学", "南京理工大学", "中国海洋大学",
    "东华大学", "华东政法大学", "北京邮电大学", "上海财经大学",
    "西南交通大学", "哈尔滨工程大学", "深圳大学", "苏州大学",
]

# ============== 国外大学数据 (QS World University Rankings) ==============

# QS TOP 50 国外大学（不含中国）
UNIVERSITIES_QS_TOP_50_FOREIGN = [
    # 美国
    "Massachusetts Institute of Technology", "MIT", "麻省理工学院",
    "Stanford University", "Stanford", "斯坦福大学",
    "Harvard University", "Harvard", "哈佛大学",
    "California Institute of Technology", "Caltech", "加州理工学院",
    "University of Chicago", "Chicago", "芝加哥大学",
    "University of Pennsylvania", "Penn", "宾夕法尼亚大学",
    "Cornell University", "Cornell", "康奈尔大学",
    "Yale University", "Yale", "耶鲁大学",
    "Columbia University", "Columbia", "哥伦比亚大学",
    "Princeton University", "Princeton", "普林斯顿大学",
    "University of Michigan", "Michigan", "密歇根大学",
    "Johns Hopkins University", "约翰霍普金斯大学",
    "University of California, Berkeley", "UC Berkeley", "加州大学伯克利分校",
    "Northwestern University", "西北大学",
    "New York University", "NYU", "纽约大学",
    "University of California, Los Angeles", "UCLA", "加州大学洛杉矶分校",
    "Duke University", "杜克大学",
    "Carnegie Mellon University", "CMU", "卡内基梅隆大学",
    "University of California, San Diego", "UCSD", "加州大学圣地亚哥分校",
    "Brown University", "布朗大学",
    "University of Texas at Austin", "德克萨斯大学奥斯汀分校",
    "University of Illinois Urbana-Champaign", "UIUC", "伊利诺伊大学厄巴纳-香槟分校",
    "University of Washington", "华盛顿大学",
    "Georgia Institute of Technology", "Georgia Tech", "佐治亚理工学院",
    "University of Wisconsin-Madison", "威斯康星大学麦迪逊分校",
    "University of North Carolina at Chapel Hill", "北卡罗来纳大学教堂山分校",
    # 英国
    "University of Oxford", "Oxford", "牛津大学",
    "University of Cambridge", "Cambridge", "剑桥大学",
    "Imperial College London", "Imperial", "帝国理工学院",
    "University College London", "UCL", "伦敦大学学院",
    "King's College London", "KCL", "伦敦国王学院",
    "University of Edinburgh", "爱丁堡大学",
    "University of Manchester", "曼彻斯特大学",
    "London School of Economics", "LSE", "伦敦政治经济学院",
    "University of Bristol", "布里斯托大学",
    # 瑞士
    "ETH Zurich", "苏黎世联邦理工学院",
    "Ecole Polytechnique Federale de Lausanne", "EPFL", "洛桑联邦理工学院",
    # 新加坡
    "Nanyang Technological University", "NTU", "南洋理工大学",
    "National University of Singapore", "NUS", "新加坡国立大学",
    # 澳大利亚
    "University of Melbourne", "墨尔本大学",
    "University of Sydney", "悉尼大学",
    "UNSW Sydney", "新南威尔士大学",
    "Australian National University", "ANU", "澳大利亚国立大学",
    # 加拿大
    "University of Toronto", "多伦多大学",
    "McGill University", "麦吉尔大学",
    "University of British Columbia", "UBC", "英属哥伦比亚大学",
    # 日本
    "University of Tokyo", "Tokyo", "东京大学",
    "Kyoto University", "京都大学",
    # 韩国
    "Korea Advanced Institute of Science and Technology", "KAIST", "韩国科学技术院",
    "Seoul National University", "首尔国立大学",
    # 法国
    "PSL Research University", "巴黎文理研究大学",
    "Institut Polytechnique de Paris", "巴黎理工学院",
    "Sorbonne University", "索邦大学",
    # 德国
    "Ludwig Maximilian University of Munich", "LMU Munich", "慕尼黑大学",
    "Technical University of Munich", "TUM", "慕尼黑工业大学",
    "Heidelberg University", "海德堡大学",
    # 荷兰
    "Delft University of Technology", "代尔夫特理工大学",
    "Utrecht University", "乌得勒支大学",
    # 中国香港
    "University of Hong Kong", "HKU", "香港大学",
    "Hong Kong University of Science and Technology", "HKUST", "香港科技大学",
    "Chinese University of Hong Kong", "CUHK", "香港中文大学",
    "City University of Hong Kong", "香港城市大学",
    "Hong Kong Polytechnic University", "香港理工大学",
    # 中国台湾
    "National Taiwan University", "NTU", "台湾大学",
]

# QS 51-100 国外大学
UNIVERSITIES_QS_51_100_FOREIGN = [
    # 美国
    "Boston University", "波士顿大学",
    "Ohio State University", "俄亥俄州立大学",
    "Purdue University", "普渡大学",
    "University of Southern California", "USC", "南加州大学",
    "University of California, Davis", "UCD", "加州大学戴维斯分校",
    "University of California, Irvine", "UCI", "加州大学欧文分校",
    "Michigan State University", "密歇根州立大学",
    "Texas A&M University", "德州农工大学",
    "University of Pittsburgh", "匹兹堡大学",
    "Penn State University", "宾州州立大学",
    "University of Florida", "佛罗里达大学",
    "Rice University", "莱斯大学",
    "University of Minnesota Twin Cities", "明尼苏达大学双城分校",
    "University of Rochester", "罗切斯特大学",
    "University of Maryland, College Park", "马里兰大学",
    "North Carolina State University", "北卡罗来纳州立大学",
    "University of California, Santa Barbara", "UCSB", "加州大学圣塔芭芭拉分校",
    "University of Virginia", "弗吉尼亚大学",
    "University of Colorado Boulder", "科罗拉多大学博尔德分校",
    "University of California, Santa Cruz", "加州大学圣克鲁兹分校",
    "Case Western Reserve University", "凯斯西储大学",
    # 英国
    "University of Warwick", "华威大学",
    "University of Glasgow", "格拉斯哥大学",
    "University of Birmingham", "伯明翰大学",
    "University of Sheffield", "谢菲尔德大学",
    "University of Leeds", "利兹大学",
    "University of Southampton", "南安普顿大学",
    "Durham University", "杜伦大学",
    "University of St Andrews", "圣安德鲁斯大学",
    # 澳大利亚
    "University of Queensland", "昆士兰大学",
    "Monash University", "莫纳什大学",
    "University of New South Wales", "UNSW", "新南威尔士大学",
    # 加拿大
    "University of Alberta", "阿尔伯塔大学",
    "University of Montreal", "蒙特利尔大学",
    "McMaster University", "麦克马斯特大学",
    # 法国
    "Aix-Marseille University", "艾克斯-马赛大学",
    "University of Paris", "巴黎大学",
    # 德国
    "Humboldt University of Berlin", "柏林洪堡大学",
    "RWTH Aachen University", "亚琛工业大学",
    "University of Freiburg", "弗莱堡大学",
    "Technical University of Berlin", "柏林工业大学",
    # 荷兰
    "Leiden University", "莱顿大学",
    "Erasmus University Rotterdam", "伊拉斯姆斯大学鹿特丹",
    # 瑞典
    "Lund University", "隆德大学",
    "Uppsala University", "乌普萨拉大学",
    "KTH Royal Institute of Technology", "瑞典皇家理工学院",
    # 比利时
    "KU Leuven", "鲁汶大学",
    "Ghent University", "根特大学",
    # 丹麦
    "University of Copenhagen", "哥本哈根大学",
    "Technical University of Denmark", "丹麦科技大学",
    # 芬兰
    "University of Helsinki", "赫尔辛基大学",
    "Aalto University", "阿尔托大学",
    # 挪威
    "University of Oslo", "奥斯陆大学",
    # 中国香港
    "Hong Kong Baptist University", "香港浸会大学",
    # 中国台湾
    "National Tsing Hua University", "清华大学", "台湾清华大学",
    "National Chiao Tung University", "交通大学", "台湾交通大学",
]

# QS 101-200 国外大学
UNIVERSITIES_QS_101_200_FOREIGN = [
    # 美国
    "Arizona State University", "亚利桑那州立大学",
    "University of Illinois Chicago", "伊利诺伊大学芝加哥分校",
    "Northeastern University", "东北大学",
    "University at Buffalo SUNY", "布法罗纽约州立大学",
    "University of California, Riverside", "加州大学河滨分校",
    "University of California, Merced", "加州大学默塞德分校",
    "University of California, San Francisco", "UCSF", "加州大学旧金山分校",
    "University of South Florida", "南佛罗里达大学",
    "University of Massachusetts Amherst", "马萨诸塞大学阿默斯特分校",
    "University of Nebraska-Lincoln", "内布拉斯加大学林肯分校",
    "University of Utah", "犹他大学",
    "Iowa State University", "爱荷华州立大学",
    "University of Oregon", "俄勒冈大学",
    "University of Kansas", "堪萨斯大学",
    "Clemson University", "克莱姆森大学",
    "Virginia Tech", "弗吉尼亚理工大学",
    "University of Kentucky", "肯塔基大学",
    "Oklahoma State University", "俄克拉荷马州立大学",
    "University of Alabama", "阿拉巴马大学",
    "University of Arizona", "亚利桑那大学",
    "Auburn University", "奥本大学",
    "University of Tennessee, Knoxville", "田纳西大学诺克斯维尔分校",
    # 英国
    "University of Nottingham", "诺丁汉大学",
    "Newcastle University", "纽卡斯尔大学",
    "Queen Mary University of London", "伦敦玛丽女王大学",
    "Royal Holloway University of London", "伦敦大学皇家霍洛威",
    "Birkbeck University of London", "伦敦大学伯贝克学院",
    "SOAS University of London", "伦敦大学亚非学院",
    "University of East Anglia", "东英吉利大学",
    "Loughborough University", "拉夫堡大学",
    "University of Sussex", "萨塞克斯大学",
    "University of York", "约克大学",
    "University of Exeter", "埃克塞特大学",
    "University of Reading", "雷丁大学",
    "University of Bath", "巴斯大学",
    "Aston University", "阿斯顿大学",
    "Brunel University London", "布鲁内尔大学",
    "Heriot-Watt University", "赫瑞瓦特大学",
    # 澳大利亚
    "University of Adelaide", "阿德莱德大学",
    "University of Western Australia", "西澳大学",
    "University of Technology Sydney", "UTS", "悉尼科技大学",
    "University of Wollongong", "伍伦贡大学",
    "Queensland University of Technology", "昆士兰科技大学",
    "RMIT University", "RMIT", "墨尔本皇家理工大学",
    "Curtin University", "科廷大学",
    "Griffith University", "格里菲斯大学",
    "Macquarie University", "麦考瑞大学",
    "University of Newcastle", "纽卡斯尔大学（澳洲）",
    "Flinders University", "弗林德斯大学",
    "La Trobe University", "拉筹伯大学",
    "Swinburne University of Technology", "斯威本科技大学",
    "Bond University", "邦德大学",
    # 新西兰
    "University of Auckland", "奥克兰大学",
    "University of Otago", "奥塔哥大学",
    "Victoria University of Wellington", "惠灵顿维多利亚大学",
    # 加拿大
    "University of Calgary", "卡尔加里大学",
    "University of Waterloo", "滑铁卢大学",
    "University of Ottawa", "渥太华大学",
    "Western University", "西安大略大学",
    "University of Saskatchewan", "萨斯喀彻温大学",
    "Dalhousie University", "达尔豪斯大学",
    "Simon Fraser University", "西蒙菲莎大学",
    "University of Victoria", "维多利亚大学",
    "Laval University", "拉瓦尔大学",
    "Concordia University", "康考迪亚大学",
    # 日本
    "Osaka University", "大阪大学",
    "Tokyo Institute of Technology", "东京工业大学",
    "Tohoku University", "东北大学",
    "Nagoya University", "名古屋大学",
    "Kyushu University", "九州大学",
    "Hokkaido University", "北海道大学",
    "Waseda University", "早稻田大学",
    "Keio University", "庆应义塾大学",
    # 韩国
    "Korea University", "高丽大学",
    "Yonsei University", "延世大学",
    "Hanyang University", "汉阳大学",
    "Sungkyunkwan University", "成均馆大学",
    "Pohang University of Science and Technology", "POSTECH", "浦项工科大学",
    "Ulsan National Institute of Science and Technology", "UNIST", "蔚山科学技术院",
    "Kyung Hee University", "庆熙大学",
    "Ewha Womans University", "梨花女子大学",
    # 中国香港
    "Lingnan University Hong Kong", "岭南大学",
    # 中国台湾
    "National Cheng Kung University", "成功大学",
    "National Yang Ming Chiao Tung University", "阳明交通大学",
    "National Central University", "中央大学",
    # 马来西亚
    "University of Malaya", "马来亚大学",
    # 泰国
    "Chulalongkorn University", "朱拉隆功大学",
    "Mahidol University", "玛希隆大学",
    # 印尼
    "University of Indonesia", "印度尼西亚大学",
    "Gadjah Mada University", "加查马达大学",
    # 菲律宾
    "University of the Philippines", "菲律宾大学",
    # 印度
    "Indian Institute of Technology Bombay", "IIT Bombay", "印度理工学院孟买分校",
    "Indian Institute of Technology Delhi", "IIT Delhi", "印度理工学院德里分校",
    "Indian Institute of Technology Madras", "IIT Madras", "印度理工学院马德拉斯分校",
    "Indian Institute of Technology Kanpur", "IIT Kanpur", "印度理工学院坎普尔分校",
    "Indian Institute of Science", "IISc", "印度科学理工学院",
    "University of Delhi", "德里大学",
    # 爱尔兰
    "Trinity College Dublin", "都柏林圣三一学院",
    "University College Dublin", "都柏林大学",
    "National University of Ireland Galway", "爱尔兰国立大学高威分校",
    # 以色列
    "Technion-Israel Institute of Technology", "以色列理工学院",
    "Hebrew University of Jerusalem", "耶路撒冷希伯来大学",
    "Tel Aviv University", "特拉维夫大学",
    # 西班牙
    "University of Barcelona", "巴塞罗那大学",
    "Autonomous University of Barcelona", "巴塞罗那自治大学",
    "Complutense University of Madrid", "马德里康普顿斯大学",
    "University of Madrid", "马德里大学",
    # 意大利
    "Sapienza University of Rome", "罗马第一大学",
    "University of Milan", "米兰大学",
    "University of Padua", "帕多瓦大学",
    "University of Bologna", "博洛尼亚大学",
    "Polytechnic University of Milan", "米兰理工大学",
    "Polytechnic University of Turin", "都灵理工大学",
    # 奥地利
    "University of Vienna", "维也纳大学",
    "Vienna University of Technology", "维也纳技术大学",
    # 挪威
    "University of Bergen", "卑尔根大学",
    # 希腊
    "National Technical University of Athens", "雅典国立技术大学",
    # 葡萄牙
    "University of Porto", "波尔图大学",
    "University of Lisbon", "里斯本大学",
    # 波兰
    "University of Warsaw", "华沙大学",
    "Jagiellonian University", "雅盖隆大学",
]

# ============== 合并数据 ==============

# 合并所有211大学（含985）
ALL_211 = set(UNIVERSITIES_985 + UNIVERSITIES_211_ONLY)

# QS TOP 50（中国 + 国外）
ALL_QS_TOP_50 = set(UNIVERSITIES_QS_TOP_50_CHINA + UNIVERSITIES_QS_TOP_50_FOREIGN)

# QS 51-100（中国 + 国外）
ALL_QS_51_100 = set(UNIVERSITIES_QS_51_100_CHINA + UNIVERSITIES_QS_51_100_FOREIGN)

# QS 101-200（中国 + 国外）
ALL_QS_101_200 = set(UNIVERSITIES_QS_101_200_CHINA + UNIVERSITIES_QS_101_200_FOREIGN)

# 创建学校名称映射（支持中英文名称和缩写）
SCHOOL_NAME_MAP = {}

# 添加所有学校到映射表
for school_list in [
    UNIVERSITIES_985, UNIVERSITIES_211_ONLY,
    UNIVERSITIES_QS_TOP_50_FOREIGN, UNIVERSITIES_QS_51_100_FOREIGN, UNIVERSITIES_QS_101_200_FOREIGN,
]:
    for school in school_list:
        SCHOOL_NAME_MAP[school.lower()] = school

# 添加中文别名校（如 台大、港大等）
SCHOOL_ALIASES = {
    "台大": "National Taiwan University",
    "台清交": "National Taiwan University",
    "港大": "University of Hong Kong",
    "港中文": "Chinese University of Hong Kong",
    "港科": "Hong Kong University of Science and Technology",
    "港城": "City University of Hong Kong",
    "港理工": "Hong Kong Polytechnic University",
    "清华": "Tsinghua University",
    "北大": "Peking University",
    "复旦": "Fudan University",
    "交大": "Shanghai Jiao Tong University",
    "浙大": "Zhejiang University",
    "南大": "Nanjing University",
    "中科大": "University of Science and Technology of China",
    "哈工大": "Harbin Institute of Technology",
    "同济": "Tongji University",
    "mit": "Massachusetts Institute of Technology",
    "stanford": "Stanford University",
    "harvard": "Harvard University",
    "oxford": "University of Oxford",
    "cambridge": "University of Cambridge",
}

for alias, full_name in SCHOOL_ALIASES.items():
    SCHOOL_NAME_MAP[alias.lower()] = full_name


def classify_university(school_name: str) -> str:
    """分类大学等级

    Args:
        school_name: 大学名称（支持中文、英文、缩写）

    Returns:
        大学等级：'QS前50', 'QS前100', 'QS前200', '985', '211', '双非'

    优先级：QS前50 > QS前100 > QS前200 > 985 > 211 > 双非
    """
    if not school_name:
        return "双非"

    import re

    # 标准化学校名称
    school_clean = school_name.strip()

    # 移除括号及其内容（如 "(211)"、"（211）"、"985"等标签）
    # 使用正则同时处理中文和英文括号
    school_clean = re.sub(r'[()（）][^()（）]*', '', school_clean).strip()

    # 移除末尾的常见标签（可能没有括号的）
    # 例如：东北农业大学211、清华大学985
    school_clean = re.sub(r'(985|211|双一流|一流大学|一流学科)$', '', school_clean).strip()

    school_lower = school_clean.lower()

    # 先通过别名映射获取正式名称
    if school_lower in SCHOOL_NAME_MAP:
        school_clean = SCHOOL_NAME_MAP[school_lower]

    # 优先级1：QS前50
    if school_clean in ALL_QS_TOP_50:
        return "QS前50"

    # 优先级2：QS前100
    if school_clean in ALL_QS_51_100:
        return "QS前100"

    # 优先级3：QS前200
    if school_clean in ALL_QS_101_200:
        return "QS前200"

    # 优先级4：985
    if school_clean in UNIVERSITIES_985:
        return "985"

    # 优先级5：211
    if school_clean in ALL_211:
        return "211"

    # 默认：双非
    return "双非"
