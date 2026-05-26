import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Union
import logging
import hashlib
import constant
import time


logger = logging.getLogger(__name__)


class MySQLHelper:
    """MySQL 数据库操作封装类（适配重构后的三国杀数据库）"""

    def __init__(self, host: str, port: int, user: str, password: str, database: str,
                 charset: str = 'utf8mb4', autocommit: bool = False,
                 connect_timeout: int = 10):
        """
        初始化数据库连接参数
        :param host: 主机地址
        :param port: 端口号
        :param user: 用户名
        :param password: 密码
        :param database: 数据库名
        :param charset: 字符集
        :param autocommit: 是否自动提交
        :param connect_timeout: 连接超时时间（秒）
        """
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': charset,
            'autocommit': autocommit,
            'cursorclass': DictCursor,
            'connect_timeout': connect_timeout,
        }

    def get_connection(self) -> pymysql.Connection:
        """获取一个新的数据库连接"""
        return pymysql.connect(**self.config)

    @contextmanager
    def get_cursor(self, commit_on_exit: bool = False):
        """
        上下文管理器，自动获取和关闭连接、游标，支持事务提交
        :param commit_on_exit: 退出时是否提交事务（默认False，需手动commit或使用transaction）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            if commit_on_exit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作异常，已回滚: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    # ---------- 基础 CRUD 方法 ----------
    def execute_query(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> List[Dict]:
        """执行查询，返回结果列表（每条记录为字典）"""
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def execute_one(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> Optional[Dict]:
        """执行查询，返回单条记录（字典）"""
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def execute_insert(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> int:
        """执行插入语句，返回自增ID"""
        with self.get_cursor(commit_on_exit=True) as cursor:
            cursor.execute(sql, params)
            return cursor.lastrowid

    def execute_update(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> int:
        """执行更新/删除语句，返回影响行数"""
        with self.get_cursor(commit_on_exit=True) as cursor:
            affected = cursor.execute(sql, params)
            return affected

    def execute_many(self, sql: str, params_list: List[Union[tuple, dict]]) -> int:
        """
        批量执行（如批量插入），返回影响总行数
        """
        with self.get_cursor(commit_on_exit=True) as cursor:
            cursor.executemany(sql, params_list)
            return cursor.rowcount

    # ---------- 事务支持 ----------
    @contextmanager
    def transaction(self):
        """
        手动事务上下文，自动提交或回滚
        用法：
            with db.transaction() as cursor:
                cursor.execute(...)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"事务执行失败，已回滚: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    # ---------- 针对《三国杀》数据库的便捷方法 ----------
    # 玩家相关
    def get_player_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取玩家信息"""
        sql = "SELECT * FROM users WHERE username = %s"
        return self.execute_one(sql, (username,))

    def get_player_by_id(self, user_id: int) -> Optional[Dict]:
        """根据玩家ID获取玩家信息"""
        sql = "SELECT * FROM users WHERE user_id = %s"
        return self.execute_one(sql, (user_id,))

    def update_player_level(self, user_id: int, new_level: int) -> bool:
        """更新玩家等级"""
        sql = "UPDATE users SET level = %s WHERE user_id = %s"
        affected = self.execute_update(sql, (new_level, user_id))
        return affected > 0

    # 武将收藏（背包）
    def get_player_heroes(self, user_id: int) -> List[Dict]:
        """获取玩家拥有的武将列表（基础信息，不包含技能）"""
        sql = """
            SELECT h.*
            FROM user_heroes uh
            JOIN heroes h ON uh.hero_id = h.hero_id
            WHERE uh.user_id = %s
            ORDER BY uh.acquired_at
        """
        return self.execute_query(sql, (user_id,))

    def add_player_hero(self, user_id: int, hero_id: int) -> bool:
        """
        为玩家添加一个武将（若已存在则忽略）
        :return: 是否添加成功（False表示已存在）
        """
        sql = "INSERT INTO user_heroes (user_id, hero_id) VALUES (%s, %s)"
        try:
            self.execute_insert(sql, (user_id, hero_id))
            return True
        except pymysql.err.IntegrityError:
            # 主键冲突（已拥有该武将）
            logger.warning(f"Player {user_id} already owns hero {hero_id}")
            return False

    def remove_player_hero(self, user_id: int, hero_id: int) -> bool:
        """移除玩家拥有的武将"""
        sql = "DELETE FROM user_heroes WHERE user_id = %s AND hero_id = %s"
        affected = self.execute_update(sql, (user_id, hero_id))
        return affected > 0

    # 武将详情（含技能）
    def get_hero_detail(self, hero_id: int) -> Optional[Dict]:
        """
        获取武将详细信息（包含技能列表）
        返回格式：{**hero基础字段, 'skills': [{'skill_id','skill_name','skill_type','skill_desc',...}]}
        """
        hero = self.execute_one("SELECT * FROM heroes WHERE hero_id = %s", (hero_id,))
        if not hero:
            return None
        skills = self.execute_query(
            "SELECT skill_id, skill_name, skill_type, skill_desc, display_order "
            "FROM hero_skills WHERE hero_id = %s ORDER BY display_order",
            (hero_id,)
        )
        hero['skills'] = skills
        return hero

    # 对局记录
    def insert_game_record(self, start_time, end_time, game_mode: str, winner_camp: str = None) -> int:
        """
        插入一场游戏对局记录，返回 game_id
        :param start_time: 开始时间 (datetime 或 timestamp)
        :param end_time: 结束时间 (datetime 或 timestamp)
        :param game_mode: 游戏模式
        :param winner_camp: 获胜阵营 ('主公方','反贼方','内奸')，可为None
        """
        sql = """
            INSERT INTO game_records (start_time, end_time, game_mode, winner_camp)
            VALUES (%s, %s, %s, %s)
        """
        return self.execute_insert(sql, (start_time, end_time, game_mode, winner_camp))

    def insert_player_stat(self, game_id: int, user_id: int, hero_id: int, seat: int,
                           role: str, is_winner: bool, kill_count: int, damage_dealt: int) -> int:
        """插入玩家对局详情"""
        sql = """
            INSERT INTO game_player_stats
            (game_id, user_id, hero_id, seat, role, is_winner, kill_count, damage_dealt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_insert(sql, (game_id, user_id, hero_id, seat, role, is_winner, kill_count, damage_dealt))

    def get_player_game_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        获取玩家最近的对局历史（带对局信息）
        """
        sql = """
            SELECT gps.*, gr.start_time, gr.end_time, gr.duration_seconds, gr.game_mode, gr.winner_camp,
                   h.name AS hero_name
            FROM game_player_stats gps
            JOIN game_records gr ON gps.game_id = gr.game_id
            JOIN heroes h ON gps.hero_id = h.hero_id
            WHERE gps.user_id = %s
            ORDER BY gr.start_time DESC
            LIMIT %s
        """
        return self.execute_query(sql, (user_id, limit))

    # 统计与排行榜
    def get_hero_winrate(self, hero_id: int) -> float:
        """查询某武将的胜率（基于 game_player_stats 表）"""
        sql = """
            SELECT 
                COUNT(*) AS total,
                SUM(is_winner) AS wins
            FROM game_player_stats
            WHERE hero_id = %s
        """
        result = self.execute_one(sql, (hero_id,))
        if result and result['total'] > 0:
            return (result['wins'] / result['total']) * 100
        return 0.0

    def get_player_winrate(self, user_id: int) -> float:
        """查询玩家的总体胜率（基于实际对局统计）"""
        sql = """
            SELECT 
                COUNT(*) AS total,
                SUM(is_winner) AS wins
            FROM game_player_stats
            WHERE user_id = %s
        """
        result = self.execute_one(sql, (user_id,))
        if result and result['total'] > 0:
            return (result['wins'] / result['total']) * 100
        return 0.0

    def get_most_popular_heroes(self, limit: int = 10) -> List[Dict]:
        """获取登场次数最多的武将排行"""
        sql = """
            SELECT h.hero_id, h.name, h.kingdom, COUNT(*) AS usage_count
            FROM game_player_stats gps
            JOIN heroes h ON gps.hero_id = h.hero_id
            GROUP BY h.hero_id
            ORDER BY usage_count DESC
            LIMIT %s
        """
        return self.execute_query(sql, (limit,))

    def get_player_ranking(self, order_by: str = 'win_rate', limit: int = 10) -> List[Dict]:
        """
        获取玩家排行榜
        :param order_by: 排序字段，可选 'win_rate', 'total_games', 'win_games'
        """
        # 使用视图 player_profile，其中包含了计算好的字段
        allowed_orders = {'win_rate', 'total_games', 'win_games'}
        if order_by not in allowed_orders:
            order_by = 'win_rate'
        sql = f"SELECT user_id, username, level, total_games, win_games, win_rate, most_used_hero FROM player_profile ORDER BY {order_by} DESC LIMIT %s"
        return self.execute_query(sql, (limit,))
    


def login_check(db: 'MySQLHelper', username: str, password: str) -> bool:
    db.get_connection()  # 获取数据库连接
    md5_obj = hashlib.md5()
    md5_obj.update(password.encode())
    password = md5_obj.hexdigest()
    result = db.execute_one("SELECT * FROM users WHERE username=%s AND password_hash=%s", (username, password))
    print(result)
    return result

def register_check(db: 'MySQLHelper', username: str) -> bool:
    db.get_connection()  # 获取数据库连接
    result = db.execute_one("SELECT * FROM users WHERE username=%s", (username,))
    return result is None

def register_check(db: 'MySQLHelper', username: str, password: str) -> bool:
    db.get_connection()  # 获取数据库连接
    md5_obj = hashlib.md5()
    md5_obj.update(password.encode())
    password = md5_obj.hexdigest()
    try:
        result = db.execute_insert(
            "INSERT INTO users (username, password_hash, icon,level,created_at,updated_at,coin) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
            (username, password, constant.ICON_DEFAULT_PATH, 1, time.strftime('%Y-%m-%d %H:%M:%S'), time.strftime('%Y-%m-%d %H:%M:%S')))
    except Exception as e:
        print(e)
        return False
    return result > 0
    