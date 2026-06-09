
## 一、Python 依赖库安装与环境配置

### 1.1 实验目标

掌握使用 `python -m pip` 命令安装 FastAPI、uvicorn、sqlmodel、python-multipart 等后端开发所需的 Python 第三方库，理解虚拟环境的创建与激活方法，能够独立配置项目运行所需的依赖环境，并排查常见的库版本冲突问题。

### 1.2 背景知识

FastAPI 是一个基于 Python 3.6+ 的高性能 Web 框架，它使用 Starlette 作为底层 ASGI 服务器框架，并利用 Pydantic 进行数据校验。开发 FastAPI 应用之前，需要安装若干核心依赖库：

| 库名 | 用途 |
|------|------|
| `fastapi` | Web 框架本体，提供路由、依赖注入、数据校验等功能 |
| `uvicorn` | ASGI 服务器，用于运行 FastAPI 应用 |
| `sqlmodel` | ORM 库，由 SQLAlchemy + Pydantic 融合而成，同时支持数据库操作与数据校验 |
| `python-multipart` | multipart 表单解析库，文件上传功能必需 |

### 1.3 操作步骤

**步骤 1：创建虚拟环境**

打开终端，在项目根目录下执行：

```bash
python -m venv venv
```

> **提示**：`python -m venv` 是 Python 内置的虚拟环境创建模块，无需额外安装。

**步骤 2：激活虚拟环境**

- Windows 系统：`venv\Scripts\activate`
- Linux/macOS 系统：`source venv/bin/activate`

**步骤 3：使用 pip 安装依赖库**

```bash
python -m pip install fastapi uvicorn sqlmodel python-multipart
```

> **思考题**：为什么使用 `python -m pip` 而不是直接 `pip install`？  
> **提示**：`python -m pip` 确保使用当前 Python 解释器对应的 pip 版本，避免多版本 Python 环境下的安装混乱。

**步骤 4：验证安装**

```bash
python -c "import fastapi; print(fastapi.__version__)"
python -c "import uvicorn; print(uvicorn.__version__)"
python -c "import sqlmodel; print(sqlmodel.__version__)"
```

**步骤 5：导出依赖清单（可选）**

```bash
python -m pip freeze > requirements.txt
```

> **后续使用**：其他同学可通过 `python -m pip install -r requirements.txt` 一键安装所有依赖。

### 1.4 常见问题排查

- **问题**：安装超时  
  **解决**：使用国内镜像源，如 `python -m pip install fastapi -i https://pypi.tuna.tsinghua.edu.cn/simple`
- **问题**：`python -m pip` 报错 "No module named pip"  
  **解决**：执行 `python -m ensurepip --upgrade` 后重试

---

## 二、FastAPI 项目结构设计与服务器启动

### 2.1 实验目标

理解 FastAPI 框架的基本项目结构设计，掌握 uvicorn ASGI 服务器的启动配置方法（包括 host、port、reload 等参数），理解 FastAPI 应用的 lifespan 上下文管理器机制，能够在应用启动时完成数据库初始化与目录创建等准备工作。

### 2.2 背景知识

一个典型的 FastAPI 单文件项目结构如下：

```
exp8codes/
├── webmain.py          # 主程序文件（FastAPI应用定义 + 数据库模型 + API路由）
├── static/             # 静态资源目录
│   ├── index.html      # 前端页面
│   ├── favicon.ico     # 网站图标
│   ├── jquery-*.js     # jQuery库
│   ├── bootstrap-*/     # Bootstrap框架
│   └── sdsimple/       # 额外前端组件
└── data/                # 数据存储目录（自动创建）
    ├── sqlite_database.db   # SQLite数据库文件
    └── post/                # 上传的PDF文件存储目录
```

### 2.3 操作步骤

**步骤 1：创建 FastAPI 应用实例**

在 `webmain.py` 中，首先导入必要的库，然后创建 FastAPI 应用实例：

> **关键 API**：`from fastapi import FastAPI` → `app = FastAPI(lifespan=lifespan)`
> 
> **提示**：`lifespan` 参数接收一个异步上下文管理器函数，用于在应用启动和关闭时执行初始化/清理操作。

**步骤 2：定义 lifespan 上下文管理器**

> **关键 API**：`from contextlib import asynccontextmanager`
> 
> 在 lifespan 函数中调用 `init_data()` 创建必要目录，调用 `create_table()` 初始化数据库表。

