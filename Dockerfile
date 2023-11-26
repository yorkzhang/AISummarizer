# 基于python:3.10镜像构建Docker镜像
FROM python:3.10

# 设置工作目录
WORKDIR /app

# 复制项目代码到容器中
COPY .env app.py index.html requirements.txt oob_queries.json /app

# 安装依赖项
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && \
    apt-get install -y wget && \
    wget http://security.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.19_amd64.deb && \
    dpkg -i libssl1.1_1.1.1f-1ubuntu2.19_amd64.deb && \
    rm libssl1.1_1.1.1f-1ubuntu2.19_amd64.deb && \
    # apt-get install build-essential cmake libboost-all-dev &&\
    apt-get remove -y wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 5000

# 启动应用程序
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app", "-t", "60"]
