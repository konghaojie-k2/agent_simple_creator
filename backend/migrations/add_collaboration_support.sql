-- -*- coding: utf-8 -*-
-- Database Migration: Add Collaboration Support
-- 执行方式: 在 SQLite 数据库上运行此脚本

-- 1. 创建实验参与者表
CREATE TABLE IF NOT EXISTS experiment_participants (
    id VARCHAR(36) PRIMARY KEY,
    experiment_id VARCHAR(36) NOT NULL,
    agent_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'worker',
    join_order INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_participants_experiment_id ON experiment_participants(experiment_id);
CREATE INDEX IF NOT EXISTS idx_participants_agent_id ON experiment_participants(agent_id);
CREATE INDEX IF NOT EXISTS idx_participants_user_id ON experiment_participants(user_id);

-- 2. 为 experiments 表添加协作相关字段
-- 注意: SQLite 有限制，需要使用 ALTER TABLE 逐个添加

-- 检查 collaboration_type 字段是否存在
ALTER TABLE experiments ADD COLUMN collaboration_type VARCHAR(20);

-- 检查 workflow_config 字段是否存在
ALTER TABLE experiments ADD COLUMN workflow_config JSON;

-- 3. 验证迁移是否成功
-- 查询表结构
PRAGMA table_info(experiments);
PRAGMA table_info(experiment_participants);