**步骤 3：配置 uvicorn 启动参数**

在 `webmain.py` 的 `if __name__ == '__main__':` 块中，使用 uvicorn 启动应用：

> **关键 API**：`uvicorn.run(app, host='0.0.0.0', port=5246, reload=False, workers=None)`
> 
> **参数说明**：
> - `host='0.0.0.0'`：监听所有网络接口，允许外部访问
> - `port=5246`：指定服务端口
> - `reload=False`：生产环境关闭热重载
> - `reload_dirs`：指定监控重载的目录

**步骤 4：启动并访问**

运行 `python webmain.py`，然后在浏览器中访问：
- `http://localhost:5246` → 主页（自动重定向到 `/static/index.html`）
- `http://localhost:5246/docs` → FastAPI 自动生成的交互式 API 文档（Swagger UI）

> **思考题**：如果在 uvicorn.run 中设置 `reload=True`，修改代码后会发生什么？

---

## 三、SQLModel 数据库模型设计与表创建

### 3.1 实验目标

掌握使用 SQLModel 定义数据模型的方法，能够设计 User（用户表）、Post（帖子表）、Favor（收藏表）三张核心数据表，理解字段类型约束、主外键关联、唯一索引与普通索引的设计原则，理解 SQLAlchemy 引擎的创建与 SQLModel.metadata.create_all() 自动建表机制。

### 3.2 背景知识

SQLModel 是由 FastAPI 作者 Tiangolo 创建的 ORM 库，它将 SQLAlchemy（数据库 ORM）和 Pydantic（数据校验）合二为一。一个 SQLModel 类同时充当数据库表定义和请求/响应数据模型。

本实验需要设计三张表，它们之间的关系为：

- **User（用户表）**：存储用户基本信息和认证数据
- **Post（帖子表）**：存储用户上传的 PDF 帖子，通过 `userid` 外键关联 User
- **Favor（收藏表）**：存储用户对帖子的收藏关系，是 User 和 Post 之间的多对多关联表

### 3.3 操作步骤

**步骤 1：创建数据库引擎**

> **关键 API**：`from sqlmodel import create_engine`
> 
> 使用 SQLite 作为数据库，连接字符串格式为 `sqlite:///相对路径.db`。
> 
> **提示**：添加 `?nolock=1` 参数可以提升 SQLite 在并发场景下的性能。

**步骤 2：定义 User 模型**

> **关键 API**：`class User(SQLModel, table=True):`
> 
> 需要定义的字段包括：
> - `id`：主键，自增整数
> - `email`：可选字符串
> - `username`：字符串，设置 `index=True` 和 `unique=True`
> - `password`：字符串（明文存储，仅用于教学演示）
> - `age`：可选整数
> - `bearer_token`：可选字符串，`unique=True`，用于认证
> - `bearer_token_datesec`：可选浮点数，记录 Token 签发时间
> - `userclass`：字符串，默认值 `'normal'`
> 
> **提示**：使用 `Field()` 函数设置字段属性，如 `Field(default=None, primary_key=True, index=True)`。

**步骤 3：定义 Post 模型**

> **关键 API**：`Field(default=None, index=True, foreign_key='user.id')`
> 
> Post 表的字段：
> - `id`：主键
> - `userid`：外键关联 `user.id`
> - `rdir`：相对目录
> - `filename`：原始文件名
> - `datesec`：发布时间戳
> - `is_del`：逻辑删除标志，默认 `False`
> - `favors`：收藏计数

**步骤 4：定义 Favor 模型**

> Favor 表作为 User 和 Post 之间的关联表，字段包括 `userid`（外键关联 User）、`postid`（外键关联 Post）、`rdir`、`datesec`。

**步骤 5：自动建表**

> **关键 API**：`SQLModel.metadata.create_all(engine, checkfirst=True)`
> 
> **参数说明**：`checkfirst=True` 表示如果表已存在则跳过，避免重复创建。

**步骤 6：会话管理**

> **关键 API**：`from sqlmodel import Session`
> 
> 使用 `with Session(engine) as session:` 上下文管理器获取数据库会话，通过 `session.exec()` 执行查询，通过 `session.add()` / `session.commit()` 提交变更。

---

## 四、用户认证系统实现（OAuth2 + Bearer Token）

### 4.1 实验目标

