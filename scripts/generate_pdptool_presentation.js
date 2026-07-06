const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const outDir = path.join(__dirname, "..");
const pptxPath = path.join(outDir, "PDPTool_桌面版系统答辩.pptx");
const scriptPath = path.join(outDir, "PDPTool_桌面版答辩讲稿.md");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "PDPTool Project Team";
pptx.company = "Software Architecture Design";
pptx.subject = "PDPTool 桌面版系统答辩";
pptx.title = "PDPTool 桌面版系统答辩";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN"
};

const W = 13.333;
const H = 7.5;
const C = {
  ink: "17202A",
  muted: "5B6572",
  bg: "F7F4EE",
  panel: "FFFFFF",
  line: "D9D1C4",
  dark: "1C1C24",
  amber: "F59E0B",
  teal: "0F766E",
  green: "2F855A",
  red: "C2410C",
  purple: "6D28D9",
  blue: "2563EB"
};

function shadow() {
  return { type: "outer", color: "000000", opacity: 0.10, blur: 2, offset: 1, angle: 45 };
}

function addBg(slide, dark = false) {
  slide.background = { color: dark ? C.dark : C.bg };
  if (!dark) {
    slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: 0.18, fill: { color: C.amber }, line: { color: C.amber } });
  }
}

function addFooter(slide, page) {
  slide.addText("PDPTool 桌面版 · 软件体系结构设计答辩", {
    x: 0.55, y: 7.08, w: 8.5, h: 0.22, fontSize: 8.5, color: "8A8175", margin: 0
  });
  slide.addText(String(page).padStart(2, "0"), {
    x: 12.25, y: 6.98, w: 0.5, h: 0.25, fontSize: 9, color: "8A8175", align: "right", margin: 0
  });
}

function title(slide, t, sub = "") {
  slide.addText(t, { x: 0.55, y: 0.42, w: 7.8, h: 0.48, fontSize: 24, bold: true, color: C.ink, margin: 0 });
  if (sub) slide.addText(sub, { x: 0.58, y: 0.93, w: 10.8, h: 0.28, fontSize: 9.5, color: C.muted, margin: 0 });
}

function chip(slide, text, x, y, w, color = C.teal) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.34, rectRadius: 0.04, fill: { color }, line: { color } });
  slide.addText(text, { x: x + 0.08, y: y + 0.07, w: w - 0.16, h: 0.18, fontSize: 8.8, bold: true, color: "FFFFFF", align: "center", margin: 0 });
}

function card(slide, x, y, w, h, head, body, color = C.teal) {
  slide.addShape(pptx.ShapeType.rect, { x, y, w, h, fill: { color: C.panel }, line: { color: C.line }, shadow: shadow() });
  slide.addShape(pptx.ShapeType.rect, { x, y, w: 0.08, h, fill: { color }, line: { color } });
  slide.addText(head, { x: x + 0.22, y: y + 0.18, w: w - 0.35, h: 0.25, fontSize: 12, bold: true, color: C.ink, margin: 0 });
  slide.addText(body, { x: x + 0.22, y: y + 0.55, w: w - 0.36, h: h - 0.7, fontSize: 9.1, color: C.muted, fit: "shrink", breakLine: false, margin: 0.02 });
}

function metric(slide, x, y, num, label, color = C.amber) {
  slide.addText(num, { x, y, w: 1.65, h: 0.55, fontSize: 27, bold: true, color, align: "center", margin: 0 });
  slide.addText(label, { x, y: y + 0.57, w: 1.65, h: 0.24, fontSize: 8.5, color: C.muted, align: "center", margin: 0 });
}

function bullets(slide, items, x, y, w, h, size = 10.2, color = C.ink) {
  slide.addText(items.map((text, i) => ({ text, options: { bullet: true, breakLine: i < items.length - 1 } })), {
    x, y, w, h, fontSize: size, color, breakLine: false, fit: "shrink", paraSpaceAfterPt: 4, margin: 0.02
  });
}

function notes(slide, text) {
  if (slide.addNotes) slide.addNotes(text.split("\n"));
}

const speaker = [];
function addScript(n, title, text) {
  speaker.push(`## 第 ${n} 页：${title}\n\n${text.trim()}\n`);
}

let p = 1;

