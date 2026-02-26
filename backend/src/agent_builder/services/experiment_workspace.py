#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验工作空间管理器

负责创建和管理实验的工作空间：
- 单Agent实验：提供Agent的临时工作空间
- 多Agent实验：提供协作共享空间

所有Agent活动通过实验组织，Agent本身无独立工作空间。
"""

import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class ExperimentWorkspace:
    """
    实验工作空间管理器

    实验是Agent活动的载体，提供：
    - 配置存储
    - 共享资源（单Agent时="自己的"，多Agent时="共享的"）
    - 工作区域
    - 结果存储
    """

    def __init__(self, workspaces_dir: str = "./workspaces"):
        self.workspaces_dir = Path(workspaces_dir)

    def _get_experiments_base_dir(self, user_id: str) -> Path:
        """获取用户实验的基础目录"""
        return self.workspaces_dir / user_id / "experiments"

    def _get_experiment_dir(self, user_id: str, experiment_id: str) -> Path:
        """获取实验目录"""
        return self._get_experiments_base_dir(user_id) / experiment_id

    def create_experiment_workspace(
        self,
        user_id: str,
        experiment_id: str,
        experiment_config: Dict[str, Any]
    ) -> dict:
        """
        创建实验工作空间

        Args:
            user_id: 用户ID
            experiment_id: 实验ID
            experiment_config: 实验配置
                {
                    "name": "实验名称",
                    "type": "single" | "collaboration",
                    "participants": [{"agent_id": "...", "role": "..."}],
                    "workflow": "sequential" | "parallel" | "debate",
                    "materials": [...],
                    "thresholds": {...}
                }

        Returns:
            创建的路径信息
        """
        exp_dir = self._get_experiment_dir(user_id, experiment_id)

        # 创建目录结构
        config_dir = exp_dir / "config"
        shared_dir = exp_dir / "shared"
        workspace_dir = exp_dir / "workspace"
        results_dir = exp_dir / "results"
        messages_dir = exp_dir / "messages"

        for dir_path in [config_dir, shared_dir, workspace_dir, results_dir, messages_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 创建manifest清单
        manifest = {
            "experiment_id": experiment_id,
            "user_id": user_id,
            "name": experiment_config.get("name", ""),
            "type": experiment_config.get("type", "single"),
            "participants": experiment_config.get("participants", []),
            "workflow": experiment_config.get("workflow", "sequential"),
            "created_at": datetime.utcnow().isoformat(),
            "status": "initialized"
        }

        manifest_path = exp_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        # 保存配置到config目录
        config_path = config_dir / "experiment.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(experiment_config, f, ensure_ascii=False, indent=2)

        return {
            "experiment_dir": str(exp_dir),
            "manifest_path": str(manifest_path),
            "config_dir": str(config_dir),
            "shared_dir": str(shared_dir),
            "workspace_dir": str(workspace_dir),
            "results_dir": str(results_dir),
            "messages_dir": str(messages_dir)
        }

    def get_experiment_directories(
        self,
        user_id: str,
        experiment_id: str
    ) -> dict:
        """获取实验目录路径"""
        exp_dir = self._get_experiment_dir(user_id, experiment_id)

        return {
            "experiment_dir": str(exp_dir),
            "manifest_path": str(exp_dir / "manifest.json"),
            "config_dir": str(exp_dir / "config"),
            "shared_dir": str(exp_dir / "shared"),
            "workspace_dir": str(exp_dir / "workspace"),
            "results_dir": str(exp_dir / "results"),
            "messages_dir": str(exp_dir / "messages")
        }

    def get_manifest(
        self,
        user_id: str,
        experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取实验清单"""
        manifest_path = self._get_experiment_dir(user_id, experiment_id) / "manifest.json"
        if not manifest_path.exists():
            return None

        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def update_manifest(
        self,
        user_id: str,
        experiment_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新实验清单"""
        manifest = self.get_manifest(user_id, experiment_id) or {}
        manifest.update(updates)
        manifest["updated_at"] = datetime.utcnow().isoformat()

        manifest_path = self._get_experiment_dir(user_id, experiment_id) / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        return manifest

    def is_collaboration_experiment(
        self,
        user_id: str,
        experiment_id: str
    ) -> bool:
        """判断是否为协作实验"""
        manifest = self.get_manifest(user_id, experiment_id)
        if not manifest:
            return False

        return manifest.get("type") == "collaboration" or len(manifest.get("participants", [])) > 1

    def add_shared_material(
        self,
        user_id: str,
        experiment_id: str,
        material_name: str,
        content: str,
        material_type: str = "text"
    ) -> str:
        """
        添加共享素材到实验空间

        Args:
            user_id: 用户ID
            experiment_id: 实验ID
            material_name: 素材名称
            content: 素材内容
            material_type: 素材类型 (text | file | url)

        Returns:
            素材文件路径
        """
        shared_dir = self._get_experiment_dir(user_id, experiment_id) / "shared"
        materials_dir = shared_dir / "materials"
        materials_dir.mkdir(parents=True, exist_ok=True)

        material_path = materials_dir / material_name
        with open(material_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(material_path)

    def save_agent_message(
        self,
        user_id: str,
        experiment_id: str,
        from_agent: str,
        to_agent: str,
        message: Dict[str, Any]
    ) -> str:
        """
        保存Agent间通信消息

        Args:
            user_id: 用户ID
            experiment_id: 实验ID
            from_agent: 发送方Agent ID
            to_agent: 接收方Agent ID ("*" 表示广播)
            message: 消息内容

        Returns:
            消息文件路径
        """
        messages_dir = self._get_experiment_dir(user_id, experiment_id) / "messages"
        messages_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp}_{from_agent}_to_{to_agent or 'all'}.json"
        message_path = messages_dir / filename

        message_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "from": from_agent,
            "to": to_agent,
            "message": message
        }

        with open(message_path, "w", encoding="utf-8") as f:
            json.dump(message_record, f, ensure_ascii=False, indent=2)

        return str(message_path)

    def get_agent_messages(
        self,
        user_id: str,
        experiment_id: str,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取Agent相关的消息

        Args:
            user_id: 用户ID
            experiment_id: 实验ID
            agent_id: Agent ID（过滤该Agent相关的消息）

        Returns:
            消息列表
        """
        messages_dir = self._get_experiment_dir(user_id, experiment_id) / "messages"
        if not messages_dir.exists():
            return []

        messages = []
        for msg_file in messages_dir.glob("*.json"):
            with open(msg_file, "r", encoding="utf-8") as f:
                msg_record = json.load(f)

                # 过滤：如果指定agent_id，只返回相关的消息
                if agent_id:
                    if (msg_record.get("from") != agent_id and
                        msg_record.get("to") != agent_id and
                        msg_record.get("to") != "*"):
                        continue

                messages.append(msg_record)

        # 按时间戳排序
        messages.sort(key=lambda x: x.get("timestamp", ""))
        return messages

    def save_experiment_result(
        self,
        user_id: str,
        experiment_id: str,
        result: Dict[str, Any],
        result_name: str = "output.json"
    ) -> str:
        """
        保存实验结果

        Args:
            user_id: 用户ID
            experiment_id: 实验ID
            result: 结果数据
            result_name: 结果文件名

        Returns:
            结果文件路径
        """
        results_dir = self._get_experiment_dir(user_id, experiment_id) / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        result_path = results_dir / result_name
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return str(result_path)

    def cleanup_experiment_workspace(
        self,
        user_id: str,
        experiment_id: str,
        archive: bool = True
    ) -> bool:
        """
        清理实验工作空间

        Args:
            user_id: 用户ID
            experiment_id: 实验ID
            archive: 是否归档（移动到archive目录）

        Returns:
            是否清理成功
        """
        exp_dir = self._get_experiment_dir(user_id, experiment_id)

        if not exp_dir.exists():
            return False

        try:
            if archive:
                # 归档到archive目录
                archive_dir = self._get_experiments_base_dir(user_id) / "_archive"
                archive_dir.mkdir(parents=True, exist_ok=True)

                archive_path = archive_dir / f"{experiment_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(str(exp_dir), str(archive_path))
            else:
                # 直接删除
                shutil.rmtree(exp_dir)

            return True
        except Exception as e:
            print(f"Failed to cleanup experiment workspace: {e}")
            return False

    def list_user_experiments(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        列出用户所有实验

        Args:
            user_id: 用户ID

        Returns:
            实验清单列表
        """
        exp_base_dir = self._get_experiments_base_dir(user_id)
        if not exp_base_dir.exists():
            return []

        experiments = []
        for exp_dir in exp_base_dir.iterdir():
            if exp_dir.is_dir() and not exp_dir.name.startswith("_"):
                manifest_path = exp_dir / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        experiments.append(json.load(f))

        # 按创建时间排序
        experiments.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return experiments


# 全局实例
_experiment_workspace: Optional[ExperimentWorkspace] = None


def get_experiment_workspace(workspaces_dir: str = "./workspaces") -> ExperimentWorkspace:
    """获取实验工作空间管理器实例"""
    global _experiment_workspace
    if _experiment_workspace is None:
        _experiment_workspace = ExperimentWorkspace(workspaces_dir)
    return _experiment_workspace
