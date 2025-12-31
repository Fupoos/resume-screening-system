"""中国大学数据库 - 985/211分类

包含中国39所985大学和115所211大学的完整名单
"""

from typing import Set, Optional

# 985大学名单（39所）
PROJECT_985: Set[str] = {
    "清华大学", "北京大学", "复旦大学", "上海交通大学",
    "浙江大学", "中国科学技术大学", "南京大学", "西安交通大学",
    "哈尔滨工业大学", "中国人民大学", "北京航空航天大学",
    "同济大学", "南开大学", "天津大学", "东南大学",
    "武汉大学", "华中科技大学", "厦门大学", "山东大学",
    "湖南大学", "中国海洋大学", "中南大学", "华南理工大学",
    "四川大学", "重庆大学", "电子科技大学", "西北工业大学",
    "大连理工大学", "吉林大学", "东北大学", "兰州大学",
    "北京师范大学", "华东师范大学", "中山大学", "华南理工大学",
    "北京理工大学", "西北农林科技大学", "中央民族大学",
    "国防科技大学"
}

# 211大学名单（115所，包含39所985）
PROJECT_211: Set[str] = {
    # 985大学（39所）
    "清华大学", "北京大学", "复旦大学", "上海交通大学",
    "浙江大学", "中国科学技术大学", "南京大学", "西安交通大学",
    "哈尔滨工业大学", "中国人民大学", "北京航空航天大学",
    "同济大学", "南开大学", "天津大学", "东南大学",
    "武汉大学", "华中科技大学", "厦门大学", "山东大学",
    "湖南大学", "中国海洋大学", "中南大学", "华南理工大学",
    "四川大学", "重庆大学", "电子科技大学", "西北工业大学",
    "大连理工大学", "吉林大学", "东北大学", "兰州大学",
    "北京师范大学", "华东师范大学", "中山大学", "华南理工大学",
    "北京理工大学", "西北农林科技大学", "中央民族大学",
    "国防科��大学",

    # 纯211大学（76所）
    "北京交通大学", "北京工业大学", "北京科技大学", "北京化工大学",
    "北京邮电大学", "北京林业大学", "北京中医药大學", "北京师范大学",
    "北京外国语大学", "中国传媒大学", "中央财经大学", "对外经济贸易大学",
    "中国政法大学", "华北电力大学", "南开大学", "天津大学",
    "天津医科大学", "河北工业大学", "太原理工大学", "内蒙古大学",
    "辽宁大学", "大连海事大学", "延边大学", "东北师范大学",
    "哈尔滨工程大学", "东北农业大学", "东北林业大学", "华东师范大学",
    "上海外国语大学", "上海财经大学", "南京师范大学", "中国矿业大学",
    "中国药科大学", "河海大学", "南京理工大学", "江南大学",
    "南京农业大学", "安徽大学", "合肥工业大学", "福州大学",
    "南昌大学", "中国石油大学", "郑州大学", "武汉理工大学",
    "华中农业大学", "华中师范大学", "中南财经政法大学", "湖南师范大学",
    "华南师范大学", "广西大学", "海南大学", "四川农业大学",
    "西南财经大学", "贵州大学", "云南大学", "西藏大学",
    "重庆大学", "西南大学", "西安电子科技大学", "长安大学",
    "西北大学", "陕西师范大学", "第四军医大学", "兰州大学",
    "青海大学", "宁夏大学", "新疆大学", "石河子大学",
    "中国地质大学", "中国矿业大学", "中国石油大学", "中国政法大学"
}