// 1
{
  const s = pptx.addSlide();
  addBg(s, true);
  s.addText("PDPTool", { x: 0.75, y: 1.05, w: 5, h: 0.7, fontSize: 42, bold: true, color: "FFFFFF", margin: 0 });
  s.addText("大学生个人发展规划桌面系统", { x: 0.8, y: 1.85, w: 6.2, h: 0.35, fontSize: 17, color: "FDE68A", margin: 0 });
  s.addText("围绕学分完成度、成绩分析、经历管理、简历生成、实习追踪与 AI 顾问的本地化桌面应用", {
    x: 0.82, y: 2.35, w: 7.0, h: 0.62, fontSize: 13, color: "D7D7DD", fit: "shrink", margin: 0
  });
  ["PySide6 桌面端", "SQLite 本地持久化", "培养方案学分审计", "DeepSeek AI 可替换密钥"].forEach((t, i) => chip(s, t, 0.82 + i * 2.2, 3.15, 1.9, [C.amber, C.teal, C.blue, C.purple][i]));
  s.addShape(pptx.ShapeType.rect, { x: 8.35, y: 0.82, w: 3.8, h: 5.15, fill: { color: "2A2A35" }, line: { color: "474759" }, shadow: shadow() });
  s.addText("桌面主界面结构", { x: 8.65, y: 1.08, w: 3.1, h: 0.25, fontSize: 12, bold: true, color: "FFFFFF", margin: 0 });
  s.addShape(pptx.ShapeType.rect, { x: 8.65, y: 1.55, w: 0.72, h: 3.65, fill: { color: "1C1C24" }, line: { color: "1C1C24" } });
  s.addShape(pptx.ShapeType.rect, { x: 9.55, y: 1.55, w: 2.25, h: 3.65, fill: { color: "FAF7F2" }, line: { color: "E8E2D8" } });
  ["总览", "课程", "GPA", "简历", "AI"].forEach((t, i) => {
    s.addShape(pptx.ShapeType.rect, { x: 8.78, y: 1.82 + i * 0.52, w: 0.46, h: 0.18, fill: { color: i === 0 ? C.amber : "555568" }, line: { color: i === 0 ? C.amber : "555568" } });
  });
  s.addText("课程表 / 学分进度 / 趋势图 / 操作区", { x: 9.83, y: 2.05, w: 1.42, h: 1.3, fontSize: 13, bold: true, color: C.ink, align: "center", valign: "mid", fit: "shrink", margin: 0.05 });
  addScript(p, "封面", "各位老师好，我们展示的是 PDPTool，定位是大学生个人发展规划桌面系统。它不是单一的成绩表，而是把课程学分、GPA、经历、简历、实习和 AI 咨询放到一个本地桌面应用里，核心场景是帮助学生知道自己已经完成了什么、还差什么、下一步该补哪里。");
  notes(s, speaker.at(-1));
}

// 2
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "评分项对齐", "PPT 结构按评分权重组织，重点放在架构、详细设计与运行效果");
  const data = [
    ["架构设计与合理性", "25", "分层架构、数据流、SQLite 存储、AI 边界"],
    ["系统实现与运行效果", "20", "桌面端功能闭环、导入导出、学分总览"],
    ["详细设计专业性", "20", "模型、仓储、服务、UI 信号联动"],
    ["设计模式应用", "10", "单例、仓储、策略、服务层、观察者式信号"],
    ["展示清晰与时间合理", "10", "按业务痛点到实现证据递进"],
    ["创新拓展 / 使用价值 / 过程规范", "15", "AI 顾问、简历、刷题、测试与管理"]
  ];
  s.addTable([["评分项", "权重", "本答辩覆盖方式"], ...data], {
    x: 0.72, y: 1.35, w: 11.85, h: 4.75, colW: [3.0, 1.1, 7.75],
    fontSize: 11, color: C.ink, border: { pt: 0.6, color: C.line },
    fill: { color: "FFFFFF" }, margin: 0.08,
    autoFit: false,
    valign: "mid",
    bold: false,
    fit: "shrink"
  });
  addFooter(s, p);
  addScript(p, "评分项对齐", "这一页说明我们的展示顺序是围绕评分要求设计的。最高权重是架构设计、运行效果和详细设计，所以后面会先讲为什么做、系统如何分层、数据如何流动，再讲设计模式、功能实现、安全稳定性、创新和过程管理。");
  notes(s, speaker.at(-1));
}

// 3
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "需求分析：从“我到底还差多少学分”出发", "真实痛点：学生知道总学分重要，但很难按培养方案拆分判断");
  card(s, 0.7, 1.35, 3.55, 3.95, "用户困扰", "我们经常因为不知道各部分学分到底修了多少而苦恼：通识、通修、专业基础、专业方向、英语、体育、数学等要求分散在培养方案里，靠人工表格核对容易漏算。", C.red);
  card(s, 4.55, 1.35, 3.55, 3.95, "设计目标", "把“已修课程”自动映射到培养方案分类，展示每个部分的已修/要求/剩余学分，让用户一眼知道短板，而不是只看到一串课程成绩。", C.teal);
  card(s, 8.4, 1.35, 3.55, 3.95, "核心用户", "主要面向大学生本人：需要规划选课、核对毕业要求、准备简历、追踪实习和复盘成长路径。系统优先服务个人本地使用和低成本维护。", C.blue);
  metric(s, 1.3, 5.65, "145", "培养方案总目标学分");
  metric(s, 3.7, 5.65, "13", "桌面总览细分学分项", C.teal);
  metric(s, 6.1, 5.65, "CSV", "成绩单可批量导入", C.blue);
  metric(s, 8.5, 5.65, "本地", "数据优先留在用户电脑", C.green);
  addFooter(s, p);
  addScript(p, "需求分析", "我们的需求不是凭空想出来的，而是来自学生选课时的实际焦虑：培养方案写了很多模块，但我们很难知道每一部分自己已经修了多少。所以系统的第一目标是把成绩单变成可视化学分进度，把总学分拆到具体类别，告诉用户哪些部分已经够了、哪些还缺。");
  notes(s, speaker.at(-1));
}

