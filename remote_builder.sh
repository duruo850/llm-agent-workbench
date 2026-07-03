#!/bin/bash
set -e  # 遇到错误立即退出

# 配置信息
VERSION="0.0.$(date +%Y%m%d%H%M)"  # 使用时间戳作为版本号

# 远程服务器信息
REMOTE_USER="ubuntu"
REMOTE_IP="124.221.95.18"
REMOTE_PORT="2222"
SSH_KEY="/Users/jayzhan/.ssh/tecent.pem"

REMOTE_DIR="/data/billmind/package"

# 镜像名称
LOCAL_SERVER_IMAGE="billmind-server"
LOCAL_WEB_IMAGE="billmind-web"
REMOTE_SERVER_IMAGE="duruo850/billmind-server"
REMOTE_WEB_IMAGE="duruo850/billmind-web"

# 临时目录
TMP_DIR="./docker_images"
mkdir -p "$TMP_DIR"

# 检查依赖项
command -v docker >/dev/null 2>&1 || { echo "错误：请先安装 Docker！"; exit 1; }

# 构建 server 镜像
echo "构建 server 镜像: $LOCAL_SERVER_IMAGE:$VERSION"
cd server
docker build . --file Dockerfile --tag "$LOCAL_SERVER_IMAGE:$VERSION"
docker tag "$LOCAL_SERVER_IMAGE:$VERSION" "$LOCAL_SERVER_IMAGE:latest"
cd ..

# 构建 web 镜像
echo "构建 web 镜像: $LOCAL_WEB_IMAGE:$VERSION"
cd web
docker build . --file Dockerfile --tag "$LOCAL_WEB_IMAGE:$VERSION"
docker tag "$LOCAL_WEB_IMAGE:$VERSION" "$LOCAL_WEB_IMAGE:latest"
cd ..

# 打包镜像
echo "打包镜像..."
# 定义文件名（将冒号替换为下划线，避免文件名问题）
SERVER_TAR_FILE="${LOCAL_SERVER_IMAGE}_${VERSION}.tar"
WEB_TAR_FILE="${LOCAL_WEB_IMAGE}_${VERSION}.tar"
docker save -o "$TMP_DIR/$SERVER_TAR_FILE" "$LOCAL_SERVER_IMAGE:$VERSION"
docker save -o "$TMP_DIR/$WEB_TAR_FILE" "$LOCAL_WEB_IMAGE:$VERSION"

# 上传到远程服务器
echo "上传镜像到远程服务器 $REMOTE_IP..."
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "mkdir -p $REMOTE_DIR"
scp -P "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$TMP_DIR"/*.tar "$REMOTE_USER@$REMOTE_IP:$REMOTE_DIR"

# 在远程服务器上导入镜像并重命名
echo "在远程服务器上导入镜像并重命名..."

# 处理服务器镜像
echo "导入服务器镜像: $SERVER_TAR_FILE"
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "docker load -i $REMOTE_DIR/$SERVER_TAR_FILE"
echo "重命名服务器镜像: $LOCAL_SERVER_IMAGE:$VERSION -> $REMOTE_SERVER_IMAGE:$VERSION"
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "docker tag $LOCAL_SERVER_IMAGE:$VERSION $REMOTE_SERVER_IMAGE:$VERSION"
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "docker tag $LOCAL_SERVER_IMAGE:$VERSION $REMOTE_SERVER_IMAGE:latest"
echo "删除远程服务器上的文件: $SERVER_TAR_FILE"
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "rm -f $REMOTE_DIR/$SERVER_TAR_FILE"

# 处理Web镜像
echo "导入Web镜像: $WEB_TAR_FILE"
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "docker load -i $REMOTE_DIR/$WEB_TAR_FILE"
echo "重命名Web镜像: $LOCAL_WEB_IMAGE:$VERSION -> $REMOTE_WEB_IMAGE:$VERSION"
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "docker tag $LOCAL_WEB_IMAGE:$VERSION $REMOTE_WEB_IMAGE:$VERSION"
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "docker tag $LOCAL_WEB_IMAGE:$VERSION $REMOTE_WEB_IMAGE:latest"
echo "删除远程服务器上的文件: $WEB_TAR_FILE"
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "rm -f $REMOTE_DIR/$WEB_TAR_FILE"

# 修改docker-compose.yml文件中的镜像版本
echo "修改远程服务器上的docker-compose.yml文件..."
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "cd /data/billmind && \
  sed -i \"s|image: \\(duruo850/\\)\\?${LOCAL_SERVER_IMAGE}:[0-9]*\\.[0-9]*\\.[0-9]*|image: ${REMOTE_SERVER_IMAGE}:${VERSION}|g\" docker-compose.yml && \
  sed -i \"s|image: \\(duruo850/\\)\\?${LOCAL_WEB_IMAGE}:[0-9]*\\.[0-9]*\\.[0-9]*|image: ${REMOTE_WEB_IMAGE}:${VERSION}|g\" docker-compose.yml"

# 在远程服务器上重启容器
echo "重启远程服务器上的容器..."
ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_IP" "cd /data/billmind && docker-compose down && docker-compose up -d"

# 清理临时目录
rm -rf "$TMP_DIR"

# 清理本地镜像（可选）
echo "清理本地镜像（所有版本）..."

# 删除本地 server 镜像的所有版本
SERVER_IDS=$(docker images "$LOCAL_SERVER_IMAGE" -q | tr '\n' ' ')
if [ -n "$SERVER_IDS" ]; then
  docker rmi -f $SERVER_IDS
else
  echo "无需清理: $LOCAL_SERVER_IMAGE 未发现本地镜像"
fi

# 删除本地 web 镜像的所有版本
WEB_IDS=$(docker images "$LOCAL_WEB_IMAGE" -q | tr '\n' ' ')
if [ -n "$WEB_IDS" ]; then
  docker rmi -f $WEB_IDS
else
  echo "无需清理: $LOCAL_WEB_IMAGE 未发现本地镜像"
fi


# 显示版本信息
echo "构建完成！"
echo "服务器镜像版本: $VERSION"
echo "远程服务器上的镜像: $REMOTE_SERVER_IMAGE:$VERSION 和 $REMOTE_WEB_IMAGE:$VERSION"
echo "远程服务器上的docker-compose.yml已更新并重启容器"
echo "所有操作已完成！"