掌握基于 OAuth2 密码模式的用户认证系统实现，理解 OAuth2PasswordBearer 方案的工作流程，能够实现用户注册（含用户名长度校验、重复检测、自动分类）与登录（含密码验证、Bearer Token 生成与持久化）的完整数据库操作，理解 Token 过期时间管理与唯一性保障机制。

### 4.2 背景知识

OAuth2 密码模式（Password Flow）是前后端分离应用中最常用的认证方案之一。其核心流程为：

1. 客户端提交 `username` 和 `password` 到服务端
2. 服务端验证凭据后生成一个 Bearer Token
3. 客户端后续请求在 HTTP 头中携带该 Token
4. 服务端验证 Token 有效性后处理请求

### 4.3 操作步骤

**步骤 1：配置 OAuth2PasswordBearer**

> **关键 API**：
> ```python
> from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
> oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
> ```
> 
> **提示**：`tokenUrl="token"` 控制着 `/docs` 页面中 "Authorize" 按钮弹出的登录表单提交地址。

**步骤 2：实现 Token 生成函数**

> **关键思路**：在 `db_make_unique_bearer_token()` 函数中，循环生成随机字符串（使用 `random.choices()` 从字母数字池中选取），查询数据库确认唯一性后返回。
> 
> **提示**：`string.digits + string.ascii_letters` 可获取所有数字和字母的组合作为随机字符池。

**步骤 3：实现用户注册逻辑**

> 在 `db_register()` 函数中需要完成：
> 1. 校验用户名和密码长度（不少于5个字符）
> 2. 检查用户名是否已存在
> 3. 判断用户类型（以 `admin` 开头的用户名自动设为管理员）
> 4. 创建 User 对象并提交到数据库
> 5. 注册成功后自动调用登录函数返回 Token

**步骤 4：实现用户登录逻辑**

> 在 `db_user_login()` 函数中需要完成：
> 1. 根据用户名查询数据库
> 2. 验证密码是否匹配
> 3. 生成唯一 Bearer Token
> 4. 将 Token 和签发时间保存到用户记录
> 5. 返回用户信息和 Token

**步骤 5：实现 Token 验证逻辑**

> 在 `db_get_user_by_token()` 函数中：
> 1. 根据 Token 查询用户
> 2. 检查 Token 是否存在（为 None 表示已登出）
> 3. 计算时间差，判断是否超过有效期（`token_expired_time = 7 * 24 * 60 * 60` 秒）

**步骤 6：创建注册和登录 API 端点**

> **关键 API**：
> ```python
> @app.post("/user/login")
> def app_login(request: Request, form_data: Form_data, session: Session = Depends(get_session)):
> ```
> 
> **提示**：`Form_data` 使用了 `Annotated` 类型别名简化参数注入，它本质上是 `Annotated[OAuth2PasswordRequestForm, Depends()]`。

---

## 五、RESTful API 接口设计与路由实现

### 5.1 实验目标

掌握 FastAPI 中 RESTful API 接口的设计与实现方法，能够使用路由装饰器（@app.get、@app.post）定义用户登录、用户注册、获取用户信息、文件上传、帖子查询、帖子操作等接口，理解 Depends 依赖注入机制与 Pydantic 模型的请求参数校验。

### 5.2 背景知识

RESTful API 设计遵循资源导向的原则，每个 URL 代表一种资源，HTTP 方法（GET/POST/PUT/DELETE）代表对资源的操作类型。FastAPI 通过装饰器将函数映射为 HTTP 端点，并自动完成请求参数的解析与校验。

### 5.3 操作步骤

**步骤 1：定义 Pydantic 请求模型**

> 对于 JSON Body 请求，需要定义继承自 `BaseModel` 的 Pydantic 模型：
> 
> **Get_posts 模型**（查询帖子列表）：
> - `scope`：查询范围（`'home'` 首页 / `'self'` 我的发布）
> - `order`：排序方式（`'time_descending'` / `'time_ascending'`）
> - `offset`：分页偏移量
> - `limit`：每页数量
> 
> **Set_one_post 模型**（操作帖子）：
> - `postid`：帖子 ID
> - `isdel`：是否删除
> - `isfavor`：是否收藏（True/False/None）

**步骤 2：实现 GET 路由——根路径重定向**