// 4
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "功能范围：基础功能与创新拓展", "桌面端功能不是堆页面，而是围绕“规划、记录、输出、反馈”形成闭环");
  const items = [
    ["课程管理", "课程增删改查、CSV 导入导出、学期/类别筛选、搜索"],
    ["学分审计", "按培养方案匹配已修课程，计算已修、剩余和完成率"],
    ["GPA 分析", "4.0 绩点、加权平均、算术平均、分学期趋势"],
    ["经历与荣誉", "项目、科研、竞赛、实习、证书等结构化记录"],
    ["简历工作台", "基于个人数据生成 HTML、Markdown、JSON、PDF 简历"],
    ["AI 顾问与刷题", "DeepSeek API 支持发展咨询、STAR 改写、代码讲解/审查"]
  ];
  items.forEach((it, i) => {
    const x = 0.72 + (i % 3) * 4.1, y = 1.35 + Math.floor(i / 3) * 2.15;
    card(s, x, y, 3.55, 1.58, it[0], it[1], [C.teal, C.green, C.amber, C.blue, C.purple, C.red][i]);
  });
  s.addShape(pptx.ShapeType.rect, { x: 0.72, y: 6.0, w: 11.85, h: 0.55, fill: { color: "FFF7E6" }, line: { color: "F4D28D" } });
  s.addText("桌面版定位：本地数据、即时反馈、低部署门槛；Web 版仅作为后续部署扩展，不是本次系统主线。", { x: 0.95, y: 6.17, w: 11.3, h: 0.18, fontSize: 10.2, color: C.ink, margin: 0 });
  addFooter(s, p);
  addScript(p, "功能范围", "基础功能包括课程管理、学分审计、GPA 分析、经历荣誉记录、简历生成。创新拓展包括 AI 顾问、AI 简历 STAR 改写、算法题讲解和代码评审。这些模块不是分散功能，而是围绕个人发展规划闭环：输入数据、分析状态、生成输出、再根据反馈调整。");
  notes(s, speaker.at(-1));
}

// 5
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "桌面系统架构", "PySide6 UI 层、Service 业务层、Repository 数据访问层、SQLite 持久化层");
  const xs = [0.75, 3.65, 6.55, 9.45];
  const heads = ["View 层", "Service 层", "Repository 层", "SQLite / 文件层"];
  const bodies = [
    "MainWindow、CourseView、DashboardView、GpaView、ResumeView、AiAssistantPanel：负责界面、交互、信号刷新。",
    "CurriculumAuditor、GpaCalculator、DataIO、ResumeExporter、AI/CodingTutor：负责业务规则和计算。",
    "CourseRepository、StudentRepository、ExperienceRepository 等：封装 SQL CRUD 和批量导入。",
    "pdptool.db 保存核心数据；training_plans/*.md 保存培养方案；coding_problems/*.md 保存题库；pdptool_config.json 可保存 API Key。"
  ];
  xs.forEach((x, i) => card(s, x, 1.45, 2.55, 3.95, heads[i], bodies[i], [C.blue, C.teal, C.green, C.amber][i]));
  [3.32, 6.22, 9.12].forEach(x => s.addShape(pptx.ShapeType.triangle, { x, y: 3.15, w: 0.28, h: 0.28, rotate: 90, fill: { color: C.muted }, line: { color: C.muted } }));
  s.addText("合理性：UI 不直接写 SQL，计算逻辑不绑定 Qt 控件，数据访问统一走仓储，便于测试、扩展和问题定位。", { x: 0.85, y: 5.95, w: 11.2, h: 0.35, fontSize: 12, bold: true, color: C.ink, align: "center", margin: 0 });
  addFooter(s, p);
  addScript(p, "桌面系统架构", "桌面版采用典型分层结构。View 层只处理界面和信号，Service 层负责学分审计、GPA 计算、导入导出、简历生成和 AI 调用，Repository 层封装数据库操作，底层使用 SQLite 和少量 Markdown/JSON 文件。这样做的好处是：UI 改版不会影响核心算法，算法测试也不需要启动桌面窗口。");
  notes(s, speaker.at(-1));
}