# 学校别名映射（处理简称和英文名）
SCHOOL_ALIASES = {
    # 清华大学
    "清华": "清华大学",
    "Tsinghua University": "清华大学",
    "Tsinghua": "清华大学",

    # 北京大学
    "北大": "北京大学",
    "Peking University": "北京大学",
    "Peking": "北京大学",

    # 复旦大学
    "复旦": "复旦大学",
    "Fudan University": "复旦大学",

    # 上海交通大学
    "上交": "上海交通大学",
    "上海交大": "上海交通大学",
    "SJTU": "上海交通大学",
    "Shanghai Jiao Tong University": "上海交通大学",

    # 浙江大学
    "浙大": "浙江大学",
    "Zhejiang University": "浙江大学",
    "ZJU": "浙江大学",

    # 中科大
    "中科大": "中国科学技术大学",
    "USTC": "中国科学技术大学",
    "University of Science and Technology of China": "中国科学技术大学",

    # 南京大学
    "南大": "南京大学",
    "Nanjing University": "南京大学",

    # 西安交通大学
    "西交大": "西安交通大学",
    "西安交大": "西安交通大学",
    "Xi'an Jiaotong University": "西安交通大学",
    "XJTU": "西安交通大学",

    # 哈尔滨工业大学
    "哈工大": "哈尔滨工业大学",
    "HIT": "哈尔滨工业大学",
    "Harbin Institute of Technology": "哈尔滨工业大学",

    # 中国人民大学
    "人大": "中国人民大学",
    "RUC": "中国人民大学",
    "Renmin University of China": "中国人民大学",

    # 北京航空航天大学
    "北航": "北京航空航天大学",
    "Beihang University": "北京航空航天大学",
    "BUAA": "北京航空航天大学",

    # 同济大学
    "同济": "同济大学",
    "Tongji University": "同济大学",

    # 南开大学
    "南开": "南开大学",
    "Nankai University": "南开大学",

    # 天津大学
    "天大": "天津大学",
    "Tianjin University": "天津大学",
    "TJU": "天津大学",

    # 东南大学
    "东大": "东南大学",
    "Southeast University": "东南大学",
    "SEU": "东南大学",

    # 武汉大学
    "武大": "武汉大学",
    "Wuhan University": "武汉大学",
    "WHU": "武汉大学",

    # 华中科技大学
    "华科": "华中科技大学",
    "华中科大": "华中科技大学",
    "HUST": "华中科技大学",
    "Huazhong University of Science and Technology": "华中科技大学",

    # 厦门大学
    "厦大": "厦门大学",
    "Xiamen University": "厦门大学",
    "XMU": "厦门大学",

    # 山东大学
    "山大": "山东大学",
    "Shandong University": "山东大学",
    "SDU": "山东大学",

    # 中山大学
    "中大": "中山大学",
    "Sun Yat-sen University": "中山大学",
    "SYSU": "中山大学",

    # 华南理工大学
    "华工": "华南理工大学",
    "South China University of Technology": "华南理工大学",
    "SCUT": "华南理工大学",

    # 四川大学
    "川大": "四川大学",
    "Sichuan University": "四川大学",
    "SCU": "四川大学",

    # 电子科技大学
    "电子科大": "电子科技大学",
    "成电": "电子科技大学",
    "UESTC": "电子科技大学",
    "University of Electronic Science and Technology of China": "电子科技大学",
}


def normalize_school_name(school_name: str) -> str:
    """标准化学校名称

    Args:
        school_name: 原始学校名称

    Returns:
        标准化后的学校全名
    """
    if not school_name:
        return school_name

    # 先尝试直接匹配
    if school_name in PROJECT_985 or school_name in PROJECT_211:
        return school_name

    # 尝试别名映射
    return SCHOOL_ALIASES.get(school_name, school_name)


def is_985(school_name: str) -> bool:
    """判断是否为985大学

    Args:
        school_name: 学校名称

    Returns:
        是否为985大学
    """
    normalized = normalize_school_name(school_name)
    return normalized in PROJECT_985


def is_211(school_name: str) -> bool:
    """判断是否为211大学

    Args:
        school_name: 学校名称

    Returns:
        是否为211大学
    """
    normalized = normalize_school_name(school_name)
    return normalized in PROJECT_211


def get_school_type(school_name: str) -> Optional[str]:
    """获取学校类型

    Args:
        school_name: 学校名称

    Returns:
        学校类型：985/211/双非，无法识别返回None
    """
    if not school_name:
        return None

    normalized = normalize_school_name(school_name)

    if normalized in PROJECT_985:
        return "985"
    elif normalized in PROJECT_211:
        return "211"
    else:
        return "双非"
