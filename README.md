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

## lixinez.icu网站文档

### 网站概述

- **网址**: https://lixinez.icu
- **服务器**: 京东云轻量云主机 (117.72.194.27)
- **技术栈**: Flask + MySQL + Redis + Nginx
- **备案号**: 沪ICP备2025124588号-1

### 网站结构

```
/var/www/LiXinTools/        # 主工作目录
├── Web/                    # Web应用程序目录
│   ├── app.py              # Flask主程序
│   ├── templates/          # HTML模板
│   │   └── index.html      # 主页模板
│   └── static/             # 静态资源
│       ├── css/            # 样式表
│       ├── js/             # JavaScript
│       ├── pic/            # 图片资源
│       └── lib/            # 第三方库(本地化CDN资源)
│           ├── bootstrap/  # Bootstrap库
│           ├── chart.js/   # Chart.js图表库
│           └── bootstrap-icons/ # 图标库
├── scripts/                # 脚本目录
│   └── query_all_rooms.py  # 定时查询脚本
├── utils/                  # 工具目录
│   └── analysis_electricity.py # 电量分析工具
└── venv/                   # Python虚拟环境
```

### 核心服务

1. **Nginx**: 前端反向代理，处理静态资源和SSL
2. **Flask**: 网站后端API和页面渲染
3. **MySQL**: 存储电量查询数据
4. **Redis**: 缓存热点数据减轻数据库压力
5. **Cron**: 定时任务，每30分钟查询一次电量

### 开发与部署流程

1. 本地开发代码并提交Git
2. 推送到云服务器Git仓库: `git push jdcloud main`
3. 服务器Git钩子自动部署代码到工作目录
4. 重启相关服务使更改生效

### 常用维护命令

```bash
# 服务管理
sudo systemctl restart lixintools-web  # 重启Web应用
sudo systemctl restart nginx           # 重启Nginx
sudo systemctl restart redis-server    # 重启Redis
sudo systemctl restart mysql           # 重启MySQL

# 日志查看
tail -f /var/log/electricity_query.log # 查看电量查询日志
journalctl -u lixintools-web -f        # 查看Web应用日志
sudo tail -f /var/log/nginx/access.log # 查看Nginx访问日志
sudo tail -f /var/log/nginx/error.log  # 查看Nginx错误日志

# 数据库操作
mysql -u elecuser -p                   # 登录MySQL
> use electricity_data;                # 选择数据库
> SELECT * FROM query_history LIMIT 5; # 查询示例

# Redis缓存操作
redis-cli                              # 连接Redis
> AUTH 您的密码                         # 认证(如果设置了密码)
> KEYS *                               # 查看所有键
> GET get_latest_query_time            # 查看缓存值
> FLUSHALL                             # 清空所有缓存

# 代码管理
git clone root@117.72.194.27:/opt/LiXinTools  # 克隆仓库到本地
git push jdcloud main                         # 推送更新到服务器

# 文件传输
scp -r local_file.py root@117.72.194.27:/var/www/LiXinTools/  # 上传文件
scp -r root@117.72.194.27:/var/www/LiXinTools/Web ./          # 下载文件
```

### 故障处理

1. **网站无法访问**:
   - 检查服务状态: `systemctl status nginx lixintools-web`
   - 检查日志: `journalctl -u lixintools-web -n 50`
   - 尝试重启服务: `systemctl restart lixintools-web nginx`

2. **数据未更新**:
   - 检查定时任务: `crontab -l`
   - 检查查询日志: `tail -f /var/log/electricity_query.log`
   - 手动执行查询: `cd /var/www/LiXinTools && source venv/bin/activate && python scripts/query_all_rooms.py`

3. **页面加载缓慢**:
   - 检查Redis缓存: `redis-cli PING`
   - 查看MySQL负载: `mysql -e "SHOW PROCESSLIST"`
   - 检查服务器资源: `htop`

## 许可证

[MIT](LICENSE)

## 贡献

欢迎提交问题报告和贡献代码！ 