// 6
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "数据怎么存：本地 SQLite 为主，文件资源为辅", "数据设计优先保证可恢复、可迁移、可离线运行");
  s.addTable([
    ["数据对象", "存放位置", "用途"],
    ["学生信息", "pdptool.db / student", "姓名、学院、专业、入学年份、联系方式、技能简介"],
    ["课程成绩", "pdptool.db / courses", "课程名、代码、学分、学期、成绩、类别、备注"],
    ["经历 / 荣誉 / 角色", "pdptool.db / experiences, achievements, roles", "简历素材与发展记录"],
    ["实习投递", "pdptool.db / internship_applications", "公司、岗位、方向、状态、截止日、面试记录"],
    ["培养方案", "training_plans/*.md 与 curriculum_plan_chunks", "学分要求、课程代码、AI 检索上下文"],
    ["API Key", "优先环境变量；可选 pdptool_config.json", "DeepSeek 调用凭证，用户可自主替换"]
  ], {
    x: 0.72, y: 1.28, w: 11.85, h: 4.65, colW: [2.2, 4.2, 5.45],
    fontSize: 9.4, color: C.ink, border: { pt: 0.6, color: C.line },
    fill: { color: "FFFFFF" }, margin: 0.07, fit: "shrink"
  });
  card(s, 0.72, 6.05, 5.65, 0.65, "迁移机制", "migrations.py 使用 _schema_version 记录版本，启动时自动补齐表结构和默认学生记录。", C.green);
  card(s, 6.92, 6.05, 5.65, 0.65, "备份机制", "DataIO 支持 JSON 全量导出/导入，课程支持 CSV 导入导出。", C.blue);
  addFooter(s, p);
  addScript(p, "数据存储", "核心数据都存到项目根目录的 pdptool.db，这是 SQLite 本地数据库。课程、经历、荣誉、实习投递和学生信息分别有自己的表。培养方案原始内容放在 training_plans 目录的 Markdown 文件里，启动时可以导入为结构化片段，供 AI 检索使用。API Key 不进入数据库，优先读环境变量，也可以保存在 pdptool_config.json。");
  notes(s, speaker.at(-1));
}

// 7
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "核心数据流：从成绩单到学分总览", "课程 CSV / 手工录入进入数据库，再由审计服务映射到培养方案类别");
  const steps = [
    ["1 输入", "CSV 成绩单或课程弹窗录入"],
    ["2 清洗", "DataIO 识别列名、转换学分和成绩、跳过异常行"],
    ["3 持久化", "CourseRepository 批量写入 courses 表"],
    ["4 审计", "CurriculumAuditor 按课程代码/名称匹配培养方案"],
    ["5 展示", "Dashboard/GPA/Resume 收到 data_changed 信号后刷新"]
  ];
  steps.forEach((st, i) => {
    const x = 0.65 + i * 2.48;
    card(s, x, 1.65, 2.05, 2.3, st[0], st[1], [C.red, C.amber, C.green, C.teal, C.blue][i]);
    if (i < 4) s.addShape(pptx.ShapeType.chevron, { x: x + 2.12, y: 2.45, w: 0.28, h: 0.42, fill: { color: C.muted }, line: { color: C.muted } });
  });
  s.addChart(pptx.ChartType.bar, [{
    name: "要求学分",
    labels: ["通识", "通修", "专业"],
    values: [14, 70, 61]
  }], {
    x: 1.0, y: 4.55, w: 5.4, h: 1.75, barDir: "col", chartColors: [C.teal],
    showLegend: false, showValue: true, valGridLine: { color: "E5E1D8", size: 0.5 },
    catAxisLabelColor: C.muted, valAxisLabelColor: C.muted, chartArea: { fill: { color: C.bg }, border: { color: C.bg } }
  });
  bullets(s, [
    "争议点：课程代码缺失时是否还能自动匹配？解决：优先代码匹配，缺失时用课程名归一化辅助匹配，并在结果中保留“计划外/待人工核对”。",
    "争议点：选修课不一定是固定课程。解决：选修类重点判断学分是否补足，不强行要求某一门课程。"
  ], 7.1, 4.65, 5.05, 1.55, 9.8);
  addFooter(s, p);
  addScript(p, "核心数据流", "以成绩单为例，用户上传 CSV 或手工录入课程，DataIO 会识别列名，把学分和成绩转成数值，异常行计入 skipped 而不是让程序崩溃。课程写入 SQLite 后，Dashboard 和 GPA 页面通过 data_changed 信号刷新。学分审计先用课程代码匹配，代码缺失时再尝试用课程名匹配，无法确定的放入计划外课程，留给用户人工核对。");
  notes(s, speaker.at(-1));
}

