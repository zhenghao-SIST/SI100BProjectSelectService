#!/usr/bin/env python
#-*- coding: utf-8 -*-
# Author: Zhenghao Li
# Email: lizhenghao@shanghaitech.edu.cn
# Institute: SIST
# Date: 2024-12-03

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

class Team:
    def __init__(self, selection):
        self.selection = selection
        self.members = set()
        self.name = []

    def add(self, member):
        self.members.add(member)

    def addName(self, name):
        self.name.append(name)

    def toList(self):
        if len(self.name) != len(self.members):
            return None

conn = sqlite3.connect('./selections.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM submissions')
rows = cursor.fetchall()

# 创建team
allID = {}
teams = [];
for row in rows:
    team = Team(row[3])
    for i in range(3):
        ID = int(row[i].strip())
        # 哪些学生说ID写错了 给他们在这里改过来
        #if ID == 2023521062 :
        #    team.selection = 5
        #if i ==2 and ID == 2025531075 :
        #    ID = 2025533126
        #if i ==2 and ID == 2025533053 :
        #    ID = 2025533066
        #if i ==2 and ID == 2025533125 :
        #    ID = 2025533129
        #if i ==2 and ID == 2025592778 :
        #    ID = 2025591040
        #if i ==2 and ID == 2025533058 :
        #    ID = 2025533033
        #if i ==2 and ID == 2025533137 :
        #    ID = 2025533062
        #if ID == 2022531121 :
        #    ID = 2025531121
        #if i == 2 and ID == 2025531050 :
        #    ID = 2025531047
        allID[ID] = row[3]
        team.add(ID)
    teams.append(team)

conn.close()


with open('lists.csv', mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)

    pool = {}
    unchosen = []
    #检查还有哪些学生没有选
    for row in csv_reader:
        if int(row[5]) not in allID:
            unchosen.append([row[5], row[6], row[14]])
        pool[int(row[5])] = (row[6],row[14])

    #把学号和名字对应上，如果一个队所有成员都找不到具体人，则删除这个队伍
    outData = []
    for t in teams:
        newRow = [t.selection]
        for m in t.members:
            if m in pool:
                newRow.append(str(m))
                newRow.append(pool[m][0])
                newRow.append(pool[m][1])
            else:
                print(f"{m} Not Found!")
        if len(newRow) > 1:
            outData.append(newRow)

    for i in range(len(outData)):
        while len(outData[i]) < 10 :
            outData[i].append(None)  # 或者填充其他默认值，如 None 或 ''

    df = pd.DataFrame(outData, columns=["selection", "ID0", "name0", "Email0",\
                                                     "ID1", "name1", "Email1",\
                                                     "ID2", "name2", "Email2"])
    with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
        for group_value, group_df in df.groupby('selection'):
            tableName = projectDict[group_value]
            group_df.to_excel(writer, sheet_name=f"{tableName}", index=False)

    #with open('output.csv', mode='w+', newline='', encoding='utf-8') as file:
    #    csv_writer = csv.writer(file)
    #    csv_writer.writerows(outData)

    with open('unchosen.csv', mode='w+', newline='', encoding='utf-8-sig') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(unchosen)
