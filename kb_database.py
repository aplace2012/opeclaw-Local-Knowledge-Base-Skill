#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库数据库管理模块
SQLite存储 + 增量更新
"""

import os
import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path

# 动态获取知识库路径
def get_kb_dir():
    """获取知识库根目录"""
    return os.path.expanduser("~/.openclaw/workspace/knowledge_base")

def get_db_path():
    """获取数据库路径"""
    return os.path.join(get_kb_dir(), "kb_storage.db")

def init_database():
    """初始化数据库和表结构"""
    kb_dir = get_kb_dir()
    os.makedirs(kb_dir, exist_ok=True)
    
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 实体表 - 包含别名字段
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            description TEXT,
            alias TEXT,
            source TEXT DEFAULT 'rule',
            source_doc TEXT,
            attributes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 关系表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            rel_type TEXT NOT NULL,
            description TEXT,
            source TEXT DEFAULT 'rule',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES entities(id),
            FOREIGN KEY (target_id) REFERENCES entities(id)
        )
    ''')
    
    # 文档索引表 - 包含文件哈希
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doc_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            file_size INTEGER,
            content TEXT,
            chunk_count INTEGER DEFAULT 0,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(file_path)
        )
    ''')
    
    # 文本块表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (doc_id) REFERENCES doc_index(id)
        )
    ''')
    
    # 实体别名表 - 用于实体消歧
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entity_alias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER NOT NULL,
            alias TEXT NOT NULL UNIQUE,
            FOREIGN KEY (entity_id) REFERENCES entities(id)
        )
    ''')
    
    # 创建索引提升查询效率
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_source ON relationships(source_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_target ON relationships(target_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id)')
    
    conn.commit()
    return conn

def compute_file_hash(file_path):
    """计算文件SHA256哈希"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def check_doc_needs_update(file_path):
    """检查文档是否需要更新（基于哈希）"""
    conn = init_database()
    cursor = conn.cursor()
    
    file_hash = compute_file_hash(file_path)
    file_size = os.path.getsize(file_path)
    
    cursor.execute(
        'SELECT id, file_hash FROM doc_index WHERE file_path = ?',
        (file_path,)
    )
    row = cursor.fetchone()
    
    conn.close()
    
    if row is None:
        return True, None  # 新文档
    elif row[1] != file_hash:
        return True, row[0]  # 已修改，需更新
    else:
        return False, row[0]  # 未修改

def add_entity(name, etype, description="", alias="", source="rule", source_doc=""):
    """添加实体"""
    conn = init_database()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''INSERT INTO entities (name, type, description, alias, source, source_doc)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (name, etype, description, alias, source, source_doc)
        )
        entity_id = cursor.lastrowid
        
        # 添加别名
        if alias:
            cursor.execute(
                'INSERT OR IGNORE INTO entity_alias (entity_id, alias) VALUES (?, ?)',
                (entity_id, alias)
            )
        
        conn.commit()
        result = entity_id
    except sqlite3.IntegrityError:
        # 实体已存在，获取ID
        cursor.execute('SELECT id FROM entities WHERE name = ?', (name,))
        result = cursor.fetchone()[0]
    finally:
        conn.close()
    
    return result

def add_relationship(source_name, target_name, rel_type, description=""):
    """添加关系"""
    conn = init_database()
    cursor = conn.cursor()
    
    # 获取实体ID
    cursor.execute('SELECT id FROM entities WHERE name = ?', (source_name,))
    source_row = cursor.fetchone()
    cursor.execute('SELECT id FROM entities WHERE name = ?', (target_name,))
    target_row = cursor.fetchone()
    
    if not source_row or not target_row:
        conn.close()
        return None
    
    try:
        cursor.execute(
            '''INSERT INTO relationships (source_id, target_id, rel_type, description)
               VALUES (?, ?, ?, ?)''',
            (source_row[0], target_row[0], rel_type, description)
        )
        rel_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        rel_id = None
    finally:
        conn.close()
    
    return rel_id