// 8
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "设计模式应用", "不是为了模式而模式，而是把变化点放到合适边界");
  const rows = [
    ["Singleton 单例", "DatabaseConnection", "全局复用同一个 SQLite 连接，避免各页面重复创建连接"],
    ["Repository 仓储", "CourseRepository 等", "隐藏 SQL 细节，View/Service 面向对象模型工作"],
    ["Strategy 策略", "GpaStrategy", "4.0 绩点、加权平均、算术平均可运行时切换"],
    ["Service Layer", "DataIO / CurriculumAuditor", "业务规则从 UI 抽离，便于测试和复用"],
    ["Observer 思想", "Qt Signal", "课程、经历、投递变更后自动刷新总览、GPA 和简历"]
  ];
  s.addTable([["模式", "项目落点", "解决的问题"], ...rows], {
    x: 0.72, y: 1.35, w: 11.85, h: 4.7, colW: [2.0, 3.0, 6.85],
    fontSize: 10, color: C.ink, border: { pt: 0.6, color: C.line },
    fill: { color: "FFFFFF" }, margin: 0.08, fit: "shrink"
  });
  addFooter(s, p);
  addScript(p, "设计模式应用", "项目里用到的模式比较直接。数据库连接用单例，保证桌面进程内连接一致；各类 Repository 负责 CRUD；GPA 使用策略模式，同一套计算器可以切换不同算法；业务功能放在 service；页面之间通过 Qt Signal 刷新，相当于观察者式联动。");
  notes(s, speaker.at(-1));
}

// 9
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "详细设计：学分审计模块", "最关键的业务逻辑：把培养方案要求转为可计算的 Requirement");
  card(s, 0.75, 1.3, 3.2, 4.15, "输入", "课程列表：Course(name, code, credit, semester, grade, category)\n培养方案：training_plans/2023.md、2024.md、2025.md 或默认 Markdown 文件", C.blue);
  card(s, 4.25, 1.3, 3.2, 4.15, "处理", "正则提取课程代码，例如 BDT220、MAT108；按模块生成 Requirement；优先 code 匹配，再做课程名归一化辅助匹配；已匹配课程避免重复计分。", C.teal);
  card(s, 7.75, 1.3, 3.2, 4.15, "输出", "ModuleResult / CategoryAuditResult：required_credits、earned_credits、remaining_credits、completion_ratio、matched_courses、missing_codes。", C.green);
  s.addShape(pptx.ShapeType.rect, { x: 11.25, y: 1.3, w: 1.05, h: 4.15, fill: { color: "FFF7E6" }, line: { color: "F4D28D" } });
  s.addText("容错", { x: 11.43, y: 1.65, w: 0.7, h: 0.35, fontSize: 15, bold: true, color: C.red, align: "center", margin: 0 });
  s.addText("计划外课程保留展示\n课程名缺失不崩溃\nrequired=0 特殊处理\n完成率上限 100%", { x: 11.4, y: 2.25, w: 0.75, h: 2.0, fontSize: 9, color: C.ink, align: "center", fit: "shrink", margin: 0.03 });
  addFooter(s, p);
  addScript(p, "学分审计模块", "学分审计是系统最核心的计算模块。它读取培养方案 Markdown，提取模块、要求学分和课程代码，再与用户课程列表比较。结果不是只有一个总分，而是每个模块都有要求学分、已修学分、剩余学分和完成率。为了避免误算，同一门课程匹配后不会重复计分，无法匹配的课程会作为计划外课程保留。");
  notes(s, speaker.at(-1));
}

// 10
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "详细设计：桌面交互与刷新机制", "MainWindow 统一页面注册，业务页面通过信号触发联动刷新");
  s.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.3, w: 2.25, h: 4.3, fill: { color: C.dark }, line: { color: C.dark } });
  s.addText("侧边导航\nDashboard\n课程管理\n经历管理\n实习追踪\nGPA\n简历\n设置", { x: 1.05, y: 1.7, w: 1.75, h: 3.5, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "mid", fit: "shrink", margin: 0.05 });
  s.addShape(pptx.ShapeType.rect, { x: 3.55, y: 1.3, w: 5.15, h: 4.3, fill: { color: "FFFFFF" }, line: { color: C.line }, shadow: shadow() });
  s.addText("QStackedWidget 内容区", { x: 4.5, y: 1.68, w: 3.3, h: 0.35, fontSize: 18, bold: true, color: C.ink, align: "center", margin: 0 });
  bullets(s, ["页面类在 PAGES 中注册", "导航按钮切换 stack index", "进入页面时调用 refresh()", "课程/经历/荣誉/投递变更发出 data_changed"], 4.0, 2.35, 4.2, 2.2, 12);
  s.addShape(pptx.ShapeType.rect, { x: 9.25, y: 1.3, w: 2.95, h: 4.3, fill: { color: "FAF7F2" }, line: { color: "E8E2D8" }, shadow: shadow() });
  s.addText("AI 侧栏", { x: 10.0, y: 1.7, w: 1.45, h: 0.35, fontSize: 18, bold: true, color: C.ink, align: "center", margin: 0 });
  bullets(s, ["悬浮助手入口", "QSplitter 可拉伸", "请求失败返回可读错误", "不阻塞主数据流程"], 9.72, 2.35, 1.95, 2.2, 11);
  addFooter(s, p);
  addScript(p, "桌面交互与刷新", "桌面端主窗口统一管理所有页面。左侧是导航，右侧是 QStackedWidget 内容区；每个页面进入时会 refresh。课程、经历、荣誉、实习投递等数据变更后会发出 data_changed 信号，总览、GPA 和简历页面自动刷新。AI 侧栏通过 QSplitter 展开，和核心数据模块解耦，AI 失败不会影响本地功能。");
  notes(s, speaker.at(-1));
}

