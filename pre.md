# PDPTool — 个人发展规划工具 · 项目展示文档

> **软件体系结构与设计模式（BDT220）课程大作业**
>
> 面向大学生的一站式学业规划与职业发展管理平台，涵盖课程管理、GPA 计算、培养方案审计、简历生成、AI 智能辅导与编程刷题等全链路功能。

---

## 目录

1. [项目概述](#1-项目概述)
2. [架构设计](#2-架构设计)
3. [设计模式应用](#3-设计模式应用)
4. [详细设计](#4-详细设计)
5. [系统实现与运行效果](#5-系统实现与运行效果)
6. [基础功能](#6-基础功能)
7. [创新拓展功能](#7-创新拓展功能)
8. [具体使用价值](#8-具体使用价值)
9. [项目过程管理规范](#9-项目过程管理规范)
10. [总结与展望](#10-总结与展望)

---

## 1. 项目概述

### 1.1 背景与痛点

大学四年，学生面临如下碎片化困境：

| 痛点 | 现状 | PDPTool 方案 |
|------|------|-------------|
| 成绩分散 | 教务系统导出不便，历史学期成绩没有总体视角 | 一键导入 CSV，自动计算 GPA 趋势 |
| 培养方案复杂 | PDF 版培养方案晦涩难读，不知道自己"还差什么" | 智能审计 13 类课程模块，可视化完成度 |
| 简历难产 | 经历零零散散，写简历时无从下手 | 结构化数据 → 一键生成 HTML/Markdown 简历 |
| 缺乏个性化指导 | 导师资源有限，AI 工具缺少个体数据 | 接入学生全量数据 + 培养方案知识库的 AI 顾问 |
| 刷题无反馈 | 刷 LeetCode 没人审代码、给提示 | 内建编程练习 + AI 代码评审/渐进提示 |

### 1.2 项目定位

PDPTool 定位为 **"大学生个人发展操作系统"** — 以学业数据为中心，打通课程 → GPA → 培养方案 → 经历 → 简历 → 实习投递 → 技能提升的完整链路。

### 1.3 技术栈

| 层 | 技术选型 | 理由 |
|----|---------|------|
| GUI | **PySide6** (Qt for Python) | 跨平台原生桌面体验，信号/槽天然适配 Observer 模式 |
| 数据库 | **SQLite** | 零配置、单文件部署、适合本地桌面应用 |
| AI 引擎 | **DeepSeek API** (OpenAI 兼容) | 国产大模型，中文能力强，性价比高 |
| 编程语言 | **Python 3.10+** | 课程要求 + 生态丰富 |
| 打包分发 | **PyInstaller** | 一键打包为独立 EXE |

---

## 2. 架构设计

### 2.1 分层架构总览

```
┌──────────────────────────────────────────────────┐
│                   Views 层                         │
│  MainWindow · DashboardView · CourseView · ...    │
│  + widgets/ (RecordTable, SearchBar)              │
│  职责：UI 渲染、用户交互、信号发射                    │
├──────────────────────────────────────────────────┤
│                  Services 层                        │
│  GpaCalculator · DataIO · ResumeExporter          │
│  CurriculumAuditor · InsightAnalyzer              │
│  AIAssistant · CodingTutor · ResumeTutor          │
│  职责：业务逻辑、算法计算、AI 调用                    │
├──────────────────────────────────────────────────┤
│                  Models 层                          │
│  Course · Experience · Achievement · Role          │
│  Student · InternshipApplication · RecordFactory   │
│  职责：数据结构定义、序列化/反序列化                   │
├──────────────────────────────────────────────────┤
│                Database 层                          │
│  DatabaseConnection (Singleton) · Migrations       │
│  Repositories (CourseRepo · ExperienceRepo · ...)  │
│  职责：持久化、SQL 执行、数据迁移                     │
└──────────────────────────────────────────────────┘
```

**关键设计原则：**
- **依赖方向：** Views → Services → Repositories → Database，上层依赖下层，下层不感知上层
- **跨层通信：** Views 通过 Qt Signals 实现松耦合的跨组件数据同步
- **每层可独立测试：** Services 和 Repositories 不依赖 GUI 即可单元测试

### 2.2 模块依赖图

```
main.py
  └── MainWindow
        ├── DashboardView ──── CurriculumAuditor, InsightAnalyzer
        ├── CourseView ─────── CourseRepository, DataIO
        ├── ExperienceView ─── ExperienceRepository, DataIO
        ├── AchievementView ── AchievementRepository, DataIO
        ├── GpaView ────────── GpaCalculator (3 strategies)
        ├── ResumeView ─────── ResumeTutor (AI), HTML/Markdown 简历生成
        ├── InternshipView ─── InternshipApplicationRepository
        ├── SettingsView ───── StudentRepository
        ├── CodingPracticeView─ CodingTutor (AI)
        └── AiAssistantPanel ── DeepSeekAssistant
              └── CurriculumPlanStore + 全量学生数据
```

### 2.3 数据流架构

```
┌──────────┐   数据录入    ┌──────────┐   存储    ┌──────────┐
│  CSV/手动 │ ──────────→ │ Services │ ───────→ │  SQLite  │
│  导入     │             │ (校验/计算)│          │  pdptool.db │
└──────────┘             └──────────┘          └──────────┘
                               │                      │
                          data_changed              读取
                          Signal                    │
                               │                      │
                               ▼                      ▼
                        ┌──────────┐          ┌──────────┐
                        │Dashboard │          │ AI查询   │
                        │GPA · 简历│          │深度上下文 │
                        │自动刷新   │          │增强回答   │
                        └──────────┘          └──────────┘
```

---

## 3. 设计模式应用

本项目系统性地应用了 6 种设计模式（含 GoF 及企业级模式），每种模式解决具体的架构问题：

### 3.1 Singleton（单例模式）

| 项目 | 说明 |
|------|------|
| **位置** | `src/database/connection.py` — `DatabaseConnection` |
| **问题** | 桌面应用需要全局唯一的数据库连接，避免连接泄漏和锁竞争 |
| **实现** | 双重检查锁定（Double-Checked Locking）的线程安全单例 |
| **OCP 体现** | 数据库路径可参数化注入，测试时可 `reset_instance()` 隔离 |

```python
# 核心代码示意
class DatabaseConnection:
    _instance = None
    _lock = Lock()

    def __new__(cls, db_path=None):
        if cls._instance is None:
            with cls._lock:            # 线程安全
                if cls._instance is None:  # 双重检查
                    cls._instance = super().__new__(cls)
        return cls._instance
```

### 3.2 Repository（仓储模式）

| 项目 | 说明 |
|------|------|
| **位置** | `src/database/repositories/` — 7 个具体 Repository |
| **问题** | 业务逻辑层不应直接写 SQL，需要统一的数据访问抽象 |
| **实现** | `BaseRepository` 提供通用方法，各子类实现特定查询 |

```
BaseRepository (抽象基类)
  ├── CourseRepository       · get_all() · add() · import_batch()
  ├── ExperienceRepository   · get_all() · get_by_type()
  ├── AchievementRepository  · get_all() · add()
  ├── RoleRepository         · 同上
  ├── StudentRepository      · get() · save() (单记录 upsert)
  ├── InternshipApplicationRepository · status_summary()
  └── CurriculumPlanRepository · replace_chunks() · get_chunks()
```

### 3.3 Strategy（策略模式）

| 项目 | 说明 |
|------|------|
| **位置** | `src/services/gpa_calculator.py` |
| **问题** | GPA 有多种算法（标准 4.0、加权平均、算术平均），用户需要运行时切换 |
| **实现** | 抽象策略接口 `GpaStrategy` + 3 个具体策略 + Context 类 `GpaCalculator` |

```
GpaStrategy (ABC)                  ← 策略接口
  ├── Standard40Strategy           ← 标准 4.0 绩点制（90+→4.0, 85-89→3.7...）
  ├── WeightedAverageStrategy      ← 学分加权平均分（百分制）
  └── ArithmeticAverageStrategy    ← 算术平均分（不分学分权重）

GpaCalculator (Context)            ← 上下文：持有策略引用，委托计算
  · set_strategy()                 ← 运行时切换策略
  · calculate(courses) → {gpa, by_semester, ...}
```

**扩展性验证：** 新增一种 GPA 算法只需：① 继承 `GpaStrategy` 实现 3 个方法；② 添加到 `available_strategies()` 列表。无需修改 `GpaCalculator` 和其他任何代码 — 完全符合开闭原则。

### 3.4 Observer（观察者模式）

| 项目 | 说明 |
|------|------|
| **位置** | `src/views/main_window.py` — Qt Signals/Slots |
| **问题** | 用户在课程页增删数据后，仪表盘、GPA 页、简历页需要同步更新 |
| **实现** | 利用 PySide6 的 `Signal` 机制，Views 发射 `data_changed` 信号，监听者自动刷新 |

```
CourseView ──data_changed──→ DashboardView.refresh()
                           → GpaView.refresh()
                           → ResumeView.refresh()

ExperienceView ──data_changed──→ DashboardView.refresh()
                              → ResumeView.refresh()
```

### 3.5 Command（命令模式）

| 项目 | 说明 |
|------|------|
| **位置** | `src/views/ai_assistant_panel.py` — `AiWorker`；`src/services/coding_tutor.py` — `TutorWorker`；`src/services/resume_ai.py` — `ResumeWorker` |
| **问题** | AI 调用可能耗时 5–30 秒，绝不能阻塞主 UI 线程 |
| **实现** | 将每种 AI 请求封装为 `QThread` 子类对象，通过 `run()` 执行具体调用，`finished` Signal 将结果安全传回主线程 |

```
QThread                         ← Qt 线程基类
  ├── AiWorker                  ← 封装 AI 顾问对话请求
  ├── TutorWorker               ← 封装编程讲解/审查/提示/生成请求
  └── ResumeWorker              ← 封装简历 STAR 改写请求

所有 Worker 统一接口：
  · __init__(method, *args)     ← 指定调用方法及参数
  · run()                       ← 在子线程执行 AI 调用
  · finished = Signal(str)      ← 结果通过信号安全传回主线程
```

**扩展性验证：** 新增一种 AI 能力只需：① 编写对应的 Service 方法；② 创建新的 Worker 子类或复用 `TutorWorker` 的参数化调用。无需修改主窗口的信号连接逻辑。

### 3.6 Facade（外观模式）

| 项目 | 说明 |
|------|------|
| **位置** | `src/services/data_io.py` — `DataIO` |
| **问题** | 导入导出涉及多个 Repository、多种格式（CSV/JSON/粘贴文本）、列名映射，逻辑复杂 |
| **实现** | `DataIO` 对外暴露简洁的 `import_csv()`, `export_csv()`, `import_from_text()` 等方法 |

---

## 4. 详细设计

### 4.1 数据库设计

**数据库：** SQLite `pdptool.db`，共 8 张表

```sql
-- 核心业务表
student(id, name, student_no, college, major, enrollment_year,
        email, phone, github, linkedin, skills, summary)
courses(id, name, code, credit, semester, grade, category, note)
experiences(id, title, exp_type, organization, start_date, end_date, role,
            description, outcome)
achievements(id, title, ach_type, issuer, date, description)
roles(id, title, role_type, organization, start_date, end_date, description)
internship_applications(id, company, position, direction, apply_date,
                        deadline, status, link, note, resume_ready,
                        project_ready, reviewed)

-- 系统表
_schema_version(version)              -- 迁移版本追踪
curriculum_plan_chunks(id, source_file, major, cohort_year, module,
                       heading, content, created_at)  -- 培养方案知识库
```

**设计原则：**
- `student` 表设计为单记录模式（`get()` / `save()`），适合个人桌面应用
- `curriculum_plan_chunks` 按 source_file + major + cohort_year 切分，支持增量更新和 AI 检索
- 所有表使用自增整数主键，以简化 CRUD 操作
- 迁移系统支持版本化升级，从 v1 到 v3 可追溯

### 4.2 培养方案审计引擎

`CurriculumAuditor` 是核心算法模块，实现了一个 **双通道匹配引擎**：

```
                    ┌─────────────┐
                    │ 培养方案 .md  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        正则提取      模块解析     课程名提取
       (CODE_PATTERN) (通识/通修/专业) (regex + 关键词)
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │  双通道匹配   │
                    │ 代码优先 +    │
                    │ 名称回退      │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        13 类分类审计   计划外汇总    总学分计算
       (CategoryAudit) (未匹配课程)  (目标145学分)
```

**匹配策略：**
1. **代码匹配（高置信度）**：正则 `[A-Z]{2,4}\d{3}` 提取课程代码（如 BDT220），精确匹配
2. **名称匹配（中置信度）**：从培养方案提取课程名，模糊匹配学生成绩单中的课程名
3. **关键词回退（低置信度）**：对于政治/英语/体育等通识课，使用关键词规则辅助识别
4. **分类体系**：13 个仪表盘分类（政治理论 19 学分、英语 20 学分、体育 4 学分...）+ 计划外分类

### 4.3 AI 增强检索生成（RAG）架构

```
用户提问
    │
    ▼
┌─────────────────────┐
│  CurriculumPlanStore │  ← 培养方案知识库（结构化 chunks）
│  context_for_ai()    │    关键词排名检索 + 专业/年级过滤
└────────┬────────────┘
         │ 前 24 条最相关 chunks
         ▼
┌─────────────────────┐
│  DeepSeekAssistant   │
│  _build_student_     │  ← 全量学生数据上下文
│  context()           │    （课程+GPA+经历+实习+荣誉+审计结果）
└────────┬────────────┘
         │ 完整上下文拼装
         ▼
┌─────────────────────┐
│  DeepSeek Chat API   │  ← temperature=0.4 保证一致性
│  System Prompt:      │     角色扮演：学长/学姐式顾问
│  领域路由 + 行为准则  │     禁止八股模板和话题强行拐弯
└────────┬────────────┘
         │
         ▼
    Markdown 格式回答（自定义渲染）
```

### 4.4 多线程设计

所有 AI 调用（可能耗时 5-30 秒）均通过 `QThread` 子类异步执行，避免阻塞 UI：

| Worker 类 | 对应 Service | 用途 |
|-----------|-------------|------|
| `AiWorker` | `DeepSeekAssistant` | AI 顾问对话 |
| `TutorWorker` | `CodingTutor` | 编程题讲解/代码审查/提示/生成 |
| `ResumeWorker` | `ResumeTutor` | STAR 法则简历改写 |

所有 Worker 通过 `finished = Signal(str)` 将结果安全传回主线程，构成了 **Command 模式**（见 3.5 节）。

---

## 5. 系统实现与运行效果

### 5.1 界面总览

系统采用 **9 页面导航 + AI 侧边滑出面板** 的布局：

```
┌──────────┬────────────────────────────────┬────────────┐
│          │                                │            │
│  导航栏   │        中央内容区              │  AI 面板    │
│ (220px)  │    (QStackedWidget)            │ (可滑出)   │
│          │                                │            │
│ ▣ 首页    │  9 个页面的切换显示             │  问答聊天   │
│ ⌨ 编程    │                                │  Markdown   │
│ 📚 课程   │                                │  渲染       │
│ 🔬 经历   │                                │            │
│ 🏢 实习   │                                │            │
│ 🏆 荣誉   │                                │            │
│ 📊 GPA   │                                │            │
│ 📄 简历   │                                │            │
│ ⚙ 设置   │                                │            │
│          │                                │            │
└──────────┴────────────────────────────────┴────────────┘
                    ┌──────────┐
                    │ AI 宠物   │  ← 浮动的 "雷電" 吉祥物
                    │ (悬浮窗)  │     点击/拖拽与 AI 面板交互
                    └──────────┘
```

### 5.2 视觉设计系统

采用 **暖纸色调** 设计语言，营造亲和、专注的学术工具氛围：

| 色彩角色 | 色值 | 用途 |
|----------|------|------|
| 主背景 | `#f7f5f0` | 全局窗口背景 |
| 卡片/表格背景 | `#fffdf8` | 内容卡片、表格底色 |
| 交替行色 | `#faf6ef` | 表格斑马纹 |
| 边框/分隔 | `#e0d5c8` / `#d9cfc1` | 卡片边框、输入框边框 |
| 强调文字 | `#3f4652` | 正文颜色 |
| 标题色 | `#424a55` | 分组框标题 |
| 选中态 | `#dfece7` | 表格行选中高亮 |
| Hover 态 | `#f1ece4` | 按钮悬停态 |

### 5.3 运行方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动应用
python main.py

# 3. 打包为独立 EXE（无需 Python 环境）
pyinstaller --onefile --windowed --name PDPTool main.py
```

### 5.4 智能化配置

支持两种方式配置 DeepSeek API Key：

1. **环境变量**（推荐）：`DEEPSEEK_API_KEY=sk-xxxx`
2. **配置文件**：`pdptool_config.json` — 通过应用内 AI 面板直接保存

同时支持自定义 API 端点：`DEEPSEEK_BASE_URL` 和 `DEEPSEEK_MODEL` 环境变量。

---

## 6. 基础功能

### 6.1 课程管理

| 功能 | 描述 |
|------|------|
| 手动录入 | 课程名、代码、学分、学期、成绩、类别、备注 — 完整 CRUD |
| CSV 导入 | 一键导入教务系统导出的成绩单 CSV，自动列名映射 |
| 粘贴导入 | 支持从教务系统直接粘贴文本，智能解析 |
| CSV 导出 | 将课程数据导出为 CSV 备份 |
| 搜索筛选 | 按课程名关键词搜索 + 学期/类别下拉筛选 |
| 批量操作 | `import_batch()` 接口支持批量写入 |

### 6.2 经历管理

| 功能 | 描述 |
|------|------|
| 多类型标签页 | 全部 / 科研项目 / 比赛 / 实习 / 其他 |
| 完整信息录入 | 标题、组织、起止时间、角色、成果描述 |
| 批量导入 | 支持按类型的 CSV 批量导入 |

### 6.3 荣誉/证书管理

| 功能 | 描述 |
|------|------|
| 荣誉/证书 CRUD | 标题、类型、颁发机构、日期、描述 |
| 类型筛选 | 按奖项 / 证书 / 其他分类查看 |

### 6.4 GPA 计算

| 功能 | 描述 |
|------|------|
| 三大指标卡片 | 绩点 (4.0) / 加权平均分 / 算术平均分 |
| 算法切换 | 运行时切换三种策略 |
| 学期趋势图 | 自定义 Qt 绘制的折线图，展示 8 个学期 GPA 变化 |
| 学期明细表 | 每学期的课程数、学分、各指标值 |

**GPA 算法说明：**

| 算法 | 说明 | 适用场景 |
|------|------|---------|
| 标准 4.0 绩点制 | 90+→4.0, 85-89→3.7, 82-84→3.3, ... | 国内高校通用 |
| 加权平均分 | 按学分加权计算百分制均分 | 保研/奖学金评定 |
| 算术平均分 | 不分学分权重的简单平均 | WES 认证等场景 |

### 6.5 简历导出

| 功能 | 描述 |
|------|------|
| 交互式内容选择 | 勾选要包含的课程、经历、荣誉 |
| HTML 预览 | 实时预览 HTML 格式简历 |
| Markdown 导出 | 生成 Markdown 源码，可直接用于技术博客 / GitHub |
| 多 section | 自动按类型分 section（项目/竞赛/实习/其他） |
| 个人信息嵌入 | 技能、联系方式、GitHub、个人简介 |

### 6.6 个人信息设置

单页表单管理学生档案：姓名、学号、学院、专业、入学年份、邮箱、电话、GitHub、LinkedIn、技能标签、个人简介。

---

## 7. 创新拓展功能

### 7.1 🤖 AI 智能顾问（DeepSeek 驱动）

**核心创新**：不是通用 AI 聊天，而是 **"带有学生全量数据上下文的专属顾问"**。

```
每次对话自动注入：
┌─────────────────────────────────────────┐
│ ► 培养方案知识库（按专业/年级过滤）       │
│ ► 全量课程成绩 + GPA                      │
│ ► 13 类培养方案审计结果 + 缺失学分        │
│ ► 全部经历摘要 + 荣誉列表                  │
│ ► 实习投递记录 + 状态                      │
│ ► 学生技能 + 个人简介                      │
└─────────────────────────────────────────┘
```

**领域路由设计（System Prompt 实现）：**
- **学分/培养方案** — 仅在用户问到时启用，逐模块对比
- **GPA/成绩分析** — 识别高低分课程类型特征，给出补弱建议
- **简历/经历优化** — STAR 法则建议、量化成果提示
- **实习投递** — 进度分析、截止日预警、优先级排序
- **技能提升/学习路径** — 发现技能盲区、推荐学习方向

**行为准则：** 问什么答什么、用数据说话、不编造、不用八股模板。

### 7.2 📝 AI 简历优化（STAR 法则改写）

- 选中经历 → AI 自动改写为 **Situation-Task-Action-Result** 格式
- 强调技术细节和量化成果（"性能提升 30%""处理 10 万条数据"）
- 批量改写：一次性处理所有经历
- 完整 Markdown 简历一键生成，含所有 section

### 7.3 ⌨️ 编程刷题练习 + AI 编程导师

**双栏布局：** 左侧题目描述 → 右侧代码编辑器

| 功能 | 描述 |
|------|------|
| 题库加载 | 内置 19 道 LeetCode 经典题（Array/Linked List/Tree/DP/Graph/Stack） |
| AI 题目讲解 | 分析关键点 → 比较 2-3 种解法 → 推荐思路 → 不直接给代码 |
| AI 代码审查 | 正确性分析 → 复杂度分析 → 代码风格 → 改进建议 → 1-10 分评分 |
| AI 渐进提示 | 从模糊到具体，逐步引导，不直接给答案 |
| AI 题目生成 | 按难度+主题自动生成对标 LeetCode 质量的新题 |
| 本地运行 | 代码编辑器 + AI 反馈，形成刷题闭环 |

### 7.4 📊 培养方案智能审计

- **代码优先 + 名称回退** 双通道课程匹配
- **13 类课程分类** 可视化仪表盘（政治理论、英语、体育、数学、经管、学科基础、专业方向等）
- **每类显示：** 已完成学分 / 要求学分 + 进度条 + 缺失课程列表
- **总学分追踪：** 目标 145 学分完成度实时计算
- **计划外课程自动归集：** 不影响完成度但保留记录
- 支持按入学年份加载不同的培养方案（2023/2024/2025 级）

### 7.5 📈 个人发展雷达图（InsightAnalyzer）

四维度发展评分：

| 维度 | 评分逻辑 | 满分 |
|------|---------|------|
| 课程积累 | 总学分 × 1.5 + GPA × 12 | 100 |
| 实践经历 | 经历数量 × 22 | 100 |
| 荣誉成果 | 荣誉数量 × 25 | 100 |
| 组织角色 | 角色数量 × 25 | 100 |

综合评分等级：发展均衡型 (≥80) / 稳步成长型 (≥60) / 待完善型 (≥40) / 起步记录型 (<40)

自动生成：**亮点**（highlights）、**风险**（risks）、**建议**（suggestions）三段式分析报告。

### 7.6 🏢 实习投递追踪

| 功能 | 描述 |
|------|------|
| 申请记录 CRUD | 公司、岗位、方向、申请日期、截止日期、状态、链接、备注 |
| 状态管理 | 待投递 → 已投递 → 笔试中 → 面试中 → 已录用 → 已拒绝 → 已过期 |
| 5 张概览卡片 | 总计 / 进行中 / 笔试面试 / 已录用 / 准备就绪状态 |
| 筛选过滤 | 按方向（算法/开发/数据/产品）+ 状态双重过滤 |
| 截止日提醒 | 可识别临近截止的投递项 |
| 准备材料标记 | 简历已准备 / 项目已准备 / 已复盘 — 投递前置 checklist |

### 7.7 🎨 浮动 AI 吉祥物

- 原创绘制的 "雷電 (Raiden)" 角色作为 AI 助手入口
- Qt 自定义 `QPaint` 组件 + 阴影/发光效果
- 悬浮在所有窗口之上，拖拽移动
- 点击与 AI 面板交互，hover 有过渡动画

---

## 8. 具体使用价值

### 8.1 对学生用户

| 使用场景 | 价值 |
|----------|------|
| **选课前** | 查看培养方案审计结果，明确"还差什么类别、还差多少学分" |
| **期末后** | 导入成绩，查看 GPA 趋势和学期对比 |
| **找实习/工作前** | 一键生成简历，AI 改写经历描述为 STAR 格式 |
| **刷题时** | 边做题边获得 AI 讲解/审查/提示，效率远超纯刷 LeetCode |
| **困惑时** | 问 AI 顾问 "我的技能组合应该补充什么？""GPA 低怎么在简历上优化？" |
| **保研/申请** | 导出完整 Markdown 简历，展示四年学习轨迹 |

### 8.2 对教学管理

- 作为 **"软件体系结构与设计模式"** 课程的教学案例，完整覆盖 6 种设计模式
- 分层架构可作为学生理解 **三层架构 + Repository 模式** 的参考实现
- AI 集成展示了 **RAG（检索增强生成）** 在桌面应用中的落地方式

### 8.3 技术亮点总结

1. **零外部 SDK 依赖的 AI 集成** — 纯 `urllib` 调用 DeepSeek API，轻量无污染
2. **自定义 Markdown 渲染器** — 不依赖 `markdown` 库，自主实现 Markdown→HTML 转换
3. **自定义 Qt 绘图** — GPA 趋势图用 `QPainter` 原生绘制，不依赖 `matplotlib`
4. **QThread 异步架构** — 所有 AI 调用不阻塞 UI
5. **版本化数据库迁移** — `_schema_version` 表 + 增量迁移函数

---

## 9. 项目过程管理规范

### 9.1 开发方法论

采用 **迭代增量开发** + **模式驱动设计**：

```
迭代 1：核心数据层
  └── 模型定义 + Singleton 连接 + Repository 模式 + 迁移系统

迭代 2：基础业务服务
  └── GPA 计算（Strategy）+ 数据导入导出（Facade）+ 简历生成（HTML/Markdown）

迭代 3：GUI 框架
  └── MainWindow + 侧边栏导航 + 9 页面骨架 + 通用组件（RecordTable/SearchBar）

迭代 4：核心页面实现
  └── 课程管理 + 经历管理 + 荣誉管理 + GPA 页面 + 设置

迭代 5：高级功能
  └── 仪表盘 + 培养方案审计 + 个人发展洞察 + 简历视图 + 实习追踪

迭代 6：AI 集成（创新功能）
  └── DeepSeek 顾问 + 编程导师 + STAR 简历优化 + 浮动吉祥物 + Command 模式异步线程

迭代 7：测试与打磨
  └── 6 个单元测试模块 + UI 样式精调 + README + 本文档
```

### 9.2 代码组织规范

```
命名规范：
  - 文件：小写+下划线（snake_case）   → gpa_calculator.py
  - 类名：大驼峰（PascalCase）        → GpaCalculator
  - 方法/变量：小写+下划线              → calculate_grade_overview()
  - 私有/静态：前缀下划线              → _build_highlights()
  - 常量：全大写                       → CODE_PATTERN, DASHBOARD_CATEGORIES

文件组织：
  - 每文件一个核心类 + 紧密相关的辅助函数
  - __init__.py 统一导出（部分模块）
  - 测试文件命名：test_<模块名>.py
```

### 9.3 测试规范

| 测试层级 | 工具 | 覆盖范围 |
|----------|------|---------|
| 单元测试 | pytest + assert | 模型序列化、GPA 算法、数据导入、洞察分析、培养方案审计、实习 CRUD |
| 隔离策略 | 临时 SQLite | 每个测试文件使用 `/tmp` 下的独立数据库 |

```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行单个测试文件
python tests/test_gpa.py
python tests/test_curriculum_auditor.py
```

**已覆盖的 6 个测试模块：**

| 测试文件 | 验证内容 |
|----------|---------|
| `test_models.py` | 模型创建/序列化、Factory 创建、绩点换算 |
| `test_gpa.py` | 3 种策略计算、空课程边界、策略切换、学期趋势 |
| `test_data_io.py` | CSV 导入导出、粘贴文本解析、多类型批量导入 |
| `test_insight_analyzer.py` | 空档案/完整档案的洞察生成 |
| `test_curriculum_auditor.py` | 方案加载、代码匹配、分类审计、名称回退 |
| `test_internship_applications.py` | CRUD、状态汇总、准备材料文本生成 |

### 9.4 版本控制与文档

| 管理项 | 方式 |
|--------|------|
| 数据库迁移 | `_schema_version` 表 + `migrations.py` 版本化迁移（v1→v3） |
| API 文档 | 每个模块文件头部 docstring 说明用途和设计模式 |
| 用户文档 | `README.md` — 快速开始、项目结构、设计模式表、功能清单 |
| 项目展示 | `pre.md`（本文档）— 架构设计、模式分析、实现细节 |

### 9.5 质量保障措施

1. **OCP 验证**：每个设计模式都可通过"添加新类型而不改旧代码"的扩展性验证
2. **边界测试覆盖**：空数据、单条数据、大量数据的边界条件均有测试
3. **线程安全**：Singleton 双重锁定、QThread 结果安全回传主线程
4. **错误处理**：AI 调用含超时+重试（`retries=2`, `timeout=90s`）、文件读取含异常兜底
5. **全局样式一致性**：`main.py` 中集中定义 QSS 样式表，所有组件统一视觉

---

## 10. 总结与展望

### 10.1 项目成果

PDPTool 从一个"课程管理 + GPA 计算"的基础工具，演化为覆盖 **学业规划 × 职业发展 × AI 辅导** 三大维度的一站式平台：

- **9 个功能页面**，覆盖从数据录入到智能决策的完整链路
- **6 种设计模式** 的系统性应用，架构可扩展、可测试
- **3 大 AI 能力**（顾问对话、简历优化、编程辅导），基于 RAG 的数据增强
- **6 个测试模块**，保障核心逻辑正确性
- **跨平台桌面应用**，可通过 PyInstaller 打包为独立 EXE

### 10.2 技术收获

| 维度 | 收获 |
|------|------|
| **架构层面** | 三层分离 + Repository 模式让业务逻辑与 UI 完全解耦 |
| **模式层面** | Strategy / Observer / Facade / Command 在实际业务中的落地经验 |
| **AI 集成** | RAG 在本地桌面应用的轻量化实现，无需向量数据库 |
| **Qt 开发** | 信号/槽、自定义绘制、多线程、样式表的实战应用 |

### 10.3 可扩展方向

- [ ] 数据云同步（接入 WebDAV / 对象存储）
- [ ] 多专业培养方案支持（当前支持大数据专业，可扩展更多专业）
- [ ] 更丰富的可视化（spider chart、heatmap）
- [ ] 社区分享功能（匿名经验、选课评价）
- [ ] 移动端适配（PySide6 支持 Android/iOS 部署）

---

> **PDPTool — 不止是工具，是大学四年的数字伙伴。**
>
> 从第一门课到第一份 Offer，让每一步成长都有迹可循。
