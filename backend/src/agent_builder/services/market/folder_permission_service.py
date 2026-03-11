#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Folder-based Permission Service

基于文件夹的权限控制：
- public/: 所有人可读
- private/{user_id}/: 仅所有者可读写
- shared/{resource_id}/: 共享资源
"""

import os
import json
from typing import Optional, List
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent
MARKET_BASE = BASE_DIR / "market" / "data"

PUBLIC_DIR = MARKET_BASE / "public"
PRIVATE_DIR = MARKET_BASE / "private"
SHARED_DIR = MARKET_BASE / "shared"

# Ensure directories exist
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
SHARED_DIR.mkdir(parents=True, exist_ok=True)


class FolderPermissionService:
    """基于文件夹的权限服务"""
    
    @staticmethod
    def get_resource_path(resource_type: str, resource_id: str, visibility: str, owner_id: str = None) -> Path:
        """获取资源的文件夹路径"""
        if visibility == "public":
            return MARKET_BASE / resource_type / "public" / resource_id
        elif visibility == "shared":
            return SHARED_DIR / resource_type / resource_id
        else:  # private
            return PRIVATE_DIR / owner_id / resource_type / resource_id
    
    @staticmethod
    def check_read_permission(resource_type: str, resource_id: str, owner_id: str, current_user_id: str, visibility: str) -> bool:
        """检查读权限"""
        # 所有者总是可以读
        if current_user_id == owner_id:
            return True
        
        # 公开资源所有人都可以读
        if visibility == "public":
            return True
        
        # 共享资源检查
        if visibility == "shared":
            share_config = FolderPermissionService.get_share_config(resource_type, resource_id)
            if share_config and current_user_id in share_config.get("allowed_users", []):
                return True
        
        return False
    
    @staticmethod
    def check_write_permission(owner_id: str, current_user_id: str) -> bool:
        """检查写权限 - 只有所有者可以写"""
        return current_user_id == owner_id
    
    @staticmethod
    def check_delete_permission(owner_id: str, current_user_id: str) -> bool:
        """检查删除权限 - 只有所有者可以删除"""
        return current_user_id == owner_id
    
    @staticmethod
    def get_share_config(resource_type: str, resource_id: str) -> Optional[dict]:
        """获取共享配置"""
        config_path = SHARED_DIR / resource_type / resource_id / "share_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return None
    
    @staticmethod
    def set_share_config(resource_type: str, resource_id: str, allowed_users: List[str], owner_id: str) -> dict:
        """设置共享配置"""
        share_dir = SHARED_DIR / resource_type / resource_id
        share_dir.mkdir(parents=True, exist_ok=True)
        
        config = {
            "allowed_users": allowed_users,
            "owner_id": owner_id,
        }
        
        config_path = share_dir / "share_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config
    
    @staticmethod
    def remove_share_config(resource_type: str, resource_id: str):
        """移除共享配置"""
        config_path = SHARED_DIR / resource_type / resource_id / "share_config.json"
        if config_path.exists():
            os.remove(config_path)
    
    @staticmethod
    def move_to_public(resource_type: str, resource_id: str, owner_id: str, current_path: Path):
        """移动资源到公开目录"""
        public_dir = MARKET_BASE / resource_type / "public" / resource_id
        public_dir.mkdir(parents=True, exist_ok=True)
        
        # 移动文件
        for item in current_path.iterdir():
            if item.is_file():
                dest = public_dir / item.name
                item.rename(dest)
        
        # 删除原目录
        if current_path.exists():
            try:
                current_path.rmdir()
            except:
                pass
        
        return public_dir
    
    @staticmethod
    def move_to_private(resource_type: str, resource_id: str, owner_id: str, current_path: Path):
        """移动资源到私有目录"""
        private_dir = PRIVATE_DIR / owner_id / resource_type / resource_id
        private_dir.mkdir(parents=True, exist_ok=True)
        
        # 移动文件
        for item in current_path.iterdir():
            if item.is_file():
                dest = private_dir / item.name
                item.rename(dest)
        
        # 删除原目录
        if current_path.exists():
            try:
                current_path.rmdir()
            except:
                pass
        
        return private_dir
    
    @staticmethod
    def move_to_shared(resource_type: str, resource_id: str, owner_id: str, current_path: Path):
        """移动资源到共享目录"""
        shared_dir = SHARED_DIR / resource_type / resource_id
        shared_dir.mkdir(parents=True, exist_ok=True)
        
        # 移动文件
        for item in current_path.iterdir():
            if item.is_file():
                dest = shared_dir / item.name
                item.rename(dest)
        
        # 删除原目录
        if current_path.exists():
            try:
                current_path.rmdir()
            except:
                pass
        
        return shared_dir


# Singleton instance
folder_permission_service = FolderPermissionService()