> **关键 API**：
> ```python
> @app.get("/", response_class=fastapi.responses.RedirectResponse)
> def app_read_root(request: Request):
>     return '/static/index.html'
> ```
> 
> **提示**：`response_class=RedirectResponse` 告诉 FastAPI 将返回值作为重定向地址处理。

**步骤 3：实现 POST 路由——用户信息查询**

> **关键 API**：使用 `Depends(oauth2_scheme)` 自动从请求头 `Authorization: Bearer <token>` 中提取 Token。
> 
> **提示**：如果 Token 无效，`oauth2_scheme` 会自动返回 401 错误响应。

**步骤 4：实现帖子查询与操作路由**

> **关键 API**：`@app.post("/user/getposts")` 和 `@app.post("/user/setpost")`
> 
> 这两个接口均接收 JSON Body（通过 Pydantic 模型校验）和 Bearer Token 认证。注意 `getposts` 的 Token 参数应设为可选（`TokenDep=None`），以允许未登录用户浏览首页帖子。

**步骤 5：配置静态文件挂载**

> **关键 API**：`app.mount("/static", StaticFiles(directory=...), name="static")`
> 
> **提示**：`check_dir=False` 参数允许在目录不存在时不报错。

> **思考题**：为什么 `getposts` 接口需要允许匿名访问（Token 可选），而 `setpost` 接口必须认证？

---

## 六、PDF 文件上传处理与静态资源管理

### 6.1 实验目标

掌握 FastAPI 中文件上传的处理方法，能够使用 UploadFile 接收客户端上传的 PDF 文件，实现文件类型校验、存储路径自动生成、文件字节流写入磁盘等完整流程，理解 FastAPI 的静态文件挂载机制与多路径静态资源服务配置。

### 6.2 操作步骤

**步骤 1：实现文件上传 API 端点**

> **关键 API**：
> ```python
> @app.post("/user/uploadfile")
> def app_uploadfile(request: Request, token: TokenDep,
>                    filePdf: UploadFile = File(media_type='application/pdf'),
>                    session: Session = Depends(get_session)):
> ```
> 
> **参数说明**：
> - `File(media_type='application/pdf')`：限制只接收 PDF 文件
> - `UploadFile` 提供了 `.file`（类文件对象）和 `.filename`（原始文件名）属性

**步骤 2：实现后端文件存储逻辑**

> 在 `db_user_uploadpdf()` 函数中完成以下操作：
> 1. 验证 Token 有效性
> 2. 校验文件扩展名是否为 `.pdf`
> 3. 创建 Post 记录并提交到数据库（此时自动获得帖子 ID）
> 4. 根据帖子 ID 生成存储路径（如 `data/post/{id}/main/main.pdf`）
> 5. 创建目录结构（`os.makedirs(..., exist_ok=True)`）
> 6. 将上传文件的字节流写入磁盘

**步骤 3：配置帖子文件的静态访问路径**

> **关键 API**：`app.mount("/post", StaticFiles(directory=gsetting.post_files_dir), name="post")`
> 
> 这样配置后，`http://localhost:5246/post/{id}/main/main.pdf` 即可直接访问上传的 PDF 文件。

**步骤 4：在前端嵌入 PDF 预览**

> 前端使用 Bootstrap 的 `embed-responsive` 组件：
> ```html
> <div class="embed-responsive embed-responsive-16by9">
>   <iframe class="embed-responsive-item" src="${url}#toolbar=0"></iframe>
> </div>
> ```
> 
> **提示**：`#toolbar=0` 参数隐藏 PDF 工具栏，使预览更简洁。

> **思考题**：如何防止用户上传非 PDF 文件造成安全问题？除了 `media_type` 限制外，后端还应做什么校验？

---

## 七、前端 Bootstrap 页面布局与组件使用

### 7.1 实验目标

掌握 Bootstrap 3 前端框架的核心组件使用方法，能够运用栅格系统构建响应式页面布局，使用导航栏组件实现页面顶部固定导航，使用模态框组件构建用户登录/注册弹窗，理解 Bootstrap CSS 类的排版、按钮、表单等基础样式的应用。

### 7.2 背景知识

Bootstrap 是目前最流行的前端 UI 框架之一。本项目使用 Bootstrap 3.3.7 版本，需要引入以下核心文件：

- `bootstrap.css`：核心样式表
- `bootstrap.js`：核心 JavaScript（依赖 jQuery）
- `jquery-1.12.4.js`：jQuery 库

