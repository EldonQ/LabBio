# 本地化实验室生物信息学智能架构升级研究报告
## 1. 执行摘要：从手动脚本到智能体编排的范式转变
在当前生物信息学研究领域，数据产出的爆炸式增长与分析流程的复杂性之间存在着日益显著的矛盾。传统的生物信息学分析模式，如实验室当前所采用的基于 OBITools3 1 和 QIIME2 1 的手动命令行操作，虽然在标准化流程下表现稳定，但在面对大规模样本批次处理、跨工具数据流转以及参数动态调优时，往往显得效率低下且容易出错。随着大语言模型（LLM）与智能体（Agent）技术的成熟，如 *PromptBio*  和 *DeepCOI* 所展示的，构建一个能够理解自然语言指令、自动规划路径、生成执行代码并具备自我纠错能力的智能分析平台已成为可能。

本报告旨在为实验室量身定制一套**纯本地化**、**双节点协同**的智能生物信息学架构。该架构严格基于实验室现有的硬件资源——一台拥有海量内存（256GB）的 Ubuntu 计算节点（“肌肉节点”）和一台配备顶级消费级显卡（RTX 4090）的 Windows 工作站（“大脑节点”）。通过局域网（LAN）内的 API 通信与文件共享协议，我们将这两台物理隔离但网络互通的设备整合成一个有机的整体，实现“Windows 端推理决策，Ubuntu 端高通量计算”的异构协同模式。

本方案的核心价值在于：

1. **API 方式与本地大模型方式**：可选择OpenAI 等云端 API，或利用 RTX 4090 本地部署量化版 30B/32B 参数级代码大模型。
2. **遗留资产的智能化重构**：不抛弃现有的 OBITools3 和 QIIME2 流程，而是通过 RAG（检索增强生成）技术，将实验室沉淀的丰富的文档协议转化为智能体的“长期记忆”，使其能够像资深实验员一样理解特定的命名规则（如 JC1、JC65）和参数阈值。
3. **面向未来的扩展性**：架构设计参考了模块化的 *PromptBio* 平台 1，预留了 DeepCOI等新工具的插件接口，使其不仅能完成当前的扩增子分析，更能平滑演进至未来的多组学整合分析。

## 2. 硬件资源拓扑与基础设施层设计
在构建分布式智能系统之前，必须对现有硬件资源进行极其精细的剖析。实验室的两台主力计算机在配置上具有极强的互补性，这种互补性决定了我们“存算分离、脑肌协作”的架构基调。

### 2.1 节点角色定义与资源深度分析
#### 2.1.1 智能推理节点（The Brain Node）：联想 P7 工作站

●    **操****作系统**：Windows 10/11

●    **核心算力**：NVIDIA GeForce RTX 4090 (24GB VRAM)

○    *分析*：这是本架构的“大脑”。24GB 显存是运行高性能本地大模型的黄金阈值。在 4-bit 量化（GPTQ/AWQ）技术下，它能够流畅运行 Qwen-2.5-Coder-32B 或 DeepSeek-Coder-33B 级别的模型（占用约 18-20GB 显存），剩余显存足以支撑 Embedding 模型和系统开销。

●    **存储资源**：2TB PCIe4.0 SSD + 7.28 TB HDD

○    *分析*：高速 SSD 用于部署向量数据库（ChromaDB）和 LLM 模型权重，保证检索和推理的低延迟；大容量 HDD 可作为 raw data 的冷备份存储。

●    **处理器与内存**：Xeon w7-3455 + 128GB RAM

○  *分析*：虽然 CPU 性能强劲，但在生信工具兼容性（Windows vs Linux）上存在天然劣势，因此它不负责运行 OBITools 或 QIIME2，而是专注于承载 Agent 编排逻辑、Web 前端服务和 Docker 容器。

#### 2.1.2 高性能执行节点（The Muscle Node）：Ubuntu 生信服务器

●    **操****作系统**：Ubuntu Linux

●    **核心算力**：Intel Core i9-10980XE (18核/36线程) + Quadro P2200

○    *分析*：这是本架构的“肌肉”。i9-10980XE 的高主频和多核心非常适合 OBITools3 这种 CPU 密集型的序列比对任务 1。Quadro P2200 显存较小（5GB），不适合跑大模型，但可用于 DeepCOI 1 的轻量级推理加速或单纯作为显示输出。