// 11
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "运行效果：桌面端使用路径", "按案例演示：录入数据、查看缺口、生成输出、获得建议");
  const flow = [
    ["个人设置", "填写姓名、学院、专业、入学年份：如 2024 级大数据专业"],
    ["导入课程", "上传 grades.csv 或手动添加：课程名、代码、学分、学期、成绩、类别"],
    ["查看总览", "总学分 145 目标，按通识/通修/专业等类别查看进度"],
    ["分析成绩", "查看 GPA、加权平均、算术平均和学期趋势"],
    ["补充经历", "录入科研、竞赛、实习、荣誉，用于简历和 AI 建议"],
    ["生成简历", "选择展示模块，导出 HTML / Markdown / JSON / PDF"]
  ];
  flow.forEach((f, i) => {
    const x = 0.72 + (i % 2) * 6.15, y = 1.25 + Math.floor(i / 2) * 1.68;
    card(s, x, y, 5.35, 1.15, `${i + 1}. ${f[0]}`, f[1], [C.blue, C.teal, C.green, C.amber, C.purple, C.red][i]);
  });
  addFooter(s, p);
  addScript(p, "运行效果路径", "运行效果可以按用户真实路径展示：先在个人设置里填专业和入学年份，再导入成绩 CSV，系统就能在总览中显示学分进度。之后用户可以看 GPA 趋势，补充经历和荣誉，最后生成简历。这个路径覆盖了从输入到分析再到输出的完整闭环。");
  notes(s, speaker.at(-1));
}

// 12
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "上传文件与填写内容案例", "答辩演示时按这个案例走，能体现系统不会因普通输入差异崩溃");
  card(s, 0.75, 1.25, 3.75, 4.7, "成绩 CSV 案例", "表头：课程名称,代码,学分,学期,成绩,类别,备注\n示例：软件体系结构与设计模式,BDT220,3,大三上,92,专业课,\n示例：高等数学(一),MAT108,5,大一上,88,通修课,\n说明：支持 UTF-8-SIG，异常行会跳过并提示 skipped。", C.teal);
  card(s, 4.78, 1.25, 3.75, 4.7, "经历填写案例", "标题：数据可视化课程项目\n类型：学术经历 / 科研经历 / 实习经历 / 竞赛经历\n组织：课程小组\n角色：数据处理与前端展示\n成果：完成可视化看板并用于课程汇报\n说明：用于简历自动填充与 AI STAR 改写。", C.blue);
  card(s, 8.82, 1.25, 3.45, 4.7, "实习追踪案例", "公司：某科技公司\n岗位：数据分析实习生\n方向：数据分析\n截止日：2026-07-15\n状态：待投递 / 已投递 / 面试中 / 已拒 / offer\n准备项：简历、项目、复盘记录\n说明：避免投递遗漏。", C.amber);
  addFooter(s, p);
  addScript(p, "案例说明", "演示时可以用这一页的案例。成绩 CSV 至少需要课程名称、代码、学分、学期、成绩和类别，系统会按列名识别。经历记录建议写清楚标题、类型、组织、角色和成果，因为这些字段会进入简历和 AI 上下文。实习追踪要记录公司、岗位、方向、截止日和状态，方便系统提醒准备进度。");
  notes(s, speaker.at(-1));
}

// 13
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "安全问题与解决方案", "桌面应用仍然需要考虑密钥、文件、数据、AI 输出和误操作风险");
  const rows = [
    ["API Key 泄露", "优先使用 DEEPSEEK_API_KEY 环境变量；本地配置 pdptool_config.json 不建议提交；部署时使用平台环境变量"],
    ["用户如何替换密钥", "修改环境变量 DEEPSEEK_API_KEY，或在 AI 助手面板保存新 key；可选设置 DEEPSEEK_BASE_URL / DEEPSEEK_MODEL"],
    ["数据库损坏 / 误删", "SQLite 本地保存，支持 JSON 导出备份；危险操作前弹窗确认"],
    ["CSV 异常输入", "导入时 try/except 转换，空行跳过，异常行计数，不让单行错误拖垮程序"],
    ["HTML 简历注入", "resume_exporter 对用户内容做 html.escape，避免将输入直接作为 HTML 执行"],
    ["AI 结果不可靠", "AI 只作为建议，培养方案审计仍由本地规则计算；错误返回可读信息，不影响主流程"]
  ];
  s.addTable([["风险", "处理方式"], ...rows], {
    x: 0.72, y: 1.25, w: 11.85, h: 5.25, colW: [2.7, 9.15],
    fontSize: 9.3, color: C.ink, border: { pt: 0.6, color: C.line },
    fill: { color: "FFFFFF" }, margin: 0.07, fit: "shrink"
  });
  addFooter(s, p);
  addScript(p, "安全设计", "安全方面我们主要考虑六类问题。API Key 优先放在环境变量，用户也可以通过 pdptool_config.json 或 AI 面板替换；数据库是本地 SQLite，并支持 JSON 备份；危险删除有确认弹窗；CSV 导入会跳过异常行；简历 HTML 生成会转义用户输入；AI 只提供建议，不能替代本地学分审计结果。");
  notes(s, speaker.at(-1));
}

