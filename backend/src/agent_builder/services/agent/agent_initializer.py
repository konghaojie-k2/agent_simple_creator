#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 初始化服务

负责创建Agent的目录结构：
workspaces/
├── user_id/
│   ├── agents/             # Agent身份存储（无状态）
│   │   └── agent_id/
│   │       ├── profile.json  # Agent配置
│   │       ├── skills/       # Agent技能（能力）
│   │       └── experiences/  # Agent经验（沉淀）
│   └── experiments/         # 实验工作空间（单Agent或多Agent）
│       └── experiment_id/
│           ├── manifest.json
│           ├── config/
│           ├── shared/
│           ├── workspace/
│           └── results/

架构原则：
- Agent = 身份 + 能力 + 经验（无独立工作空间）
- Experiment = 工作任务的载体（提供工作空间）
- 单Agent实验 = Agent的"临时工作空间"
- 多Agent实验 = 协作共享空间
"""

import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class AgentInitializer:
    """
    Agent 初始化器

    负责创建Agent的目录结构（仅存储身份和能力，无工作空间）
    """

    def __init__(self, workspaces_dir: str = "./workspaces"):
        self.workspaces_dir = Path(workspaces_dir)

    def _get_agents_base_dir(self, user_id: str) -> Path:
        """获取用户Agents的基础目录"""
        return self.workspaces_dir / user_id / "agents"

    def _get_agent_dir(self, user_id: str, agent_id: str) -> Path:
        """获取Agent目录"""
        return self._get_agents_base_dir(user_id) / agent_id

    def initialize_agent_directories(
        self,
        user_id: str,
        agent_id: str,
        name: str = "",
        description: str = ""
    ) -> dict:
        """
        初始化Agent目录结构

        Args:
            user_id: 用户ID
            agent_id: Agent ID
            name: Agent名称
            description: Agent描述

        Returns:
            创建的路径信息
        """
        agent_dir = self._get_agent_dir(user_id, agent_id)

        # 确保workspaces根目录存在
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录（身份、能力、经验、工作空间）
        skills_dir = agent_dir / "skills"
        experiences_dir = agent_dir / "experiences"
        workspace_dir = agent_dir / "workspace"

        skills_dir.mkdir(parents=True, exist_ok=True)
        experiences_dir.mkdir(parents=True, exist_ok=True)
        workspace_dir.mkdir(parents=True, exist_ok=True)

        # 创建Agent配置文件
        profile_path = agent_dir / "profile.json"
        if not profile_path.exists():
            profile = {
                "agent_id": agent_id,
                "name": name,
                "description": description,
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)

        return {
            "agent_dir": str(agent_dir),
            "profile_path": str(profile_path),
            "skills_dir": str(skills_dir),
            "experiences_dir": str(experiences_dir)
        }

    def get_agent_directories(
        self,
        user_id: str,
        agent_id: str
    ) -> dict:
        """
        获取Agent目录路径

        Args:
            user_id: 用户ID
            agent_id: Agent ID

        Returns:
            路径信息字典
        """
        agent_dir = self._get_agent_dir(user_id, agent_id)

        return {
            "agent_dir": str(agent_dir),
            "profile_path": str(agent_dir / "profile.json"),
            "skills_dir": str(agent_dir / "skills"),
            "experiences_dir": str(agent_dir / "experiences")
        }

    def ensure_agent_directories(
        self,
        user_id: str,
        agent_id: str
    ) -> dict:
        """
        确保Agent目录存在

        Args:
            user_id: 用户ID
            agent_id: Agent ID

        Returns:
            路径信息字典
        """
        return self.initialize_agent_directories(user_id, agent_id)

    def copy_shared_skills_to_agent(
        self,
        user_id: str,
        agent_id: str,
        shared_skills_dir: str = "./market/skills"
    ) -> List[str]:
        """
        将共享技能目录下的所有技能复制到Agent的skills目录

        Args:
            user_id: 用户ID
            agent_id: Agent ID
            shared_skills_dir: 共享技能目录路径

        Returns:
            复制的技能目录名称列表
        """
        agent_skills_dir = self._get_agent_dir(user_id, agent_id) / "skills"
        shared_dir = Path(shared_skills_dir)

        if not shared_dir.exists():
            return []

        copied_skills = []

        # 遍历共享技能目录
        for item in shared_dir.iterdir():
            if not item.is_dir():
                continue

            # 跳过隐藏目录
            if item.name.startswith("."):
                continue

            # 目标路径
            dest_path = agent_skills_dir / item.name

            # 如果已存在则跳过
            if dest_path.exists():
                continue

            # 复制整个目录
            shutil.copytree(item, dest_path)
            copied_skills.append(item.name)

        return copied_skills

    def get_agent_profile(
        self,
        user_id: str,
        agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取Agent配置信息"""
        profile_path = self._get_agent_dir(user_id, agent_id) / "profile.json"
        if not profile_path.exists():
            return None

        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def update_agent_profile(
        self,
        user_id: str,
        agent_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新Agent配置信息"""
        profile = self.get_agent_profile(user_id, agent_id) or {}
        profile.update(updates)
        profile["updated_at"] = datetime.utcnow().isoformat()

        profile_path = self._get_agent_dir(user_id, agent_id) / "profile.json"
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

        return profile


# 全局实例
_agent_initializer: Optional[AgentInitializer] = None


def get_agent_initializer(workspaces_dir: str = "./workspaces") -> AgentInitializer:
    """获取Agent初始化器实例"""
    global _agent_initializer
    if _agent_initializer is None:
        _agent_initializer = AgentInitializer(workspaces_dir)
    return _agent_initializer
