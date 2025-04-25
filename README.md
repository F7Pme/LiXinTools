# LiXinTools

LiXinTools是一个基于PySide6的工具集应用程序，专为上海立信立信会计金融学院的学生开发，提供一卡通和学习通服务的便捷访问。

## 联系作者

- **作者**：顾佳俊 上海立信会计金融学院 2023级 金融科技5班
- **微信**：AL-0729-zK
- **电子邮件**：3298732438@qq.com

## 功能特点

- 一卡通服务访问与查询
- 学习通课程管理和通知查看
- 开发者日志模式，方便调试
- 现代化UI界面设计
- 会话管理与自动登录

## 程序截图

### 登录界面
<img src="screenshots/登录界面.png" width="500" alt="登录界面">

### 多账户管理
<img src="screenshots/多账户管理.png" width="500" alt="多账户管理">

### 一卡通功能
<img src="screenshots/账单查询分析.png" width="500" alt="账单查询分析">
<img src="screenshots/电费查询分析.png" width="500" alt="电费查询分析">

### 电量网站
<img src="screenshots/电量网站.png" width="500" alt="电量网站">


## 安装要求

- Python 3.8+
- PySide6
- 其他依赖库（详见requirements.txt）

## 如何使用

1. 克隆仓库
```
git clone https://github.com/F7Pme/LiXinTools.git
```

2. 安装依赖
```
pip install -r requirements.txt
```

3. 运行程序
```
python main.py
```

4. 打包为可执行文件（Windows）
```
build_exe.bat
```

## 项目结构

- `main.py`: 程序入口文件
- `build_exe.bat`: Windows下打包可执行文件的脚本
- `LiXinTools.spec`: PyInstaller打包配置文件
- `requirements.txt`: 项目依赖库列表
- `core/`: 核心功能模块
  - `auth.py`: 认证和会话管理
  - `__init__.py`: 包初始化文件
- `gui/`: 图形用户界面组件
  - `BaseWindow.py`: 窗口基类
  - `LoginWindow.py`: 登录窗口
  - `MainWindow.py`: 主窗口
  - `MessageWindow.py`: 消息提示窗口
  - `LoadWindow.py`: 加载窗口
  - `LogWindow.py`: 日志窗口
  - `SideBar.py`: 侧边栏基础组件
  - `SideBar_author.py`: 作者信息侧边栏
  - `SideBar_bill.py`: 账单查询侧边栏
  - `SideBar_electricity.py`: 电费查询侧边栏
  - `SideBar_info.py`: 信息展示侧边栏
  - `SideBar_xxt.py`: 学习通侧边栏
  - `TitleBar.py`: 标题栏组件
  - `styles.py`: UI样式定义
  - `__init__.py`: 包初始化文件
  - `styles/`: 样式资源文件
  - `pic/`: 图片资源文件
- `config/`: 配置文件和数据
  - `config.py`: 应用程序配置
  - `room_data/`: 房间数据
  - `__init__.py`: 包初始化文件
- `utils/`: 工具函数
  - `query_xxt.py`: 学习通查询工具
  - `query_bill.py`: 账单查询工具
  - `query_electricity.py`: 电费查询工具
  - `analysis_bill.py`: 账单分析工具
  - `analysis_electricity.py`: 电费分析工具
  - `data_parser.py`: 数据解析器
  - `__init__.py`: 包初始化文件
- `dist/`: 打包后的可执行文件目录
- `build/`: 构建临时文件目录
- `screenshots/`: 应用程序截图目录
- `Log/`: 日志文件目录
- `cookies/`: 保存的会话数据
- `__pycache__/`: Python缓存文件目录
- `Web/`: Web应用目录
  - `app.py`: Flask Web应用
  - `templates/`: HTML模板
  - `static/`: 静态资源文件

## 开发者模式

启动时会自动检测开发者模式设置，在开发者模式下会显示日志窗口，方便调试和开发。

## 许可证

[MIT](LICENSE)

## 贡献

欢迎提交问题报告和贡献代码！ 

---

# 电量查询系统云服务器部署文档

## 部署环境

- 服务器：京东云轻量云主机 (117.72.194.27)
- 操作系统：Ubuntu
- 部署架构：Flask应用(5000端口) + MySQL数据库 + Nginx反向代理

## 核心部署步骤

1. **系统准备**
```bash
# 安装必要软件包
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv mysql-server nginx
```

2. **代码部署**
```bash
# 创建Git仓库和工作目录
mkdir -p /opt/LiXinTools && cd /opt/LiXinTools
git init --bare

# 设置Git钩子
cat > /opt/LiXinTools/hooks/post-receive << 'EOL'
#!/bin/bash
GIT_WORK_TREE=/var/www/LiXinTools git checkout -f main
echo "部署已完成!"
EOL
chmod +x /opt/LiXinTools/hooks/post-receive

# 创建工作目录
mkdir -p /var/www/LiXinTools
```

3. **数据库配置**
```bash
# 创建数据库和用户
sudo mysql -e "CREATE DATABASE electricity_data;"
sudo mysql -e "CREATE USER 'elecuser'@'localhost' IDENTIFIED WITH mysql_native_password BY '123456';"
sudo mysql -e "GRANT ALL PRIVILEGES ON electricity_data.* TO 'elecuser'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

4. **Python环境设置**
```bash
# 创建虚拟环境并安装依赖
cd /var/www/LiXinTools
python3 -m venv venv
source venv/bin/activate
pip install flask pymysql beautifulsoup4 requests cryptography
```

5. **定时任务配置**
```bash
# 设置30分钟查询一次
crontab -e
# 添加: */30 * * * * cd /var/www/LiXinTools && ./venv/bin/python ./scripts/query_all_rooms.py >> /var/log/electricity_query.log 2>&1
```

6. **Web服务配置**
```bash
# 创建systemd服务
sudo nano /etc/systemd/system/lixintools-web.service
# 添加服务配置（见下方服务配置内容）

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable lixintools-web
sudo systemctl start lixintools-web
```

7. **Nginx配置**
```bash
# 创建网站配置
sudo nano /etc/nginx/sites-available/lixintools
# 添加Nginx配置（见下方Nginx配置内容）

# 启用站点
sudo ln -s /etc/nginx/sites-available/lixintools /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo ufw allow 'Nginx Full'
```

## 常用配置文件

### systemd服务配置
```
[Unit]
Description=LiXinTools Web Application
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/LiXinTools
ExecStart=/var/www/LiXinTools/venv/bin/python -m Web.app --host=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx配置
```
server {
    listen 80;
    server_name xxx;

    location /static {
        alias /var/www/LiXinTools/Web/static;
        expires 30d;
    }

    location / {
        proxy_pass xxx;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 常用维护命令

```bash
# 服务管理
sudo systemctl start/stop/restart lixintools-web
sudo systemctl status lixintools-web

# 数据库操作
mysql -u elecuser -p123456 electricity_data
mysqldump -u elecuser -p123456 electricity_data > backup.sql

# 手动执行查询
cd /var/www/LiXinTools && source venv/bin/activate
python scripts/query_all_rooms.py

# 查看日志
tail -f /var/log/electricity_query.log
journalctl -u lixintools-web

# Git操作
git remote add jdcloud root@117.72.194.27:/opt/LiXinTools
git push jdcloud main
```