#!/usr/bin/env python
# Author: Zhenghao Li
# Email: lizhenghao@shanghaitech.edu.cn
# Institute: SIST
# Created: 2026-06-05
# Last Modified: 2026-06-06
# Description: TODO
#!/usr/bin/env python
# Author: Zhenghao Li
# Email: lizhenghao@shanghaitech.edu.cn
# Institute: SIST
# Created: 2026-06-05
# Last Modified: 2026-06-05
# Description: 删除指定学号对应的队伍及其所有成员

import sqlite3
import sys
import argparse
import logging

DB_FILE = "selections.db"

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

def is_valid(student_id: str) -> bool:
    """验证学号是否合法"""
    if not student_id:
        return False
    if not student_id.isdigit():
        return False
    sid = int(student_id)
    return 2021000000 <= sid <= 2026000000

def delete_team_by_student_id(student_id: str, dry_run: bool = False):
    """
    删除指定学号所在的整个队伍

    Args:
        student_id: 学号
        dry_run: 如果为 True，只显示要删除的内容，不实际删除

    Returns:
        bool: 是否成功删除
    """

    if not is_valid(student_id):
        logging.error(f"学号 {student_id} 不合法")
        return False

    try:
        with get_db() as conn:
            # 1. 查找学号所在的队伍
            row = conn.execute("""
                SELECT team_id
                FROM members
                WHERE student_id = ?
            """, (student_id,)).fetchone()

            if row is None:
                logging.error(f"未找到学号 {student_id} 的报名记录")
                return False

            team_id = row["team_id"]

            # 2. 获取队伍信息
            team_info = conn.execute("""
                SELECT team_id, selection, created_at
                FROM teams
                WHERE team_id = ?
            """, (team_id,)).fetchone()

            # 3. 获取队伍所有成员
            members = conn.execute("""
                SELECT student_id
                FROM members
                WHERE team_id = ?
                ORDER BY student_id
            """, (team_id,)).fetchall()

            member_list = [m["student_id"] for m in members]

            # 4. 获取队伍选择的项目
            selection = team_info["selection"]

            # 显示要删除的信息
            print("\n" + "="*60)
            print(f"找到以下记录：")
            print(f"  队伍ID: {team_id}")
            print(f"  项目: {selection}")
            print(f"  创建时间: {team_info['created_at']}")
            print(f"  成员数量: {len(member_list)}")
            print(f"  成员列表: {', '.join(member_list)}")
            print("="*60)

            if dry_run:
                print("\n[DRY RUN] 未执行实际删除操作")
                return True

            # 5. 确认删除
            print("\n⚠️  警告：此操作将删除整个队伍及其所有成员的报名记录！")
            confirm = input(f"确认删除学号 {student_id} 所在的整个队伍？(yes/no): ")

            if confirm.lower() != 'yes':
                print("操作已取消")
                return False

            # 6. 执行删除
            # 由于设置了 ON DELETE CASCADE，删除 teams 表中的记录会自动删除 members 中的相关记录
            cursor = conn.execute("""
                DELETE FROM teams
                WHERE team_id = ?
            """, (team_id,))

            if cursor.rowcount > 0:
                # 7. 更新统计表（减少对应项目的计数）
                #conn.execute("""
                #    UPDATE selection_counts
                #    SET count = count - 1
                #    WHERE option = ?
                #""", (selection,))

                conn.commit()

                logging.info(f"成功删除队伍 {team_id}（项目 {selection}），包含 {len(member_list)} 名成员")
                print(f"\n✅ 删除成功！")
                print(f"   已删除队伍 {team_id}（项目 {selection}）")
                print(f"   已移除成员: {', '.join(member_list)}")
                return True
            else:
                logging.error(f"删除失败：未找到队伍 {team_id}")
                return False

    except sqlite3.Error as e:
        logging.error(f"数据库错误: {e}")
        return False
    except Exception as e:
        logging.exception(f"未知错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='删除指定学号对应的队伍及其所有成员',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python delete.py 2023123456        # 删除学号 2023123456 所在的队伍
  python delete.py --dry-run 2023123456  # 预览要删除的内容，不实际删除
  python delete.py --force 2023123456    # 跳过确认提示（慎用）
        """
    )

    parser.add_argument(
        'student_id',
        help='要删除的学号'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，只显示要删除的内容，不实际删除'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制删除，跳过确认提示（慎用）'
    )

    args = parser.parse_args()

    # 检查数据库文件是否存在
    import os
    if not os.path.exists(DB_FILE):
        logging.error(f"数据库文件 {DB_FILE} 不存在")
        sys.exit(1)

    # 执行删除
    success = delete_team_by_student_id(args.student_id, args.dry_run)

    if not success:
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