●    **关键资源**：257GB 内存

○  *分析*：这是最宝贵的资源。在处理大规模扩增子合并（如 OBI alignpairedend 1）或 QIIME2 的 DADA2 降噪 1 时，大内存能避免 I/O 交换瓶颈，显著提升批处理速度。

### 2.2 局域网互联与数据传输协议

根据现状，两台电脑“无法通过网线直连，但都在同一个局域网下”。这意味着网络带宽和延迟是潜在瓶颈。

#### 2.2.1 存储共享协议：SMB (Server Message Block)

为了让 Windows 端的智能体能够“看见” Ubuntu 端的文件结构（以便编写正确的路径代码），必须建立文件系统映射。

●    **配置策略**：在 Ubuntu 上配置 Samba 服务，将数据存储目录（如 /media/dell/eDNA）暴露为网络共享。

●    **Windows** **挂载**：将该共享映射为网络驱动器 F:\LabData。

●  **性能优化**：由于通过路由器转发，需在 Samba 配置中开启 socket options = TCP_NODELAY IPTOS_LOWDELAY 以减少延迟，并不传输大文件，仅传输目录树信息和日志文件（Log files）。

#### 2.2.2 指令通信协议：RESTful API (FastAPI)

不能依赖 SSH 的交互式 shell，因为智能体需要结构化的反馈（JSON）。

●    **设计**：在 Ubuntu 上部署一个轻量级的 FastAPI 服务，监听特定端口（如 8000）。

●    **机制**：Windows 发送包含 Shell 脚本的 JSON Payload -> Ubuntu 接收并异步执行 -> Ubuntu 返回 stdout/stderr 和 return_code。

## 3. 系统架构设计：本地化智能体编排框架 (Local-IA)

本架构参考 *PromptBio* 1 的多智能体协作模式，设计了一个基于 **LangGraph** 的状态机系统。该系统运行在 Windows 节点上，通过网络控制 Ubuntu 节点。

### 3.1 架构分层图解

| **层****级** | **模块名称**               | **部署位置**   | **技术栈**           | **功能描述**                                                 |
| ------------ | -------------------------- | -------------- | -------------------- | ------------------------------------------------------------ |
| **交互层**   | **Bio-Chat Dashboard**     | Windows        | Streamlit   | 用户输入自然语言指令，查看分析进度和可视化图表。             |
| **编排层**   | **Master Agent (Planner)** | Windows        | LangGraph + LLM      | 任务拆解、状态管理、错误路由。类似于 PromptBio 的 "PromptGenie" 1。 |
| **认知层**   | **Knowledge Base (RAG)**   | Windows        | ChromaDB + Embedding | 存储实验室的 Word 文档协议 1 和 DeepCOI 论文 1。             |
| **能力层**   | **Coder Agent**            | Windows        | Qwen-2.5-Coder       | 专职编写 Python/Bash 脚本，负责将抽象任务转化为具体的 OBITools/QIIME 命令。 |
| **通信层**   | **Exec-Bridge**            | Windows/Ubuntu | HTTP / JSON          | 跨系统的指令传递与状态同步。                                 |
| **执行层**   | **Tool Runner**            | Ubuntu         | FastAPI + Celery     | 在 Conda 环境中执行具体的生信工具（OBITools,  QIIME2, VSEARCH）。 |
| **数据层**   | **Shared Storage**         | Ubuntu (Host)  | Ext4 / NTFS          | 原始数据、中间文件、结果数据库。                             |

 
### 3.2 核心智能体 (Agents) 定义

#### 3.2.1 主管智能体 (Planner Agent)

●    **职****责**：作为系统的入口，它不写代码，只负责“思考”。它分析用户意图（例如“处理2023年11月的样本”），并将其转化为一系列步骤（1. 文件查找；2. 导入；3. 比对...）。

●  **决策逻辑**：基于 *ReAct* (Reasoning + Acting) 模式。如果用户提到“DeepCOI”，它会调度 DeepCOI 工具；如果用户提到“聚类”，它会调度 QIIME2 工具。

#### 3.2.2 文献专员 (Librarian Agent)