### 7.3 操作步骤

**步骤 1：搭建页面基本结构**

> 创建 `index.html`，在 `<head>` 中引入 Bootstrap CSS，在 `<body>` 末尾引入 jQuery 和 Bootstrap JS。
> 
> **提示**：注意引入顺序——jQuery 必须在 Bootstrap JS 之前加载。

**步骤 2：使用栅格系统构建主内容区**

> Bootstrap 3 的栅格系统将页面分为 12 列：
> ```html
> <div class="container-fluid">
>   <div class="row">
>     <div class="col-xs-9">帖子列表区域</div>
>     <div class="col-xs-3">侧边栏推荐区域</div>
>   </div>
> </div>
> ```
> 
> **提示**：`col-xs-*` 适用于所有屏幕尺寸（包括手机）。

**步骤 3：创建固定导航栏**

> **关键组件**：使用 `position: sticky; top: 0; z-index: 2` 实现导航栏的粘性定位（滚动时不消失）。
> 
> 导航栏内容包括：
> - 左侧：首页图标（`glyphicon-home`）、"我的发表"链接、排序下拉按钮
> - 右侧：文件上传表单、"登陆或注册"按钮
> 
> **提示**：使用 `display: table` + `display: table-cell` + `vertical-align: middle` 实现导航栏内容的垂直居中。

**步骤 4：构建登录/注册模态框**

> 使用自定义 CSS（`.styleDiv1Hide` + `.styleDiv2Hide`）实现模态框效果：
> - 外层 `div`：全屏遮罩层（`position: fixed; width: 100%; height: 100%`）
> - 内层 `div`：居中白色表单区域（`max-width: 330px; margin: 15% auto`）
> - 渐变背景：`linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%)`
> 
> 模态框中的表单使用 Bootstrap 的 `form-signin` 样式，包含邮箱输入框、密码输入框、切换注册/登录的链接和提交按钮。

**步骤 5：添加 Jumbotron 欢迎区域**

> 使用 Bootstrap 的 `jumbotron` 组件创建页面顶部的欢迎区域：
> ```html
> <div class="jumbotron">
>   <div class="container">
>     <h1>Hello, world!</h1>
>     <p>欢迎来到社区...</p>
>   </div>
> </div>
> ```

> **思考题**：Bootstrap 3 和 Bootstrap 5 在栅格系统和组件命名上有哪些主要差异？

---

## 八、jQuery AJAX 前后端异步通信

### 8.1 实验目标

掌握使用 jQuery 的 `$.ajax` 方法发起异步 HTTP 请求，实现前端页面与 FastAPI 后端 API 的数据交互，理解请求方法（GET/POST）、Content-Type 设置、请求头中 Bearer Token 的注入方式，以及 success/error 回调函数的响应处理逻辑。

### 8.2 操作步骤

**步骤 1：发起 POST 请求——用户登录**

> **关键 API**：
> ```javascript
> $.ajax({
>   type: 'post',
>   url: '/user/login',
>   data: new FormData(formElement),
>   processData: false,
>   contentType: false,
>   success: function(res) { /* 处理成功 */ },
>   error: function(res) { /* 处理失败 */ }
> });
> ```
> 
> **参数说明**：
> - `processData: false`：不将 FormData 转换为查询字符串
> - `contentType: false`：不设置 Content-Type 头（让浏览器自动设置 `multipart/form-data` 及边界）

**步骤 2：发起 POST 请求——JSON Body 类型**

> 对于需要发送 JSON 数据的接口（如 `getposts`、`setpost`）：
> ```javascript
> $.ajax({
>   url: "/user/getposts",
>   type: "POST",
>   headers: {"Authorization": "Bearer " + $.cookie('bearer_token')},
>   contentType: "application/json",
>   data: JSON.stringify(requestBody),
>   success: function(res) { /* 处理帖子数据 */ },
>   error: function(res) { /* 处理错误 */ }
> });
> ```
> 
> **提示**：JSON 请求必须显式设置 `contentType: "application/json"` 并使用 `JSON.stringify()` 序列化请求体。

**步骤 3：理解 Token 注入机制**

> 大部分需要认证的接口都需要在请求头中携带 Bearer Token：
> ```javascript
> headers: {"Authorization": "Bearer " + $.cookie('bearer_token')}
> ```
> 
> Token 存储在 Cookie 中（通过 jQuery Cookie 插件的 `$.cookie('bearer_token', token)` 设置）。

