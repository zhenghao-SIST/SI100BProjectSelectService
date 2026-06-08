#!/usr/bin/env python
# Author: Zhenghao Li
# Email: lizhenghao@shanghaitech.edu.cn
# Institute: SIST
# Created: 2026-06-05
# Last Modified: 2026-06-08
# Description: Project selection service for SI100B

from flask import Flask, request, jsonify, render_template
import sqlite3
import logging
import os

app = Flask(__name__)

DB_FILE = "data/selections.db"

# ==========================================================
# Logging
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ==========================================================
# Database
# ==========================================================

def get_db():
    conn = sqlite3.connect(
        DB_FILE,
        timeout=10,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_db():
    with get_db() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        # -------------------------
        # 队伍表
        # -------------------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS teams(
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            selection INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # -------------------------
        # 成员表
        # student_id 全局唯一
        # -------------------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS members(
            student_id TEXT PRIMARY KEY,
            team_id INTEGER NOT NULL,

            FOREIGN KEY(team_id)
            REFERENCES teams(team_id)
            ON DELETE CASCADE
        )
        """)

        # -------------------------
        # 统计表
        # -------------------------
        #conn.execute("""
        #CREATE TABLE IF NOT EXISTS selection_counts(
        #    option INTEGER PRIMARY KEY,
        #    count INTEGER NOT NULL DEFAULT 0
        #)
        #""")

        #for i in range(1, 6):

        #    conn.execute("""
        #    INSERT OR IGNORE INTO selection_counts(
        #        option,
        #        count
        #    )
        #    VALUES(?,0)
        #    """, (i,))

        # -------------------------
        # 索引
        # -------------------------

        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_members_team
        ON members(team_id)
        """)

        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_teams_selection
        ON teams(selection)
        """)

        conn.commit()

    logging.info("Database initialized")


# ==========================================================
# Utils
# ==========================================================

def is_valid(student_id: str) -> bool:

    if not student_id:
        return False

    if not student_id.isdigit():
        return False

    sid = int(student_id)

    return 2021000000 <= sid <= 2026000000


def get_json():

    data = request.get_json(silent=True)

    if data is None:
        raise ValueError("Invalid JSON")

    return data


def get_selection_counts():
    with get_db() as conn:
        rows = conn.execute("""
        SELECT
            selection,
            COUNT(*) AS cnt
        FROM teams
        GROUP BY selection
        """).fetchall()

    counts = {i: 0 for i in range(1, 6)}

    for row in rows:
        counts[row["selection"]] = row["cnt"]

    return counts

# ==========================================================
# Routes
# ==========================================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================================
# Submit
# ==========================================================

@app.route("/submit", methods=["POST"])
def submit_selection():

    try:

        data = get_json()

        request_data = [
            data["student_id"].strip(),
            data["student_id1"].strip(),
            data["student_id2"].strip()
        ]

        student_ids = [x for x in request_data if x != '']

        selection = int(data["selection"])

    except Exception:

        return jsonify({
            "success": False,
            "message": "参数错误"
        }), 400

    # --------------------------------
    # 队内重复检查
    # --------------------------------

    if len(set(student_ids)) != len(student_ids):

        return jsonify({
            "success": False,
            "message": "队伍内存在重复学号"
        })

    # --------------------------------
    # 学号合法性
    # --------------------------------

    for sid in student_ids:

        if not is_valid(sid):

            return jsonify({
                "success": False,
                "message": f"学号 {sid} 不合法"
            })

    # --------------------------------
    # 名额限制
    # --------------------------------
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("BEGIN IMMEDIATE")  # 获取写锁

            # 在事务内检查名额
            counts = cursor.execute(
                "SELECT COUNT(*) FROM teams WHERE selection=?",
                (selection,)
            ).fetchone()[0]

            if selection == 2 and counts >= 12:
                return jsonify({
                    "success": False,
                    "message": "手写数字识别选择已满"
                })

            if selection == 3 and counts >= 20:
                return jsonify({
                    "success": False,
                    "message": "物联网选择已满"
                })

            # 创建队伍
            cursor.execute("""
            INSERT INTO teams(selection)
            VALUES(?)
            """, (selection,))

            team_id = cursor.lastrowid

            # 插入成员
            # student_id 为 PRIMARY KEY
            # 自动实现全局查重
            for sid in student_ids:
                cursor.execute("""
                INSERT INTO members(
                    student_id,
                    team_id
                )
                VALUES(?,?)
                """, (
                    sid,
                    team_id
                ))
            conn.commit()

        logging.info(
            "Team %s submitted option %s",
            team_id,
            selection
        )

        return jsonify({
            "success": True,
            "message": "提交成功"
        })

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "队伍中存在已报名学号"
        })

    except Exception as e:

        logging.exception(e)

        return jsonify({
            "success": False,
            "message": "服务器内部错误"
        }), 500


# ==========================================================
# Query
# ==========================================================

@app.route("/query", methods=["POST"])
def query_selection():

    try:

        data = get_json()

        student_id = data["student_id"].strip()

    except Exception:

        return jsonify({
            "success": False,
            "message": "参数错误"
        }), 400

    if not is_valid(student_id):

        return jsonify({
            "success": False,
            "message": "学号不合法"
        })

    try:

        with get_db() as conn:

            # 找队伍

            row = conn.execute("""
            SELECT team_id
            FROM members
            WHERE student_id=?
            """, (student_id,)).fetchone()

            if row is None:

                return jsonify({
                    "success": False,
                    "message": "未查询到记录"
                })

            team_id = row["team_id"]

            # 查询项目

            row = conn.execute("""
            SELECT selection
            FROM teams
            WHERE team_id=?
            """, (team_id,)).fetchone()

            selection = row["selection"]

            # 查询成员

            rows = conn.execute("""
            SELECT student_id
            FROM members
            WHERE team_id=?
            ORDER BY student_id
            """, (team_id,)).fetchall()

            members = [
                r["student_id"]
                for r in rows
            ]

        return jsonify({
            "success": True,
            "selection": selection,
            "members": members
        })

    except Exception as e:

        logging.exception(e)

        return jsonify({
            "success": False,
            "message": "服务器内部错误"
        }), 500


# ==========================================================
# Admin (可选)
# ==========================================================

@app.route("/stats")
def stats():

    counts = get_selection_counts()

    return jsonify(counts)


# ==========================================================
# Main
# ==========================================================

if not os.path.exists(DB_FILE):
    logging.info("Creating database")
init_db()

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True,
        debug=False
    )
