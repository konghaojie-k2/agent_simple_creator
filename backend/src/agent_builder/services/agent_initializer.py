#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 初始化服务

负责创建Agent的目录结构：
workspaces/
├── user_id/
│   └── agent_id/
│       ├── skills/          # Agent 专属技能
│       ├── experiences/     # 经验（沉淀的技能）
│       └── workspace/       # 工作目录
"""

import shutil
from pathlib import Path
from typing import Optional, List


class AgentInitializer:
    """
    Agent 初始化器

    负责创建Agent所需的目录结构
    """

    def __init__(self, workspaces_dir: str = "./workspaces"):
        self.workspaces_dir = Path(workspaces_dir)

    def _get_agent_dir(self, user_id: str, agent_id: str) -> Path:
        """获取Agent目录"""
        return self.workspaces_dir / user_id / agent_id

    def initialize_agent_directories(
        self,
        user_id: str,
        agent_id: str
    ) -> dict:
        """
        初始化Agent目录结构

        Args:
            user_id: 用户ID
            agent_id: Agent ID

        Returns:
            创建的路径信息
        """
        agent_dir = self._get_agent_dir(user_id, agent_id)

        # 创建子目录
        skills_dir = agent_dir / "skills"
        experiences_dir = agent_dir / "experiences"
        workspace_dir = agent_dir / "workspace"

        skills_dir.mkdir(parents=True, exist_ok=True)
        experiences_dir.mkdir(parents=True, exist_ok=True)
        workspace_dir.mkdir(parents=True, exist_ok=True)

        return {
            "agent_dir": str(agent_dir),
            "skills_dir": str(skills_dir),
            "experiences_dir": str(experiences_dir),
            "workspace_dir": str(workspace_dir)
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
            "skills_dir": str(agent_dir / "skills"),
            "experiences_dir": str(agent_dir / "experiences"),
            "workspace_dir": str(agent_dir / "workspace")
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
        shared_skills_dir: str = "./skills"
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


# 全局实例
_agent_initializer: Optional[AgentInitializer] = None


def get_agent_initializer(workspaces_dir: str = "./workspaces") -> AgentInitializer:
    """获取Agent初始化器实例"""
    global _agent_initializer
    if _agent_initializer is None:
        _agent_initializer = AgentInitializer(workspaces_dir)
    return _agent_initializer
