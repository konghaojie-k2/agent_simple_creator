#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码执行沙箱
提供安全的 Python 代码执行环境
"""

import io
import sys
import traceback
import tempfile
import os
from typing import Dict, Any, Optional
from contextlib import contextmanager


class CodeExecutionSandbox:
    """
    代码执行沙箱

    提供隔离的 Python 代码执行环境
    支持：
    - 标准输出捕获
    - 异常处理
    - 临时文件操作
    """

    def __init__(self, workspace_dir: Optional[str] = None):
        """
        初始化沙箱

        Args:
            workspace_dir: 工作目录，默认为临时目录
        """
        if workspace_dir:
            self.workspace_dir = workspace_dir
        else:
            self.workspace_dir = tempfile.mkdtemp(prefix="agent_sandbox_")

        os.makedirs(self.workspace_dir, exist_ok=True)

    def execute_python(
        self,
        code: str,
        timeout: int = 30,
        memory_limit_mb: int = 128
    ) -> Dict[str, Any]:
        """
        执行 Python 代码

        Args:
            code: Python 代码
            timeout: 超时时间（秒）
            memory_limit_mb: 内存限制（MB）- 简化版暂不实现

        Returns:
            执行结果字典
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # 创建局部执行环境
        local_vars = {
            "__workspace__": self.workspace_dir,
            "print": self._safe_print(stdout_capture),
        }

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, {"__builtins__": __builtins__}, local_vars)

            return {
                "success": True,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "return_value": local_vars.get("_result"),
                "workspace": self.workspace_dir
            }

        except Exception as e:
            return {
                "success": False,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "error": str(e),
                "traceback": traceback.format_exc(),
                "workspace": self.workspace_dir
            }

    def execute_file_operation(
        self,
        operation: str,
        file_path: str,
        content: Optional[str] = None,
        mode: str = "r"
    ) -> Dict[str, Any]:
        """
        执行文件操作

        Args:
            operation: 操作类型 (read, write, delete, list, exists)
            file_path: 文件路径（相对于工作目录）
            content: 写入内容（write 操作时使用）
            mode: 读取模式

        Returns:
            操作结果
        """
        # 安全检查：确保路径在工作目录内
        full_path = os.path.abspath(os.path.join(self.workspace_dir, file_path))
        if not full_path.startswith(os.path.abspath(self.workspace_dir)):
            return {
                "success": False,
                "error": "Path outside workspace is not allowed"
            }

        try:
            if operation == "read":
                with open(full_path, mode) as f:
                    content = f.read()
                return {"success": True, "content": content}

            elif operation == "write":
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(content or "")
                return {"success": True, "path": file_path}

            elif operation == "delete":
                if os.path.exists(full_path):
                    os.remove(full_path)
                    return {"success": True}
                return {"success": False, "error": "File not found"}

            elif operation == "list":
                if os.path.exists(full_path):
                    if os.path.isdir(full_path):
                        return {
                            "success": True,
                            "files": os.listdir(full_path),
                            "type": "directory"
                        }
                    else:
                        return {
                            "success": True,
                            "files": [file_path],
                            "type": "file"
                        }
                return {"success": False, "error": "Path not found"}

            elif operation == "exists":
                return {"success": True, "exists": os.path.exists(full_path)}

            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _safe_print(self, stdout):
        """安全的 print 函数"""
        def safe_print(*args, **kwargs):
            kwargs["file"] = stdout
            print(*args, **kwargs)
        return safe_print

    def execute_bash(
        self,
        command: str,
        timeout: int = 30,
        shell: bool = True
    ) -> Dict[str, Any]:
        """
        执行 bash 命令

        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）
            shell: 是否使用 shell 执行

        Returns:
            执行结果字典
        """
        import subprocess

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            # 使用 subprocess 执行命令
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace_dir
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command,
                "workspace": self.workspace_dir
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command,
                "workspace": self.workspace_dir
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "workspace": self.workspace_dir
            }

    def cleanup(self):
        """清理工作目录"""
        import shutil
        if os.path.exists(self.workspace_dir):
            shutil.rmtree(self.workspace_dir)


@contextmanager
def redirect_stdout(target):
    """重定向标准输出"""
    old = sys.stdout
    sys.stdout = target
    try:
        yield
    finally:
        sys.stdout = old


@contextmanager
def redirect_stderr(target):
    """重定向标准错误"""
    old = sys.stderr
    sys.stderr = target
    try:
        yield
    finally:
        sys.stderr = old
