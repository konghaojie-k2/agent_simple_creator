#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 客户端管理器
管理 MCP Server 连接，支持权限隔离
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent_builder.db.models import MCPServerConfig


class MCPClientManager:
    """管理用户级 MCP 客户端连接"""

    def __init__(self):
        # user_id -> {server_name: client_session}
        self._clients: Dict[str, Dict[str, ClientSession]] = {}
        # 存储 server 配置
        self._configs: Dict[str, Dict[str, Any]] = {}

    async def connect_server(
        self,
        user_id: str,
        server_config: MCPServerConfig
    ) -> ClientSession:
        """
        连接到 MCP Server
        每个用户有自己的连接池
        """
        if user_id not in self._clients:
            self._clients[user_id] = {}

        server_name = server_config.name

        # 如果已连接，返回现有连接
        if server_name in self._clients[user_id]:
            return self._clients[user_id][server_name]

        # 创建新连接
        if server_config.transport == "stdio":
            session = await self._connect_stdio(server_config)
        elif server_config.transport == "sse":
            session = await self._connect_sse(server_config)
        else:
            raise ValueError(f"Unknown transport: {server_config.transport}")

        self._clients[user_id][server_name] = session
        self._configs.setdefault(user_id, {})[server_name] = server_config

        return session

    async def _connect_stdio(self, config: MCPServerConfig) -> ClientSession:
        """连接 stdio 类型的 MCP Server"""
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args or [],
            env={**os.environ, **(config.env or {})}
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return session

    async def _connect_sse(self, config: MCPServerConfig) -> ClientSession:
        """连接 SSE 类型的 MCP Server"""
        # 实现 SSE 连接 - 暂时抛出未实现错误
        raise NotImplementedError("SSE transport not yet implemented")

    async def list_tools(
        self,
        user_id: str,
        server_name: str
    ) -> List[Dict[str, Any]]:
        """列出指定 Server 的所有工具"""
        session = self._clients.get(user_id, {}).get(server_name)
        if not session:
            raise ValueError(f"Server {server_name} not connected for user {user_id}")

        response = await session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

    async def call_tool(
        self,
        user_id: str,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用指定工具"""
        session = self._clients.get(user_id, {}).get(server_name)
        if not session:
            raise ValueError(f"Server {server_name} not connected for user {user_id}")

        result = await session.call_tool(tool_name, arguments)
        return {
            "content": [c.text for c in result.content if hasattr(c, 'text')],
            "is_error": result.isError if hasattr(result, 'isError') else False,
        }

    async def disconnect_user(self, user_id: str):
        """断开用户的所有连接"""
        if user_id in self._clients:
            # 关闭所有 session
            for session in self._clients[user_id].values():
                await session.close()
            del self._clients[user_id]
            if user_id in self._configs:
                del self._configs[user_id]

    async def disconnect_server(self, user_id: str, server_name: str):
        """断开指定 Server 的连接"""
        if user_id in self._clients and server_name in self._clients[user_id]:
            await self._clients[user_id][server_name].close()
            del self._clients[user_id][server_name]
            if user_id in self._configs and server_name in self._configs[user_id]:
                del self._configs[user_id][server_name]

    def is_connected(self, user_id: str, server_name: str) -> bool:
        """检查指定 Server 是否已连接"""
        return server_name in self._clients.get(user_id, {})

    def get_connected_servers(self, user_id: str) -> List[str]:
        """获取用户已连接的所有 Server 名称"""
        return list(self._clients.get(user_id, {}).keys())
