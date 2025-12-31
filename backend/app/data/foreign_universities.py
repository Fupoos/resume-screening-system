"""国外大学QS排名数据库

包含QS世界大学排名前100的大学名单
数据来源：QS World University Rankings
"""

from typing import Set, Optional

# QS前50大学（2024��排名）
QS_TOP_50: Set[str] = {
    # 美国
    "麻省理工学院", "哈佛大学", "斯坦福大学", "加州理工学院",
    "芝加哥大学", "普林斯顿大学", "耶鲁大学", "宾夕法尼亚大学",
    "康奈尔大学", "哥伦比亚大学", "密歇根大学", "约翰霍普金斯大学",
    "西北大学", "加州大学伯克利分校", "加州大学洛杉矶分校",

    # 英国
    "剑桥大学", "牛津大学", "帝国理工学院", "伦敦大学学院",
    "爱丁堡大学", "曼彻斯特大学", "伦敦国王学院", "伦敦政治经济学院",

    # 瑞士
    "苏黎世联邦理工学院", "洛桑联邦理工学院",

    # 新加坡
    "新加坡国立大学", "南洋理工大学",

    # 澳大利亚
    "墨尔本大学", "新南威尔士大学", "悉尼大学", "澳大利亚国立大学",

    # 加拿大
    "多伦多大学", "麦吉尔大学", "不列颠哥伦比亚大学",

    # 荷兰
    "代尔夫特理工大学", "阿姆斯特丹大学",

    # 中国香港
    "香港大学", "香港中文大学", "香港科技大学",

    # 日本
    "东京大学",

    # 法国
    "巴黎文理研究大学",

    # 德国
    "慕尼黑工业大学",

    # 韩国
    "首尔国立大学",

    # 中国大陆（已经在985名单中）
    "北京大学", "清华大学", "复旦大学", "上海交通大学",
    "浙江大学", "中国科学技术大学",
}

# QS前100大学（包含前50）
QS_TOP_100: Set[str] = QS_TOP_50.copy()

# QS 51-100的大学
QS_TOP_100.update({
    # 美国
    "杜克大学", "布朗大学", "加州大学圣迭戈分校", "加州大学戴维斯分校",
    "卡内基梅隆大学", "圣路易斯华盛顿大学", "范德堡大学",
    "圣母大学", "乔治城大学", "埃默里大学", "纽约大学",
    "加州大学圣塔芭芭拉分校", "华盛顿大学",

    # 英国
    "布里斯托大学", "华威大学", "格拉斯哥大学", "利兹大学",
    "杜伦大学", "南安普顿大学", "伯明翰大学", "谢菲尔德大学",
    "圣安德鲁斯大学",

    # 澳大利亚
    "蒙纳士大学", "昆士兰大学", "西澳大学", "阿德莱德大学",

    # 加拿大
    "阿尔伯塔大学", "麦克马斯特大学", "蒙特利尔大学", "滑铁卢大学",

    # 德国
    "海德堡大学", "慕尼黑大学", "柏林自由大学", "亚琛工业大学",
    "柏林洪堡大学", "卡尔斯鲁厄理工学院",

    # 法国
    "巴黎理工学院", "索邦大学",

    # 荷兰
    "乌得勒支大学", "莱顿大学", "瓦赫宁根大学", "伊拉斯姆斯大学鹿特丹",

    # 中国香港
    "香港城市大学", "香港理工大学",

    # 新加坡
    -

    # 日本
    "京都大学", "大阪大学", "东京工业大学",

    # 韩国
    "韩国科学技术院", "成均馆大学", "高丽大学", "延世大学", "汉阳大学",

    # 瑞典
    "隆德大学", "皇家理工学院", "乌普萨拉大学", "斯德哥尔摩大学",

    # 丹麦
    "哥本哈根大学", "丹麦技术大学",

    # 挪威
    "奥斯陆大学",

    # 芬兰
    "赫尔辛基大学",

    # 比利时
    "鲁汶大学",

    # 爱尔兰
    "都柏林圣三一学院",

    # 意大利
    "米兰大学", "博科尼大学", "罗马第一大学",

    # 西班牙
    "巴塞罗那大学", "马德里自治大学",

    # 新西兰
    "奥克兰大学",
})

