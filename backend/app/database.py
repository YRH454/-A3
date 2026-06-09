import pymysql
from app.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE


def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, autocommit=False,
    )


def query(sql: str, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def execute(sql: str, params=None) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


import time, random as _random

def insert(table: str, data: dict) -> int:
    """插入一行并返回新 ID（时间戳+随机数，DUCKDB无自增主键的替代方案）"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            nid = int(time.time() * 1000) * 1000 + _random.randint(0, 999)
            cols = ["id"] + list(data.keys())
            vals = [nid] + list(data.values())
            ph = ", ".join(["%s"] * len(cols))
            cursor.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({ph})", vals)
            conn.commit()
            return nid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
