"""Parse curriculum plan markdown files into structured AI chunks."""

import re
from pathlib import Path
from typing import Iterable, List

from ..database.repositories.curriculum_plan_repo import CurriculumPlanRepository


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PLAN_FILE = PROJECT_ROOT / "大数据专业培养方案要求学分.md"
CODE_PATTERN = re.compile(r"(?<![A-Z0-9])[A-Z]{2,4}\d{3}(?![A-Z0-9])")


class CurriculumPlanStore:
    """Build and retrieve structured curriculum plan chunks."""

    def __init__(self, repo: CurriculumPlanRepository | None = None):
        self.repo = repo or CurriculumPlanRepository()

    def import_default_plans(self) -> int:
        paths = []
        plans_dir = PROJECT_ROOT / "training_plans"
        if plans_dir.exists():
            paths.extend(sorted(plans_dir.glob("*.md")))
        if DEFAULT_PLAN_FILE.exists():
            paths.append(DEFAULT_PLAN_FILE)
        return self.import_files(paths)

    def import_files(self, paths: Iterable[Path | str]) -> int:
        chunks = []
        for path in paths:
            chunks.extend(self.parse_file(Path(path)))
        return self.repo.replace_chunks(chunks)

    def parse_file(self, path: Path) -> List[dict]:
        text = path.read_text(encoding="utf-8")
        major = self._infer_major(text, path)
        cohort_year = self._infer_cohort_year(text, path)
        chunks: List[dict] = []
        current_module = "总览"
        order = 0

        for raw_line in text.splitlines():
            line = raw_line.strip().strip("`")
            if not line:
                continue

            module_match = re.match(r"^(.{2,30}?课程)\s+(\d+(?:\.\d+)?)\s*$", line)
            if module_match:
                current_module = module_match.group(1).strip()
                order += 1
                chunks.append(self._chunk(
                    major=major,
                    cohort_year=cohort_year,
                    module=current_module,
                    section_title=current_module,
                    required_credits=float(module_match.group(2)),
                    content=line,
                    source_file=str(path),
                    order=order,
                ))
                continue

            item_match = re.match(r"^-\s*(.*?)\s+(\d+(?:\.\d+)?)\s*(.*)$", line)
            if item_match:
                title = item_match.group(1).strip(" -")
                credits = float(item_match.group(2))
                order += 1
                chunks.append(self._chunk(
                    major=major,
                    cohort_year=cohort_year,
                    module=current_module,
                    section_title=title,
                    required_credits=credits,
                    content=line,
                    source_file=str(path),
                    order=order,
                ))

        if not chunks:
            chunks.append(self._chunk(
                major=major,
                cohort_year=cohort_year,
                module="全文",
                section_title=path.stem,
                required_credits=0,
                content=text,
                source_file=str(path),
                order=0,
            ))

        return chunks

    def context_for_ai(
        self,
        major: str = "",
        cohort_year: str = "",
        question: str = "",
        limit: int = 24,
    ) -> str:
        chunks = self.repo.get_chunks(major=major, cohort_year=cohort_year, limit=limit)
        if not chunks and (major or cohort_year):
            chunks = self.repo.get_all_chunks(limit=limit)
        if not chunks:
            return "暂无结构化培养方案。"

        if question:
            chunks = self._rank_chunks(chunks, question)[:limit]

        lines = []
        for chunk in chunks:
            lines.append(
                f"[{chunk['major']} {chunk['cohort_year']} | {chunk['module']} | "
                f"{chunk['section_title']} | {chunk['required_credits']:g}学分]\n"
                f"{chunk['content']}"
            )
        return "\n\n".join(lines)

    @staticmethod
    def _chunk(
        major: str,
        cohort_year: str,
        module: str,
        section_title: str,
        required_credits: float,
        content: str,
        source_file: str,
        order: int,
    ) -> dict:
        return {
            "major": major,
            "cohort_year": cohort_year,
            "module": module,
            "section_title": section_title,
            "required_credits": required_credits,
            "course_codes": sorted(set(CODE_PATTERN.findall(content.upper()))),
            "content": content,
            "source_file": source_file,
            "chunk_order": order,
        }

    @staticmethod
    def _infer_major(text: str, path: Path) -> str:
        for pattern in (
            r"([\u4e00-\u9fa5A-Za-z0-9（）()]+专业)",
            r"专业[:：]\s*([\u4e00-\u9fa5A-Za-z0-9（）()]+)",
        ):
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        name_match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9（）()]+专业)", path.stem)
        return name_match.group(1) if name_match else path.stem

    @staticmethod
    def _infer_cohort_year(text: str, path: Path) -> str:
        match = re.search(r"(20\d{2})", path.stem)
        if match:
            return match.group(1)
        for pattern in (r"(20\d{2})\s*级", r"(20\d{2})\s*版", r"(20\d{2})"):
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""

    @staticmethod
    def _rank_chunks(chunks: List[dict], question: str) -> List[dict]:
        keywords = [
            word for word in re.split(r"[\s,，。；;：:？?、/]+", question)
            if len(word) >= 2
        ]
        aliases = {
            "通识": ["通识", "美育", "核心通识", "非美育"],
            "通修": ["通修", "英语", "体育", "数学", "政治", "经管法", "职业发展"],
            "专业": ["专业", "学科基础", "方向必修", "专业选修"],
            "毕业": ["总学分", "通识", "通修", "专业"],
            "学分": ["学分"],
            "英语": ["英语", "ENG"],
            "体育": ["体育", "PED"],
            "数学": ["数学", "MAT", "概率", "线性代数"],
            "实习": ["职业发展", "创新创业"],
        }
        expanded = set(keywords)
        for key, values in aliases.items():
            if key in question:
                expanded.update(values)

        def score(chunk: dict) -> int:
            text = " ".join([
                chunk.get("module", ""),
                chunk.get("section_title", ""),
                chunk.get("content", ""),
                ",".join(chunk.get("course_codes", [])),
            ])
            value = 0
            for word in expanded:
                if word and word in text:
                    value += 4
            if chunk.get("module") in ("通识课程", "通修课程", "专业课程"):
                value += 1
            return value

        return sorted(chunks, key=lambda item: (-score(item), item.get("chunk_order", 0)))
