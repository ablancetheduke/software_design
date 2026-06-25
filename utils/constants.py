"""Application-wide constants."""

APP_NAME = "PDPTool - 个人发展规划工具"
APP_VERSION = "1.0.0"
DB_FILENAME = "pdptool.db"

# Course categories
COURSE_CATEGORIES = ["必修课", "选修课", "通识课"]

# Semester labels
SEMESTERS = [
    "大一上", "大一下",
    "大二上", "大二下",
    "大三上", "大三下",
    "大四上", "大四下",
]

# Grade system
GRADE_SCALE_100 = (0, 100)  # 百分制
GRADE_SCALE_40 = (0.0, 4.0)  # 4.0 绩点制
GRADE_SCALE_50 = (0.0, 5.0)  # 5.0 绩点制

# Experience types
EXPERIENCE_TYPES = ["竞赛", "项目", "实习", "科研", "其他"]

# Achievement types
ACHIEVEMENT_TYPES = ["奖学金", "奖项", "荣誉", "证书", "其他"]

# Role types
ROLE_TYPES = ["班级代表", "模块代表", "志愿者", "社团干部", "学生会", "其他"]

# Export formats
EXPORT_FORMATS = ["CSV", "JSON", "HTML简历"]
