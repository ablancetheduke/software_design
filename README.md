# PDPTool — 个人发展规划工具

> **软件体系结构与设计模式（BDT220）课程小组作业**
>
> 面向大学生的一站式学业规划与职业发展管理平台。

---

> 💡 **关于本项目**：本仓库为课程小组作业的提交版本。项目的完整开发历程、更早的提交记录以及更完备的代码结构，请参见 [Software-architecture-design-group-assignment](https://github.com/ablancetheduke/Software-architecture-design-group-assignment) —— 那里收录了从项目立项到功能迭代的全部 commit 历史，所有代码均由开发者独立完成（包括架构设计、前后端实现、AI 集成与测试），更完整地体现了本项目的实际工作量与工程能力。因提交时间节点所限，此处为同步整理后的版本；如需了解完整的设计思路、设计模式应用分析以及详细的架构文档，也请优先查阅前述仓库中的 `pre.md`。

---

## 项目简介

PDPTool 定位为 **"大学生个人发展操作系统"** — 以学业数据为中心，打通 **课程 → GPA → 培养方案 → 经历 → 简历 → 实习投递 → 升学规划 → 技能提升** 的完整链路，帮助大学生集中管理四年学习与发展历程。

### 核心功能

| 模块 | 功能 |
|------|------|
| 📚 课程管理 | 课程增删改查、CSV 导入导出、学期/类别筛选 |
| 📊 GPA 分析 | 标准 4.0 绩点、加权/算术平均、学期趋势图 |
| 🎓 培养方案审计 | 解析培养方案、智能匹配已修课程、学分缺口可视化 |
| 🏆 经历荣誉 | 项目/科研/竞赛/实习经历分类管理、奖项证书记录 |
| 📄 简历工作台 | 一键生成 HTML/Markdown 简历、AI STAR 改写、Word 导出 |
| 💼 实习追踪 | 投递状态看板、截止日期提醒、面试进度管理 |
| 🎯 升学规划 | 研究生申请管理、甘特图时间线、培养方案审核 |
| 🤖 AI 顾问 | 结合个人全量数据的智能发展规划建议 |
| 💻 编程练习 | 内建算法题库、AI 代码评审与渐进提示 |
| 🌐 Web 版 | FastAPI + Jinja2 浏览器访问（支持云端部署） |

### 技术栈

- **GUI**：PySide6（Qt for Python）
- **Web**：FastAPI + Jinja2
- **数据库**：SQLite（零配置本地部署）
- **AI**：DeepSeek API（OpenAI 兼容协议）
- **语言**：Python 3.10+
- **打包**：PyInstaller → 独立 EXE（`PDPTool.spec`）

## 快速开始

```bash
# 桌面版
pip install -r requirements.txt
python main.py

# Web 版
pip install -r requirements_web.txt
python web_app.py
```

> 🖥️ **双击即用**：项目根目录下的 `PDPTool.spec` 可通过 PyInstaller 打包为独立 EXE 文件：
> ```bash
> pyinstaller PDPTool.spec
> ```
> 打包后生成的 `PDPTool.exe` 可脱离 Python 环境直接双击运行。

AI 功能需要 DeepSeek API Key（可选）：
```bash
DEEPSEEK_API_KEY=你的key
```

## 项目结构

```text
├── main.py                    # 桌面版入口
├── web_app.py                 # Web 版入口
├── PDPTool.spec               # PyInstaller 打包配置（→ 独立 EXE）
├── src/
│   ├── models/                # 数据模型（含研究生申请模型）
│   ├── database/              # SQLite 连接、迁移、仓储层
│   ├── services/              # 业务逻辑（GPA、审计、AI、简历、升学）
│   ├── views/                 # PySide6 界面、甘特图组件
│   └── utils/                 # 常量、主题、工具函数
├── tests/                     # pytest 单元测试
├── training_plans/            # 培养方案（2023/2024/2025 级）
├── coding_problems/           # 编程练习题（20 道 LeetCode 风格）
└── web/                       # Web 前端模板与静态资源
```

## 设计模式应用

本项目综合运用了多种经典设计模式（详见 [pre.md](./pre.md) 完整分析）：

- **Repository 模式** — 数据访问层抽象
- **Singleton** — 数据库连接管理
- **Observer** — Qt 信号/槽驱动的 UI 更新
- **Factory** — 记录对象创建
- **Strategy** — GPA 计算策略、简历导出策略
- **Facade** — AI 服务统一调用接口

---

## 📋 提交记录与版本更新说明

> **2026 年 7 月 5 日更新**：本仓库在同步最新代码（升学规划模块、PyInstaller 打包配置、Word 简历导出等）时，由于整体替换文件结构的操作不慎覆盖了小组同学此前在 6 月 25 日上传的原始文件（`LICENSE`、`Q&A.md`、`grades.csv`、`models/`、`utils/`、`views/` 等扁平结构代码及根级测试文件）。发现问题后已立即通过 `git revert` 恢复所有被覆盖的文件，并在保留小组全部原始贡献的前提下重新叠加了最新版本代码。
>
> 小组各成员的原始提交记录 **完整保留在 Git 历史中**，可通过 [Commits 页面](https://github.com/ablancetheduke/software_design/commits/main) 查看：
> - **Camellia-224**（6 月 25 日 15:05）— `liushuhan add files`
> - **zmjjbb11**（6 月 25 日 16:23）— `Add files via upload`
> - **anzimu324-cell**（6 月 25 日 16:39）— `Add files via upload`
> - **Lucaslee127**（6 月 25 日 20:38–20:43）— 多次 `Add files via upload`
>
> 这些提交记录和对应的时间戳均可追溯，体现了小组每位成员的实际贡献。本次 7 月 5 日的文件覆盖及恢复过程同样记录在 commit 历史中，操作透明可查。

## 维护者

如对架构设计、实现细节或设计模式应用有疑问，欢迎直接联系 [@ablancetheduke](https://github.com/ablancetheduke) 提 Issue 或参考 [完整开发仓库](https://github.com/ablancetheduke/Software-architecture-design-group-assignment) 中的提交历史与设计文档。
