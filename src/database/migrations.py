"""Database schema creation and migration.
follows the same structure: check version → apply → record).
"""

from .connection import DatabaseConnection


class Migration:
    """Handles database schema initialization and migration."""

    VERSION = 4

    @staticmethod
    def run(db: DatabaseConnection = None):
        """Run all pending migrations."""
        if db is None:
            db = DatabaseConnection.get_instance()

        # Create version table
        db.execute("""
            CREATE TABLE IF NOT EXISTS _schema_version (
                version INTEGER PRIMARY KEY
            )
        """)

        current = db.fetch_one("SELECT MAX(version) FROM _schema_version")
        current_version = current[0] if current and current[0] else 0

        if current_version < 1:
            Migration._migrate_v1(db)
        if current_version < 2:
            Migration._migrate_v2(db)
        if current_version < 3:
            Migration._migrate_v3(db)
        if current_version < 4:
            Migration._migrate_v4(db)

    @staticmethod
    def _migrate_v1(db: DatabaseConnection):
        """Initial schema: all core tables."""

        # Student profile
        db.execute("""
            CREATE TABLE IF NOT EXISTS student (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '',
                student_no TEXT DEFAULT '',
                college TEXT DEFAULT '',
                major TEXT DEFAULT '',
                enrollment_year TEXT DEFAULT '',
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                github TEXT DEFAULT '',
                linkedin TEXT DEFAULT '',
                skills TEXT DEFAULT '',
                summary TEXT DEFAULT ''
            )
        """)

        # Courses
        db.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT DEFAULT '',
                credit REAL DEFAULT 0.0,
                semester TEXT DEFAULT '',
                grade REAL DEFAULT 0.0,
                category TEXT DEFAULT '必修课',
                note TEXT DEFAULT ''
            )
        """)

        # Experiences
        db.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                exp_type TEXT DEFAULT '项目',
                organization TEXT DEFAULT '',
                start_date TEXT DEFAULT '',
                end_date TEXT DEFAULT '',
                description TEXT DEFAULT '',
                role TEXT DEFAULT '',
                outcome TEXT DEFAULT ''
            )
        """)

        # Achievements
        db.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                ach_type TEXT DEFAULT '奖项',
                issuer TEXT DEFAULT '',
                date TEXT DEFAULT '',
                description TEXT DEFAULT ''
            )
        """)

        # Roles
        db.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                role_type TEXT DEFAULT '志愿者',
                organization TEXT DEFAULT '',
                start_date TEXT DEFAULT '',
                end_date TEXT DEFAULT '',
                description TEXT DEFAULT ''
            )
        """)

        # Record migration version
        db.execute(
            "INSERT INTO _schema_version (version) VALUES (?)",
            (1,)
        )

    @staticmethod
    def _migrate_v2(db: DatabaseConnection):
        """Internship application tracking table."""
        db.execute("""
            CREATE TABLE IF NOT EXISTS internship_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                position TEXT NOT NULL,
                direction TEXT DEFAULT '',
                apply_date TEXT DEFAULT '',
                deadline TEXT DEFAULT '',
                status TEXT DEFAULT '待投递',
                link TEXT DEFAULT '',
                note TEXT DEFAULT '',
                resume_ready INTEGER DEFAULT 0,
                project_ready INTEGER DEFAULT 0,
                reviewed INTEGER DEFAULT 0
            )
        """)
        db.execute(
            "INSERT INTO _schema_version (version) VALUES (?)",
            (2,)
        )

    @staticmethod
    def _migrate_v3(db: DatabaseConnection):
        """Structured curriculum plan chunks for AI retrieval."""
        db.execute("""
            CREATE TABLE IF NOT EXISTS curriculum_plan_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                major TEXT NOT NULL,
                cohort_year TEXT NOT NULL DEFAULT '',
                module TEXT NOT NULL DEFAULT '',
                section_title TEXT NOT NULL DEFAULT '',
                required_credits REAL DEFAULT 0.0,
                course_codes TEXT DEFAULT '',
                content TEXT NOT NULL,
                source_file TEXT DEFAULT '',
                chunk_order INTEGER DEFAULT 0,
                UNIQUE(major, cohort_year, module, section_title, source_file, chunk_order)
            )
        """)
        db.execute(
            "INSERT INTO _schema_version (version) VALUES (?)",
            (3,)
        )


    @staticmethod
    def _migrate_v4(db: DatabaseConnection):
        """Interview tracking fields on internship_applications."""
        db.execute(
            "ALTER TABLE internship_applications ADD COLUMN interview_date TEXT DEFAULT ''"
        )
        db.execute(
            "ALTER TABLE internship_applications ADD COLUMN interview_notes TEXT DEFAULT ''"
        )
        db.execute(
            "INSERT INTO _schema_version (version) VALUES (?)",
            (4,)
        )


def init_database(db_path: str = None):
    """Initialize the database: create connection and run migrations."""
    db = DatabaseConnection.get_instance(db_path)
    Migration.run(db)
    # Ensure there's a student record
    existing = db.fetch_one("SELECT COUNT(*) FROM student")
    if existing and existing[0] == 0:
        db.execute(
            "INSERT INTO student (name) VALUES (?)",
            ("未设置",)
        )
    try:
        from ..services.curriculum_plan_store import CurriculumPlanStore
        CurriculumPlanStore().import_default_plans()
    except (OSError, ImportError, ValueError):
        pass  # curriculum plan import must not block app startup
    return db
