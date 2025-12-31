"""评分分类服务 - 根据Agent返回的分数进行分类"""
import logging

logger = logging.getLogger(__name__)


class ScreeningClassifier:
    """筛选结果分类器"""

    # 分数阈值
    PASS_THRESHOLD = 70    # 可以发offer
    REVIEW_THRESHOLD = 40  # 待定

    def classify(self, agent_score: int) -> str:
        """根据外部agent分数分类

        Args:
            agent_score: Agent返回的分数(0-100)

        Returns:
            "可以发offer"  # 70-100
            "待定"        # 40-70
            "不合格"      # 0-40
        """
        if agent_score >= self.PASS_THRESHOLD:
            return "可以发offer"
        elif agent_score >= self.REVIEW_THRESHOLD:
            return "待定"
        else:
            return "不合格"

    def get_thresholds(self) -> dict:
        """获取当前阈值配置

        Returns:
            阈值字典 {pass: int, review: int}
        """
        return {
            "pass": self.PASS_THRESHOLD,
            "review": self.REVIEW_THRESHOLD
        }