●    **职****责**：解决“领域知识幻觉”。通用的 LLM 不知道实验室具体的 obi grep 阈值是 score_norm > 0.7 1，也不知道 QIIME2 分类器的具体路径 /media/dell/eDNA3/... 1。

●    **实现**：基于 RAG 技术。当 Coder Agent 需要写代码时，先询问 Librarian：“OBITools 的过滤标准是什么？”，Librarian 从 ChromaDB 中检索 1 的片段并返回。


#### 3.2.3 首席架构师 (Coder Agent)

●    **职****责**：这是 RTX 4090 发挥最大价值的地方。它接收 Planner 的任务和 Librarian 的上下文，生成精准的 Shell 脚本。

●  **特异性**：它必须知道 Ubuntu 上的环境名称（obi3 或 qiime2-amplicon-2024.10），并在脚本头部加入 source activate 指令。

#### 3.2.4 现场技术员 (Executor Agent)

●    **职****责**：运行在 Ubuntu 上的“手”。它是一个“听话”的执行器，接收脚本，运行，并捕获所有输出。它具备基本的“看守”能力，如果进程卡死（如 OBI alignpairedend 运行超过预设时间），它会杀掉进程并报错。

## 4. 详细开发文档与技术实现

本章节面向实际开发，详细列出每个模块的构建步骤。

### 4.1 模块一：Windows 端大模型推理服务 (The Brain)

为了满足“本地部署”且“高性能”的要求，我们选择 **vLLM** 作为推理后端，因为它专门优化了显存吞吐量。

●    **环境准备**：

○    在 Windows 上安装 WSL2 (Ubuntu 22.04 子系统)。这是运行 vLLM 的最佳方式，因为 Windows 原生支持尚不完善。

○    安装 CUDA Toolkit 12.1。

●    **模型选择**：

○    **Qwen-2.5-Coder-32B-Instruct-GPTQ-Int4**。

○    *理由*：通义千问 2.5 代码版在代码生成任务上表现优异，32B 参数量是 4090 (24GB) 能跑下的极限模型（约占用 18GB 显存），Int4 量化几乎不损失代码生成精度。

●    **启动命令 (WSL2)**：
 Bash
 python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int4 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 8192 \
  --port 8080
 
 *此时，本地 http://localhost:8080/v1 就成为了一个兼容 OpenAI 格式的 API 接口，后续所有 Agent 均调用此接口。*


### 4.2 模块二：知识库 RAG 构建 (The Memory)

实验室的两份文档 1 是系统的核心资产。我们需要将其结构化。

●    **数据清洗与分块 (Chunking)**：

○    OBITools3.docx 1：该文档包含大量的命令流。不能简单按字符切分。

○    *策略*：编写 Python 脚本，利用 docx 库，按“标题”进行语义切分。

■    Chunk A: #激活obitools 到 #准备map文件。

■    Chunk B: #导入数据 (包含具体的命名规则 JC1, JC2)。

■    Chunk C: #双向合并 (包含 obi alignpairedend 命令)。

○    *重点*：必须保留所有的文件路径和参数（如 score_norm > 0.7），因为这是实验室的“金标准”。

○    QIIME2.doc 1：包含复杂的 awk 命令和分类器路径。

■    *策略*：提取所有以 /media/dell/ 开头的绝对路径，建立一个专门的“路径字典”，防止模型幻觉编造路径。

●    **向量数据库 (ChromaDB)**：

○    部署在 Windows 本地。

○    Embedding 模型：使用 nomic-embed-text-v1.5 (轻量级，效果好，可跑在 CPU 上，不占用显存)。

○  *查询逻辑*：当用户问“如何做物种注释？”时，系统检索 1 中的 qiime feature-classifier 相关段落。

### 4.3 模块三：Ubuntu 执行端服务 (The Muscle)

在 Ubuntu 服务器上开发一个 Python 服务，作为 Windows 的“傀儡”。

●    **技术栈**：Python 3.9 + FastAPI + Uvicorn。