**步骤 4：封装通用工具函数**

> 将常用的 AJAX 逻辑封装为工具函数，如：
> - `get_userinfo_by_bearer_token()`：通过 Token 获取用户信息
> - `tokenShowUsername()`：获取用户信息后更新导航栏显示
> - `alertAjaxError()`：统一的错误提示函数
> 
> **提示**：使用 JavaScript 闭包（IIFE）模式组织工具函数，避免全局命名空间污染。

> **思考题**：为什么登录请求不需要手动添加 Authorization 头，而其他接口需要？

---

## 九、前端用户登录注册交互与 Cookie Token 管理

### 9.1 实验目标

掌握前端用户登录与注册的交互实现，能够使用 jQuery 动态控制模态框的显示与隐藏、登录/注册表单的切换，理解使用 jQuery Cookie 插件存储和管理 Bearer Token 的方法，以及基于 Token 状态的页面元素动态更新。

### 9.2 操作步骤

**步骤 1：封装登录/注册模态框类**

> 使用 JavaScript 类（`class DivLoginRegister`）封装模态框的行为：
> - `constructor()`：解析 HTML 模板字符串生成 jQuery 元素，缓存各个子元素的引用（表单、输入框、按钮、链接、标题等）
> - `show()`：设置 `display: block` 显示模态框，聚焦用户名输入框
> - `hide()`：设置 `display: none` 隐藏模态框
> - `switchToLogin()`：修改标题为"用户登陆"，表单 action 改为 `/user/login`
> - `switchToRegister()`：修改标题为"注册用户"，表单 action 改为 `/user/register`
> - `switchToOther()`：根据当前状态切换为另一种模式

**步骤 2：实现表单提交处理**

> 在 `init()` 方法中绑定事件：
> - 关闭按钮 `.on('click')` → 调用 `hide()`
> - 切换链接 `.on('click')` → 调用 `switchToOther()`
> - 提交按钮 `.on('click')` → 使用 `$.ajax` 提交 `FormData`，成功后将 Token 存入 Cookie 并刷新页面
> 
> **关键 API**：`$.cookie('bearer_token', res.bearer_token)` 将 Token 存储到 Cookie。

**步骤 3：实现基于 Token 的页面状态更新**

> 页面加载时调用 `tokenShowUsername()`：
> 1. 从 Cookie 读取 `bearer_token`
> 2. 发送 POST 请求到 `/user/userinfo` 获取用户信息
> 3. 如果成功，将导航栏的"登陆或注册"文字替换为实际用户名
> 4. 同时将导航栏背景色从 `bg-danger`（红色）切换为 `bg-primary`（蓝色）

**步骤 4：处理页面导航栏的登录触发**

> 为导航栏中的"登陆或注册"链接绑定点击事件，点击时调用 `divLoginRegister.show()` 弹出模态框。

> **思考题**：为什么登录成功后要调用 `location.reload(true)` 刷新整个页面？是否可以不刷新而局部更新页面状态？

---

## 十、帖子列表展示与无限滚动加载

### 10.1 实验目标

掌握前端帖子列表的动态渲染与无限滚动加载实现，能够使用 jQuery 动态拼接 HTML 字符串并向页面注入帖子卡片，理解基于 scroll 事件的滚动监听机制、可视区域判断逻辑以及分页偏移量的递增管理策略。

### 10.2 操作步骤

**步骤 1：封装帖子数据管理对象**

> 使用原型继承模式（`function EleDivPosts()` + `prototype`）封装帖子数据管理逻辑：
> - `req` 对象：存储当前查询参数（`scope`、`order`、`offset`、`limit`）
> - `isLimited` 标志：标记是否已加载全部帖子
> - `set_posts_ajax(req)`：发起 AJAX 请求获取帖子数据
> - `onclick_del(e)`：删除帖子的点击事件处理
> - `onclick_favor(e)`：收藏/取消收藏的点击事件处理

**步骤 2：实现帖子卡片动态渲染**

