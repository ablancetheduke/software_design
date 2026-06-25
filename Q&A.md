# PDPTool — 期末答辩 Q&A 准备

> **课程：** 软件体系结构与设计模式（BDT220）
> **项目：** PDPTool — 个人发展规划工具
> **策略：** 每个回答都引用具体代码位置，用"做了什么 → 为什么这样做 → 带来了什么好处"三段式结构。

---

## 目录

1. [架构设计类](#1-架构设计类)
2. [设计模式类](#2-设计模式类)
3. [设计原则类](#3-设计原则类)
4. [数据库设计类](#4-数据库设计类)
5. [AI 集成类](#5-ai-集成类)
6. [实现细节类](#6-实现细节类)
7. [测试与质量类](#7-测试与质量类)
8. [扩展与展望类](#8-扩展与展望类)

---

## 1. 架构设计类

### Q1：你的项目采用了什么架构？为什么选择这种架构？

**答：** 采用了 **四层分层架构**：Views → Services → Repositories → Database。

**为什么：**
- 这是桌面应用中最成熟的架构模式，与课程讲授的三层架构一脉相承
- PySide6 的 Signal/Slot 机制天然适合 Views 层的松耦合通信
- SQLite 作为本地数据库，Repository 层可以完全隔离 SQL 细节

**怎么做的：**
- `main.py:17` — 入口只做 QApplication 创建 + 全局样式，然后交给 `MainWindow`
- `src/views/main_window.py:93` — `MainWindow.__init__()` 中调用 `init_database()`，但不直接操作数据库
- `src/services/data_io.py:21` — `DataIO` 持有多个 Repository 引用，业务逻辑只调用 Repository 方法
- `src/database/repositories/base_repo.py:5` — `BaseRepository` 封装 `DatabaseConnection` 单例的获取

**好处：**
- 每层可独立单元测试：Services 测试用临时 SQLite，不启动 GUI
- 替换数据库（如换成 PostgreSQL）只需改 Database 层
- 替换 GUI 框架（如换成 Web）只需重写 Views 层

---

### Q2：你的分层架构中，依赖方向是怎样的？为什么下层不能依赖上层？

**答：** 依赖方向严格遵循 **自上而下**：Views → Services → Repositories → Database。

具体体现：
- `src/views/course_view.py` import `DataIO` 和 `CourseRepository`，但不被它们 import
- `src/services/data_io.py` import `CourseRepository` 和各 Model 类，但不被 Repository import
- `src/database/repositories/course_repo.py` import `DatabaseConnection` 和 `Course` Model
- **没有任何下层模块 import 上层模块**

**为什么不能反过来：**
- 如果 Repository 依赖 View，换 GUI 框架时数据库层也要改 — 违反"高内聚低耦合"
- 如果 Service 依赖具体的 UI 控件，单元测试就必须启动 GUI
- 依赖倒置的唯一例外是抽象（接口/ABC），比如 `GpaStrategy` 是抽象，Service 依赖它、View 也通过它获取数据 — 这是合理的

---

### Q3：你的 Views 层有 9 个页面，它们之间怎么通信？为什么不直接互相调用？

**答：** 通过 **Qt Signals/Slots（观察者模式）** 实现跨页面通信，页面之间不直接互相调用。

核心代码在 `src/views/main_window.py:224-244`：

```python
def _connect_signals(self):
    course_view.data_changed.connect(gpa_view.refresh)
    course_view.data_changed.connect(dashboard_view.refresh)
    course_view.data_changed.connect(resume_view.refresh)
    experience_view.data_changed.connect(dashboard_view.refresh)
    experience_view.data_changed.connect(resume_view.refresh)
    ...
```

**为什么不直接调用：**
- 如果 `CourseView` 直接调用 `GpaView.refresh()`，两者就强耦合了
- 新增一个需要监听数据变化的页面时，只需在 `_connect_signals()` 中加一行 `connect`，不需要改 `CourseView` 的任何代码 — **符合开闭原则**
- 信号发射者不知道自己被谁监听，监听者不知道信号来自哪里 — 双向解耦

---

### Q4：你的模块依赖图中有哪些关键模块？它们各负责什么？

**答：** 按分层列举核心模块：

| 层 | 关键模块 | 职责 |
|----|---------|------|
| Views | `MainWindow` ([main_window.py:90](src/views/main_window.py#L90)) | 侧边栏导航、AI 面板动画、宠物定位、信号总线 |
| Views | `DashboardView` | 聚合展示：审计结果 + 个人洞察 + GPA 概览 + 实习状态 |
| Views | `CodingPracticeView` | 编程刷题双栏布局：题目 + 代码编辑器 + AI 交互 |
| Services | `GpaCalculator` ([gpa_calculator.py:96](src/services/gpa_calculator.py#L96)) | 策略上下文，运行时切换 3 种 GPA 算法 |
| Services | `CurriculumAuditor` ([curriculum_auditor.py:88](src/services/curriculum_auditor.py#L88)) | 双通道匹配引擎：代码优先 + 名称回退 |
| Services | `DataIO` ([data_io.py:21](src/services/data_io.py#L21)) | 外观模式：CSV/JSON/粘贴文本的导入导出统一入口 |
| Services | `DeepSeekAssistant` ([ai_assistant.py:103](src/services/ai_assistant.py#L103)) | RAG 增强的 AI 顾问，注入全量学生数据上下文 |
| Database | `DatabaseConnection` ([connection.py:11](src/database/connection.py#L11)) | 线程安全的单例数据库连接 |
| Database | `Migration` ([migrations.py:8](src/database/migrations.py#L8)) | 版本化数据库迁移（v1→v3） |

---

## 2. 设计模式类

### Q5：你用了哪些设计模式？各自解决了什么问题？

**答：** 系统性地应用了 **6 种设计模式**（5 种 GoF + 1 种企业级）：

| 模式 | 代码位置 | 解决的核心问题 |
|------|---------|--------------|
| **Singleton** | [connection.py:11](src/database/connection.py#L11) `DatabaseConnection` | 全局唯一的数据库连接，避免连接泄漏和锁竞争 |
| **Repository** | [repositories/](src/database/repositories/) 7 个具体 repo | 隔离 SQL 细节，业务层不写 SQL |
| **Strategy** | [gpa_calculator.py:13](src/services/gpa_calculator.py#L13) `GpaStrategy` + 3 子类 | GPA 算法运行时切换（4.0 绩点 / 加权 / 算术） |
| **Observer** | [main_window.py:224](src/views/main_window.py#L224) Qt Signals | 跨页面数据同步，页面间不直接耦合 |
| **Command** | [coding_tutor.py:170](src/services/coding_tutor.py#L170) `TutorWorker` / [resume_ai.py:93](src/services/resume_ai.py#L93) `ResumeWorker` / [ai_assistant_panel.py:26](src/views/ai_assistant_panel.py#L26) `AiWorker` | AI 调用异步化，封装请求为 QThread 命令 |
| **Facade** | [data_io.py:21](src/services/data_io.py#L21) `DataIO` | 统一导入导出入口，隐藏多 Repository + 多格式的复杂性 |

---

### Q6：Singleton 模式你是怎么实现的？线程安全吗？

**答：** 采用 **双重检查锁定（Double-Checked Locking）**，线程安全。

`src/database/connection.py:11-51`：

```python
class DatabaseConnection:
    _instance = None
    _lock = Lock()

    def __new__(cls, db_path=None):
        if cls._instance is None:          # 第一次检查（无锁，快速路径）
            with cls._lock:                # 加锁
                if cls._instance is None:  # 第二次检查（锁内，安全）
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**设计要点：**
- **第一次检查**：大多数调用（实例已存在时）不需要加锁，性能友好
- **第二次检查**：防止多个线程同时通过第一次检查后重复创建实例
- `reset_instance()` 用于测试隔离 — 每个测试文件用临时 SQLite 路径
- `check_same_thread=False` 允许跨线程查询（Qt 主线程 + AI Worker 线程）

**常见的追问：为什么不用模块级别的全局变量？**
- 模块全局变量无法延迟初始化（数据库路径需要在运行时确定）
- 无法做 `reset_instance()` 进行测试隔离
- 不符合"单例作为类职责"的封装原则

---

### Q7：Strategy 模式你是怎么用的？如果要加一种新的 GPA 算法（比如 5.0 绩点制），需要改哪些代码？

**答：** 策略模式的核心是 **"封装变化点，让算法可以独立于使用它的客户端而变化"**。

当前实现（[gpa_calculator.py](src/services/gpa_calculator.py)）：

```
GpaStrategy (ABC)                  ← 抽象策略接口
  ├── Standard40Strategy           ← 4.0 绩点制
  ├── WeightedAverageStrategy      ← 加权平均分
  └── ArithmeticAverageStrategy    ← 算术平均分

GpaCalculator (Context)            ← 持有策略引用
  · set_strategy()                 ← 运行时切换
  · calculate(courses)             ← 委托策略计算
```

**要加 5.0 绩点制，只需 2 步，0 处修改现有代码：**

1. 新增一个类：
```python
class Standard50Strategy(GpaStrategy):
    def name(self): return "标准5.0绩点制"
    def description(self): return "90-100→5.0, 85-89→4.5, ..."
    def grade_to_point(self, grade): ...
```

2. 在 `available_strategies()` 列表中添加一行：
```python
return [Standard40Strategy(), WeightedAverageStrategy(),
        ArithmeticAverageStrategy(), Standard50Strategy()]
```

**不需要修改：**
- `GpaCalculator.calculate()` — 它只依赖 `GpaStrategy` 抽象接口
- 任何 View 层代码 — GPA 页面通过 `available_strategies()` 动态获取可选算法列表
- 任何测试 — 已有的策略测试不受影响

这就是 **开闭原则（OCP）** 的典型体现：对扩展开放，对修改封闭。

---

### Q8：Observer 模式你是基于什么实现的？为什么不自己写观察者？

**答：** 基于 **PySide6/Qt 的 Signal/Slot 机制**，而不是自己实现 `addObserver` / `notifyAll`。

**为什么用 Qt 的而不是自己写：**
1. **线程安全**：Qt 的 `Signal` 自动处理跨线程调度（`QueuedConnection`），AI Worker 在子线程 emit 信号，UI 在主线程安全接收
2. **松耦合**：发射者不需要知道谁在监听，监听者不需要知道信号来源 — 一个 `data_changed` 信号，多个页面各自 connect
3. **代码量**：一行 `course_view.data_changed.connect(gpa_view.refresh)` 等价于自己写一个完整的 Observer 注册/通知机制
4. **与框架一致**：在 Qt 应用中用原生机制是惯例，强行自己写反而增加理解成本

**体现了观察者模式的核心思想：**
- Subject（被观察者）：`CourseView`、`ExperienceView` 等 — 发射 `data_changed` 信号
- Observer（观察者）：`DashboardView`、`GpaView`、`ResumeView` — 收到信号后调用 `refresh()`
- 一对多依赖：一个数据变更自动通知多个订阅者

---

### Q9：Command 模式在你的项目中是如何体现的？为什么不直接用线程？

**答：** 3 个 Worker 类将 AI 请求封装为命令对象：

| Worker | 封装的请求 | 代码位置 |
|--------|----------|---------|
| `AiWorker` | AI 顾问对话 | [ai_assistant_panel.py:26](src/views/ai_assistant_panel.py#L26) |
| `TutorWorker` | 编程讲解/审查/提示/出题 | [coding_tutor.py:170](src/services/coding_tutor.py#L170) |
| `ResumeWorker` | STAR 法则简历改写 | [resume_ai.py:93](src/services/resume_ai.py#L93) |

**Command 模式的体现：**
- **命令封装**：每个 Worker 封装了"调用哪个 Service 的哪个方法 + 传什么参数"
- **命令执行**：`run()` 方法在子线程执行 AI 调用
- **结果回传**：`finished = Signal(str)` 将结果安全传回主线程
- **调用者与执行者解耦**：View 层只需要 `worker.start()`，不关心 AI 调用细节

**为什么不直接用 `threading.Thread`：**
- QThread 与 Qt 事件循环集成 — `finished` 信号自动在正确的线程执行槽函数
- 手动 `threading.Thread` + `Queue` 需要在主线程轮询结果，代码更复杂
- QThread 生命周期管理更安全 — 窗口关闭时自动清理

---

### Q10：Facade 模式在你的 DataIO 中具体隐藏了什么复杂性？

**答：** `DataIO`（[data_io.py:21](src/services/data_io.py#L21)）对外暴露 8 个简洁方法：

```python
class DataIO:
    import_courses_csv(filepath)       # CSV 导入课程
    import_courses_text(text)          # 粘贴文本导入课程
    import_experiences_csv(filepath)   # CSV 导入经历
    import_experiences_text(text)      # 粘贴文本导入经历
    import_achievements_csv(filepath)  # CSV 导入荣誉
    import_achievements_text(text)     # 粘贴文本导入荣誉
    export_all_json(filepath)          # JSON 全量导出备份
    export_courses_csv(filepath)       # CSV 导出课程
```

**隐藏的复杂性：**
1. **4 个 Repository**：`CourseRepository`、`ExperienceRepository`、`AchievementRepository`、`RoleRepository`
2. **3 种输入格式**：CSV 文件、粘贴文本（Tab 分隔 / 逗号分隔 / 空格分隔）、JSON
3. **列名智能映射**：CSV 列名可能是"课程名"或"name"、"学分"或"credit" — `import_courses_csv()` 自动识别，代码在 [data_io.py:50-64](src/services/data_io.py#L50-L64)
4. **分隔符自动检测**：`_split_pasted_course_line()` 依次尝试 Tab → 逗号 → 空格分隔
5. **数据校验**：跳过空行、标题行、格式错误的行，返回 `{imported, skipped}` 计数

**如果不用 Facade：** View 层需要知道 4 个 Repository 的存在，需要自己处理列名映射、分隔符检测、数据校验 — 每个导入功能页面都有大量重复代码。

---

## 3. 设计原则类

### Q11：你的项目体现了哪些 SOLID 原则？举例说明。

**答：** 5 个原则都有体现：

| 原则 | 体现 | 代码证据 |
|------|------|---------|
| **S** 单一职责 | `Course` 只做数据模型（dataclass），`CourseRepository` 只做持久化，`DataIO` 只做导入导出 | [course.py:10](src/models/course.py#L10) vs [data_io.py:21](src/services/data_io.py#L21) |
| **O** 开闭原则 | 新增 GPA 算法不改 `GpaCalculator`；新增课程类别不改 `CurriculumAuditor` 的 `DASHBOARD_CATEGORIES` 列表 | [gpa_calculator.py:179-186](src/services/gpa_calculator.py#L179-L186) |
| **L** 里氏替换 | 任何 `GpaStrategy` 子类都可以替换 `GpaCalculator` 中的策略，`calculate()` 行为正确 — 每个子类的 `grade_to_point()` 都返回合法的浮点数 | [gpa_calculator.py:13-29](src/services/gpa_calculator.py#L13-L29) |
| **I** 接口隔离 | `GpaStrategy` 只有 3 个抽象方法（`name`、`description`、`grade_to_point`），没有强迫子类实现不需要的方法 | [gpa_calculator.py:13-29](src/services/gpa_calculator.py#L13-L29) |
| **D** 依赖倒置 | `GpaCalculator` 依赖抽象 `GpaStrategy` 而不是具体策略类；`BaseRepository` 子类依赖 `DatabaseConnection` 的抽象方法而非直接 `sqlite3.connect()` | [gpa_calculator.py:99-100](src/services/gpa_calculator.py#L99-L100) |

**最典型的 OCP 例子：** `DASHBOARD_CATEGORIES` 列表在 [curriculum_auditor.py:93-107](src/services/curriculum_auditor.py#L93-L107)。如果学校调整了某类课程的学分要求，只需修改列表中的一个数字 — 所有审计逻辑（`audit_dashboard_categories()`、`audit_total()`）自动适配。

---

### Q12：你提到 Repository 模式隔离了 SQL 细节，具体是怎么做的？

**答：** `BaseRepository` 提供统一的数据库访问基类（[base_repo.py](src/database/repositories/base_repo.py)）：

```python
class BaseRepository:
    def __init__(self, db=None):
        self.db = db or DatabaseConnection.get_instance()
```

7 个具体 Repository 继承它，每个只暴露业务语义的方法：

```python
# CourseRepository — 业务层调用
course_repo.get_all()                        # → List[Course]
course_repo.add(course)                      # → course_id
course_repo.import_batch(courses)            # → count
course_repo.get_by_semester("大一上")         # → List[Course]

# InternshipApplicationRepository
internship_repo.status_summary()             # → {total, in_progress, ...}
```

**隔离效果：**
- 业务层代码中 **零 SQL 字符串**（可以 grep 验证：`src/services/` 中没有 `SELECT`/`INSERT`）
- 换数据库时（如 SQLite → PostgreSQL），改 8 个 Repository 文件即可，Service 层 0 改动
- 测试时注入临时 SQLite 路径的 `DatabaseConnection`，测试之间完全隔离

---

### Q13：你的系统里有哪些地方体现了"高内聚、低耦合"？

**答：** 从三个层面举例：

**模块级内聚：**
- `curriculum_auditor.py`：所有培养方案解析、匹配、审计逻辑都在一个文件中（400 行），不分散到多个模块
- `markdown_renderer.py`：Markdown→HTML 转换完全自包含，0 外部依赖，可以在任何需要渲染的地方 `import`

**模块间耦合：**
- Views 之间 **零直接引用**：`CourseView` 不知道 `GpaView` 的存在，通过 Signal 通信
- Service 层 **不依赖 View**：`GpaCalculator.calculate()` 接受纯数据 `List[Course]`，不接触任何 Qt 类型
- Repository 层 **不依赖 Service**：只做数据存取，不包含业务逻辑

**可替换性验证：**
- 要换 AI 提供商（DeepSeek → OpenAI）：改 `ai_assistant.py` 和 `coding_tutor.py` 的 base_url + model，其他 0 改动
- 要换 GUI 框架（PySide6 → Web）：重写 `src/views/`，`src/services/` 和 `src/database/` 完全复用

---

## 4. 数据库设计类

### Q14：你的数据库有哪些表？为什么 student 表设计成单记录？

**答：** 共 **8 张表**，其中 6 张业务表 + 2 张系统表：

**业务表：**
`student`、`courses`、`experiences`、`achievements`、`roles`、`internship_applications`

**系统表：**
`_schema_version`（迁移版本追踪）、`curriculum_plan_chunks`（培养方案知识库）

**为什么 `student` 表设计成单记录模式：**
- 这是 **个人桌面应用**，一台电脑一个用户，不存在多用户场景
- 单记录模式简化 CRUD：`StudentRepository` 只有 `get()` 和 `save()` 两个方法，不需要 `WHERE id = ?`
- `init_database()` 在 [migrations.py:170-175](src/database/migrations.py#L170-L175) 自动创建默认学生记录（name="未设置"），确保应用启动即可用
- 如果后续需要多用户（比如实验室共享电脑），只需在 `student` 表加一个 `profile_name` 字段，改动范围可控

---

### Q15：数据库迁移系统是怎么设计的？如果新版本要加一张表怎么做？

**答：** 采用 **版本化增量迁移**，设计在 [migrations.py](src/database/migrations.py)：

```
_schema_version 表记录当前版本号
  └── Migration.run() 检查版本 → 依次执行未应用的迁移
        ├── _migrate_v1()   → 核心 5 张业务表
        ├── _migrate_v2()   → internship_applications 表
        └── _migrate_v3()   → curriculum_plan_chunks 表
```

**加一张新表的步骤（例如加 `notes` 表）：**

1. `VERSION` 改为 4
2. 新增 `_migrate_v4()` 方法：
```python
@staticmethod
def _migrate_v4(db):
    db.execute("""CREATE TABLE IF NOT EXISTS notes (...);""")
    db.execute("INSERT INTO _schema_version (version) VALUES (?)", (4,))
```
3. 在 `run()` 中加一行 `if current_version < 4: Migration._migrate_v4(db)`

**设计要点：**
- 每个迁移是幂等的（`CREATE TABLE IF NOT EXISTS`），重复执行不会出错
- 老用户升级时自动执行未应用的迁移，数据不丢失
- 新用户从头执行所有迁移，最终状态一致
- `curriculum_plan_chunks` 表有 `UNIQUE` 约束防止重复导入

---

### Q16：培养方案数据是怎么存和查的？为什么不用向量数据库？

**答：** 培养方案以 **结构化 chunks** 形式存在 SQLite 的 `curriculum_plan_chunks` 表中（[migrations.py:143-163](src/database/migrations.py#L143-L163)）。

**存储结构：**
```sql
curriculum_plan_chunks(
    major, cohort_year,        -- 专业 + 年级 → 支持多方案
    module, section_title,     -- 模块 + 子项标题
    required_credits,          -- 该子项要求的学分
    course_codes,              -- JSON 数组：匹配到的课程代码
    content,                   -- 原始文本
    chunk_order                -- 排序 → 保持原文结构
)
```

**查询流程（[curriculum_plan_store.py:95-118](src/services/curriculum_plan_store.py#L95-L118)）：**
1. 按 `major` + `cohort_year` 过滤 → 获取该学生对应培养方案
2. 关键词排名检索（纯 Python，无外部依赖）：
   - 对用户问题分词
   - 对每个 chunk 按 module + section_title + content + course_codes 加权计分
   - 排序后取 top-24
3. 拼接为文本上下文注入 AI prompt

**为什么不用向量数据库：**
- 培养方案只有几百个 chunk，关键词检索已经足够了
- 桌面应用不能要求用户装向量数据库（ChromaDB / Milvus 等）
- 零外部依赖 — 这个项目的一个重要设计原则（参考 [pre.md §8.3](pre.md#83-技术亮点总结)）
- 如果数据量增长到上万条，可以加一个 `sqlite-vec` 扩展，架构不需要大改

---

## 5. AI 集成类

### Q17：你的 AI 功能是怎么实现的？为什么选择 DeepSeek？

**答：** 通过 DeepSeek 的 OpenAI 兼容 API 实现，纯 `urllib` 调用，**零 SDK 依赖**。

核心代码在 [ai_assistant.py:103-157](src/services/ai_assistant.py#L103-L157)：

```python
class DeepSeekAssistant:
    def ask(self, question: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": 培养方案上下文 + 学生数据上下文 + 问题},
            ],
            "temperature": 0.4,
        }
        # 纯 urllib POST，无 openai SDK
        req = urllib.request.Request(f"{self.base_url}/chat/completions", ...)
```

**为什么选 DeepSeek：**
1. **中文能力强** — 培养方案、简历都是中文内容，DeepSeek 的中文理解优于多数模型
2. **性价比高** — 学生个人使用，API 价格极低
3. **OpenAI 兼容** — 如果换成 OpenAI / 通义千问 / 智谱，只需改 `base_url` + `model`
4. **课程契合** — 国产大模型在课程项目中是加分项

---

### Q18：你的 RAG（检索增强生成）是怎么做的？上下文包含哪些内容？

**答：** 每次 AI 对话自动注入 **两层上下文**，代码在 [ai_assistant.py:111-157](src/services/ai_assistant.py#L111-L157)：

**第一层：培养方案知识库（`_build_plan_context()`）**
- 根据学生专业 + 入学年份，从 `curriculum_plan_chunks` 表检索
- 用问题关键词排名，取 top-24 最相关的 chunks
- 每个 chunk 包含模块名 + 课程代码 + 学分要求 + 原文

**第二层：学生全量数据（`_build_student_context()`）**
```
► 个人信息：姓名、学院、专业、入学年份、技能标签、个人简介
► 课程数据：全部已修课程（名+代码+学分+成绩）、GPA（三指标）
► 培养方案审计：13 类完成度 + 总学分（145）进度 + 待补齐类别
► 经历摘要：竞赛/项目/实习/科研（类型+标题+角色+成果）
► 荣誉证书：类型+标题+日期
► 实习投递：公司+岗位+方向+状态+截止日期
```

**最终 Prompt 结构：**
```
System: 角色设定 + 领域路由规则 + 行为准则
User:
  【培养方案知识库】← 24 条 chunks
  【学生数据摘要】← 全量上下文
  【用户问题】    ← 用户输入
```

**为什么不用 LangChain / LlamaIndex：**
- 这个项目的 RAG 逻辑非常简单（关键词检索 + 文本拼接），引入框架是过度工程化
- 手工实现只有约 200 行代码，完全可控，调试方便
- 同样遵循"零外部 SDK 依赖"原则

---

### Q19：AI 调用怎么做到不阻塞 UI？如果 AI 请求失败怎么处理？

**答：** 三个层面解决：

**1. 异步执行（Command 模式 + QThread）**

3 个 Worker 类（[ai_assistant_panel.py:26](src/views/ai_assistant_panel.py#L26)、[coding_tutor.py:170](src/services/coding_tutor.py#L170)、[resume_ai.py:93](src/services/resume_ai.py#L93)）都继承 `QThread`：

```python
class AiWorker(QThread):
    finished = Signal(str)
    def run(self):
        self.finished.emit(DeepSeekAssistant().ask(self.question))
```

- `worker.start()` → 子线程执行 → `finished` 信号在主线程被接收 → UI 更新
- 用户可以在 AI 回答期间正常操作界面（滚动、切换页面等）

**2. 超时 + 重试机制（[coding_tutor.py:76-126](src/services/coding_tutor.py#L76-L126)）**

```python
def _call(self, ..., retries=2):
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp: ...
        except Exception:
            if attempt < retries:
                time.sleep(1.5)  # 重试前等待
```

- AI 顾问：timeout=25s，无重试（对话场景，快速失败 > 长时间等待）
- 编程导师：timeout=90s，retries=2（代码生成可能更耗时）

**3. 优雅降级**

- 无 API Key → 返回中文提示"请先配置 API Key"，不崩溃
- HTTP 错误 → 返回 `HTTP {code}\n{detail}`，用户可据此排查
- 网络超时 → 返回 `请求失败：{exc}`，不阻塞界面

---

### Q20：AI 编程导师支持哪些功能？题目从哪里来？

**答：** 4 个功能 + 2 种题目来源，实现在 [coding_tutor.py](src/services/coding_tutor.py)：

**4 个 AI 功能：**

| 功能 | 方法 | Temperature | 特点 |
|------|------|------------|------|
| 题目讲解 | `explain_problem()` | 0.4 | 分析关键点 → 比较 2-3 种解法 → 推荐思路，**不给代码** |
| 代码审查 | `review_code()` | 0.3 | 正确性 + 复杂度 + 风格 + 改进建议 + 1-10 分评分 |
| 渐进提示 | `give_hint()` | 0.5 | 从模糊到具体，只看学生已写代码，**不直接给答案** |
| 随机出题 | `generate_problem()` | 0.7 | 按难度+主题生成对标 LeetCode 质量的新题 |

**2 种题目来源：**
1. **内置题库**：`coding_problems/` 目录下的 `.md` 文件，覆盖 Array / Linked List / Tree / DP / Graph / Stack
2. **AI 生成**：`generate_problem(difficulty, topic)` — 可自定义难度和主题

**设计亮点：**
- 每个功能有独立的 System Prompt（[coding_tutor.py:14-61](src/services/coding_tutor.py#L14-L61)），精确控制 AI 行为
- 讲解不给代码、提示不给答案 — 这是刻意设计，避免学生直接抄答案
- Temperature 按场景精细调节：审查时 0.3（严谨），出题时 0.7（创意）

---

## 6. 实现细节类

### Q21：GPA 计算中，通过制（P/F）课程和"在修"课程怎么处理？

**答：** 有专门的过滤逻辑。

`Course` 模型在 [course.py:22-30](src/models/course.py#L22-L30) 定义了两种特殊状态：

```python
@property
def is_pass_fail(self) -> bool:
    return self.grade == 60 and PF_MARKER in (self.note or "")
    # 通过制课程：成绩存 60 + 备注含 [P/F]

@property
def is_in_progress(self) -> bool:
    return self.grade < 0
    # 在修课程：成绩存 -1
```

`GpaCalculator.calculate()`（[gpa_calculator.py:137-139](src/services/gpa_calculator.py#L137-L139)）计算 GPA 时跳过这两类：

```python
for course in courses:
    total_credits += course.credit         # 总学分计入（毕业要求）
    if course.is_in_progress or course.is_pass_fail:
        continue                           # 但不参与 GPA 计算
```

**设计原因：**
- 通过制课程只有"通过/不通过"，没有具体分数，强行折算为绩点会扭曲 GPA
- 在修课程还没有成绩，参与计算没有意义
- 但这两种课程的学分都计入总学分 — 因为它们确实满足了学分要求

---

### Q22：培养方案审计的"双通道匹配引擎"是什么？为什么需要名称回退？

**答：** 实现在 [curriculum_auditor.py:299-334](src/services/curriculum_auditor.py#L299-L334)。

**通道 1：课程代码匹配（高置信度）**
- 正则 `[A-Z]{2,4}\d{3}` 从培养方案提取课程代码（如 BDT220、MAT108）
- 与学生成绩单中的 `code` 字段精确匹配
- 置信度高 — 代码是一一对应的

**通道 2：课程名称匹配（中置信度）**
- 从培养方案的课程代码后面提取课程名（如 "MAT108高等数学"）
- 与学生成绩单中的 `name` 字段模糊匹配
- 处理教务系统导出数据中代码缺失或不一致的情况

**通道 3：关键词回退（低置信度，仅用于通识课）**
- 政治理论类：关键词 "马克思"、"毛泽东"、"思想道德"……
- 英语类：代码 `ENG` 前缀 或 关键词 "英语"、"英汉翻译"……
- 体育类：代码 `PED` 前缀 或 关键词 "体育"、"篮球"……
- 这些课程在不同学校的代码体系差异大，但课程名有共性

**为什么需要名称回退：**
- 不是所有教务系统都导出了课程代码字段
- 同一门课在不同学校有不同的代码（如"高等数学"可能是 MAT108 或 MATH1001）
- 培养方案来源文件可能没有列出所有课程的代码
- 回退机制让系统在数据不完整时仍能给出合理的审计结果

---

### Q23：自定义 Markdown 渲染器是怎么实现的？支持哪些语法？

**答：** 实现在 [markdown_renderer.py](src/utils/markdown_renderer.py)，约 110 行，**0 外部依赖**。

**处理流程（12 步管道）：**
1. HTML 转义（防注入）
2. 保护围栏代码块 → 占位符替换
3. 行内代码 `` `...` ``
4. 粗体 `**...**`
5. 斜体 `*...*`
6. 标题 `##` / `###` / `####`
7. 无序列表 `- ` / `* ` → `<ul><li>`
8. 有序列表 `1. ` → `<ol><li>`
9. 水平线 `---`
10. 引用 `> `
11. 换行符 → `<br>`
12. 恢复围栏代码块

**为什么不直接用 `markdown` 库：**
- 需要精确控制 HTML 输出的样式（内联 CSS 适配 QTextBrowser）
- 避免额外的依赖 — 110 行代码解决的问题不值得引入一个库
- QTextBrowser 只支持 HTML 子集，标准 Markdown 库的某些输出（如 `<table>`）不兼容

**关键技术点：**
- 围栏代码块使用占位符保护（`<!--PDP_MD_BLOCK_N-->`），防止被后续正则误伤
- 列表项通过 `_wrap_list_blocks()` 将连续匹配行合并为一个 `<ul>` 或 `<ol>`，而非每行一个

---

### Q24：你的 CSV 导入是怎么做列名映射的？支持哪些格式？

**答：** 列名映射实现在 [data_io.py:50-64](src/services/data_io.py#L50-L64)：

```python
for i, col_name in enumerate(header):
    col_name = col_name.strip()
    if "课程名" in col_name or "name" in col_name.lower():
        col_map["name"] = i
    elif "学分" in col_name or "credit" in col_name.lower():
        col_map["credit"] = i
    elif "成绩" in col_name or "grade" in col_name.lower() or "分数" in col_name:
        col_map["grade"] = i
    ...
```

**设计思路：**
- 使用 **关键词包含匹配** 而非精确匹配 — 兼容 "课程名称"、"课名"、"Course Name" 等多种表头写法
- 同时支持中文和英文列名 — 适配不同教务系统的导出格式
- 未识别的列被忽略 — 多余列不影响导入

**支持的导入格式（[data_io.py:91-149](src/services/data_io.py#L91-L149)）：**
1. **CSV 文件**：标准 CSV，自动检测 UTF-8-BOM 编码
2. **粘贴文本（Tab 分隔）**：从 Excel/WPS 直接复制粘贴
3. **粘贴文本（逗号分隔）**：中英文逗号都支持
4. **粘贴文本（空格分隔）**：通过正则 `\s+` 切分，最后回退方案

**容错设计：**
- 空行跳过
- 标题行（含"课程名"等关键词）自动识别并跳过
- 格式错误的行 → `skipped += 1`，不阻塞其他行的导入
- 返回 `{imported: N, skipped: M}` — 用户清楚知道导入结果

---

### Q25：浮动吉祥物是怎么实现的？为什么要有这个功能？

**答：** 实现在 [assistant_pet_widget.py](src/views/widgets/assistant_pet_widget.py) + [main_window.py:248-313](src/views/main_window.py#L248-L313)。

**技术实现：**
- `AssistantPetWidget`：继承 `QWidget`，使用 `Qt.WindowStaysOnTopHint` 悬浮在所有窗口之上
- 自定义 `paintEvent` 用 `QPainter` 绘制角色图像 + 阴影/发光效果
- 拖拽移动：重写 `mousePressEvent` / `mouseMoveEvent`
- Hover 动画：`hovered_changed` 信号 → `_animate_pet_x()` 用 `QVariantAnimation` 做平滑过渡

**三种定位模式（[main_window.py:266-296](src/views/main_window.py#L266-L296)）：**

| 模式 | 位置 | 触发条件 |
|------|------|---------|
| Peek（窥视） | 窗口右下角，只露出约 28% | 默认状态 |
| Visible（可见） | 窗口右下角，完全可见 | 鼠标悬停 |
| Panel（面板） | AI 面板左侧 | AI 面板打开时 |

**为什么要有这个功能：**
- 降低 AI 功能的使用门槛 — 比起在菜单栏找"AI 助手"按钮，点击一个可爱的浮动角色更直观
- 增加应用的亲和力 — 面向大学生的工具，活泼的交互比严肃的菜单更受欢迎
- 展示 Qt 自定义绘制能力 — 证明不依赖图片资源也能做复杂的 UI 效果
- 课程加分项 — 这个功能在同类学生项目中非常罕见，答辩时有记忆点

---

## 7. 测试与质量类

### Q26：你写了哪些测试？覆盖了哪些模块？怎么保证测试之间的隔离？

**答：** 6 个测试模块，覆盖核心业务逻辑，在 `tests/` 目录下：

| 测试文件 | 覆盖模块 | 验证内容 |
|---------|---------|---------|
| `test_models.py` | 数据模型 | 模型创建/序列化、`Course.to_dict()`/`from_dict()`、通过制判断、绩点换算 |
| `test_gpa.py` | GPA 计算 | 3 种策略独立验证、空课程边界、策略切换、学期趋势、通过制/在修过滤 |
| `test_data_io.py` | 数据导入导出 | CSV 导入导出、粘贴文本解析、多类型批量导入、JSON 全量备份 |
| `test_curriculum_auditor.py` | 培养方案审计 | 方案加载、代码匹配、分类审计、名称回退、总学分计算 |
| `test_insight_analyzer.py` | 个人发展洞察 | 空档案/完整档案的洞察生成、评分边界、亮点/风险/建议生成 |
| `test_internship_applications.py` | 实习投递 | CRUD 操作、状态汇总、准备材料文本生成 |

**隔离策略：**
- 每个测试文件使用 `DatabaseConnection.reset_instance()` 创建临时 SQLite 数据库
- 临时数据库路径使用 `/tmp` 或系统临时目录，测试结束后删除
- 测试之间不共享数据库实例，一个测试的数据不会污染另一个
- 不启动 GUI — 所有测试在命令行运行，不需要显示设备

**运行方式（[pre.md §9.3](pre.md#93-测试规范)）：**
```bash
python -m pytest tests/ -v          # 全部测试
python tests/test_gpa.py            # 单个测试文件
```

---

### Q27：你的代码组织有什么规范？为什么用 snake_case 文件名 + PascalCase 类名？

**答：** 规范定义在 [pre.md §9.2](pre.md#92-代码组织规范)：

| 元素 | 规范 | 示例 |
|------|------|------|
| 文件 | snake_case（小写+下划线） | `gpa_calculator.py` |
| 类名 | PascalCase（大驼峰） | `GpaCalculator` |
| 方法/变量 | snake_case | `calculate_grade_overview()` |
| 私有方法 | 前缀 `_` | `_build_highlights()` |
| 常量 | 全大写 | `CODE_PATTERN`, `DASHBOARD_CATEGORIES` |

**为什么：**
- 这遵循 PEP 8（Python 官方风格指南），是 Python 社区的事实标准
- 文件名与类名的对应关系一目了然：`gpa_calculator.py` → `GpaCalculator`
- 使用 PyCharm / VS Code 时，自动导入和重构功能与这个规范兼容最好
- 课程项目需要展示工程素养，编码规范是最基本的体现

**文件组织原则：**
- 每个文件一个核心类 + 紧密相关的辅助函数（如 `gpa_calculator.py` 除 `GpaCalculator` 还有 `calculate_grade_overview()`）
- `__init__.py` 中显式 `__all__` 声明公开 API
- 测试文件 `test_<模块名>.py` 与被测模块一一对应

---

### Q28：你是怎么保证代码质量的？除了测试还有什么措施？

**答：** 5 个层面的质量保障：

1. **测试覆盖**：6 个测试模块覆盖核心业务逻辑，包括边界条件（空数据、单条数据、大量数据）
2. **编码规范**：统一的命名规范 + 每文件一个核心类 + PEP 8 兼容
3. **文档注释**：每个模块文件头部有 docstring 说明用途和设计模式（如 `data_io.py` 头部注明 "外观模式"）
4. **OCP 自检**：每个声称使用了设计模式的地方，都可以通过"加新类型不改旧代码"来验证
5. **语法检查**：`python -m compileall -q src` 确保所有模块至少没有语法错误

**错误处理策略：**
- AI 调用：超时 + 重试 + 中文错误提示（不给用户看技术堆栈）
- 文件操作：try/except + 友好的错误消息
- 数据库迁移：幂等设计 + 事务保护
- 空数据：所有计算函数都有空列表的边界处理

---

## 8. 扩展与展望类

### Q29：如果有更多时间，你会怎么改进这个项目？

**答：** 按优先级排序：

1. **数据云同步**（高优先）：接入 WebDAV / 阿里云 OSS，让数据在多台电脑间同步。技术上只需要在 `DatabaseConnection` 中加一个 `sync()` 方法 — 分层架构让这个改动影响范围极小。

2. **更多可视化**：当前只有 GPA 折线图（QPainter 手绘），可以加雷达图（个人发展四维度）、热力图（学期课程密度）。`matplotlib` 嵌入 Qt 窗口是成熟方案。

3. **多专业培养方案**：当前主要支持大数据专业，架构已经支持多方案（`DASHBOARD_CATEGORIES` 是列表，`load_plan_text()` 按年份查找），只需补充其他专业的 `.md` 方案文件。

4. **移动端适配**：PySide6 支持 Android/iOS 部署，但需要适配触摸交互和屏幕尺寸。分层架构让 Views 层可以独立重写。

5. **社区功能**：匿名分享经历/选课评价 — 但需要后端服务，超出了桌面应用的范围。

---

### Q30：如果要把这个项目从个人桌面应用扩展为多用户 Web 应用，需要改哪些部分？

**答：** 得益于分层架构，改动范围有限：

| 层 | 改动量 | 具体改动 |
|----|-------|---------|
| **Database** | 小 | SQLite → PostgreSQL；`student` 表加 `user_id` 字段；Repository SQL 加 `WHERE user_id = ?` |
| **Models** | 无 | 数据结构不变 |
| **Services** | 极小 | `GpaCalculator`、`CurriculumAuditor` 等都不需要改 — 它们只依赖数据模型，不依赖数据库类型 |
| **Views** | **全部重写** | PySide6 → React/Vue；Signal/Slot → HTTP API + WebSocket |
| **AI 集成** | 小 | API Key 管理从本地配置 → 服务端环境变量；QThread → 异步 HTTP 请求 |

**关键结论：** 约 60% 的代码可以复用（Models + Services + 部分 Database），只需重写 Views 层和加一个 API 层。这证明了分层架构的价值 — **UI 和业务逻辑的真正解耦**。

---

### Q31：这个项目最大的技术挑战是什么？你是怎么解决的？

**答：** 最大的挑战是 **培养方案审计引擎的双通道匹配**。

**为什么难：**
- 培养方案是半结构化的 Markdown 文本，不是数据库表 — 需要从自然语言中提取结构化信息
- 不同学校的课程代码体系不同，同一门课在不同教务系统中代码可能不一样
- 学生成绩单数据质量参差不齐 — 有的有课程代码，有的只有课程名
- 13 类课程分类体系需要同时满足"精确匹配"和"兜底覆盖"

**解决思路（[curriculum_auditor.py](src/services/curriculum_auditor.py)）：**
1. 先做正则提取：课程代码 `[A-Z]{2,4}\d{3}` + 学分数字 + 模块标题
2. 建立三层匹配策略（代码精确 > 名称模糊 > 关键词规则）
3. 每种匹配策略赋不同的置信度（代码匹配 ≈ 100% 可靠，关键词 ≈ 60% 可靠）
4. 审计结果不做"对/错"判断，而是给出"已匹配 X 学分 / 要求 Y 学分 / 缺失课程列表"
5. 计划外课程单独归类，不影响完成度计算 — 给用户人工核对的入口

**收获：**
- 现实世界的数据从来不是干净的，工程中需要"能用"而非"完美"
- 分层匹配策略在信息检索领域（precision/recall trade-off）有理论基础
- 这个引擎的架构可以泛化到任何"半结构化文本 vs 结构化数据"的匹配场景

---

> **答辩策略提示：**
>
> 1. **回答要有代码位置** — 每个问题都引用具体文件和行号，展示你对代码的掌控力
> 2. **用三段式结构** — "做了什么 → 为什么这样做 → 带来了什么好处"
> 3. **主动展示运行效果** — 如果允许演示，提前准备好各页面的数据
> 4. **诚实面对不足** — 被问到缺点时不要说"没有缺点"，说"当前已知的局限 + 改进方向"
> 5. **记住关键数字**：6 种模式、8 张表、9 个页面、13 类课程审计、6 个测试模块、3 大 AI 能力
