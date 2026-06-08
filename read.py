#!/usr/bin/env python
# Author: Zhenghao Li
# Email: lizhenghao@shanghaitech.edu.cn
# Institute: SIST
# Created: 2026-06-05
# Last Modified: 2026-06-06
# Description: TODO
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import csv
import pandas as pd

projectDict = {
    1: "miniCPU",
    2: "手写数字识别",
    3: "IOT",
    4: "人脸表情检测",
    5: "puzzle solver",
    6: "文本",
}

DB_FILE = "selections.db"
CSV_FILE = "lists.csv"

# ==========================================================
# 读取数据库
# ==========================================================

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row

# 获取所有队伍

teams = conn.execute("""
SELECT
    team_id,
    selection
FROM teams
ORDER BY team_id
""").fetchall()

# 获取所有成员

members = conn.execute("""
SELECT
    student_id,
    team_id
FROM members
""").fetchall()

conn.close()

# ==========================================================
# team_id -> 成员列表
# ==========================================================

team_members = {}

all_selected_ids = set()

for row in members:

    sid = int(row["student_id"])
    team_id = row["team_id"]

    all_selected_ids.add(sid)

    team_members.setdefault(team_id, []).append(sid)

# ==========================================================
# CSV 学生信息
# ==========================================================

pool = {}
unchosen = []

with open(
    CSV_FILE,
    mode="r",
    encoding="utf-8"
) as file:

    reader = csv.reader(file)

    next(reader)

    for row in reader:

        try:

            sid = int(row[5])

            name = row[6]
            email = row[14]

            pool[sid] = (
                name,
                email
            )

            if sid not in all_selected_ids:

                unchosen.append([
                    sid,
                    name,
                    email
                ])

        except Exception:
            pass

# ==========================================================
# 输出Excel
# ==========================================================

all_output_rows = []

for team in teams:

    team_id = team["team_id"]
    selection = team["selection"]

    row_data = [
        team_id,
        selection
    ]

    members_list = team_members.get(
        team_id,
        []
    )

    valid_member_count = 0

    for sid in members_list:

        if sid in pool:

            name, email = pool[sid]

            row_data.extend([
                sid,
                name,
                email
            ])

            valid_member_count += 1

        else:

            print(
                f"{sid} Not Found!"
            )

    if valid_member_count > 0:

        all_output_rows.append(
            row_data
        )

# ==========================================================
# 动态生成列名
# 支持任意人数队伍
# ==========================================================

max_member_num = 0

for row in all_output_rows:

    member_num = (len(row) - 2) // 3

    max_member_num = max(
        max_member_num,
        member_num
    )

columns = [
    "team_id",
    "selection"
]

for i in range(max_member_num):

    columns.extend([
        f"ID{i}",
        f"name{i}",
        f"Email{i}"
    ])

# 补齐长度

required_len = len(columns)

for row in all_output_rows:

    while len(row) < required_len:

        row.append(None)

df = pd.DataFrame(
    all_output_rows,
    columns=columns
)

# ==========================================================
# Excel输出
# ==========================================================

with pd.ExcelWriter(
    "output.xlsx",
    engine="openpyxl"
) as writer:

    for selection, group_df in df.groupby("selection"):

        sheet_name = projectDict.get(
            selection,
            f"Project_{selection}"
        )

        group_df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False
        )

print(
    f"Exported {len(df)} teams"
)

# ==========================================================
# 未选择学生
# ==========================================================

with open(
    "unchosen.csv",
    mode="w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "student_id",
        "name",
        "email"
    ])

    writer.writerows(
        unchosen
    )

print(
    f"Unchosen students: {len(unchosen)}"
)
