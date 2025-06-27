# 使用Python官方完整镜像，包含所有编译工具
FROM python:3.9

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 容器默认时区为UTC，如需使用上海时间请启用以下时区设置命令
# RUN apt-get update && apt-get install -y tzdata && \
#     ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
#     echo "Asia/Shanghai" > /etc/timezone

# 安装基础编译工具和必要的系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖，使用国内镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip config set global.trusted-host mirrors.aliyun.com \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 80

# 启动命令
CMD ["python3", "run.py", "0.0.0.0", "80"] 