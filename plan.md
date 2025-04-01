```markdown
# 简易 HTTP 服务器（带文件上传下载功能）

## 核心需求
1. 文件列表（目录浏览）- 类似于 http.server 的默认 UI
2. 文件下载功能
3. 文件上传功能
4. 简洁、最小化的用户界面

## 技术方案

### 后端 (基于Python标准库)
- 使用 `http.server` 作为基础 HTTP 服务器
- 继承并扩展 `SimpleHTTPRequestHandler` 类
- 添加以下功能：
  - 目录列表（已有功能，保持原样）
  - 文件下载（已有功能，保持原样）
  - 文件上传（新增功能）
- 仅使用 Python 标准库，无需额外依赖

### 前端
- UI 保持与默认 http.server 界面相似
- 简单的 HTML 文件列表包含：
  - 下载文件的链接（原有功能）
  - 基本的文件上传表单（新增功能）
  - 当前目录路径显示
- 最小化 CSS 实现基础样式

### 安全考虑
- 净化文件路径以防止目录遍历攻击

## 项目目录结构
simple_http_server/
├── server/
│   ├── __init__.py
│   ├── handler.py        # HTTP请求处理器
│   ├── html_generator.py # HTML生成函数
│   └── path_utils.py     # 路径处理工具
├── templates/
│   └── upload_form.html  # 上传表单模板
├── static/
│   └── style.css         # 基本样式
├── main.py               # 主程序入口
└── README.md             # 项目说明

## 编程最佳实践
- **模块化设计**：将功能分为独立模块，易于维护
- **零依赖**：仅使用Python标准库，无需安装任何第三方包
- **代码精简**：保持代码量少而功能完整
- **低耦合**：各组件之间依赖性低，便于单独修改
- **兼容性**：确保在Python 3.6+版本上运行
- **清晰的错误处理**：提供明确的错误信息，便于排查
- **注释清晰**：关键逻辑添加简洁明了的注释
- **路径处理安全**：防止目录遍历等安全问题

## 详细开发计划

### 1. 路径工具模块 (server/path_utils.py)
- 实现路径规范化函数
- 添加路径安全验证
- 提供目录遍历防护

### 2. HTML生成模块 (server/html_generator.py)
- 创建增强版目录列表HTML生成器
- 集成上传表单到目录列表
- 保持与原始http.server风格一致

### 3. 请求处理器 (server/handler.py)
- 继承SimpleHTTPRequestHandler
- 添加POST请求处理方法
- 实现文件上传功能
- 集成HTML生成器

### 4. 模板和样式 (templates/upload_form.html, static/style.css)
- 创建上传表单HTML模板
- 设计简单样式，保持与http.server风格一致

### 5. 主程序入口 (main.py)
- 设置命令行参数解析
- 配置和启动HTTP服务器
- 提供简洁的帮助信息

## 实现细节

### 路径工具 (path_utils.py)
- 封装所有路径操作
- 确保文件操作安全
- 处理相对路径和绝对路径

### HTML生成器 (html_generator.py)
- 扩展原始目录列表HTML
- 添加上传表单
- 保持界面一致性

### 请求处理器 (handler.py)
- 处理GET请求显示目录和下载文件
- 处理POST请求接收上传文件
- 实现multipart/form-data解析

### 主程序 (main.py)
- 解析命令行参数
- 设置服务器配置
- 启动HTTP服务器

## 使用方法
python main.py [端口] [目录]

此实现方案使用纯Python标准库，采用模块化设计，无需安装任何额外包，用户可以直接运行Python脚本启动带有文件上传功能的HTTP服务器。
```