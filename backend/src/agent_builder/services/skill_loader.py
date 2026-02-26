#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件系统技能加载器
支持从 skills/ 目录动态加载技能

支持两种格式：
1. SKILL.md - 提示词模板（Mini-Agent 格式）
2. skill.json + implement.py - 可执行技能
"""

import os
import json
import importlib.util
import inspect
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass


@dataclass
class SkillDefinition:
    """技能定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Optional[Callable] = None  # 异步处理函数（可选）
    source_type: str = "native"  # native | mcp | custom | prompt
    content: str = ""  # 技能内容（用于 prompt 类型的技能）


class FileSystemSkillLoader:
    """
    文件系统技能加载器

    从指定目录加载技能，支持两种格式：
    1. Python 模块 (skill.py) - 定义 name, description, parameters, execute
    2. Skill Manifest (skill.json) + 实现文件
    """

    def __init__(self, skills_dir: Optional[str] = None):
        """
        初始化技能加载器

        Args:
            skills_dir: 技能目录路径，默认为项目根目录下的 skills/
        """
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            # skill_loader.py 在 backend/src/agent_builder/services/
            # 向上 4 级: services -> agent_builder -> src -> backend -> 项目根
            self._root = Path(__file__).parent.parent.parent.parent
            self.skills_dir = self._root / "skills"

            # 如果 backend/skills 不存在，尝试项目根目录的 skills
            if not self.skills_dir.exists():
                # 尝试上一级（以防万一）
                self.skills_dir = self._root.parent / "skills"

        self._loaded_skills: Dict[str, SkillDefinition] = {}

    def discover_skills(self) -> List[SkillDefinition]:
        """
        发现并加载所有技能

        支持两种格式：
        1. skill.json + implement.py - 可执行技能
        2. SKILL.md - 提示词模板（Mini-Agent 格式）

        Returns:
            技能定义列表
        """
        if not self.skills_dir.exists():
            return []

        skills = []

        # 扫描所有子目录
        for item in self.skills_dir.iterdir():
            if not item.is_dir():
                continue

            # 跳过隐藏目录
            if item.name.startswith("."):
                continue

            skill = self._load_skill_from_directory(item)
            if skill:
                self._loaded_skills[skill.name] = skill
                skills.append(skill)

        # 也检查是否有 SKILL.md 在根目录（链接外部技能）
        root_skill_md = self.skills_dir / "SKILL.md"
        if root_skill_md.exists():
            skill = self._load_skill_md(root_skill_md)
            if skill:
                self._loaded_skills[skill.name] = skill
                skills.append(skill)

        return skills

    def _load_skill_from_directory(self, skill_dir: Path) -> Optional[SkillDefinition]:
        """
        从目录加载技能

        期望目录结构:
        skill_name/
            skill.json    # 技能元数据
            implement.py  # 实现代码 (可选)
        或者:
        skill_name/
            SKILL.md     # Mini-Agent 格式
        """
        # 优先检查 SKILL.md (Mini-Agent 格式)
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            return self._load_skill_md(skill_md)

        # 然后检查 skill.json
        skill_json = skill_dir / "skill.json"
        if not skill_json.exists():
            return None

        try:
            with open(skill_json, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"Failed to load skill.json from {skill_dir}: {e}")
            return None

        name = metadata.get("name", skill_dir.name)
        description = metadata.get("description", "")
        parameters = metadata.get("parameters", {})

        # 2. 查找实现文件
        implement_file = skill_dir / "implement.py"
        handler = None

        if implement_file.exists():
            handler = self._load_handler_from_file(implement_file, name)
        else:
            # 如果没有实现文件，创建一个默认的空处理
            handler = self._create_default_handler(name, metadata)

        if not handler:
            return None

        return SkillDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            source_type="native"
        )

    def _load_skill_md(self, skill_md: Path) -> Optional[SkillDefinition]:
        """
        从 SKILL.md 文件加载技能（Mini-Agent 格式）

        SKILL.md 格式:
        ---
        name: skill-name
        description: 技能描述
        allowed_tools:
          - tool1
          - tool2
        ---
        技能内容...
        """
        try:
            content = skill_md.read_text(encoding="utf-8")

            # 解析 YAML frontmatter
            frontmatter_match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)

            if not frontmatter_match:
                # 没有 frontmatter，使用文件名作为名称
                name = skill_md.stem.lower().replace("-", "_")
                description = "Skill from SKILL.md"
                skill_content = content
            else:
                frontmatter_text = frontmatter_match.group(1)
                skill_content = frontmatter_match.group(2).strip()

                # 解析 YAML（简化版）
                import yaml
                try:
                    frontmatter = yaml.safe_load(frontmatter_text)
                except:
                    frontmatter = {}

                name = frontmatter.get("name", skill_md.stem.lower().replace("-", "_"))
                description = frontmatter.get("description", "")

            return SkillDefinition(
                name=name,
                description=description,
                parameters={},
                handler=None,  # prompt 类型技能没有 handler
                source_type="prompt",
                content=skill_content
            )

        except Exception as e:
            print(f"Failed to load SKILL.md from {skill_md}: {e}")
            return None

    def _load_handler_from_file(self, implement_file: Path, skill_name: str) -> Optional[Callable]:
        """从 Python 文件加载处理函数"""
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(f"skill_{skill_name}", implement_file)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找 execute 函数
            if hasattr(module, "execute"):
                return module.execute
            elif hasattr(module, "handler"):
                return module.handler
            else:
                # 查找任何异步函数
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and inspect.iscoroutinefunction(attr):
                        return attr

            return None

        except Exception as e:
            print(f"Failed to load handler from {implement_file}: {e}")
            return None

    def _create_default_handler(self, name: str, metadata: Dict) -> Callable:
        """创建默认处理函数"""
        async def default_handler(**kwargs) -> Dict[str, Any]:
            return {
                "success": True,
                "skill": name,
                "message": f"Skill '{name}' executed with params: {kwargs}",
                "metadata": metadata
            }
        return default_handler

    def get_skill(self, name: str) -> Optional[SkillDefinition]:
        """获取指定技能"""
        # 如果还没加载，先发现
        if not self._loaded_skills:
            self.discover_skills()
        return self._loaded_skills.get(name)

    def list_skills(self) -> List[str]:
        """列出所有已加载的技能"""
        if not self._loaded_skills:
            self.discover_skills()
        return list(self._loaded_skills.keys())

    async def execute_skill(
        self,
        name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行技能"""
        skill = self.get_skill(name)
        if not skill:
            return {
                "success": False,
                "error": f"Skill not found: {name}"
            }

        try:
            result = await skill.handler(**parameters)
            return result if isinstance(result, dict) else {"success": True, "result": result}
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "skill": name
            }


class SkillRegistry:
    """
    统一的技能注册表

    整合：
    1. 内置工具 (tool_registry.py)
    2. 文件系统技能 (FileSystemSkillLoader)
    3. MCP 技能 (后续集成)
    """

    def __init__(self, skills_dir: Optional[str] = None):
        self.fs_loader = FileSystemSkillLoader(skills_dir)
        self._native_tools = self._load_native_tools()
        self._discovered_skills: Dict[str, SkillDefinition] = {}

    def _load_native_tools(self) -> Dict[str, SkillDefinition]:
        """加载内置工具"""
        from agent_builder.services.tool_registry import get_tool_registry

        tools = {}

        # 延迟获取 registry，避免循环导入
        def create_tool_handler(tool_name: str):
            async def handler(**kwargs):
                registry = get_tool_registry()
                return await registry.execute_tool(tool_name, kwargs)
            return handler

        # 假设工具列表（实际从 registry 获取）
        registry = get_tool_registry()
        for tool_name in registry.list_tools():
            tools[tool_name] = SkillDefinition(
                name=tool_name,
                description=f"Built-in tool: {tool_name}",
                parameters={},
                handler=create_tool_handler(tool_name),
                source_type="native"
            )
        return tools

    def discover_all_skills(self) -> None:
        """发现所有技能"""
        # 发现文件系统技能
        fs_skills = self.fs_loader.discover_skills()
        for skill in fs_skills:
            self._discovered_skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[SkillDefinition]:
        """获取技能"""
        # 优先检查内置工具
        if name in self._native_tools:
            return self._native_tools[name]

        # 然后检查文件系统技能
        if name in self._discovered_skills:
            return self._discovered_skills[name]

        # 尝试动态加载
        skill = self.fs_loader.get_skill(name)
        if skill:
            self._discovered_skills[name] = skill
            return skill

        return None

    def list_all_skills(self) -> List[str]:
        """列出所有技能"""
        self.discover_all_skills()

        all_skills = set(self._native_tools.keys())
        all_skills.update(self._discovered_skills.keys())
        return sorted(list(all_skills))

    async def execute_skill(
        self,
        name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行技能"""
        skill = self.get_skill(name)
        if not skill:
            return {
                "success": False,
                "error": f"Skill not found: {name}"
            }

        try:
            result = await skill.handler(**parameters)
            return result if isinstance(result, dict) else {"success": True, "result": result}
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "skill": name
            }


# 全局技能注册表
_global_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry(skills_dir: Optional[str] = None) -> SkillRegistry:
    """获取技能注册表实例"""
    global _global_skill_registry
    if _global_skill_registry is None:
        _global_skill_registry = SkillRegistry(skills_dir)
    return _global_skill_registry
