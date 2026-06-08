#!/usr/bin/env python
# Author: Zhenghao Li
# Email: lizhenghao@shanghaitech.edu.cn
# Institute: SIST
# Created: 2026-06-06
# Last Modified: 2026-06-07
# Description: TODO
# gunicorn_config.py
import multiprocessing

# 基础配置
bind = "0.0.0.0:5000"
workers = 2
worker_class = "gthread"  # 或 "gevent"
threads = 4
timeout = 10
keepalive = 2


# 日志
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"

# 进程命名（方便管理）
proc_name = "selection_app"

# 优雅重启
graceful_timeout = 30
max_requests = 1000  # 处理1000个请求后重启worker
max_requests_jitter = 100  # 随机偏移，避免同时重启