# 学校别名映射（英文名和中文名）
FOREIGN_SCHOOL_ALIASES = {
    # 美国
    "MIT": "麻省理工学院",
    "Massachusetts Institute of Technology": "麻省理工学院",
    "Harvard": "哈佛大学",
    "Harvard University": "哈佛大学",
    "Stanford": "斯坦福大学",
    "Stanford University": "斯坦福大学",
    "Caltech": "加州理工学院",
    "California Institute of Technology": "加州理工学院",
    "University of Chicago": "芝加哥大学",
    "Princeton": "普林斯顿大学",
    "Princeton University": "普林斯顿大学",
    "Yale": "耶鲁大学",
    "Yale University": "耶鲁大学",
    "UPenn": "宾夕法尼亚大学",
    "University of Pennsylvania": "宾夕法尼亚大学",
    "Cornell": "康奈尔大学",
    "Cornell University": "康奈尔大学",
    "Columbia": "哥伦比亚大学",
    "Columbia University": "哥伦比亚大学",
    "UMich": "密歇根大学",
    "University of Michigan": "密歇根大学",
    "Johns Hopkins": "约翰霍普金斯大学",
    "JHU": "约翰霍普金斯大学",
    "Northwestern": "西北大学",
    "Northwestern University": "西北大学",
    "UC Berkeley": "加州大学伯克利分校",
    "University of California, Berkeley": "加州大学伯克利分校",
    "UCLA": "加州大学洛杉矶分校",
    "University of California, Los Angeles": "加州大学洛杉矶分校",

    # 英国
    "Cambridge": "剑桥大学",
    "University of Cambridge": "剑桥大学",
    "Oxford": "牛津大学",
    "University of Oxford": "牛津大学",
    "Imperial College": "帝国理工学院",
    "Imperial": "帝国理工学院",
    "UCL": "伦敦大学学院",
    "University College London": "伦敦大学学院",
    "Edinburgh": "爱丁堡大学",
    "University of Edinburgh": "爱丁堡大学",
    "Manchester": "曼彻斯特大学",
    "University of Manchester": "曼彻斯特大学",
    "KCL": "伦敦国王学院",
    "King's College London": "伦敦国王学院",
    "LSE": "伦敦政治经济学院",
    "London School of Economics": "伦敦政治经济学院",

    # 瑞士
    "ETH Zurich": "苏黎世联邦理工学院",
    "EPFL": "洛桑联邦理工学院",

    # 新加坡
    "NUS": "新加坡国立大学",
    "National University of Singapore": "新加坡国立大学",
    "NTU": "南洋理工大学",
    "Nanyang Technological University": "南洋理工大学",

    # 澳大利亚
    "Melbourne": "墨尔本大学",
    "University of Melbourne": "墨尔本大学",
    "UNSW": "新南威尔士大学",
    "University of New South Wales": "新南威尔士大学",
    "Sydney": "悉尼大学",
    "University of Sydney": "悉尼大学",
    "ANU": "澳大利亚国立大学",
    "Australian National University": "澳大利亚国立大学",

    # 加拿大
    "University of Toronto": "多伦多大学",
    "McGill": "麦吉尔大学",
    "McGill University": "麦吉尔大学",
    "UBC": "不列颠哥伦比亚大学",
    "University of British Columbia": "不列颠哥伦比亚大学",

    # 中国香港
    "HKU": "香港大学",
    "University of Hong Kong": "香港大学",
    "CUHK": "香港中文大学",
    "Chinese University of Hong Kong": "香港中文大学",
    "HKUST": "香港科技大学",
    "Hong Kong University of Science and Technology": "香港科技大学",

    # 日本
    "University of Tokyo": "东京大学",
    "Tokyo University": "东京大学",
    "Kyoto University": "京都大学",
    "Osaka University": "大阪大学",
    "Tokyo Tech": "东京工业大学",

    # 韩国
    "Seoul National University": "首尔国立大学",
    "SNU": "首尔国立大学",
    "KAIST": "韩国科学技术院",
    "Korea Advanced Institute of Science and Technology": "韩国科学技术院",
}


def normalize_foreign_school_name(school_name: str) -> str:
    """标准化国外学校名称

    Args:
        school_name: 原始学校名称

    Returns:
        标准化后的学校中文名
    """
    if not school_name:
        return school_name

    # 先尝试直接匹配
    if school_name in QS_TOP_100:
        return school_name

    # 尝试别名映射
    return FOREIGN_SCHOOL_ALIASES.get(school_name, school_name)


def get_qs_ranking(school_name: str) -> Optional[str]:
    """获取QS排名

    Args:
        school_name: 学校名称

    Returns:
        QS排名等级：QS前50/QS前100/None
    """
    if not school_name:
        return None

    normalized = normalize_foreign_school_name(school_name)

    if normalized in QS_TOP_50:
        return "QS前50"
    elif normalized in QS_TOP_100:
        return "QS前100"
    else:
        return None
