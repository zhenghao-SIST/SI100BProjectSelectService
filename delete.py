#!/usr/bin/env python
#-*- coding: utf-8 -*-
# Author: Zhenghao Li
# Email: lizhenghao@shanghaitech.edu.cn
# Institute: SIST
# Date: 2025-12-06
import sqlite3
import sys

DB_PATH = "./selections.db"   # 修改为你的DB路径


def delete_by_value(x):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM submissions
        WHERE student_id = ?
           OR student_id1 = ?
           OR student_id2 = ?
    """, (x, x, x))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete.py <student_id>")
        exit(1)

    x = sys.argv[1]
    delete_by_value(x)
    print("Deleted records where student_id / student_id1 / student_id2 = ", x)
