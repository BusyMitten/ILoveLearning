# ILoveLearning - 交互式学习平台

ILoveLearning是一个基于Flask的交互式学习平台，支持多种题型（选择题、填空题），具有答题反馈、进度跟踪等功能。

本指南将详细介绍如何在Debian系统上部署ILoveLearning Flask应用，包括使用Nginx作为反向代理和Let's Encrypt SSL证书配置。

## 项目概述

ILoveLearning是一个基于Flask的交互式学习平台，支持多种题型（选择题、填空题），具有答题反馈、进度跟踪等功能。

GitHub仓库: https://github.com/BusyMitten/ILoveLearning

## 系统要求

- Debian 10/11/12 (Bullseye 或更新版本)
- 至少 1GB RAM
- 至少 2GB 磁盘空间
- 域名指向服务器IP（用于SSL证书）

## 部署步骤

### 1. 系统更新

首先更新系统包列表并升级现有包：

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 安装必要软件

安装Python、pip、Git和其他必要工具：

```bash
sudo apt install -y python3 python3-pip python3-venv git nginx curl supervisor
```

### 3. 获取项目代码

创建项目目录并克隆代码：

```bash
sudo mkdir -p /var/www
cd /var/www
sudo git clone https://github.com/BusyMitten/ILoveLearning.git
sudo chown -R $(whoami):$(whoami) ILoveLearning
cd ILoveLearning
```

### 4. 创建Python虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 配置应用

创建一个启动脚本，让Gunicorn运行Flask应用：

```bash
cat > gunicorn_config.py << 'EOF'
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 30
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF
```

### 6. 测试应用

```bash
source venv/bin/activate
gunicorn -c gunicorn_config.py app:app
```

在另一个终端中测试：

```bash
curl http://127.0.0.1:8000
```

确认应用正常工作后，按Ctrl+C停止Gunicorn。

### 7. 配置Supervisor管理应用

创建Supervisor配置文件：

```bash
sudo cat > /etc/supervisor/conf.d/ilovelearning.conf << 'EOF'
[program:ilovelearning]
directory=/var/www/ILoveLearning
command=/var/www/ILoveLearning/venv/bin/gunicorn -c gunicorn_config.py app:app
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/ilovelearning.log
environment=PATH="/var/www/ILoveLearning/venv/bin"
EOF
```

重新加载Supervisor配置：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ilovelearning
```

### 8. 配置Nginx反向代理

删除默认站点配置：

```bash
sudo rm /etc/nginx/sites-enabled/default
```

创建Nginx配置文件：

```bash
sudo cat > /etc/nginx/sites-available/ilovelearning << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件缓存（如果有的话）
    location /static {
        alias /var/www/ILoveLearning/static;
        expires 30d;
    }
}
EOF
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/ilovelearning /etc/nginx/sites-enabled/
sudo nginx -t  # 测试Nginx配置
sudo systemctl reload nginx
```

### 9. 安装Let's Encrypt SSL证书

安装Certbot：

```bash
sudo apt install -y certbot python3-certbot-nginx
```

获取SSL证书（替换your-domain.com为你的实际域名）：

```bash
sudo certbot --nginx -d your-domain.com
```

### 10. 设置自动续期

Let's Encrypt证书有效期为90天，需要自动续期：

```bash
sudo crontab -e
```

添加以下行到crontab文件中：

```bash
0 12 * * * /usr/bin/certbot renew --quiet
```

### 11. 配置防火墙（可选）

如果启用了UFW防火墙：

```bash
sudo apt install -y ufw
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

### 12. 最终验证

检查所有服务状态：

```bash
sudo systemctl status nginx
sudo supervisorctl status ilovelearning
```

访问你的域名，确认应用正常运行。

## 项目结构说明