> 在 `set_posts(posts)` 函数中遍历后端返回的帖子数据，为每个帖子动态拼接 HTML：
> ```javascript
> let content = `
>   <div aria-cusname="${v.id}">
>     <h5>${v.username}  ${v.title}  ${v.date}</h5>
>     <div class="embed-responsive embed-responsive-16by9">
>       <iframe class="embed-responsive-item" src="${v.url}#toolbar=0"></iframe>
>     </div>
>     <div class="container-fluid">
>       <div class="row">
>         <div class="col-xs-6"><button>删除</button></div>
>         <div class="col-xs-6">
>           <button>${v.isfavor ? '已喜欢' : '喜欢'}</button>
>           <a href="${v.url}" target="_blank">全屏</a>
>         </div>
>       </div>
>     </div>
>   </div>
> `;
> ```
> 
> **提示**：使用 jQuery 的 XPath 插件（`$(document).xpath()`）精确选中动态创建的子元素并绑定事件。

**步骤 3：实现无限滚动加载**

> 使用 `EleBottomLoad` 函数封装无限滚动逻辑：
> 1. 在页面底部添加"加载更多"提示区域
> 2. 监听 `scroll` 和 `resize` 事件
> 3. 在事件回调中判断底部元素是否进入可视区域（`isShow()` 方法）
> 4. 如果可见且不在请求队列中，延时 500ms 后触发加载
> 5. 加载完成后递增 `offset`，如果返回数据少于 `limit` 则标记为已全部加载

**步骤 4：实现可视区域判断**

> 自定义 `$.fn.isShow()` 方法，通过比较元素边界（`offset()`）与窗口可视区域（`scrollTop + height`）判断元素是否可见：
> ```javascript
> $.fn.isShow = function() {
>   if (this.css('display') === 'none') return false;
>   let viewport = { top: win.scrollTop(), ... };
>   let bounds = this.offset();
>   return !(viewport.right < bounds.left || ...);
> };
> ```

> **思考题**：为什么要在滚动事件处理中加入 `isInQueue` 锁和 500ms 延时？如果不加会有什么问题？

---

## 十一、后端 API 自动化测试

### 11.1 实验目标

掌握使用 FastAPI 内置的 TestClient 对后端 API 进行自动化测试的方法，能够编写针对用户注册、用户登录、文件上传、帖子查询等接口的测试用例，理解测试中模拟认证 Token 的注入、请求参数的构造以及响应状态码与响应体断言的编写规范。

### 11.2 背景知识

FastAPI 内置的 `TestClient` 基于 `httpx` 库，它可以在不实际启动服务器的情况下模拟 HTTP 请求，对 FastAPI 应用进行测试。这使得测试执行速度极快，且可以在 CI/CD 流水线中方便地集成。

### 11.3 操作步骤

**步骤 1：安装测试依赖**

```bash
python -m pip install httpx pytest
```

> **提示**：安装 FastAPI 时通常会自动安装 httpx 依赖。

**步骤 2：创建测试文件**

> 新建 `test_webmain.py` 文件，导入测试所需的模块和 FastAPI 应用实例：
> 
> **关键 API**：`from fastapi.testclient import TestClient`
> 
> **提示**：需要将 `webmain.py` 中的 `app` 对象导入到测试文件中。由于 `webmain.py` 在 `if __name__ == '__main__'` 中才启动 uvicorn，导入时不会实际启动服务器。

**步骤 3：编写用户注册测试**

> **关键 API**：`client.post("/user/register", data={"username": "testuser", "password": "testpass"})`
> 
> **断言要点**：
> - 状态码应为 200
> - 返回 JSON 中 `result` 应为 `'success'`
> - 返回 JSON 中应包含 `bearer_token` 字段
> 
> **提示**：使用 `data=` 参数发送表单数据（与 OAuth2PasswordRequestForm 兼容）。

**步骤 4：编写用户登录测试**

> 使用注册时获取的凭据登录，验证返回的 Token 是否有效。
> 
> **边界测试**：
> - 用户名不存在时应返回 `{'result': 'username_unexist'}`
> - 密码错误时应返回 `{'result': 'password_wrong'}`

**步骤 5：编写认证保护的接口测试**

> **关键 API**：
> ```python
> response = client.post("/user/userinfo",
>     headers={"Authorization": "Bearer " + token})
> ```
> 
> **测试场景**：
> - 使用有效 Token 请求 `/user/userinfo`，验证返回正确用户信息
> - 使用无效 Token 请求，验证返回 401 或 `{'result': 'token_expired'}`
> - 不携带 Token 请求，验证返回 401

**步骤 6：编写文件上传测试**

