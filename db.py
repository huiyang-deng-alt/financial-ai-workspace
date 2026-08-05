import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "users.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 之后能按列名取：row["username"]
    return conn

def init_db():
    """建表（启动时调用一次）"""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def create_user(username: str, password_hash: str):
    """注册：插入用户，返回新用户 id；用户名重复返回 None"""
    conn = get_conn()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # username 重复（UNIQUE 约束触发）
    finally:
        conn.close()

def get_user_by_username(username: str):
    """登录用：按用户名查用户"""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return row

def get_user_by_id(user_id: int):
    """/me 用：按 id 查用户"""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row

def save_message(user_id: int, question: str, answer: str):
    """存一轮问答，返回消息 id"""
    conn = get_conn()
    cursor = conn.execute(
        "INSERT INTO messages (user_id, question, answer) VALUES (?, ?, ?)",
        (user_id, question, answer),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid

def get_messages_by_user(user_id: int):
    """按用户查对话历史，按时间正序"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows