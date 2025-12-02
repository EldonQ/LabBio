# Local-IA 开发规范与架构设计文档

## 1. 项目概述
本项目旨在构建一个**本地化、双节点协同**的生物信息学智能分析平台。
- **Windows 节点 (Brain)**: 负责用户交互、逻辑编排、代码生成与知识检索。
- **Ubuntu 节点 (Muscle)**: 负责高性能计算任务执行（OBITools, QIIME2）。
- **通信机制**: 通过 HTTP API (FastAPI) 进行指令下发，通过 SMB 共享存储进行数据交换。

---

## 2. 项目目录结构设计

为了保证代码的可维护性与模块化，我们将采用以下目录结构。建议在 Windows 端建立此结构，并通过 Git 进行版本控制。

```text
e:\LabBio\
├── .gitignore                  # Git 忽略文件配置
├── README.md                   # 项目说明文档
├── requirements.txt            # Windows 端 Python 依赖
├── config.yaml                 # 全局配置文件 (路径映射、API地址等)
│
├── backend/                    # [Windows] 核心逻辑层
│   ├── __init__.py
│   ├── main.py                 # Windows 端主程序入口
│   ├── config.py               # 配置加载模块
│   │
│   ├── agents/                 # LangGraph 智能体定义
│   │   ├── __init__.py
│   │   ├── planner.py          # 规划智能体 (Planner)
│   │   ├── coder.py            # 编码智能体 (Coder)
│   │   ├── librarian.py        # 知识检索智能体 (Librarian)
│   │   └── state.py            # LangGraph 状态定义
│   │
│   ├── rag/                    # 知识库模块 (RAG)
│   │   ├── __init__.py
│   │   ├── ingest.py           # 文档切分与向量化脚本
│   │   ├── retriever.py        # 检索逻辑封装
│   │   └── vector_db/          # ChromaDB 本地存储目录 (自动生成)
│   │
│   └── utils/                  # 通用工具库
│       ├── __init__.py
│       ├── llm_client.py       # LLM API 客户端 (OpenAI/vLLM)
│       └── executor_client.py  # Ubuntu Executor API 客户端
│
├── frontend/                   # [Windows] 用户界面层
│   ├── app.py                  # Streamlit 启动入口
│   ├── components/             # UI 组件
│   │   ├── chat.py             # 聊天窗口组件
│   │   ├── sidebar.py          # 侧边栏组件
│   │   └── visualization.py    # 图表展示组件
│   └── assets/                 # 静态资源 (Logo, CSS)
│
├── executor/                   # [Ubuntu] 执行端代码 (需部署到 Ubuntu)
│   ├── server.py               # FastAPI 服务端
│   ├── start_executor.sh       # Ubuntu 启动脚本
│   ├── requirements.txt        # Ubuntu 端依赖
│   └── deploy.py               # 自动部署脚本 (Windows -> Ubuntu)
│
└── Documents/                  # 项目文档与知识库源文件
    ├── IntelligentArchitecture.md
    ├── DevelopmentSpecification.md
    ├── protocols/              # 原始协议文档 (Word/PDF)
    │   ├── OBITools3.docx
    │   └── QIIME2.doc
    └── logs/                   # 运行日志
```

---

## 3. 开发规范

### 3.1 命名规范
- **Python 文件**: `snake_case.py` (如 `llm_client.py`)
- **类名**: `PascalCase` (如 `PlannerAgent`)
- **变量/函数**: `snake_case` (如 `run_analysis`, `user_input`)
- **常量**: `UPPER_CASE` (如 `EXECUTOR_API_URL`)

### 3.2 路径处理 (关键)
由于涉及 Windows 和 Linux 跨平台协作，路径处理必须严格遵循以下规则：
- **配置文件化**: 所有绝对路径（如 `/media/dell/eDNA3` 或 `F:\LabData`）**严禁硬编码**在代码中，必须提取到 `config.yaml`。
- **路径转换**: Windows 端生成的 Shell 脚本必须使用 **Linux 绝对路径**。
    - *错误*: `obi import F:\LabData\data\file.fastq ...`
    - *正确*: `obi import /media/dell/eDNA3/data/file.fastq ...`
- **使用 `pathlib`**: 在 Python 代码中尽量使用 `pathlib.Path` 处理路径。

### 3.3 异常处理
- **Executor 通信**: 调用 Ubuntu API 时必须设置超时 (Timeout) 和重试机制。
- **Shell 执行**: 检查 `return_code`，非 0 即视为失败，必须捕获 `stderr` 并反馈给 Agent 进行自我修正。

---

## 4. 模块详细设计

### 4.1 核心配置 (`config.yaml`)
```yaml
system:
  mode: "dev" # dev (local windows executor) or prod (remote ubuntu)

llm:
  api_base: "http://localhost:8080/v1" # vLLM 地址
  model_name: "Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int4"
  api_key: "EMPTY"

executor:
  host: "10.24.22.176" # 或 localhost
  port: 8000
  remote_root: "/media/dell/eDNA3/Lab" # Ubuntu 上的根目录
  windows_mount: "F:/LabData"          # Windows 上的挂载点 (需确保该文件夹存在)

rag:
  persist_directory: "./backend/rag/vector_db"
  collection_name: "lab_protocols"
```

### 4.2 智能体编排 (LangGraph)
采用 **StateGraph** 架构：
1. **State**:
   ```python
   class AgentState(TypedDict):
       messages: List[BaseMessage]
       plan: List[str]
       current_step: int
       code_snippet: str
       execution_result: str
       error: Optional[str]
   ```
2. **Nodes**:
   - `planner_node`: 接收用户输入，生成/更新 Plan。
   - `librarian_node`: 根据当前 Step 检索 RAG，注入 Context。
   - `coder_node`: 生成 Bash/Python 脚本。
   - `executor_node`: 发送脚本到 Executor，等待结果。
   - `reviewer_node`: 检查结果，决定是 Proceed 还是 Retry。

### 4.3 知识库 (RAG)
- **Loader**: 使用 `UnstructuredWordDocumentLoader` 加载 `.docx`。
- **Splitter**: 自定义 Splitter，按**标题层级**切分，保证命令块的完整性。
- **Metadata**: 提取文档中的文件路径作为 Metadata，用于后续校验。

---

## 5. 接口定义 (API Specification)

### 5.1 Windows -> Executor (HTTP)

#### `POST /run`
执行 Shell 命令。
- **Request**:
  ```json
  {
    "script": "obi import ...",
    "cwd": "/media/dell/eDNA3/Lab/project_1",
    "env_name": "lab"
  }
  ```
- **Response**:
  ```json
  {
    "stdout": "Importing...",
    "stderr": "",
    "return_code": 0
  }
  ```

#### `GET /health`
健康检查。
- **Response**: `{"status": "ok", "node": "muscle"}`

---

## 6. 开发路线图 (Roadmap)

1.  **Phase 1: 基础设施 (当前)**
    - [x] Executor 服务部署 (Windows/Ubuntu)
    - [ ] 建立项目目录结构
    - [ ] 配置 `config.yaml`

2.  **Phase 2: 知识库构建**
    - [ ] 解析 OBITools3/QIIME2 文档
    - [ ] 建立 ChromaDB 索引

3.  **Phase 3: 智能体核心**
    - [ ] 实现 Planner & Coder
    - [ ] 跑通 "Hello World" 级生信任务

4.  **Phase 4: 前端集成**
    - [ ] Streamlit 界面开发
    - [ ] 联调测试