> **关键 API**：
> ```python
> files = {"filePdf": ("test.pdf", open("test.pdf", "rb"), "application/pdf")}
> response = client.post("/user/uploadfile", files=files,
>     headers={"Authorization": "Bearer " + token})
> ```
> 
> **断言要点**：
> - 上传 PDF 文件应返回成功
> - 上传非 PDF 文件应返回错误

**步骤 7：编写帖子查询与操作测试**

> 测试 `/user/getposts` 和 `/user/setpost` 接口：
> - 查询帖子列表，验证返回数据格式
> - 收藏帖子，验证 `isfavor` 状态变化
> - 删除帖子，验证 `is_del` 标志更新
> - 测试分页功能（修改 `offset` 和 `limit` 参数）

**步骤 8：运行测试**

```bash
python -m pytest test_webmain.py -v
```

> **提示**：使用 `-v` 参数显示详细测试输出。

---

## 十二、前端功能测试

### 12.1 实验目标

掌握前端功能的测试方法，能够使用浏览器开发者工具对前端页面进行功能测试，验证用户注册登录流程、文件上传交互、帖子列表加载与无限滚动、收藏/删除操作等完整用户交互链路的正确性，理解前端调试的基本技巧与常见问题的排查思路。

### 12.2 操作步骤

**步骤 1：使用 Network 面板检查 AJAX 请求**

> 打开浏览器开发者工具（F12），切换到 Network 面板：
> 1. 触发用户登录操作，观察是否发出 POST 请求到 `/user/login`
> 2. 检查请求的 Form Data 中是否正确携带了 `username` 和 `password`
> 3. 查看响应状态码（应为 200）和响应体（应包含 `bearer_token`）
> 4. 触发帖子列表加载，观察 `/user/getposts` 请求的 Payload 和 Response
> 
> **提示**：勾选 "Preserve log" 可保留页面刷新前的请求记录。

**步骤 2：使用 Console 面板检查 JavaScript 执行**

> 1. 打开 Console 面板，检查页面加载时是否有 JavaScript 错误
> 2. 手动执行 `$.cookie('bearer_token')` 检查 Token 是否正确存储
> 3. 手动执行 `$.cookie('loginUserId')` 检查用户 ID 是否正确存储
> 4. 观察是否有 jQuery 相关的错误（如 `$ is not defined`，通常意味着 jQuery 未正确加载）

**步骤 3：验证用户注册登录流程**

> 测试步骤：
> 1. 点击导航栏"登陆或注册"按钮 → 模态框应弹出
> 2. 点击"切换为注册" → 标题和表单 action 应切换
> 3. 输入用户名和密码（均不少于5个字符），点击"确认" → 应提示成功并刷新页面
> 4. 刷新后导航栏应显示用户名，背景色应为蓝色
> 
> **异常场景测试**：
> - 用户名少于5个字符，验证后端返回错误提示
> - 重复注册相同用户名，验证返回"已存在"提示

**步骤 4：验证文件上传功能**

> 1. 点击"选择文件"按钮选择一个 PDF 文件
> 2. 点击"开始上传"按钮
> 3. 在 Network 面板中观察请求是否发送到 `/user/uploadfile`
> 4. 检查请求的 Content-Type 是否为 `multipart/form-data`
> 5. 验证响应中 `result` 是否为 `'success'`
> 6. 验证帖子列表中是否出现了新上传的 PDF

**步骤 5：验证帖子列表与无限滚动**

> 1. 页面加载后检查首页帖子列表是否正确渲染（标题、作者、日期、PDF 预览框）
> 2. 点击帖子上的"全屏"按钮，验证是否在新标签页打开 PDF
> 3. 点击"喜欢"按钮，验证按钮文字变为"已喜欢"
> 4. 向下滚动页面，验证到达底部时自动加载更多帖子
> 5. 当所有帖子加载完毕时，验证显示"这就是全部了"

**步骤 6：验证删除功能**

> 1. 使用管理员账号或帖子作者账号登录
> 2. 在自己发布的帖子中找到"删除"按钮
> 3. 点击删除，确认弹窗提示成功
> 4. 验证帖子从列表中移除
> 
> **权限测试**：使用非作者/非管理员账号登录，验证删除按钮不可见（`display:none`）。

> **思考题**：如何使用 Selenium 或 Playwright 等自动化测试工具将上述手动测试流程转化为自动化脚本？


