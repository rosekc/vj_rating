from abc import ABCMeta, abstractmethod

import pytz
from bs4 import BeautifulSoup as bs
from dateutil import parser

from .. import db
from ..models import Contest, Contestant, User
from .moment import CHINA_STANDART_TIME_ZONE


class HtmlParser(metaclass=ABCMeta):
    """定义了一个抽象类，为以后支持其他榜单的转换提供接口
    """

    @staticmethod
    @abstractmethod
    def parse(html):
        """是一个抽象方法，定义处理榜单文件的接口

        Arguments:
            html {str} -- html源文件
        """


class VjudgeParser(HtmlParser):
    """提供Vj榜单信息提取功能
    """

    @staticmethod
    def clean(sp):
        """清理榜单
        Arguments:
            sp {BeautifulSoup} -- 输入`BeautifulSoup`对象

        Returns:
            BeautifulSoup -- 输出处理后的`BeautifulSoup`对象
        """
        for i in sp.head.find_all(lambda tag: tag.name != 'title', recursive=False):
            i.decompose()
        for i in sp.body.find_all(lambda tag: tag.get('class') is None
                                  or 'container' not in tag.get('class'), recursive=False):
            i.decompose()
        del_ids = ['discuss', 'status', 'problem', 'contest-tabs']
        sp.body.find(class_='rank_tool').decompose()
        for i in del_ids:
            sp.body.find(id=i).decompose()
        return sp

    @staticmethod
    def parse(html):
        """对榜单进行处理
        主要流程是：
        1. 整理html源文件，对其进行压缩
        2. 读取榜单，创建相应对象，进行相应处理后存储进数据库中

        注意:
        1.写的比较hardcode，可能随着网站更新而需要重写，请定时进行单元测试。
        2.要对排名进行重新计算，这点在爆零用户尤为明显，出现了虽然爆零然而排名不一样的错误。

        Arguments:
            html {str} -- html源文件
        """
        sp = bs(html, 'html.parser')

        VjudgeParser.clean(sp)

        time_span = sp.div.find(
            id='time-info').find_all('span', class_='timestamp')
        rank_tbody = sp.div.find(id='contest_rank').tbody

        contest = Contest(
            id=int(rank_tbody.find('tr')['c']),
            name=sp.title.string.strip().replace(' - Virtual Judge', ''),
            #暂时来看vjudge全站使用中国标准时间，然而CST有多种意思。所以直接转了
            start_time=parser.parse(time_span[0].string, ignoretz=True).astimezone(
                CHINA_STANDART_TIME_ZONE).astimezone(pytz.utc),
            end_time=parser.parse(time_span[1].string, ignoretz=True).astimezone(
                CHINA_STANDART_TIME_ZONE).astimezone(pytz.utc),
            html=str(sp)
        )
        if db.session.query(Contest).filter_by(id=contest.id).first():
            return
        db.session.add(contest)

        last_penalty = ''
        last_solved = -1
        last_rank = -1
        for line in rank_tbody.find_all('tr'):
            user_id = int(line['u'])
            user = User.query.filter_by(id=user_id).first()
            if not user:
                name = line.a.contents[0].strip()
                nickname = line.a.span.string.strip('()')
                user = User(id=user_id, name=name, nickname=nickname)
                db.session.add(user)
            rank = int(line.find(class_='rank meta').string)
            penalty = int(line.find(class_='minute').string)
            solved = int(line.find(class_='solved meta').string)
            if penalty == last_penalty and solved == last_solved:
                rank = last_rank
            contestant = Contestant(user_id=user_id, contest_id=contest.id,
                                    rank=rank, penalty=penalty, solved=solved, before_rating=user.rating)
            db.session.add(contestant)
            last_penalty = penalty
            last_solved = solved
            last_rank = rank
        db.session.commit()
        return contest
