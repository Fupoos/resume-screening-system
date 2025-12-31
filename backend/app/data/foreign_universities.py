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

# QS前200大学（包含前100）
QS_TOP_200: Set[str] = QS_TOP_100.copy()

# QS 101-200的大学
QS_TOP_200.update({
    # 美国
    "加州大学欧文分校", "加州大学圣克鲁兹分校", "宾夕法尼亚州立大学",
    "北卡罗来纳大学教堂山分校", "波士顿大学", "俄亥俄州立大学", "佐治亚理工学院",
    "伊利诺伊大学厄巴纳-香槟分校", "德克萨斯大学奥斯汀分校", "威斯康星大学麦迪逊分校",
    "佛罗里达大学", "明尼苏达大学双城分校", "密歇根州立大学", "马里兰大学帕克分校",
    "罗切斯特大学", "凯斯西储大学", "里海大学", "东北大学",

    # 英国
    "兰卡斯特大学", "巴斯大学", "拉夫堡大学", "萨塞克斯大学",
    "东英吉利大学", "斯特灵大学", "赫尔大学", "伦敦大学玛丽女王学院",

    # 澳大利亚
    "悉尼科技大学", "堪培拉大学", "纽卡斯尔大学", "麦考瑞大学", "墨尔本皇家理工大学",

    # 加拿大
    "卡尔加里大学", "渥太华大学", "韦仕敦大学", "皇后大学", "西门菲莎大学",

    # 德国
    "汉堡大学", "图宾根大学", "埃尔朗根-纽伦堡大学", "达姆施塔特工业大学",
    "德累斯顿工业大学", "不来梅大学", "波恩大学", "美因茨大学", "汉诺威大学",

    # 法国
    "巴黎萨克雷大学", "格勒诺布尔-阿尔卑斯大学", "巴黎大学", "里昂第一大学",

    # 荷兰
    "阿姆斯特丹自由大学", "埃因霍温理工大学", "特文特大学",

    # 中国香港
    "香港浸会大学", "香港岭南大学", "香港教育大学",

    # 日本
    "九州大学", "东北大学", "北海道大学", "筑波大学", "早稻田大学", "庆应义塾大学",

    # 韩国
    "浦项工科大学", "韩国外国语大学", "中央大学", "韩国加图立大学", "汉阳大学", "庆熙大学",

    # 瑞典
    "哥德堡大学", "查尔姆斯理工大学", "斯德哥尔摩经济学院", "瑞典农业科学大学",

    # 丹麦
    "奥胡斯大学", "南丹麦大学", "技术大学",

    # 挪威
    "挪威科技大学", "卑尔根大学",

    # 芬兰
    "阿尔托大学", "坦佩雷大学", "图尔库大学",

    # 比利时
    "根特大学", "安特卫普大学",

    # 爱尔兰
    "爱尔兰国立都柏林大学", "爱尔兰科克大学", "爱尔兰高威大学",

    # 意大利
    "帕多瓦大学", "博洛尼亚大学", "都灵理工大学", "佛罗伦萨大学", "比萨大学",

    # 西班牙
    "马德里康普顿斯大学", "庞培法布拉大学", "马德里卡洛斯三世大学", "巴塞罗那自治大学",

    # 奥地利
    "维也纳大学", "维也纳技术大学",

    # 瑞士
    "巴塞尔大学", "伯尔尼大学", "洛桑大学",

    # 新加坡
    "新加坡管理大学",

    # 马来西亚
    "马来亚大学",
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

    # QS 101-200 大学英文名映射
    "Lancaster University": "兰卡斯特大学",
    "University of Lancaster": "兰卡斯特大学",
    "Lancaster": "兰卡斯特大学",

    "University of Bristol": "布里斯托大学",
    "University of Warwick": "华威大学",
    "University of Glasgow": "格拉斯哥大学",
    "University of Leeds": "利兹大学",
    "University of Birmingham": "伯明翰大学",
    "University of Sheffield": "谢菲尔德大学",
    "University of Southampton": "南安普顿大学",
    "Newcastle University": "纽卡斯尔大学",
    "University of York": "约克大学",

    "Boston University": "波士顿大学",
    "Ohio State University": "俄亥俄州立大学",
    "Georgia Institute of Technology": "佐治亚理工学院",
    "Georgia Tech": "佐治亚理工学院",
    "UIUC": "伊利诺伊大学厄巴纳-香槟分校",
    "University of Illinois Urbana-Champaign": "伊利诺伊大学厄巴纳-香槟分校",
    "UT Austin": "德克萨斯大学奥斯汀分校",
    "University of Texas at Austin": "德克萨斯大学奥斯汀分校",
    "Penn State": "宾夕法尼亚州立大学",
    "Pennsylvania State University": "宾夕法尼亚州立大学",
    "UNC Chapel Hill": "北卡罗来纳大学教堂山分校",
    "University of North Carolina at Chapel Hill": "北卡罗来纳大学教堂山分校",
    "UC Irvine": "加州大学欧文分校",
    "University of California, Irvine": "加州大学欧文分校",
    "UC Santa Cruz": "加州大学圣克鲁兹分校",
    "University of California, Santa Cruz": "加州大学圣克鲁兹分校",

    "University of Calgary": "卡尔加里大学",
    "University of Ottawa": "渥太华大学",
    "Western University": "韦仕敦大学",
    "University of Western Ontario": "韦仕敦大学",
    "Queen's University": "皇后大学",

    "Kyushu University": "九州大学",
    "Tohoku University": "东北大学",
    "Hokkaido University": "北海道大学",
    "University of Tsukuba": "筑波大学",
    "Waseda University": "早稻田大学",
    "Keio University": "庆应义塾大学",

    "KAIST": "韩国科学技术院",
    "POSTECH": "浦项工科大学",
    "Pohang University of Science and Technology": "浦项工科大学",

    "University of Gothenburg": "哥德堡大学",
    "Chalmers University of Technology": "查尔姆斯理工大学",
    "Aarhus University": "奥胡斯大学",
    "University of Auckland": "奥克兰大学",
    "University of Malaya": "马来亚大学",
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

    # 清理学校名称
    cleaned = school_name.strip()

    # 去除常见的英文名后缀（格式：中文名 English Name）
    # 例如："兰卡斯特大学 Lancaster University" -> "兰卡斯特大学"
    # 使用正则表达式匹配：中文 + 空格/符号 + 英文字母
    import re
    # 匹配：中文部分 + (空格/符号) + 英文部分
    # 保留中文名部分
    match = re.match(r'^([\u4e00-\u9fa5（）()学院大学]+)\s+[A-Za-z\s\'\-.&]+$', cleaned)
    if match:
        cleaned = match.group(1).strip()

    # 再次去除可能残留的英文
    cleaned = re.sub(r'\s*[A-Za-z\s\'\-.&]+$', '', cleaned).strip()

    # 先尝试直接匹配
    if cleaned in QS_TOP_200:
        return cleaned

    # 尝试别名映射
    return FOREIGN_SCHOOL_ALIASES.get(cleaned, FOREIGN_SCHOOL_ALIASES.get(school_name, cleaned))


def get_qs_ranking(school_name: str) -> Optional[str]:
    """获取QS排名

    Args:
        school_name: 学校名称

    Returns:
        QS排名等级：QS前50/QS前100/QS前200/None
    """
    if not school_name:
        return None

    normalized = normalize_foreign_school_name(school_name)

    if normalized in QS_TOP_50:
        return "QS前50"
    elif normalized in QS_TOP_100:
        return "QS前100"
    elif normalized in QS_TOP_200:
        return "QS前200"
    else:
        return None