●    **核心代码逻辑 (agent_server.py)**：
 Python
 from fastapi import FastAPI, HTTPException
 from pydantic import BaseModel
 import subprocess
 import os
 
 app = FastAPI()
 
 class ShellCommand(BaseModel):
   script: str # 接收完整的 Bash 脚本
   cwd: str = "/home/bio/analysis" # 默认工作目录
   env_name: str = "base" # Conda 环境名
 
 @app.post("/run")
 async def run_command(cmd: ShellCommand):
   \# 1. 构建执行命令，确保加载 Conda 环境
   \# 注意：这里硬编码了 中提到的 miniconda 路径
   full_command = f"""
   source /BioAnalyse/miniconda3/etc/profile.d/conda.sh
   conda activate {cmd.env_name}
   {cmd.script}
   """
 
   \# 2. 异步执行 (使用 subprocess)
   try:
     process = subprocess.run(
       full_command,
       shell=True,
       executable="/bin/bash",
       capture_output=True,
       text=True,
       cwd=cmd.cwd
     )
     return {
       "stdout": process.stdout,
       "stderr": process.stderr,
       "return_code": process.returncode
     }
   except Exception as e:
     return {"error": str(e)}
 

●    **安全加固**：由于是在局域网内，建议通过防火墙（UFW）仅允许 Windows 机器的 IP 访问该端口（如 8000）。



## 5. 编排逻辑与业务流程实现

本节详细描述如何利用 **LangGraph** 将上述组件串联，实现 1 和 1 中复杂流程的自动化。

### 5.1 案例研究 A：OBITools3 批量处理的智能化

**挑****战**：在 1 中，用户需要手动输入几十行 obi import 命令，且文件名（如 GZ24053819...）与样本名（JC5）之间存在极其复杂的对应关系，极易出错。

**智能体工作流**：

1. **感知阶段 (DataAgent)**：

○    Windows 智能体通过 SMB 挂载（Z盘）扫描 Ubuntu 的原始数据目录。

○    它读取文件列表，利用 LLM 的正则能力分析文件名模式。

○    *Prompt*：“分析以下文件列表：GZ24053819-1F5-1F5_combined_R1.fastq.gz... 请推断出样本编号与文件名的映射关系。”

○    *LLM* *输出*：JC5 对应 GZ24053819...，JC6 对应 GZ24053820...。

2. **规划阶段 (Planner)**：

○    生成任务链：Import -> Align -> Stats -> Filter -> Export。

○    参考 1 的“双向合并(SLOW)”注释，智能体意识到这是一个耗时操作，决定采用异步非阻塞模式执行。

3. **编码阶段 (Coder)**：

○    Coder Agent 依据 RAG 检索到的 1 模板，生成一个**循环脚本**。

○    *生成的脚本示例*：
 Bash
 \# Auto-generated by Bio-Agent
 for i in {61..65}; do
   SAMPLE="JC${i}"
   \# 动态匹配文件名
   R1=$(find. -name "*${i}F*_R1.fastq.gz")
   R2=$(find. -name "*${i}F*_R2.fastq.gz")
 
   obi import $R1 $SAMPLE/r1
   obi import $R2 $SAMPLE/r2
   obi alignpairedend -R $SAMPLE/r1 $SAMPLE/r2 $SAMPLE/aligned
   \# 应用 中的硬性阈值
   obi grep -p "sequence['score_norm'] > 0.7" $SAMPLE/aligned $SAMPLE/good_aligned
 done
 

4. **执行与监控 (Executor)**：

○    脚本发送至 Ubuntu。

○  智能体轮询状态。一旦发现 stderr 中出现 "MemoryError"（虽然 256GB 内存很难溢出，但需防万一），自动建议分批处理。

### 5.2 案例研究 B：QIIME2 Manifest 文件的自动生成

**挑****战**：1中展示了一个非常复杂的 awk 命令来生成 manifest 文件。对于人类来说，理解并修改这个 awk 脚本以适应新数据是非常痛苦的。

**智能体解决方案**：

●    **不使用 awk**。Windows 智能体利用 Python 的 Pandas 库在本地处理。

●    **逻辑**：

1. DataAgent 扫描 Z 盘，获取所有 fastq 文件的绝对路径。
2. Coder Agent 编写 Python 代码，在内存中构建 manifest 表格（Sample-ID, Forward-Path, Reverse-Path）。
3. 将生成的 CSV/TSV 文件通过 API 推送到 Ubuntu 的临时目录。
4. 发送 qiime tools import 命令，指向该生成的 manifest 文件。

●    **优势**：利用 Python 的强逻辑性替代脆弱的 Shell 字符串处理，完美解决路径转义和匹配问题。

 

