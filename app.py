#!/usr/bin/env python
#-*- coding: utf-8 -*-
# Author: Zhenghao Li
# Email: lizhenghao@shanghaitech.edu.cn
# Institute: SIST
# Date: 2024-12-03
from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)

def is_valid(student_id) -> bool:
    try :
        if student_id.isdigit():
            v = int( student_id)
            if v < 2021000000 or v > 2026000000 :
                return False
            return True
        else:
            return False
    except :
        return False

def check_duplicate_student_ids(student_id, student_id1, student_id2):
    conn = sqlite3.connect('selections.db', timeout=10)
    c = conn.cursor()

    # 检查是否有重复学号，并返回重复的学号
    c.execute('''
        SELECT student_id, student_id1, student_id2 FROM submissions
        WHERE ? IN (student_id, student_id1, student_id2)
           OR ? IN (student_id, student_id1, student_id2)
           OR ? IN (student_id, student_id1, student_id2)
        LIMIT 1
    ''', (student_id, student_id1, student_id2))

    result = c.fetchone()
    conn.close()

    if result:
        # 返回重复的学号
        for sid in (student_id, student_id1, student_id2):
            if sid in result:
                return sid
    return None

# 初始化数据库
def init_db():
    conn = sqlite3.connect('selections.db', timeout=10)
    c = conn.cursor()

    # 创建选择计数表
    c.execute('''CREATE TABLE IF NOT EXISTS selection_counts (option INTEGER, count INTEGER)''')
    for i in range(1, 6):
        c.execute('INSERT OR IGNORE INTO selection_counts (option, count) VALUES (?, ?)', (i, 0))

    # 创建提交记录表，用于存储学号和选择
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (student_id TEXT, student_id1 TEXT, student_id2 TEXT, selection INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(student_id))''')

    conn.commit()
    conn.close()

# 获取当前选项选择数量
def get_selection_counts():
    conn = sqlite3.connect('selections.db', timeout=10)
    c = conn.cursor()
    c.execute('SELECT option, count FROM selection_counts')
    counts = c.fetchall()
    conn.close()
    return dict(counts)

# 更新选项选择数量
def update_selection_count(option):
    conn = sqlite3.connect('selections.db', timeout=10)
    c = conn.cursor()
    c.execute('UPDATE selection_counts SET count = count + 1 WHERE option = ?', (option,))
    conn.commit()
    conn.close()

# 存储提交记录到 submissions 表
def store_submission(student_id, student_id1, student_id2, selection):
    conn = sqlite3.connect('selections.db',timeout=10)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO submissions (student_id, student_id1, student_id2, selection) VALUES (?, ?, ?, ?)',
                  (student_id, student_id1, student_id2, selection))
        conn.commit()
    except sqlite3.IntegrityError:
        # 如果重复插入，返回错误
        conn.close()
        raise ValueError("重复提交！")
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['GET','POST'])
def submit_selection():
    data = request.get_json()
    student_id = data['student_id'].strip()
    student_id1 = data['student_id1'].strip()
    student_id2 = data['student_id2'].strip()
    selection = int(data['selection'])

    counts = get_selection_counts()

    # 检查选项是否超出限制
    if selection == 2 and counts[2] >= 12:
        return jsonify({'success': False, 'message': '手写数字识别选择已满！'})
    if selection == 3 and counts[3] >= 20:
        return jsonify({'success': False, 'message': '物联网的选择已满！'})

    # 存储学号和选择到 submissions 表
    for std in (student_id, student_id1, student_id2): 
        if not is_valid(std):
            #print("ILLEGAL: {}".format(std))
            return jsonify({'success': False, 'message': f'学号 {std} 不合法！'})

    duplicate_id = check_duplicate_student_ids(student_id, student_id1, student_id2)
    if duplicate_id:
        return jsonify({'success': False, 'message': f'学号 {duplicate_id} 已存在，不允许重复提交！'})

    try:
        store_submission(student_id, student_id1, student_id2, selection)
    except ValueError:
        print("high {} {} {}".format(student_id, student_id1, student_id2))
        return jsonify({'success': False, 'message': '同学你手速太快了，第一次已受理，重复提交，本次被拒绝！'})
    # 更新选择数量
    update_selection_count(selection)
    
    return jsonify({'success': True, 'message': f'学号 {student_id} {student_id1} {student_id2} 选择了选项 {selection}！'})

@app.route('/query', methods=['POST'])
def query_selection():
    data = request.get_json()
    student_id = data['student_id'].strip()

    if not is_valid(student_id):
        return jsonify({
            'success': False,
            'message': '学号不合法！'
        })

    conn = sqlite3.connect('selections.db', timeout=10)
    c = conn.cursor()

    c.execute('''
        SELECT student_id, student_id1, student_id2, selection
        FROM submissions
        WHERE student_id = ?
           OR student_id1 = ?
           OR student_id2 = ?
        LIMIT 1
    ''', (student_id, student_id, student_id))

    result = c.fetchone()
    conn.close()


    if result:
        sid0, sid1, sid2, selection = result

        return jsonify({
            'success': True,
            'selection': selection,
            'members': [sid0, sid1, sid2]
        })

    return jsonify({
        'success': False,
        'message': '未查询到该学号的选项信息！'
    })

if os.path.exists("selections.db"):
    print("exist DB")
else:
    print("init_db")
    init_db()  # 初始化数据库

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