// 14
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "稳定性检查：系统不能被轻易玩坏", "已经做的保护 + 当前测试暴露的问题");
  card(s, 0.75, 1.3, 3.7, 4.3, "输入稳定性", "课程导入支持 CSV/TSV/粘贴文本；空行和格式错误行被跳过；成绩、学分转换失败不会让整个导入中断；在修和通过制课程不参与 GPA。", C.green);
  card(s, 4.82, 1.3, 3.7, 4.3, "运行稳定性", "启动时自动初始化数据库和迁移；培养方案导入失败不会阻塞启动；AI 请求设置超时和异常捕获；AI 面板失败返回错误文本。", C.blue);
  card(s, 8.9, 1.3, 3.2, 4.3, "测试状态", "已运行 pytest：36 通过，5 失败。\n失败集中在简历导出测试：show_custom、skills section、header intent、经历自动填充等预期与当前实现不一致。\n答辩态度：作为回归问题纳入后续修复清单。", C.red);
  s.addText("质量原则：如实报告测试结果，比“演示能跑”更接近卓越软件开发者的行为习惯。", { x: 1.05, y: 6.1, w: 11.25, h: 0.3, fontSize: 12, bold: true, color: C.ink, align: "center", margin: 0 });
  addFooter(s, p);
  addScript(p, "稳定性检查", "我们做了输入容错、启动迁移、AI 异常捕获和危险操作确认。需要如实说明的是，当前自动化测试不是全绿：36 个通过，5 个失败，集中在简历导出相关测试。这说明主流程大部分被测试覆盖，但简历模块存在回归风险，后续会优先修复。答辩时这样讲更可信。");
  notes(s, speaker.at(-1));
}

// 15
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "开发困难与解决过程", "把遇到的问题转化成架构边界和工程规范");
  const rows = [
    ["培养方案文本复杂", "课程名长、代码分散、选修规则不固定", "用正则抽取课程代码；按模块/要求建模；课程名归一化辅助匹配；无法确认的进入计划外"],
    ["桌面页面相互依赖", "课程改动后总览、GPA、简历都要同步", "用 Qt Signal 触发刷新，避免页面之间互相直接调用内部逻辑"],
    ["CSV 来源不统一", "Excel/WPS 导出的编码、列名、顺序可能不同", "使用 utf-8-sig 读取，按列名映射，异常行 skipped"],
    ["AI 密钥与失败处理", "没有 key 或网络失败时容易卡住体验", "优先环境变量；可配置文件替换；请求异常返回可读错误，不影响本地功能"],
    ["简历输出安全", "用户输入可能包含 HTML 特殊字符", "生成 HTML 前统一 escape，PDF/Markdown/JSON 由同一数据源生成"]
  ];
  s.addTable([["困难", "具体表现", "解决方案"], ...rows], {
    x: 0.72, y: 1.2, w: 11.85, h: 5.4, colW: [2.4, 3.45, 6.0],
    fontSize: 8.9, color: C.ink, border: { pt: 0.6, color: C.line },
    fill: { color: "FFFFFF" }, margin: 0.06, fit: "shrink"
  });
  addFooter(s, p);
  addScript(p, "困难与解决", "开发中最大的困难是培养方案文本复杂，不能简单按总学分相加，所以我们把它转成 Requirement 模型。第二个困难是页面联动，课程变更会影响多个页面，所以采用信号刷新。第三个困难是 CSV 格式不统一，我们按列名识别并跳过错误行。AI 和简历输出也分别做了密钥配置、异常处理和 HTML 转义。");
  notes(s, speaker.at(-1));
}

