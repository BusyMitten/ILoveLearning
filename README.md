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

---

完成以上步骤后，你的ILoveLearning应用将在Debian服务器上通过HTTPS安全访问。记得将配置文件中的`your-domain.com`替换为你的实际域名。