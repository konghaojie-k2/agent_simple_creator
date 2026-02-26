#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验执行工具集
提供代码执行、文件操作、任务管理、Web等工具
"""

import json
import os
import uuid
from typing import Dict, Any, Callable, Awaitable, Optional, List
from datetime import datetime
from agent_builder.services.code_sandbox import CodeExecutionSandbox


class TodoItem:
    """待办事项"""
    def __init__(self, id: str, title: str, description: str = "", status: str = "pending"):
        self.id = id
        self.title = title
        self.description = description
        self.status = status  # pending, in_progress, completed
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class NoteItem:
    """笔记"""
    def __init__(self, id: str, title: str, content: str, tags: List[str] = None):
        self.id = id
        self.title = title
        self.content = content
        self.tags = tags or []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class ToolRegistry:
    """
    工具注册表

    管理可用的工具函数
    """

    def __init__(self, workspace: Optional[str] = None):
        self.tools: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {}
        self.workspace = workspace  # 共享工作目录
        self._todo_store: Dict[str, TodoItem] = {}  # 待办存储
        self._note_store: Dict[str, NoteItem] = {}   # 笔记存储
        self._skill_system = None  # 技能系统（动态设置）
        self._register_default_tools()

    def set_skill_system(self, skill_system):
        """设置技能系统（用于 get_skill 工具）"""
        self._skill_system = skill_system

    def _register_default_tools(self):
        """注册默认工具"""
        # ==================== 代码执行 ====================
        self.tools["execute_code"] = self._execute_code
        self.tools["execute_python"] = self._execute_python
        self.tools["execute_bash"] = self._execute_bash
        self.tools["bash"] = self._execute_bash

        # ==================== 文件操作 ====================
        self.tools["read_file"] = self._read_file
        self.tools["write_file"] = self._write_file
        self.tools["delete_file"] = self._delete_file
        self.tools["list_files"] = self._list_files
        self.tools["file_exists"] = self._file_exists
        self.tools["search_files"] = self._search_files
        self.tools["search_content"] = self._search_content

        # ==================== Todo 任务管理 ====================
        self.tools["todo_create"] = self._todo_create
        self.tools["todo_update"] = self._todo_update
        self.tools["todo_list"] = self._todo_list
        self.tools["todo_complete"] = self._todo_complete
        self.tools["todo_delete"] = self._todo_delete

        # ==================== 笔记工具 ====================
        self.tools["note_create"] = self._note_create
        self.tools["note_read"] = self._note_read
        self.tools["note_list"] = self._note_list
        self.tools["note_update"] = self._note_update
        self.tools["note_delete"] = self._note_delete
        self.tools["note_search"] = self._note_search

        # ==================== Web 工具 ====================
        self.tools["fetch_url"] = self._fetch_url
        self.tools["web_search"] = self._web_search

        # ==================== 技能工具 ====================
        self.tools["get_skill"] = self._get_skill

        # ==================== 经验查询工具 ====================
        self.tools["search_user_experiences"] = self._search_user_experiences

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            执行结果
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}"
            }

        try:
            result = await self.tools[tool_name](**params)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== 代码执行 ====================

    async def _execute_code(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30
    ) -> Dict[str, Any]:
        """执行代码"""
        if language.lower() != "python":
            return {
                "success": False,
                "error": f"Unsupported language: {language}"
            }

        sandbox = CodeExecutionSandbox(self.workspace)
        result = sandbox.execute_python(code, timeout=timeout)
        return result

    async def _execute_python(
        self,
        code: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """执行 Python 代码（别名）"""
        return await self._execute_code(code, "python", timeout)

    async def _execute_bash(
        self,
        command: str,
        timeout: int = 30,
        shell: bool = True
    ) -> Dict[str, Any]:
        """执行 bash 命令"""
        sandbox = CodeExecutionSandbox(self.workspace)
        result = sandbox.execute_bash(command, timeout=timeout, shell=shell)
        return result

    # ==================== 文件操作 ====================

    async def _read_file(
        self,
        path: str,
        workspace: str = None
    ) -> Dict[str, Any]:
        """读取文件"""
        sandbox = CodeExecutionSandbox(workspace or self.workspace)
        result = sandbox.execute_file_operation("read", path)
        return result

    async def _write_file(
        self,
        path: str,
        content: str,
        workspace: str = None
    ) -> Dict[str, Any]:
        """写入文件"""
        sandbox = CodeExecutionSandbox(workspace or self.workspace)
        result = sandbox.execute_file_operation("write", path, content)
        return result

    async def _delete_file(
        self,
        path: str,
        workspace: str = None
    ) -> Dict[str, Any]:
        """删除文件"""
        sandbox = CodeExecutionSandbox(workspace or self.workspace)
        result = sandbox.execute_file_operation("delete", path)
        return result

    async def _list_files(
        self,
        path: str = ".",
        workspace: str = None
    ) -> Dict[str, Any]:
        """列出文件"""
        sandbox = CodeExecutionSandbox(workspace or self.workspace)
        result = sandbox.execute_file_operation("list", path)
        return result

    async def _file_exists(
        self,
        path: str,
        workspace: str = None
    ) -> Dict[str, Any]:
        """检查文件是否存在"""
        sandbox = CodeExecutionSandbox(workspace or self.workspace)
        result = sandbox.execute_file_operation("exists", path)
        return result

    async def _search_files(
        self,
        pattern: str,
        path: str = ".",
        workspace: str = None
    ) -> Dict[str, Any]:
        """搜索文件（类似 Glob）"""
        import fnmatch
        sandbox = CodeExecutionSandbox(workspace or self.workspace)
        base_path = sandbox.workspace_dir

        matches = []
        try:
            for root, dirs, files in os.walk(base_path):
                for filename in files:
                    if fnmatch.fnmatch(filename, pattern):
                        rel_path = os.path.relpath(os.path.join(root, filename), base_path)
                        matches.append(rel_path)
            return {"success": True, "matches": matches, "pattern": pattern}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _search_content(
        self,
        query: str,
        path: str = ".",
        workspace: str = None,
        file_pattern: str = "*"
    ) -> Dict[str, Any]:
        """搜索文件内容（类似 Grep）"""
        import fnmatch
        sandbox = CodeExecutionSandbox(workspace or self.workspace)
        base_path = sandbox.workspace_dir

        matches = []
        try:
            for root, dirs, files in os.walk(base_path):
                # 检查文件是否符合模式
                for filename in files:
                    if not fnmatch.fnmatch(filename, file_pattern):
                        continue

                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line_num, line in enumerate(f, 1):
                                if query.lower() in line.lower():
                                    rel_path = os.path.relpath(file_path, base_path)
                                    matches.append({
                                        "file": rel_path,
                                        "line": line_num,
                                        "content": line.strip()
                                    })
                    except Exception:
                        continue

            return {"success": True, "matches": matches, "query": query}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== Todo 任务管理 ====================

    async def _todo_create(
        self,
        title: str,
        description: str = "",
        task_id: str = None
    ) -> Dict[str, Any]:
        """创建待办事项"""
        todo_id = task_id or str(uuid.uuid4())[:8]
        todo = TodoItem(todo_id, title, description)
        self._todo_store[todo_id] = todo
        return {
            "success": True,
            "id": todo_id,
            "title": title,
            "status": todo.status
        }

    async def _todo_update(
        self,
        task_id: str,
        title: str = None,
        description: str = None,
        status: str = None
    ) -> Dict[str, Any]:
        """更新待办事项"""
        if task_id not in self._todo_store:
            return {"success": False, "error": f"Todo not found: {task_id}"}

        todo = self._todo_store[task_id]
        if title:
            todo.title = title
        if description:
            todo.description = description
        if status:
            todo.status = status
        todo.updated_at = datetime.utcnow()

        return {
            "success": True,
            "id": task_id,
            "title": todo.title,
            "status": todo.status
        }

    async def _todo_list(
        self,
        status: str = None
    ) -> Dict[str, Any]:
        """列出待办事项"""
        todos = list(self._todo_store.values())
        if status:
            todos = [t for t in todos if t.status == status]

        return {
            "success": True,
            "todos": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "created_at": t.created_at.isoformat()
                }
                for t in todos
            ]
        }

    async def _todo_complete(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """完成待办事项"""
        return await self._todo_update(task_id, status="completed")

    async def _todo_delete(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """删除待办事项"""
        if task_id not in self._todo_store:
            return {"success": False, "error": f"Todo not found: {task_id}"}

        del self._todo_store[task_id]
        return {"success": True, "id": task_id}

    # ==================== 笔记工具 ====================

    async def _note_create(
        self,
        title: str,
        content: str,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """创建笔记"""
        note_id = str(uuid.uuid4())[:8]
        note = NoteItem(note_id, title, content, tags)
        self._note_store[note_id] = note
        return {
            "success": True,
            "id": note_id,
            "title": title
        }

    async def _note_read(
        self,
        note_id: str
    ) -> Dict[str, Any]:
        """读取笔记"""
        if note_id not in self._note_store:
            return {"success": False, "error": f"Note not found: {note_id}"}

        note = self._note_store[note_id]
        return {
            "success": True,
            "id": note_id,
            "title": note.title,
            "content": note.content,
            "tags": note.tags
        }

    async def _note_list(
        self,
        tag: str = None
    ) -> Dict[str, Any]:
        """列出笔记"""
        notes = list(self._note_store.values())
        if tag:
            notes = [n for n in notes if tag in n.tags]

        return {
            "success": True,
            "notes": [
                {
                    "id": n.id,
                    "title": n.title,
                    "tags": n.tags,
                    "created_at": n.created_at.isoformat()
                }
                for n in notes
            ]
        }

    async def _note_update(
        self,
        note_id: str,
        title: str = None,
        content: str = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """更新笔记"""
        if note_id not in self._note_store:
            return {"success": False, "error": f"Note not found: {note_id}"}

        note = self._note_store[note_id]
        if title:
            note.title = title
        if content:
            note.content = content
        if tags:
            note.tags = tags
        note.updated_at = datetime.utcnow()

        return {
            "success": True,
            "id": note_id,
            "title": note.title
        }

    async def _note_delete(
        self,
        note_id: str
    ) -> Dict[str, Any]:
        """删除笔记"""
        if note_id not in self._note_store:
            return {"success": False, "error": f"Note not found: {note_id}"}

        del self._note_store[note_id]
        return {"success": True, "id": note_id}

    async def _note_search(
        self,
        query: str
    ) -> Dict[str, Any]:
        """搜索笔记"""
        results = []
        query_lower = query.lower()

        for note in self._note_store.values():
            if (query_lower in note.title.lower() or
                query_lower in note.content.lower() or
                any(query_lower in tag.lower() for tag in note.tags)):
                results.append({
                    "id": note.id,
                    "title": note.title,
                    "content": note.content[:100] + "..." if len(note.content) > 100 else note.content,
                    "tags": note.tags
                })

        return {"success": True, "results": results}

    # ==================== Web 工具 ====================

    async def _fetch_url(
        self,
        url: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """获取网页内容"""
        import urllib.request

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; AgentBot/1.0)"
            })
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode("utf-8", errors="ignore")
                return {
                    "success": True,
                    "url": url,
                    "content": content[:5000],  # 限制返回长度
                    "status": response.status
                }
        except Exception as e:
            return {"success": False, "error": str(e), "url": url}

    async def _web_search(
        self,
        query: str,
        num_results: int = 5
    ) -> Dict[str, Any]:
        """网络搜索（模拟实现）"""
        # 注意：实际实现需要接入搜索引擎 API
        # 这里返回一个提示信息
        return {
            "success": True,
            "query": query,
            "results": [],
            "message": "Web search requires external API integration. Use fetch_url for specific URLs."
        }

    # ==================== 技能工具 ====================

    async def _get_skill(
        self,
        skill_name: str
    ) -> Dict[str, Any]:
        """
        获取技能完整内容（渐进式披露 Level 2）

        Args:
            skill_name: 技能名称

        Returns:
            技能内容
        """
        if not self._skill_system:
            return {
                "success": False,
                "error": "Skill system not initialized"
            }

        skill = self._skill_system.get_skill(skill_name)
        if not skill:
            available = ", ".join(self._skill_system.list_all_skills())
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found. Available: {available}"
            }

        return {
            "success": True,
            "name": skill.name,
            "description": skill.description,
            "content": skill.to_prompt(),
            "allowed_tools": skill.allowed_tools or []
        }

    # ==================== 经验查询工具 ====================

    async def _search_user_experiences(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        查询用户的所有经验（跨Agent）

        Args:
            user_id: 用户ID
            status_filter: 状态过滤 (verified, draft, deprecated)
            limit: 返回结果的最大数量

        Returns:
            经验列表
        """
        try:
            from agent_builder.services.experience_service import ExperienceService

            # 这里需要AsyncSession，临时创建或者从外部注入
            # 由于工具注册表的设计，我们返回一个说明，实际查询应在服务层完成
            return {
                "success": False,
                "error": "This tool requires database session. Use the API endpoint /api/experiences/user/{user_id} instead.",
                "endpoint": f"/api/experiences/user/{user_id}",
                "params": {
                    "status": status_filter or "verified",
                    "limit": limit
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def list_tools(self) -> list:
        """列出所有可用工具"""
        return list(self.tools.keys())


# 全局工具注册表
_tool_registry = ToolRegistry()


def get_tool_registry(workspace: Optional[str] = None) -> ToolRegistry:
    """获取工具注册表实例"""
    if workspace:
        return ToolRegistry(workspace)
    return _tool_registry
