#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 技能服务
完整的技能生命周期管理：发现 -> 加载 -> 执行
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from agent_builder.db.models import AgentSkill, Agent, MCPServerConfig
from agent_builder.services.mcp_client_manager import MCPClientManager


@dataclass
class SkillMatch:
    """技能匹配结果"""
    server_name: str
    tool_name: str
    description: str
    match_score: float
    input_schema: Dict[str, Any]


class SkillService:
    """
    Agent 技能服务

    提供：
    1. 技能发现 - 在 MCP Servers 中搜索匹配的工具
    2. 技能加载 - 将发现的工具安装到 Agent 技能库
    3. 技能执行 - 从 Agent 技能库调用技能
    4. 技能管理 - 列出、卸载、更新技能
    """

    def __init__(
        self,
        db: AsyncSession,
        mcp_manager: Optional[MCPClientManager] = None
    ):
        self.db = db
        self.mcp_manager = mcp_manager or MCPClientManager()

    # ========== 技能发现 ==========

    async def discover_skills(
        self,
        user_id: str,
        agent_id: str,
        capability_need: str,
        top_k: int = 5
    ) -> List[SkillMatch]:
        """
        在用户的 MCP Servers 中搜索匹配的技能

        流程：
        1. 获取用户可用的 MCP Servers
        2. 连接到每个 Server 列出工具
        3. 计算匹配分数
        4. 返回排序后的结果
        """
        # 获取用户配置且允许此 Agent 使用的 MCP Servers
        configs = await self._get_user_mcp_configs(user_id, agent_id)

        all_matches = []

        for config in configs:
            try:
                # 连接并列出工具
                session = await self.mcp_manager.connect_server(user_id, config)
                tools = await self.mcp_manager.list_tools(user_id, config.name)

                for tool in tools:
                    score = self._calculate_match(
                        capability_need,
                        tool["name"],
                        tool["description"]
                    )

                    if score > 0.3:
                        all_matches.append(SkillMatch(
                            server_name=config.name,
                            tool_name=tool["name"],
                            description=tool["description"],
                            match_score=score,
                            input_schema=tool["input_schema"]
                        ))

            except Exception as e:
                print(f"Failed to list tools from {config.name}: {e}")
                continue

        all_matches.sort(key=lambda x: x.match_score, reverse=True)
        return all_matches[:top_k]

    # ========== 技能加载 ==========

    async def load_skill(
        self,
        agent_id: str,
        user_id: str,
        source_server: str,
        source_tool: str,
        custom_name: Optional[str] = None,
        description: Optional[str] = None,
        wrapper_config: Optional[Dict[str, Any]] = None
    ) -> Optional[AgentSkill]:
        """
        将 MCP 工具加载到 Agent 技能库

        Args:
            agent_id: Agent ID
            user_id: 用户 ID（权限验证）
            source_server: MCP Server 名称
            source_tool: 原始工具名
            custom_name: 自定义技能名（可选，默认使用 tool_name）
            description: 自定义描述（可选）
            wrapper_config: 封装配置（可选）
                {
                    "default_values": {...},
                    "parameter_mapping": {...}
                }

        Returns:
            AgentSkill 实例
        """
        import uuid

        # 验证 Agent 属于用户
        agent_result = await self.db.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.user_id == user_id
            )
        )
        agent = agent_result.scalar_one_or_none()
        if not agent:
            return None

        # 检查是否已加载
        existing = await self._get_agent_skill_by_source(
            agent_id, source_server, source_tool
        )
        if existing:
            # 已存在，返回现有技能
            return existing

        # 从 MCP Server 获取工具详情
        try:
            tool_info = await self._get_tool_info(user_id, source_server, source_tool)
        except Exception as e:
            print(f"Failed to get tool info: {e}")
            return None

        # 创建 AgentSkill
        agent_skill = AgentSkill(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            source_type="mcp",
            source_server=source_server,
            source_tool=source_tool,
            name=custom_name or source_tool,
            description=description or tool_info.get("description", ""),
            parameters_schema=tool_info.get("input_schema", {}),
            default_values=wrapper_config.get("default_values") if wrapper_config else None,
            call_count=0,
            success_count=0
        )

        self.db.add(agent_skill)
        await self.db.commit()
        await self.db.refresh(agent_skill)

        return agent_skill

    # ========== 技能执行 ==========

    async def execute_skill(
        self,
        agent_id: str,
        user_id: str,
        skill_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行 Agent 技能库中的技能

        Args:
            agent_id: Agent ID
            user_id: 用户 ID（权限验证）
            skill_name: 技能名（AgentSkill.name）
            parameters: 调用参数

        Returns:
            执行结果
        """
        # 获取技能
        skill = await self._get_agent_skill_by_name(agent_id, user_id, skill_name)
        if not skill:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found in agent's skill library"
            }

        # 合并默认参数
        final_params = self._merge_parameters(skill.default_values, parameters)

        # 执行
        try:
            result = await self.mcp_manager.call_tool(
                user_id=user_id,
                server_name=skill.source_server,
                tool_name=skill.source_tool,
                arguments=final_params
            )

            # 更新统计
            skill.call_count += 1
            skill.last_used_at = datetime.utcnow()

            is_success = not result.get("is_error", False)
            if is_success:
                skill.success_count += 1

            await self.db.commit()

            return {
                "success": is_success,
                "result": result,
                "skill_used": skill_name,
                "call_count": skill.call_count
            }

        except Exception as e:
            skill.call_count += 1
            await self.db.commit()
            return {
                "success": False,
                "error": str(e),
                "skill_used": skill_name
            }

    # ========== 技能管理 ==========

    async def list_agent_skills(
        self,
        agent_id: str,
        user_id: str
    ) -> List[AgentSkill]:
        """列出 Agent 的所有技能"""
        result = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.agent_id == agent_id,
                AgentSkill.user_id == user_id
            ).order_by(AgentSkill.call_count.desc())
        )
        return list(result.scalars().all())

    async def get_skill(self, skill_id: str, user_id: str) -> Optional[AgentSkill]:
        """获取技能详情"""
        result = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.id == skill_id,
                AgentSkill.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def unload_skill(
        self,
        agent_id: str,
        user_id: str,
        skill_id: str
    ) -> bool:
        """卸载技能"""
        result = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.id == skill_id,
                AgentSkill.agent_id == agent_id,
                AgentSkill.user_id == user_id
            )
        )
        skill = result.scalar_one_or_none()

        if not skill:
            return False

        await self.db.delete(skill)
        await self.db.commit()
        return True

    async def find_skill_for_capability(
        self,
        agent_id: str,
        user_id: str,
        capability: str
    ) -> Optional[AgentSkill]:
        """
        在 Agent 技能库中查找匹配某能力的技能
        用于 Experiment 引擎执行前检查
        """
        skills = await self.list_agent_skills(agent_id, user_id)

        best_match = None
        best_score = 0.0

        for skill in skills:
            score = self._calculate_match(
                capability,
                skill.name,
                skill.description or ""
            )
            if score > best_score and score > 0.5:
                best_score = score
                best_match = skill

        return best_match

    # ========== 辅助方法 ==========

    async def _get_user_mcp_configs(self, user_id: str, agent_id: str) -> List[MCPServerConfig]:
        """获取用户可用的 MCP 配置"""
        result = await self.db.execute(
            select(MCPServerConfig).where(
                MCPServerConfig.user_id == user_id,
                MCPServerConfig.is_active == True,
                or_(
                    MCPServerConfig.allowed_agents == [],
                    MCPServerConfig.allowed_agents == None,
                    MCPServerConfig.allowed_agents.contains([agent_id])
                )
            )
        )
        return list(result.scalars().all())

    async def _get_tool_info(self, user_id: str, server_name: str, tool_name: str) -> Dict[str, Any]:
        """从 MCP Server 获取工具详情"""
        tools = await self.mcp_manager.list_tools(user_id, server_name)
        for tool in tools:
            if tool["name"] == tool_name:
                return tool
        raise ValueError(f"Tool {tool_name} not found in server {server_name}")

    async def _get_agent_skill_by_source(
        self,
        agent_id: str,
        source_server: str,
        source_tool: str
    ) -> Optional[AgentSkill]:
        """通过来源查找已加载的技能"""
        result = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.agent_id == agent_id,
                AgentSkill.source_server == source_server,
                AgentSkill.source_tool == source_tool
            )
        )
        return result.scalar_one_or_none()

    async def _get_agent_skill_by_name(
        self,
        agent_id: str,
        user_id: str,
        name: str
    ) -> Optional[AgentSkill]:
        """通过名字查找技能"""
        result = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.agent_id == agent_id,
                AgentSkill.user_id == user_id,
                AgentSkill.name == name
            )
        )
        return result.scalar_one_or_none()

    def _calculate_match(self, need: str, name: str, description: str) -> float:
        """计算匹配分数"""
        need_words = set(need.lower().split())
        name_words = set(name.lower().replace("_", " ").split())
        desc_words = set(description.lower().split())

        name_score = len(need_words & name_words) / len(need_words) if need_words else 0
        desc_score = len(need_words & desc_words) / len(need_words) if need_words else 0

        return name_score * 0.6 + desc_score * 0.4

    def _merge_parameters(
        self,
        defaults: Optional[Dict[str, Any]],
        provided: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并默认参数和提供的参数"""
        result = dict(defaults) if defaults else {}
        result.update(provided)
        return result