def add_document(filename, file_path, content, chunks):
    """添加文档"""
    conn = init_database()
    cursor = conn.cursor()
    
    file_hash = compute_file_hash(file_path)
    file_size = os.path.getsize(file_path)
    
    try:
        cursor.execute(
            '''INSERT INTO doc_index (filename, file_path, file_hash, file_size, content, chunk_count)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (filename, file_path, file_hash, file_size, content, len(chunks))
        )
        doc_id = cursor.lastrowid
        
        # 添加文本块
        for i, chunk in enumerate(chunks):
            cursor.execute(
                'INSERT INTO chunks (doc_id, chunk_index, content) VALUES (?, ?, ?)',
                (doc_id, i, chunk)
            )
        
        conn.commit()
    except sqlite3.IntegrityError:
        # 更新已存在的文档
        cursor.execute(
            'SELECT id FROM doc_index WHERE file_path = ?',
            (file_path,)
        )
        doc_id = cursor.fetchone()[0]
        
        cursor.execute(
            'UPDATE doc_index SET file_hash=?, content=?, chunk_count=?, processed_at=CURRENT_TIMESTAMP WHERE id=?',
            (file_hash, content, len(chunks), doc_id)
        )
        
        # 删除旧的chunks
        cursor.execute('DELETE FROM chunks WHERE doc_id = ?', (doc_id,))
        
        # 添加新的chunks
        for i, chunk in enumerate(chunks):
            cursor.execute(
                'INSERT INTO chunks (doc_id, chunk_index, content) VALUES (?, ?, ?)',
                (doc_id, i, chunk)
            )
        
        conn.commit()
    finally:
        conn.close()
    
    return doc_id

def search_entities(keyword):
    """搜索实体"""
    conn = init_database()
    cursor = conn.cursor()
    
    cursor.execute(
        '''SELECT e.id, e.name, e.type, e.description, e.alias
           FROM entities e
           LEFT JOIN entity_alias ea ON e.id = ea.entity_id
           WHERE e.name LIKE ? OR e.alias LIKE ? OR e.type LIKE ?''',
        (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')
    )
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {"id": r[0], "name": r[1], "type": r[2], "description": r[3], "alias": r[4]}
        for r in results
    ]

def get_entity_relations(entity_name):
    """获取实体的关联关系"""
    conn = init_database()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, type, description FROM entities WHERE name = ?', (entity_name,))
    entity = cursor.fetchone()
    
    if not entity:
        conn.close()
        return None
    
    entity_id = entity[0]
    
    # 获取发出的关系
    cursor.execute(
        '''SELECT r.id, r.rel_type, r.description, e.name, e.type
           FROM relationships r
           JOIN entities e ON r.target_id = e.id
           WHERE r.source_id = ?''',
        (entity_id,)
    )
    outgoing = cursor.fetchall()
    
    # 获取接收的关系
    cursor.execute(
        '''SELECT r.id, r.rel_type, r.description, e.name, e.type
           FROM relationships r
           JOIN entities e ON r.source_id = e.id
           WHERE r.target_id = ?''',
        (entity_id,)
    )
    incoming = cursor.fetchall()
    
    conn.close()
    
    return {
        "entity": {"id": entity[0], "type": entity[1], "description": entity[2]},
        "outgoing": [{"rel": r[0], "type": r[1], "desc": r[2], "target": r[3], "target_type": r[4]} for r in outgoing],
        "incoming": [{"rel": r[0], "type": r[1], "desc": r[2], "source": r[3], "source_type": r[4]} for r in incoming]
    }

def search_chunks(keyword, limit=10):
    """搜索文本块"""
    conn = init_database()
    cursor = conn.cursor()
    
    cursor.execute(
        '''SELECT c.content, d.filename, c.chunk_index
           FROM chunks c
           JOIN doc_index d ON c.doc_id = d.id
           WHERE c.content LIKE ?
           LIMIT ?''',
        (f'%{keyword}%', limit)
    )
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {"content": r[0], "filename": r[1], "chunk_index": r[2]}
        for r in results
    ]

def get_stats():
    """获取统计信息"""
    conn = init_database()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM entities')
    entity_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM relationships')
    rel_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM doc_index')
    doc_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM chunks')
    chunk_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "entities": entity_count,
        "relationships": rel_count,
        "documents": doc_count,
        "chunks": chunk_count
    }

def get_all_entities():
    """获取所有实体（用于内存索引）"""
    conn = init_database()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, type, description FROM entities')
    entities = cursor.fetchall()
    
    conn.close()
    
    return {e[1]: {"id": e[0], "type": e[2], "description": e[3]} for e in entities}

def get_all_relationships():
    """获取所有关系（用于内存索引）"""
    conn = init_database()
    cursor = conn.cursor()
    
    cursor.execute(
        '''SELECT r.id, e1.name, e2.name, r.rel_type
           FROM relationships r
           JOIN entities e1 ON r.source_id = e1.id
           JOIN entities e2 ON r.target_id = e2.id'''
    )
    rels = cursor.fetchall()
    
    conn.close()
    
    return [{"id": r[0], "from": r[1], "to": r[2], "type": r[3]} for r in rels]

# 初始化数据库
init_database()
