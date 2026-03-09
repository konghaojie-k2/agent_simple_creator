#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill System - 技能系统

实现 Mini-Agent 风格的渐进式披露：
1. Level 1: 系统提示包含技能元数据
2. Level 2: get_skill 工具按需加载完整内容
"""

import re
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Skill:
    """技能数据"""
    name: str
    description: str
    content: str
    allowed_tools: Optional[List[str]] = None
    skill_path: Optional[Path] = None

    def to_prompt(self) -> str:
        """转换为提示格式"""
        skill_root = str(self.skill_path.parent) if self.skill_path else "unknown"
        return f"""
# Skill: {self.name}

{self.description}

**Skill Root Directory:** `{skill_root}`

---

{self.content}
"""


class SkillLoader:
    """技能加载器"""

    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.loaded_skills: Dict[str, Skill] = {}

    def load_skill(self, skill_path: Path) -> Optional[Skill]:
        """从 SKILL.md 加载技能"""
        try:
            content = skill_path.read_text(encoding="utf-8")

            # 解析 YAML frontmatter
            frontmatter_match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
            if not frontmatter_match:
                return None

            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            skill_content = frontmatter_match.group(2).strip()

            return Skill(
                name=frontmatter["name"],
                description=frontmatter["description"],
                content=skill_content,
                allowed_tools=frontmatter.get("allowed-tools"),
                skill_path=skill_path
            )
        except Exception as e:
            print(f"Failed to load skill {skill_path}: {e}")
            return None

    def discover_skills(self) -> List[Skill]:
        """发现所有技能"""
        skills = []
        if not self.skills_dir.exists():
            return skills

        for skill_file in self.skills_dir.rglob("SKILL.md"):
            skill = self.load_skill(skill_file)
            if skill:
                skills.append(skill)
                self.loaded_skills[skill.name] = skill

        return skills

    def get_skill(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self.loaded_skills.get(name)

    def list_skills(self) -> List[str]:
        """列出所有技能名称"""
        return list(self.loaded_skills.keys())

    def get_metadata_prompt(self) -> str:
        """
        Level 1: 生成技能元数据提示
        只包含名称和描述，用于系统提示
        """
        if not self.loaded_skills:
            return ""

        lines = ["## Available Skills\n"]
        lines.append("You can load a skill's full content using the `get_skill` tool when needed.\n")

        for skill in self.loaded_skills.values():
            lines.append(f"- `{skill.name}`: {skill.description}")

        return "\n".join(lines)


class AgentSkillSystem:
    """
    Agent 技能系统

    管理 Agent 的所有技能来源：
    1. 共享技能（shared_skills/）
    2. Agent 专属技能（workspaces/{user}/{agent}/skills/）
    3. 沉淀的经验（workspaces/{user}/{agent}/experiences/）
    """

    def __init__(
        self,
        user_id: str,
        agent_id: str,
        shared_skills_dir: str = "./market/skills",
        workspaces_dir: str = "./workspaces"
    ):
        self.user_id = user_id
        self.agent_id = agent_id

        # 多个技能来源
        # 1. 公开共享技能 (market/skills/public)
        self.public_loader = SkillLoader(f"{shared_skills_dir}/public")
        # 2. 私有共享技能 (market/skills/private) - 只有登录用户可用
        self.private_loader = SkillLoader(f"{shared_skills_dir}/private")
        # 3. Agent专属技能 (workspaces/{user}/{agent}/skills)
        self.agent_loader = SkillLoader(
            f"{workspaces_dir}/{user_id}/{agent_id}/skills"
        )
        # 4. 经验沉淀 (workspaces/{user}/{agent}/experiences)
        self.experience_loader = SkillLoader(
            f"{workspaces_dir}/{user_id}/{agent_id}/experiences"
        )

        # 加载所有技能
        self._load_all_skills()

    def _load_all_skills(self):
        """加载所有来源的技能"""
        self.public_loader.discover_skills()
        self.private_loader.discover_skills()
        self.agent_loader.discover_skills()
        self.experience_loader.discover_skills()

    def get_system_prompt(self) -> str:
        """
        生成系统提示（包含技能元数据）
        这是 Level 1 渐进式披露
        """
        parts = []

        # 公开共享技能
        public_prompt = self.public_loader.get_metadata_prompt()
        if public_prompt:
            parts.append(public_prompt)

        # 私有共享技能
        private_prompt = self.private_loader.get_metadata_prompt()
        if private_prompt:
            parts.append(private_prompt)

        # Agent 专属技能
        agent_prompt = self.agent_loader.get_metadata_prompt()
        if agent_prompt:
            parts.append("\n### Your Custom Skills\n")
            parts.append(agent_prompt)

        # 沉淀的经验
        exp_prompt = self.experience_loader.get_metadata_prompt()
        if exp_prompt:
            parts.append("\n### Your Experiences\n")
            parts.append(exp_prompt)

        return "\n\n".join(parts)

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Level 2: 获取技能完整内容
        按优先级搜索：经验 > Agent技能 > 私有共享 > 公开共享
        """
        # 1. 先搜索经验
        skill = self.experience_loader.get_skill(name)
        if skill:
            return skill

        # 2. 再搜索 Agent 专属技能
        skill = self.agent_loader.get_skill(name)
        if skill:
            return skill

        # 3. 搜索私有共享技能
        skill = self.private_loader.get_skill(name)
        if skill:
            return skill

        # 4. 最后搜索公开共享技能
        return self.public_loader.get_skill(name)

    def list_all_skills(self) -> List[str]:
        """列出所有可用技能"""
        skills = set()
        skills.update(self.public_loader.list_skills())
        skills.update(self.private_loader.list_skills())
        skills.update(self.agent_loader.list_skills())
        skills.update(self.experience_loader.list_skills())
        return sorted(list(skills))
