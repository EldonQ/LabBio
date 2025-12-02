# Local-IA: 本地化实验室生物信息学智能架构

## 项目概述

Local-IA 是一个基于大语言模型的智能生物信息学分析平台，旨在将传统的手动命令行工作流转变为自然语言驱动的智能系统。

### 核心特性
- 🧠 **智能任务规划**：自动将用户需求分解为可执行步骤
- 📚 **协议知识库**：基于 RAG 的实验室协议检索
- 💻 **代码自动生成**：生成符合实验室标准的 Bash 脚本
- 🖥️ **双节点协同**：Windows 推理 + Ubuntu 高性能计算
- 🔒 **数据隐私**：完全本地部署，无需云端 API

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows "Brain Node"                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Streamlit  │→ │ LangGraph    │→ │ RAG (Chroma) │       │
│  │  Frontend   │  │ Orchestrator │  │ Knowledge DB │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│         ↓                  ↓                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    (LAN Network)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Ubuntu "Muscle Node"                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI Executor                                    │   │
│  │  - OBITools3 (Conda: obi3)                           │   │
│  │  - QIIME2 (Conda: qiime2-amplicon-2024.10)           │   │
│  │  - DeepCOI (Conda: deepcoi_env)                      │   │
│  └──────────────────────────────────────────────────────┘   │
│         256GB RAM + i9-10980XE (18 cores)                   │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 一键启动（Windows）
```bash
# 启动后端 API
.\start_brain.bat

# 启动前端界面（新终端）
.\start_frontend.bat
```

### 2. 部署 Ubuntu Executor（首次）
```bash
conda activate lab
python executor\deploy.py
```

### 3. 在 Ubuntu 服务器上启动
```bash
cd /media/dell/eDNA3/Lab/executor
uvicorn server:app --host 0.0.0.0 --port 8080
```

详细说明请查看 [快速启动指南.md](快速启动指南.md)

## 项目结构

```
LabBio/
├── frontend/               # Streamlit 用户界面
│   └── app.py
├── backend/                # Brain Node (Windows)
│   ├── main.py            # FastAPI 入口
│   ├── agents.py          # LangGraph 多智能体
│   ├── ingest.py          # RAG 知识库构建
│   └── config.yaml        # 系统配置
├── executor/               # Muscle Node (Ubuntu)  
│   ├── server.py          # 命令执行服务
│   ├── deploy.py          # 自动部署脚本
│   └── start_executor.sh  # 启动脚本
└── Documents/             # 实验室协议文档（已忽略）
```

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **前端** | Streamlit | 纯 Python Web UI |
| **编排** | LangGraph | 多智能体工作流 |
| **知识库** | ChromaDB + HuggingFace Embeddings | 向量数据库 |
| **LLM** | OpenAI-compatible API | 支持 vLLM/Ollama |
| **后端** | FastAPI | 异步 Python Web 框架 |
| **执行** | Uvicorn + Conda | Ubuntu 命令执行 |

## 使用示例

在 Streamlit 界面输入：
```
请帮我处理 2024年8月的扩增子数据，使用 OBITools3 流程进行双向合并和过滤
```

系统将自动：
1. **规划**：分解为导入、合并、过滤等步骤
2. **检索**：从协议库提取 `obi alignpairedend` 参数
3. **生成**：创建完整的 Bash 脚本
4. **执行**：在 Ubuntu 上运行并返回结果

## 配置说明

编辑 `backend/config.yaml` 设置路径：

```yaml
muscle_node:
  host: "10.24.22.176"
  port: 8080

paths:
  ubuntu_lab_dir: "/media/dell/eDNA3/Lab"
  silva_database: "/media/dell/eDNA3/SILVA/silva-138-99-nb-classifier.qza"

conda:
  path: "/BioAnalyse/miniconda3"
  environments:
    obitools: "obi3"
    qiime2: "qiime2-amplicon-2024.10"
```

## 故障排除

### SSH 连接失败
- 确认 Ubuntu SSH 服务运行：`sudo systemctl start ssh`
- 检查防火墙：`sudo ufw allow 22`

### Brain Node 无法启动
- 检查端口 8000 是否被占用
- 确认 Conda 环境 `lab` 已激活

### 前端无法连接后端
- 确认 `backend/main.py` 正在运行
- 访问 `http://localhost:8000/health` 测试

## 下一步计划

- [ ] 集成本地 vLLM（Qwen-2.5-Coder-32B）
- [ ] 添加 DeepCOI 智能分类
- [ ] SMB 文件共享（挂载 Ubuntu 为 Z: 盘）
- [ ] 实时日志流式传输
- [ ] 多样本批处理优化

## 许可证

内部研究使用

## 联系方式

实验室内部项目 - 如有问题请联系系统管理员

---

**版本**: 1.0.0  
**最后更新**: 2025-11-30
