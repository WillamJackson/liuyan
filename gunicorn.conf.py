# Gunicorn配置文件

# 服务器套接字
bind = "0.0.0.0:8000"
backlog = 2048

# 工作进程
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 重启
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 调试
reload = False
daemon = False

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 进程命名
proc_name = "liuyan_cms"

# 用户和组
# user = "www-data"
# group = "www-data"

# SSL (如果需要)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile" 