- [app.py](file:///D:/PycharmProjects/ILoveLearning/app.py) - 主Flask应用
- [utils.py](file:///D:/PycharmProjects/ILoveLearning/utils.py) - 工具函数（加载训练、题目等）
- [training/](file:///D:/PycharmProjects/ILoveLearning/training) - 存储训练元数据的JSON文件
- [problem/](file:///D:/PycharmProjects/ILoveLearning/problem) - 存储题目数据的JSON文件
- [templates/](file:///D:/PycharmProjects/ILoveLearning/templates) - HTML模板文件

## 管理命令

### 重启应用
```bash
sudo supervisorctl restart ilovelearning
```

### 查看应用日志
```bash
sudo tail -f /var/log/supervisor/ilovelearning.log
```

### 重新加载Nginx配置
```bash
sudo nginx -t && sudo systemctl reload nginx
```

### 更新应用代码
```bash
cd /var/www/ILoveLearning
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # 如果有requirements.txt文件
sudo supervisorctl restart ilovelearning
```

## 安全建议

1. 定期更新系统和软件包
2. 使用强密码保护服务器
3. 配置防火墙规则
4. 定期备份数据
5. 监控服务器性能和安全日志

## 故障排除

### 应用无法启动
- 检查Supervisor日志：`sudo tail -f /var/log/supervisor/ilovelearning.log`
- 确认虚拟环境已激活且依赖已安装

### Nginx配置错误
- 检查语法：`sudo nginx -t`
- 查看错误日志：`sudo tail -f /var/log/nginx/error.log`

### SSL证书问题
- 检查域名是否正确指向服务器IP
- 确认80和443端口未被防火墙阻止
- 验证证书状态：`sudo certbot certificates`

## 性能优化建议

1. 调整Gunicorn工作进程数（通常为CPU核心数的2倍+1）
2. 配置Nginx静态文件缓存
3. 使用CDN加速静态资源加载
4. 定期监控服务器资源使用情况

## 备份策略

定期备份以下内容：
- 项目代码：`/var/www/ILoveLearning/`
- Nginx配置：`/etc/nginx/sites-available/ilovelearning`
- Supervisor配置：`/etc/supervisor/conf.d/ilovelearning.conf`
- 任何用户数据或数据库（如果使用）

## 项目维护

- 定期检查应用更新
- 监控SSL证书到期时间
- 定期审查访问日志
- 保持系统和软件包更新

## Debian 12.12 + 宝塔面板部署指南

除了传统的部署方式，你也可以使用宝塔面板来简化部署过程。宝塔面板提供了图形化界面，使得部署、配置和管理变得更加直观和便捷。

### 1. 安装宝塔面板

首先，在Debian系统上安装宝塔面板：

```bash
# 更新系统包
sudo apt update

# 安装宝塔面板
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh
sudo bash install.sh ed84842
```

安装完成后，系统会显示宝塔面板的访问地址、用户名和密码，请妥善保存这些信息。

### 2. 配置宝塔面板

1. 使用浏览器访问宝塔面板地址（通常是 `http://服务器IP:8888`）
2. 使用提供的用户名和密码登录
3. 在面板中安装以下软件：
   - Nginx
   - Python项目管理器
   - PM2（用于进程管理，如果可用）

### 3. 配置Python项目

1. 在宝塔面板左侧菜单中找到“软件商店”
2. 搜索并安装“Python项目管理器”
3. 安装完成后，在左侧菜单中点击“Python项目”
4. 点击“添加部署项目”

### 4. 部署ILoveLearning项目

1. 在“添加部署项目”页面中：
   - 项目名称：ILoveLearning
   - 项目路径：`/www/wwwroot/ilovelearning`
   - Python版本：选择Python 3.8或更高版本
   - 项目类型：选择“Flask应用”
   - 项目文件：`app.py`
   - 端口：8000（或任意可用端口）

2. 点击“提交”开始创建项目

### 5. 获取项目代码

在服务器上使用SSH执行以下命令：

```bash
# 创建项目目录
sudo mkdir -p /www/wwwroot/ilovelearning
sudo chown -R www:www /www/wwwroot/ilovelearning

cd /www/wwwroot/ilovelearning

git clone https://github.com/BusyMitten/ILoveLearning.git .
```

### 6. 配置虚拟环境和依赖

在宝塔面板的Python项目管理中：

1. 进入ILoveLearning项目的管理页面
2. 点击“虚拟环境”选项卡
3. 创建新的虚拟环境
4. 在终端或项目管理界面中安装依赖：

```bash
cd /www/wwwroot/ilovelearning
source venv/bin/activate
pip install -r requirements.txt
```

### 7. 配置Gunicorn

1. 在项目管理页面中，编辑Gunicorn配置
2. 将配置文件设置为：

```
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 30
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

### 8. 配置Nginx反向代理

1. 在宝塔面板左侧菜单中点击“网站”
2. 点击“添加站点”
3. 填写以下信息：
   - 域名：你的域名
   - FTP：否
   - 数据库：否
   - 程序类型：纯静态
4. 点击“提交”

5. 点击新创建的站点名称，进入站点设置
6. 在左侧菜单中点击“反向代理”
7. 点击“添加反向代理”
8. 配置如下：
   - 代理名称：ILoveLearning
   - 目标URL：`http://127.0.0.1:8000`
   - 发送域名：留空
9. 点击“提交”

### 9. 配置SSL证书

1. 在站点设置中，点击“SSL”菜单
2. 选择“Let's Encrypt”选项卡
3. 点击“申请”按钮
4. 填写邮箱地址并勾选同意条款
5. 等待证书申请完成

### 10. 配置自动续期

宝塔面板会自动处理Let's Encrypt证书的续期，但你可以确认设置：

1. 在宝塔面板左侧菜单中点击“计划任务”
2. 确保有Let's Encrypt证书自动续期的任务

### 11. 管理应用

通过宝塔面板，你可以轻松管理应用：

- 启动/停止/重启Python项目
- 查看应用日志
- 监控资源使用情况
- 配置防火墙规则
- 管理SSL证书

### 12. 备份和恢复

利用宝塔面板的备份功能：

1. 在“计划任务”中设置自动备份
2. 定期备份项目文件和配置
3. 使用“备份”功能手动备份重要数据

### 13. 性能优化

在宝塔面板中优化性能：

1. 使用“安全”功能配置防火墙
2. 在“监控”中查看服务器资源使用情况
3. 配置Nginx缓存提升性能
4. 使用“文件”功能优化静态资源

## 宝塔面板部署优势

- 图形化界面，操作直观
- 一键安装和配置常用软件
- 内置SSL证书管理
- 简化的防火墙配置
- 直观的进程和资源监控
- 便捷的备份和恢复功能

完成以上步骤后，你的ILoveLearning应用将在Debian 12.12 + 宝塔面板环境下通过HTTPS安全访问。记得将配置文件中的`your-domain.com`替换为你的实际域名。

---

完成以上步骤后，你的ILoveLearning应用将在Debian服务器上通过HTTPS安全访问。记得将配置文件中的`your-domain.com`替换为你的实际域名。