// 16
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "争议问题与方案取舍", "主动提出边界，说明系统为什么这样设计");
  card(s, 0.75, 1.35, 3.7, 4.55, "争议 1：本地还是云端？", "本项目选择本地 SQLite。理由：学生隐私数据多，桌面版部署简单，离线可用。代价：多设备同步较弱。解决：提供 JSON 备份导入导出，Web/云同步作为后续扩展。", C.teal);
  card(s, 4.82, 1.35, 3.7, 4.55, "争议 2：AI 是否参与学分判断？", "AI 不作为最终学分裁判。理由：培养方案判断应可追溯、可测试。解决：学分审计由本地规则计算，AI 只解释结果和给规划建议。", C.amber);
  card(s, 8.9, 1.35, 3.2, 4.55, "争议 3：代码缺失如何匹配？", "课程代码最可靠，但真实成绩单可能缺失。解决：优先代码，缺失时课程名辅助；不确定就不强算，进入计划外并提示人工核对。", C.blue);
  addFooter(s, p);
  addScript(p, "争议与取舍", "我们主动说明三个取舍。第一，本地还是云端：本项目以桌面版为主，所以选择 SQLite 本地存储，隐私和部署更简单。第二，AI 是否判断学分：我们不让 AI 做最终裁判，因为规则计算更可追溯。第三，课程代码缺失怎么办：优先代码，必要时用课程名辅助，仍不确定就进入计划外，不硬算。");
  notes(s, speaker.at(-1));
}

// 17
p++;
{
  const s = pptx.addSlide(); addBg(s); title(s, "项目过程管理规范", "按卓越软件开发者的习惯：分层、测试、文档、风险透明");
  const items = [
    ["需求管理", "从学分痛点出发，围绕评分项拆解展示重点；每个功能都有明确用户价值。"],
    ["代码组织", "models / database / repositories / services / views / utils 分层，减少跨层耦合。"],
    ["版本演进", "数据库迁移有 _schema_version；新增字段通过 migration 升级。"],
    ["测试验证", "pytest 覆盖模型、GPA、数据导入导出、培养方案审计、实习逻辑等。"],
    ["文档交付", "README、DEPLOY、Q&A、测试用例和示例数据；本次另交付 PPT 与讲稿。"],
    ["风险管理", "如实记录测试失败、AI 密钥风险、CSV 容错边界和后续修复项。"]
  ];
  items.forEach((it, i) => {
    const x = 0.72 + (i % 3) * 4.1, y = 1.28 + Math.floor(i / 3) * 2.1;
    card(s, x, y, 3.55, 1.48, it[0], it[1], [C.green, C.teal, C.blue, C.amber, C.purple, C.red][i]);
  });
  addFooter(s, p);
  addScript(p, "过程管理规范", "过程管理方面，我们不是只看最终界面，而是把项目按需求、架构、实现、测试、文档和风险来管理。代码分层清楚，数据库迁移有版本记录，README 和部署文档说明运行方式。自动化测试覆盖了多个核心模块，同时我们也记录了当前失败项，这符合软件工程里风险透明的要求。");
  notes(s, speaker.at(-1));
}

// 18
p++;
{
  const s = pptx.addSlide(); addBg(s, true);
  s.addText("总结", { x: 0.78, y: 0.9, w: 2.3, h: 0.55, fontSize: 34, bold: true, color: "FFFFFF", margin: 0 });
  s.addText("PDPTool 的价值：把分散的学生发展数据变成可计算、可解释、可输出的规划工具", {
    x: 0.82, y: 1.7, w: 8.8, h: 0.55, fontSize: 17, color: "FDE68A", margin: 0
  });
  card(s, 0.9, 2.75, 3.25, 2.1, "架构清楚", "桌面 UI、业务服务、仓储、SQLite 分层明确，核心逻辑可测试。", C.blue);
  card(s, 4.55, 2.75, 3.25, 2.1, "价值明确", "解决学分分项不清、经历分散、简历输出重复劳动的问题。", C.teal);
  card(s, 8.2, 2.75, 3.25, 2.1, "可持续演进", "AI、刷题、Web 部署、备份迁移都保留扩展边界。", C.amber);
  s.addText("后续优先事项：修复简历导出测试回归；补充 UI 自动化验收；完善 API Key 配置页的脱敏显示。", {
    x: 1.0, y: 5.55, w: 10.9, h: 0.4, fontSize: 13, bold: true, color: "FFFFFF", align: "center", margin: 0
  });
  addScript(p, "总结", "最后总结一下：PDPTool 的重点是把学生分散的数据变成可计算、可解释、可输出的规划工具。架构上采用清晰分层，价值上解决学分分项不清和材料管理分散的问题，扩展上预留了 AI、刷题、备份和 Web 部署方向。后续我们会优先修复简历导出测试回归，并继续补充 UI 自动化验收。");
  notes(s, speaker.at(-1));
}

fs.writeFileSync(scriptPath, `# PDPTool 桌面版答辩讲稿\n\n建议总时长：8-10 分钟。每页按 25-35 秒讲，架构与安全稳定性页可略慢。\n\n${speaker.join("\n")}`, "utf8");

pptx.writeFile({ fileName: pptxPath });
