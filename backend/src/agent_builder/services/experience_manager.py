#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Experience Manager - 经验管理器

以文件目录形式存储经验（完整技能）
workspaces/
├── user_id/
│   ├── agent_id/
│   │   ├── skills/          # Agent 专属技能
│   │   ├── experiences/     # 经验（沉淀的技能）
│   │   │   ├── skill_xxx/
│   │   │   │   ├── SKILL.md
│   │   │   │   ├── implement.py
│   │   │   │   └── ...
│   │   │   └── metadata.json
│   │   └── workspace/
"""

import json
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class ExperienceManager:
    """
    经验管理器

    负责：
    1. 创建经验（技能目录）
    2. 列出经验
    3. 读取经验
    4. 删除经验
    5. 复制技能到经验
    """

    def __init__(self, workspaces_dir: str = "./workspaces"):
        self.workspaces_dir = Path(workspaces_dir)

    def _get_agent_experiences_dir(
        self,
        user_id: str,
        agent_id: str
    ) -> Path:
        """获取 Agent 的经验目录"""
        return self.workspaces_dir / user_id / agent_id / "experiences"

    def _ensure_experiences_dir(
        self,
        user_id: str,
        agent_id: str
    ) -> Path:
        """确保经验目录存在"""
        exp_dir = self._get_agent_experiences_dir(user_id, agent_id)
        exp_dir.mkdir(parents=True, exist_ok=True)
        return exp_dir

    def _get_metadata_path(
        self,
        user_id: str,
        agent_id: str
    ) -> Path:
        """获取元数据文件路径"""
        return self._get_agent_experiences_dir(user_id, agent_id) / "metadata.json"

    def _load_metadata(
        self,
        user_id: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """加载元数据"""
        metadata_path = self._get_metadata_path(user_id, agent_id)
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"experiences": []}

    def _save_metadata(
        self,
        user_id: str,
        agent_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """保存元数据"""
        metadata_path = self._get_metadata_path(user_id, agent_id)
        self._ensure_experiences_dir(user_id, agent_id)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    # ==================== 核心操作 ====================

    async def create_experience(
        self,
        user_id: str,
        agent_id: str,
        name: str,
        description: str,
        skill_content: str = "",
        implement_code: str = "",
        task_context: str = "",
        source: str = "agent_created"
    ) -> Dict[str, Any]:
        """
        创建经验

        Args:
            user_id: 用户 ID
            agent_id: Agent ID
            name: 经验/技能名称
            description: 经验描述
            skill_content: SKILL.md 内容
            implement_code: implement.py 代码
            task_context: 任务背景
            source: 来源 (agent_created | downloaded)

        Returns:
            经验信息字典
        """
        experience_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().isoformat()

        # 创建经验目录
        exp_dir = self._ensure_experiences_dir(user_id, agent_id) / f"{name}_{experience_id}"
        exp_dir.mkdir(parents=True, exist_ok=True)

        # 创建 SKILL.md
        if skill_content:
            skill_md = exp_dir / "SKILL.md"
            skill_md.write_text(skill_content, encoding="utf-8")

        # 创建 implement.py
        if implement_code:
            implement_py = exp_dir / "implement.py"
            implement_py.write_text(implement_code, encoding="utf-8")

        # 更新元数据
        metadata = self._load_metadata(user_id, agent_id)
        experience_info = {
            "id": experience_id,
            "name": name,
            "description": description,
            "task_context": task_context,
            "source": source,
            "created_at": timestamp,
            "last_used_at": timestamp,
            "success_count": 0,
            "usage_count": 0,
            "path": str(exp_dir)
        }
        metadata["experiences"].append(experience_info)
        self._save_metadata(user_id, agent_id, metadata)

        return experience_info

    async def copy_skill_to_experience(
        self,
        user_id: str,
        agent_id: str,
        source_skill_path: str,
        name: Optional[str] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        复制技能到经验

        Args:
            user_id: 用户 ID
            agent_id: Agent ID
            source_skill_path: 源技能目录路径
            name: 经验名称（默认使用目录名）
            description: 经验描述

        Returns:
            经验信息字典
        """
        source_path = Path(source_skill_path)
        if not source_path.exists():
            return {
                "success": False,
                "error": f"Source skill not found: {source_skill_path}"
            }

        # 使用目录名作为默认名称
        if not name:
            name = source_path.name

        # 复制技能目录
        exp_dir = self._ensure_experiences_dir(user_id, agent_id) / f"{name}_{str(uuid.uuid4())[:8]}"
        shutil.copytree(source_path, exp_dir, dirs_exist_ok=True)

        # 更新元数据
        metadata = self._load_metadata(user_id, agent_id)
        timestamp = datetime.utcnow().isoformat()
        experience_info = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "description": description or f"Copied from {source_path.name}",
            "task_context": "",
            "source": "copied",
            "created_at": timestamp,
            "last_used_at": timestamp,
            "success_count": 0,
            "usage_count": 0,
            "path": str(exp_dir)
        }
        metadata["experiences"].append(experience_info)
        self._save_metadata(user_id, agent_id, metadata)

        return experience_info

    def list_experiences(
        self,
        user_id: str,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """
        列出所有经验

        Args:
            user_id: 用户 ID
            agent_id: Agent ID

        Returns:
            经验列表
        """
        metadata = self._load_metadata(user_id, agent_id)
        return metadata.get("experiences", [])

    def get_experience(
        self,
        user_id: str,
        agent_id: str,
        experience_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定经验

        Args:
            user_id: 用户 ID
            agent_id: Agent ID
            experience_id: 经验 ID

        Returns:
            经验信息字典
        """
        metadata = self._load_metadata(user_id, agent_id)
        for exp in metadata.get("experiences", []):
            if exp["id"] == experience_id:
                return exp
        return None

    def get_experience_content(
        self,
        user_id: str,
        agent_id: str,
        experience_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取经验内容

        Args:
            user_id: 用户 ID
            agent_id: Agent ID
            experience_id: 经验 ID

        Returns:
            经验内容字典
        """
        exp = self.get_experience(user_id, agent_id, experience_id)
        if not exp:
            return None

        exp_path = Path(exp["path"])
        content = {
            "id": exp["id"],
            "name": exp["name"],
            "description": exp["description"],
            "source": exp["source"],
            "skill_md": "",
            "implement_code": ""
        }

        # 读取 SKILL.md
        skill_md = exp_path / "SKILL.md"
        if skill_md.exists():
            content["skill_md"] = skill_md.read_text(encoding="utf-8")

        # 读取 implement.py
        implement_py = exp_path / "implement.py"
        if implement_py.exists():
            content["implement_code"] = implement_py.read_text(encoding="utf-8")

        return content

    def delete_experience(
        self,
        user_id: str,
        agent_id: str,
        experience_id: str
    ) -> bool:
        """
        删除经验

        Args:
            user_id: 用户 ID
            agent_id: Agent ID
            experience_id: 经验 ID

        Returns:
            是否成功
        """
        metadata = self._load_metadata(user_id, agent_id)
        experiences = metadata.get("experiences", [])

        # 找到并删除
        for i, exp in enumerate(experiences):
            if exp["id"] == experience_id:
                # 删除目录
                exp_path = Path(exp["path"])
                if exp_path.exists():
                    shutil.rmtree(exp_path)

                # 更新元数据
                del experiences[i]
                metadata["experiences"] = experiences
                self._save_metadata(user_id, agent_id, metadata)
                return True

        return False

    def update_experience_stats(
        self,
        user_id: str,
        agent_id: str,
        experience_id: str,
        success: bool = True
    ) -> None:
        """
        更新经验统计

        Args:
            user_id: 用户 ID
            agent_id: Agent ID
            experience_id: 经验 ID
            success: 是否成功
        """
        metadata = self._load_metadata(user_id, agent_id)

        for exp in metadata.get("experiences", []):
            if exp["id"] == experience_id:
                exp["usage_count"] = exp.get("usage_count", 0) + 1
                if success:
                    exp["success_count"] = exp.get("success_count", 0) + 1
                exp["last_used_at"] = datetime.utcnow().isoformat()
                break

        self._save_metadata(user_id, agent_id, metadata)


# 全局实例
_experience_manager: Optional[ExperienceManager] = None


def get_experience_manager(workspaces_dir: str = "./workspaces") -> ExperienceManager:
    """获取经验管理器实例"""
    global _experience_manager
    if _experience_manager is None:
        _experience_manager = ExperienceManager(workspaces_dir)
    return _experience_manager