### 5.3 案例研究 C：DeepCOI 的集成 (Optional Tool)

根据 1，DeepCOI 是一个基于深度学习的分类器，用于解决 COI 基因分类难题。

●    **部署**：由于 DeepCOI 依赖 TensorFlow/PyTorch，且 Ubuntu 机器有 P2200 显卡，我们将其环境部署在 Ubuntu 的一个独立 Conda 环境 deepcoi_env 中。

●    **集成方式**：

○    当 QIIME2 的分类结果出现大量 "Unassigned" 时，Planner Agent 触发“深层诊断模式”。

○    Coder Agent 生成调用 DeepCOI 的命令：python deepcoi_classify.py --input unknown_seqs.fasta...。

○    Executor 在 Ubuntu 上运行该命令，利用 P2200 进行推理。

○    结果返回 Windows 进行汇总展示。

## 6. 前端交互页面设计 (Frontend)

为了让非编程背景的实验人员也能使用，我们需要一个直观的 Web 界面。**Streamlit** 是最佳选择，因为它是纯 Python 开发，开发周期极短。

**界面布局设计**：

1. **侧边栏 (Sidebar) - 环境配置**：

○    **连接状态**：显示 Windows Brain 和 Ubuntu Muscle 的心跳状态（绿灯/红灯）。

○    **资源监控**：实时显示 Ubuntu 的 CPU/内存占用率（通过 API 每5秒获取一次）。

○    **工作目录选择**：一个下拉菜单，列出 Z 盘（Ubuntu 共享）下的所有文件夹，供用户选择当前项目根目录。

2. **主聊天区 (Chat Interface)**：

○    **输入框**：“请帮我处理 2024 年 8 月的数据，使用 OBITools 流程。”

○    **消息流**：

■    用户消息。

■    *Agent* *思考过程（可折叠）*：显示 "正在检索...1", "正在匹配文件名...", "正在生成脚本..."。

■    *代码预览卡片*：显示生成的 Bash 脚本，带有“执行”和“修改”按钮。这意味着用户可以在执行前人工干预（Human-in-the-loop）。

■    *执行日志*：实时流式显示 Ubuntu 返回的 stdout。

3. **结果展示区 (Data Viz)**：

○    当流程结束后，Agent 会自动生成统计图表。例如，读取 1 流程生成的 JC_obi_results.tab，在 Windows 端用 Python 绘制物种丰度柱状图，并直接展示在网页上。

## 7. 详细技术栈与工具链清单

 

为了满足“项目开发周期”和“前期学习成本”的考量，我们精选了最主流、文档最全的工具。

| **模块**          | **推荐技术/工具**        | **选择理由**                                                 | **部署位置**                  |
| ----------------- | ------------------------ | ------------------------------------------------------------ | ----------------------------- |
| **LLM Server**    | **vLLM**                 | 当前最快的推理引擎，支持 PagedAttention，完美适配 4090。     | Windows (WSL2)                |
| **LLM Model**     | **Qwen-2.5-Coder-32B**   | 32B是单卡24G显存能跑的最强代码模型，中文支持极好。           | Windows                       |
| **Vector DB**     | **ChromaDB**             | 轻量级，本地文件存储，无需复杂的 Docker 部署。               | Windows                       |
| **Orchestration** | **LangGraph**            | LangChain 的升级版，支持循环图（Loop），非常适合需要“试错-重试”的生信任务。 | Windows                       |
| **Frontend**      | **Streamlit**            | 开发速度比 React 快 10 倍，适合内部工具。                    | Windows                       |
| **Backend**       | **FastAPI**              | 现代 Python Web 框架标准，性能高，自带文档。                 | Windows                       |                    |
| **Network**       | **Samba (SMB)**          | Windows/Linux 局域网文件共享的标准协议。                     | Ubuntu (Server), Win (Client) |


## 8. 开发者指南：面向 AI 辅助编程的提示词 (Prompts)

为了加速开发，建议使用 Cursor 或 Antigravity。以下是针对核心模块的 Prompt 设计，开发者可直接复制使用。

### 8.1 针对 Ubuntu 执行端 API 的开发提示词 (For Cursor)

Context: 你是一个资深的 Python 后端工程师。

Task: 请为我编写一个基于 FastAPI 的服务 executor.py。

