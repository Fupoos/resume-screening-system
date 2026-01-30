"""基本信息提取器 - 提取姓名、电话、邮箱"""
import re
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class BasicInfoExtractor:
    """基��信息提取器"""

    # 常见姓氏（百家姓）
    COMMON_SURNAMES = set('弼保赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董粱杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍万柯卢莫房裘缪干解应宗丁宣邓郁单杭洪包诸左石崔吉钮程虞乔童游迟湛闻鲍庞逄党蓝牟裘牛农曲刘付白范郝邵叶勤易晏柯蔡贺崔廖江关霍邢程��余潘游戴欧阳司马上官诸葛夏侯东方皇甫尉迟公羊穆可司徒端木易蔡尹于袁邵葛汪田莫雷黎崔盖郝卢安戴严杜季萧饶贾庄邹熊江游姜黎薛叶阎杜余耿芦路毕聂满隋游魏鲁盖葛莫文于董萧任岑顾潘汤彭庞范倪金邵覃汪秦孔毛宁戴骆曹严田霍茹盖景廉史缪夏乔窦岳常盛武奚童柯施梅宾鲁安辛曲蓝鲍蒋耿崔丁票练唐甄祖冷谈宗蓬仇池狄冀钭劳胥逄富栾皮乌索伊乔简尚邢坂巫曾湛蔡邱侯邵康龙万段饶孔邓邵欧阳')

    # 姓名黑名单词
    NAME_BLACKLIST = {
        # 标题类
        '教育背景', '基本信息', '个人优势', '工作经历', '项目经验',
        '求职意向', '教育经历', '专业技能', '自我评价', '联系方式',
        '个人简历', '简历', '姓名', '名字', '候选人', '应聘',
        '求职信息', '出生年月', '政治面貌', '工作年限',
        '个人信息', '个人总结', '个人简介', '个人评价', '优势亮点',
        '掌握技能', '资格证书',
        # 政治面貌（新增）
        '党员', '中共党员', '预备党员', '共青团员', '群众', '民主党派', '无党派',
        '性别', '手机', '电话', '邮箱', '出生日期', '出生年月', '年龄',
        '籍贯', '地址', '婚姻状况', '民族', '现居住地', '通讯地址',
        '邮政编码', '最高学历', '期望薪资', '期望城市', '应聘岗位',
        '求职信息', '工作年限', '政治面貌',
        #第二轮：补充无效名字
        '同学', '微信号', '手机号', '先生', '女士', '小姐',
        #第三轮：更多字段标签
        '出生年日', '工作时长', '联系电话', '现所在地', '相关课程',
        '项目描述', '发件人', '实习留用', '综合绩点', '手机号码',
        '学校住址', '工作地点', '居住地址', '户籍地址', '电子邮箱',
        '主修专业', '所学专业', '专业名称',
        '应用化学', '计算机', '财务管理', '市场营销', '工商管理',
        '信息管理', '软件技术', '网络工程', '电子信息', '机械设计',
        '土木工程', '材料科学', '生物工程', '环境工程', '化学工程',
        #第四轮：更多无效提取结果
        '意向城市', '户籍', '现居城市', '毕业院校', '英语水平',
        '英语', '产品运营', '费用报销', '发送时间', '发送日期', '后端开发',
        '前端开发', '测试开发', '运营管理', '项目管理', '系统架构',
        '数据分析', '数据管理', '技术支持', '软件开发', '系统设计',
        #第五轮：更多字段标签
        '收件人', '客户成功', '求职类型', '业务支持', '客户服务',
        '售后服务', '销售支持', '市场支持', '运营支持', '技术总监',
        '产品总监', '运营总监', '销售经理', '市场经理', '项目经理',
        # 信息字段（原有）
        '男', '女', '年龄', '电话', '邮箱', '邮箱', '地址', '籍贯',
        '学历', '学位', '专业', '学校', '毕业', '院校',
        # 学历
        '本科', '硕士', '博士', '大专', '专科', '高中', '中专',
        '专升本', '研究生', '本科生', '硕士生', '博士生',
        '本科学位', '硕士学位', '博士学位', '双一流',
        # 学科/专业
        '会计', '会计学', '审计', '统计学', '软件工程', '电子信息',
        '计算机科学', '通信工程', '机械工程', '数据科学',
        '人工智能', '自动化', '电气工程', '财务管理',
        # 职位/岗位相关
        '总账会计', '财务专员', '销售总监', '软件工程师', '产品经理',
        '项目经历', '实习经历', '工作内容', '主要职责',
        # 城市/地点
        '上海', '北京', '深圳', '广州', '杭州', '成都', '武汉',
        '西安', '南京', '重庆', '天津', '苏州', '长沙', '青岛', '长春',
        # 公司名（常见误识别）
        '明源云', '用友', '金蝶', '卫泰集团',
        # 其他常见非姓名词汇
        '个人介绍', '基本信息', '专业技能', '主修课程', '获奖情况',
        '证书情况', '语言能力', '计算机能力', '工作内容',
        # 技术术语（防止误识别为姓名）
        '软考', '编程语言', '编程', '数据库', '算法', '前端', '后端',
        '全栈', '运维', '架构', '开发', '设计', '分析', '数据结构',
        '计算机网络', '操作系统', '计算机科学', '软件工程', '人工智能',
        '机器学习', '深度学习', '大数据', '云计算', '区块链',
        '移动开发', 'Web开发', '嵌入式', '网络安全', '游戏开发',
    }

    # 更多现代常见姓氏
    MORE_SURNAMES = set('肖詹陶翟邝佟仲景詹覃桂卜仇全但郇麦嵇荀邴查党隋巢茆莒邴揭雒冼幸邴胥宓蓬荪訾能隗靳郇蓟蔺鄢邴蒯宿邴邴辛奚柏洪穆傅燕段曾湛蔡邱侯邵康')

    @classmethod
    def is_valid_name(cls, name: str, blacklist: set = None) -> bool:
        """判断是否为有效的姓名"""
        if not name:
            return False

        # 使用传入的黑名单或默认黑名单
        if blacklist is None:
            blacklist = cls.NAME_BLACKLIST

        # 检查是否在黑名单中
        if name in blacklist:
            return False

        # 检查是否为称呼而非真实姓名（如"魏女士"、"张先生"）
        if name.endswith('女士') or name.endswith('先生') or name.endswith('小姐') or name.endswith('同学'):
            return False

        # 特殊处理：带·分隔符的姓名（如维吾尔族姓名）
        if '·' in name:
            # 只允许中文和·分隔符
            if not re.match(r'^[\u4e00-\u9fa5·]+$', name):
                return False
            # 去掉·后的长度应该至少2个字
            name_without_dots = name.replace('·', '')
            if len(name_without_dots) < 2:
                return False
            # 长度限制：带·的姓名可以更长（如麦力哈巴·麦麦提江 = 9个字符）
            if len(name) > 20:
                return False
            # 检查第一个字是否是常见姓氏
            all_surnames = cls.COMMON_SURNAMES.copy()
            all_surnames.update(cls.MORE_SURNAMES)
            if name[0] not in all_surnames:
                return False
            return True

        # 检查是否包含非中文字符
        if not re.match(r'^[\u4e00-\u9fa5]+$', name):
            return False

        # 检查长度（姓名通常是2-4个字）
        if len(name) < 2 or len(name) > 4:
            return False

        # 合并所有姓氏
        all_surnames = cls.COMMON_SURNAMES.copy()
        all_surnames.update(cls.MORE_SURNAMES)

        if name[0] not in all_surnames:
            return False

        # 检查是否包含明显的非姓名词汇
        invalid_suffixes = [
            '工程师', '专员', '总监', '经理', '助理', '顾问',
            '经历', '经验', '内容', '职责', '情况', '能力',
            '简历', '应聘', '招聘', '岗位', '职位', '公司',
            '专业', '工程', '科学', '技术', '管理', '经济',
        ]
        for suffix in invalid_suffixes:
            if name.endswith(suffix) or name.startswith(suffix):
                return False

        return True

    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """提取手机号 - 支持多种格式

        支持格式：
        1. 13800138000（连续11位）
        2. 158 0066 4286（带空格）
        3. 139-1234-5678（带横杠）
        4. （+86）139-1234-5678（带国家代码）
        5. Tel:(+86)139-1234-5678（英文格式）
        6. 416-836-8018（北美格式：XXX-XXX-XXXX）
        """
        # 预处理：移除所有空格和中文空格
        text_no_spaces = text.replace(' ', '').replace('　', '')

        # 先尝试直接匹配11位手机号
        match = re.search(r'1[3-9]\d{9}', text_no_spaces)
        if match:
            return match.group()

        # 尝试匹配带国家代码的格式：(+86) 139-1234-5678 或 （+86）139-1234-5678
        match = re.search(r'[\(（]\+86[\)）]\s*-?\s*1[3-9]\d{9}', text_no_spaces)
        if match:
            # 提取纯手机号
            phone_match = re.search(r'1[3-9]\d{9}', match.group())
            if phone_match:
                return phone_match.group()

        # 尝试匹配带横杠的手机号
        match = re.search(r'1[3-9]\d[-\s]?\d{4}[-\s]?\d{4}', text_no_spaces)
        if match:
            # 清理横杠和空格
            phone = match.group()
            phone = phone.replace('-', '').replace(' ', '')
            if len(phone) == 11:
                return phone

        # 匹配座机号（中国）
        match = re.search(r'\d{3,4}-\d{7,8}', text)
        if match:
            return match.group()

        # 匹配北美电话号码格式：XXX-XXX-XXXX 或 (XXX) XXX-XXXX
        # 例如：416-836-8018, (416) 836-8018
        na_patterns = [
            r'\d{3}-\d{3}-\d{4}',           # 416-836-8018
            r'\(\d{3}\)\s*\d{3}-\d{4}',    # (416) 836-8018
            r'\d{3}\.\d{3}\.\d{4}',        # 416.836.8018
            r'\d{10}',                     # 4168368018 (连续10位，但避免匹配纯数字)
        ]
        for pattern in na_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group()
                # 清理格式，统一为 XXX-XXX-XXXX
                phone = re.sub(r'[^\d]', '', phone)
                if len(phone) == 10:
                    # 重新格式化为 XXX-XXX-XXXX
                    return f'{phone[:3]}-{phone[3:6]}-{phone[6:]}'

        return None

    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """提取邮箱"""
        # 匹配邮箱格式
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(pattern, text)

        if match:
            return match.group()

        return None

    @classmethod
    def extract_name(cls, text: str) -> Optional[str]:
        """提取姓名 - 改进版"""
        lines = text.strip().split('\n')

        # 黑名单词
        blacklist = cls.NAME_BLACKLIST

        # 模式：支持带空格的姓名（如"李 晓 斌"）
        for line in lines[:20]:
            line = line.strip()
            if not line:
                continue

            # 匹配 "李 晓 斌" 或 "李 晓" 格式（姓和名之间有空格）
            # 支持二到三个字之间有空格
            match = re.search(r'^([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])(?:\s+([\u4e00-\u9fa5]))?', line)
            if match:
                # 提取姓名（去除空格）
                parts = [g for g in match.groups() if g]
                name = ''.join(parts)
                # 验证：2-4个字，且在黑名单之外
                if 2 <= len(name) <= 4 and cls.is_valid_name(name, blacklist):
                    logger.info(f"从带空格格式提取姓名: {line} → {name}")
                    return name

        # 模式0：支持带·分隔符的姓名（如维吾尔族姓名"麦力哈巴·麦麦提江"）
        for line in lines[:20]:
            line = line.strip()
            if not line:
                continue

            # 匹配带·分隔符的姓名（3-15个汉字，中间可能有·）
            # 例如：麦力哈巴·麦麦提江、阿依古丽·艾合麦提
            match = re.search(r'^([\u4e00-\u9fa5·]{3,20})$', line)
            if match:
                name = match.group(1).strip()
                # 验证：包含·分隔符或超过4个字，且在黑名单之外
                if ('·' in name or len(name.replace('·', '')) > 4) and cls.is_valid_name(name, blacklist):
                    logger.info(f"从带·分隔符格式提取姓名: {line} → {name}")
                    return name

        # 模式0: 查找行首的姓名（常见格式：姓名 求职意向:xxx）
        for line in lines[:20]:
            line = line.strip()
            # 跳过空行和太长的行
            if not line or len(line) > 50:
                continue
            # 匹配行首的2-4个汉字（后面可能跟空格、"求职意向"、"应聘"等）
            match = re.search(r'^([一-龥]{2,4})\s+(求职意向|应聘|意向|岗位)', line)
            if match:
                name = match.group(1).strip()
                if cls.is_valid_name(name, blacklist):
                    return name

            # 匹配行首的2-4个汉字加冒号（可能是姓名但后面是其他信息）
            match = re.search(r'^([一-龥]{2,4})\s*[:：]', line)
            if match:
                name = match.group(1).strip()
                if cls.is_valid_name(name, blacklist):
                    return name

        # 模式0: 优先匹配 "姓名:王 舒" 格式（姓名中间可能有空格）
        for line in lines[:20]:
            line = line.strip()
            # 匹配 "姓名:" 后跟2-4个汉字（可能中间有空格，如 "王 舒"）
            match = re.search(r'姓\s*名\s*[:：]\s*([\u4e00-\u9fa5])\s*([\u4e00-\u9fa5])\s*([\u4e00-\u9fa5])?\s*([\u4e00-\u9fa5])?\s*(?=[^\u4e00-\u9fa5]|$)', line)
            if match:
                parts = [g for g in match.groups() if g]
                name = ''.join(parts)
                if 2 <= len(name) <= 4 and cls.is_valid_name(name, blacklist):
                    logger.info(f"从姓名:xxx格式提取姓名（支持中间空格）: {line} → {name}")
                    return name

        # 模式1: 查找明确的"姓名：xxx"或"名字：xxx"格式
        for line in lines[:20]:
            line = line.strip()
            # 优先匹配紧凑格式：姓名刘唤性别女年龄23联系电话
            # 姓名后紧跟"性别"、"年龄"、"联系"、"电话"、"手机"等关键词
            match = re.search(r'姓\s*名\s*([\u4e00-\u9fa5]{2,4})(?=性\s*别|年\s*龄|联\s*系|电\s*话|手\s*机)', line)
            if match:
                name = match.group(1).strip()
                if cls.is_valid_name(name, blacklist):
                    logger.info(f"从紧凑格式提取姓名: {line} → {name}")
                    return name

            # 匹配 "姓名：张三" 或 "名字：张三" 或 "候选人：张三"
            match = re.search(r'姓\s*名\s*[:：]\s*([^\s|]{2,4})', line)
            if match:
                name = match.group(1).strip()
                if cls.is_valid_name(name, blacklist):
                    return name

            # 匹配 "Name: 张三"
            match = re.search(r'[Nn]ame\s*[:：]\s*([^\s|]{2,4})', line)
            if match:
                name = match.group(1).strip()
                if cls.is_valid_name(name, blacklist):
                    return name

        # 模式2: 查找独立成行的姓名（2-4个汉字）
        for line in lines[:20]:
            line = line.strip()
            # 跳过太长的行
            if len(line) > 15:
                continue
            # 跳过包含特殊字符的行（但不包括空格、冒号、竖线）
            if re.search(r'[0-9@\.]', line):
                continue
            # 匹配纯中文姓名（2-4个汉字）
            match = re.search(r'^([\u4e00-\u9fa5]{2,4})$', line)
            if match:
                name = match.group(1).strip()
                if cls.is_valid_name(name, blacklist):
                    return name

        # 模式3: 从格式化的行中提取（如 "张三 | 男 | 25岁"）
        for line in lines[:20]:
            line = line.strip()
            # 匹配 "张三|男|25" 或 "张三 | 男 | 25"
            parts = re.split(r'\s*[|｜]\s*', line)
            for part in parts:
                part = part.strip()
                # 第一个部分通常是姓名
                if re.match(r'^[\u4e00-\u9fa5]{2,4}$', part):
                    name = part
                    if cls.is_valid_name(name, blacklist):
                        return name
                    break  # 只检查第一个部分

        # 模式4: 在联系方式附近查找姓名（邮箱/电话前后）
        for i, line in enumerate(lines):
            line = line.strip()
            # 查找包含邮箱或电话号码的行
            if '@' in line or re.search(r'1[3-9]\d{9}', line):
                # 检查前1-3行是否有独立成行的2-4个汉字
                for j in range(max(0, i-3), i):
                    check_line = lines[j].strip()
                    # 匹配独立的2-4个汉字（可能前后有空格）
                    match = re.search(r'^[\s]*([\u4e00-\u9fa5]{2,4})[\s]*$', check_line)
                    if match:
                        name = match.group(1).strip()
                        # 严格检查：不能是黑名单词，第一个字必须是常见姓氏
                        if name not in blacklist and name[0] in cls.COMMON_SURNAMES:
                            if cls.is_valid_name(name, blacklist):
                                return name

                # 检查后1-5行是否有"姓名:xxx"格式
                for j in range(i+1, min(len(lines), i+6)):
                    check_line = lines[j].strip()
                    # 匹配 "姓名:xxx" 或 "姓名：xxx" 格式
                    match = re.search(r'姓\s*名\s*[:：]\s*([^\s:：|]{2,4})', check_line)
                    if match:
                        name = match.group(1).strip()
                        if cls.is_valid_name(name, blacklist):
                            return name

        # 模式5: 在整个文件中搜索"姓名:xxx"格式（支持中间空格）
        # 简历的个人信息通常在末尾，需要扫描全文件
        for line in lines:
            line = line.strip()
            # 优先匹配带空格的格式：姓名:王 舒
            match = re.search(r'姓\s*名\s*[:：]\s*([\u4e00-\u9fa5])\s*([\u4e00-\u9fa5])\s*([\u4e00-\u9fa5])?\s*([\u4e00-\u9fa5])?\s*(?=[^\u4e00-\u9fa5]|$)', line)
            if match:
                parts = [g for g in match.groups() if g]
                name = ''.join(parts)
                if 2 <= len(name) <= 4 and cls.is_valid_name(name, blacklist):
                    logger.info(f"从全文件搜索提取姓名（支持空格）: {line} → {name}")
                    return name

            # 兼容格式：姓名:xxx（无空格）
            match = re.search(r'姓\s*名\s*[:：]\s*([^\s:：|]{2,4})', line)
            if match:
                name = match.group(1).strip()
                # 确保提取到的不是"女士"或"先生"等称呼
                if name not in ['女士', '先生', '先生', '小姐'] and not name.endswith('女士') and not name.endswith('先生'):
                    if cls.is_valid_name(name, blacklist):
                        logger.info(f"从全文件搜索提取姓名: {line} → {name}")
                        return name

        return None

    @classmethod
    def extract_name_from_email_subject(cls, subject: str) -> Optional[str]:
        """从邮件标题中提取姓名

        常见格式（80%是职位-姓名格式）：
        - "产品经理助理-郭子义-西交利物浦大学" （职位-姓名-学校）
        - "Java开发工程师-王明-上海" （职位-姓名-地点）
        - "财务信息化顾问-李景-澳门科技大学" （职位-姓名-学校）
        - "张三 | 10年以上，应聘 销售总监 | 上海40-70K【BOSS直聘】" （姓名在前）
        """
        if not subject:
            return None

        # 黑名单词
        blacklist = {
            '同学', '先生', '女士', '求职者', '候选人', '应届生',
            '开发', '工程师', '设计师', '实施', '顾问',
        }

        # 模式1: "职位-姓名-其他"（最常见，80%的情况）
        # 匹配：职位 - 姓名 - 其他
        # 例如："产品经理助理-郭子义-西交利物浦大学"
        match = re.search(r'-([\u4e00-\u9fa5]{2,4})(?:-|$)', subject)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                return name

        # 模式1b: "职位-姓名（备注）-其他" 或 "职位-姓名（备注）"
        # 例如："财务信息化顾问-李景昱（中）.pdf"、"产品经理-张三（男）"
        match = re.search(r'-([\u4e00-\u9fa5]{2,4})(?:（[^）]*）)?(?:-|$|\.|\s)', subject)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                return name

        # 模式2: "姓名 | 其他信息"（姓名在最前面）
        # 例如："张三 | 10年以上，应聘 销售总监 | 上海40-70K"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})\s*\|', subject)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                return name

        # 模式3: "姓名|其他信息"（没有空格的竖线分隔）
        # 例如："张三|应聘销售总监"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})\|', subject)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                return name

        # 模式4: "【岗位】姓名_其他信息"
        # 例如："【销售总监】张三_简历"
        match = re.search(r'【[^】]*】\s*([\u4e00-\u9fa5]{2,4})_', subject)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                return name

        # 模式5: 尝试从竖线分隔的第一部分提取
        # 例如："张三 | 10年以上 | 应聘岗位"
        parts = re.split(r'\s*[|｜]\s*', subject)
        if len(parts) > 0:
            first_part = parts[0].strip()
            # 第一个部分是纯2-4个汉字
            if re.match(r'^[\u4e00-\u9fa5]{2,4}$', first_part):
                name = first_part
                if cls.is_valid_name(name, blacklist):
                    return name

        return None

    @classmethod
    def extract_name_from_filename(cls, filename: str) -> Optional[str]:
        """从文件名中提取姓名

        常见格式:
        - "财务信息化顾问-李景昱（中）.pdf"
        - "20250130_123456_职位-姓名（备注）.pdf"
        - "产品经理-张三.pdf"
        """
        if not filename:
            return None

        from pathlib import Path

        # 提取纯文件名（去掉路径和扩展名）
        basename = Path(filename).stem

        # 黑名单词
        blacklist = {
            '简历', 'resume', 'cv', '附件', '文档', '同学', '先生', '女士',
            '求职者', '候选人',
        }

        # 模式1: 去除时间戳前缀
        # "20250130_123456_职位-姓名（备注）" -> "职位-姓名（备注）"
        # 匹配开头的时间戳模式：数字_数字_
        basename = re.sub(r'^\d{8}_\d{6}_', '', basename)

        # 模式2: "【职位_地点_薪资】姓名_年限"（BOSS直聘格式）
        # 例如："【财务咨询顾问（深圳）_深圳_10-15K】邹喆_2年.pdf"
        match = re.search(r'】([\u4e00-\u9fa5]{2,4})_', basename)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                return name

        # 模式3: 职位-姓名-其他（支持复杂分隔符）
        # 例如："张先寿-销售管理&IT项目管理 案例-简历25-12.pdf"
        # 例如："市场运营助理-Yoana Li 李珮瑶（中）.pdf"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})[-—]', basename)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                logger.info(f"从文件名提取姓名（职位-姓名格式）: {basename} → {name}")
                return name

        # 模式4: 姓名（备注）格式
        # 例如："李珮瑶（中）" 或 "李珮瑶(中)"
        # 例如："张三（男）" 或 "张三(男)"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})[（\(][^）\)]*[）\)]', basename)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                logger.info(f"从文件名提取姓名（姓名备注格式）: {basename} → {name}")
                return name

        # 模式5: "职位-姓名（备注）-其他" 或 "职位-姓名（备注）"（最常见）
        # 例如："财务信息化顾问-李景昱（中）"
        # 例如："市场运营助理-刘悦（中）.pdf"
        match = re.search(r'-([\u4e00-\u9fa5]{2,4})(?:（[^）]*）)?(?:-|$|\.)', basename)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                return name

        # 模式6: "职位-姓名"（无括号）
        # 例如："产品经理-张三"
        match = re.search(r'-([\u4e00-\u9fa5]{2,4})$', basename)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                return name

        # 模式7: "姓名-简历" 或 "姓名-resume"
        # 例如："李四-简历"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})-(?:简历|resume|cv|附件)$', basename, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                return name

        # 模式8: "姓名_其他信息"格式
        # 例如："彭坤_本科_Java开发工程师.pdf"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})_', basename)
        if match:
            name = match.group(1).strip()
            if cls.is_valid_name(name, blacklist):
                logger.info(f"从文件名提取姓名（姓名_其他格式）: {basename} → {name}")
                return name

        # 模式9: 纯姓名（只有2-4个汉字）
        # 例如："王五.pdf"
        if re.match(r'^[\u4e00-\u9fa5]{2,4}$', basename):
            name = basename.strip()
            if cls.is_valid_name(name, blacklist):
                return name

        return None

    @staticmethod
    def extract_work_years_from_subject(subject: str) -> Optional[int]:
        """从邮件主题中提取工作年限

        支持格式：
        - "张三 | 10年以上，应聘 销售总监"
        - "Java开发工程师-李四-2年经验"
        - "产品经理-王五-5年"
        - "应届生" → 返回 0
        - "24年毕业" → 返回 0（应届生）

        Returns:
            工作年限（年数），应届生返回0，无法提取返回None
        """

        if not subject:
            return None

        # 优先级1: 检查"应届生"关键词
        if '应届生' in subject or '应届毕业生' in subject:
            logger.info(f"从邮件主题识别为应届生")
            return 0

        # 优先级2: 检查"XX年毕业"格式（应届生）
        # 例如: "24年毕业"、"2024年毕业"、"26年毕业"
        match = re.search(r'(\d{2}|\d{4})\s*年\s*毕业', subject)
        if match:
            logger.info(f"从邮件主题识别为应届生（XX年毕业格式）")
            return 0

        # 模式1: "X年以上"
        match = re.search(r'(\d+)\s*年\s*以上', subject)
        if match:
            years = int(match.group(1))
            logger.info(f"从邮件主题提取工作年限: {years}年以上")
            return years

        # 模式2: "X年经验"
        match = re.search(r'(\d+)\s*年\s*经验', subject)
        if match:
            years = int(match.group(1))
            logger.info(f"从邮件主题提取工作年限: {years}年经验")
            return years

        # 模式3: "X年" (单独的数字+年，排除年份如2024年)
        # 但排除"毕业"关键词
        match = re.search(r'(\d+)\s*年(?![以经])', subject)
        if match:
            # 检查这个"X年"是否与"毕业"相关
            # 先看看上下文是否有"毕业"
            before_match = subject[:match.start()]
            after_match = subject[match.end():match.end()+10]
            if '毕业' in before_match or '毕业' in after_match:
                # 这是"XX年毕业"格式，应该是应届生
                logger.info(f"从邮件主题识别为应届生（XX年毕业格式）")
                return 0

            years = int(match.group(1))
            # 排除年份（如2024年）和过大的数字
            if 1 <= years <= 50:  # 工作年限一般在1-50年之间
                logger.info(f"从邮件主题提取工作年限: {years}年")
                return years

        return None
