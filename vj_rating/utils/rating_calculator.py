# coding=utf-8

import math
from abc import ABCMeta, abstractmethod


class RatingCalculator(metaclass=ABCMeta):
    """一个计算rating抽象类，为以后更多rating方式提供接口
    """
    @classmethod
    @abstractmethod
    def calculate_rating(contestants):
        """提供`Contestant`的list，对其进行算分，并更新分数

        Arguments:
            contestants {[Contestant]} -- 已经经过排名处理的列表
        """


class CodeforcesCalculator(RatingCalculator):
    """Codeforces方式的算分算法
    """

    class ContestantAdapter():
        '''为这个类的计算构造适配类。
        '''
        rank = 0
        rating = 0
        need_rating = -1
        seed = 1.0
        delta = 0

        @classmethod
        def adapt(cls, contestant):
            c = cls()
            c.contestant = contestant
            c.rating = c.contestant.before_rating
            c.rank = c.contestant.rank
            if c.rating is None:
                c.rating = 1500
            return c

        @classmethod
        def creator_extra_contestant(cls, rating):
            c = cls()
            c.rating = rating
            return c

        def __repr__(self):
            return '<ContestAdaptor %d %d>' % (self.rank, self.rating)

    @classmethod
    def calculate_rating(self, contestants):
        adapt_list = [self.ContestantAdapter.adapt(x) for x in contestants]
        CodeforcesCalculator.process(adapt_list)
        for c in adapt_list:
            c.contestant.user.rating = c.contestant.after_rating = int(c.rating + c.delta)
        return [x.contestant for x in adapt_list]

    @staticmethod
    def get_elo_win_probability(ra, rb):
        return 1.0 / (1.0 + math.pow(10.0, (rb - ra) / 400.0))

    @staticmethod
    def get_seed(contestants, contestant, rating):
        extra_contestant = CodeforcesCalculator.ContestantAdapter.creator_extra_contestant(
            rating)
        result = 1.0
        for other in contestants:
            if not contestant is other:
                result += CodeforcesCalculator.get_elo_win_probability(other.rating,
                                                                       extra_contestant.rating)
        return result

    @staticmethod
    def get_rating_to_rank(contestants, contestant, rank):
        left = 1
        right = 8000
        while right - left > 1:
            mid = (left + right) / 2
            if CodeforcesCalculator.get_seed(contestants, contestant, mid) < rank:
                right = mid
            else:
                left = mid
        return left

    @staticmethod
    def process(contestants):
        if not contestants:
            return

        # RankCalculator.reassignRanks(contestants)
        # 本来应该有的重配排名，这一步骤移动到了`HtmlParser`类里
        for i in contestants:
            i.seed = 1.0
            for j in contestants:
                if not i is j:
                    i.seed += CodeforcesCalculator.get_elo_win_probability(
                        j.rating, i.rating)

        for i in contestants:
            mid_rank = math.sqrt(i.rank * i.seed)
            i.need_rating = CodeforcesCalculator.get_rating_to_rank(
                contestants, i, mid_rank)
            i.delta = (i.need_rating - i.rating) / 2

        contestants.sort(key=lambda d: d.rating, reverse=True)

        s = 0
        for c in contestants:
            s += c.delta
        inc = -s / len(contestants) - 1
        for c in contestants:
            c.delta += inc

        s = 0
        zero_sum_count = min(
            int(4 * round(math.sqrt(len(contestants)))), len(contestants))
        for i in range(0, zero_sum_count):
            s += contestants[i].delta

        inc = min(max(-s / zero_sum_count, -10), 0)
        for c in contestants:
            c.delta += inc