Requirements:

1. 该服务运行在 Ubuntu 上，需要执行 Bash 命令。
2. 必须接受一个参数 env_name，用于在执行命令前激活 Conda 环境（路径硬编码为 /BioAnalyse/miniconda3/）。
3. 提供一个 POST 接口 /execute，接收 JSON 数据。
4. 使用 subprocess.run 执行命令，并捕获 stdout 和 stderr。
5. **安全**：限制只能执行特定目录下的操作，禁止 rm -rf / 等危险命令。
6. 添加一个 /files GET 接口，列出指定目录下的文件，以便远程查看。

### 8.2 针对 RAG 知识库构建的开发提示词

Context: 我有两个包含生物信息学协议的文档 OBITools3.docx 和 qiime2.doc。

Task: 编写一个 Python 脚本 ingest.py 来构建向量知识库。

Steps:

1. 使用 langchain_community.document_loaders 加载 docx。
2. 编写一个自定义的 Splitter，不要按字符长度切分，而是按“标题”切分（例如以 # 开头的行）。这很重要，因为每个命令块必须保持完整。
3. 对于 qiime2.doc，额外提取其中所有的文件路径（以 / 开头的字符串），并将其作为 metadata 存入。
4. 使用 Chroma 和 nomic-embed-text 将切分后的文档存入本地目录 ./chroma_db。

### 8.3 针对 LangGraph 编排逻辑的开发提示词

Context: 我们正在构建一个生信分析 Agent。

Task: 定义一个 LangGraph 的 StateGraph。

State Schema: 包含 messages (聊天记录), plan (当前步骤列表), current_step (索引), working_dir (当前目录)。

Nodes:

1. planner: 分析用户输入，生成步骤列表。
2. coder: 根据当前步骤和 RAG 检索结果，生成 Bash 代码。
3. executor: 调用远程 API 执行代码。
4. monitor: 检查执行结果。如果 return_code!= 0，跳转回 coder 进行修复；否则跳转回 planner 执行下一步。

 Edges: 定义上述跳转逻辑。请给出完整的 Python 代码框架。

## 9. 深度研究洞察与二阶思考

### 9.1 “路径依赖”与自动化悖论

在分析 1 和 1 时，我们发现实验室严重依赖**硬编码路径**（如 /media/dell/eDNA1/...）。这是自动化的大忌。

●    **洞察**：仅仅让 AI 学会这些路径是不够的，硬盘可能会换，挂载点可能会变。

●    **解决方案**：系统必须引入一个“配置抽象层”。在 Windows 端维护一个 config.yaml，将“Silva 数据库”映射到具体路径。Agent 只能读取这个配置，而不能将路径硬编码在 Prompt 中。这使得系统在未来更换存储设备时，无需重新训练或调整 Prompt。

### 9.2 “软硬件错配”的优化策略

Ubuntu 机器拥有惊人的 256GB 内存，但只有一张 P2200 显卡；Windows 机器显存强大但内存相对较小。

●    **洞察**：目前的 OBITools 流程 1 是单线程或基于文件的。它没有充分利用 256GB 内存。

●    **优化**：Agent 在生成 OBITools 脚本时，应主动建议使用 Ramdisk（内存盘）。

○    *策略*：Agent 生成代码，在 Ubuntu 上创建一个 100GB 的 tmpfs 挂载点 /mnt/ramdisk。

○  *效果*：将 FASTQ 文件拷贝到内存盘进行比对和排序。这将使 I/O 密集型的 OBI 流程速度提升 10 倍以上，充分榨干 i9 平台的内存优势，而这是传统手动操作很难习惯性去做的。

### 9.3 智能体的“自我意识”与边界

1 提到的 DeepCOI 是一个很好的补充，但必须设定边界。

●    **洞察**：AI 不应盲目使用 DeepCOI。

●    **策略**：在 RAG 中注入规则——“仅当 QIIME2 分类结果中 Unassigned 比例超过 20% 时，才建议用户使用 DeepCOI”。这避免了滥用算力，体现了“专家系统”的决策价值。

## 10. 结论与展望

本报告详细阐述了如何利用现有的异构硬件资源，通过引入 LLM 和 Agent 技术，将一个依赖手动文档的传统实验室改造为智能化的计算中心。