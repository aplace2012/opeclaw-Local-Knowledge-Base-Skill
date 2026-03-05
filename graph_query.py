#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱查询脚本 - 重构版
支持: 内存索引、预取优化、快速路径查找
"""

import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入数据库模块
sys.path.insert(0, os.path.dirname(__file__))
import kb_database

# ==================== 内存索引 ====================
class GraphIndex:
    """基于字典的内存索引 - 提升查询速度"""
    
    _instance = None
    _entities = None
    _relationships = None
    _entity_relations = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load(self, force=False):
        """加载索引到内存"""
        if self._entities is None or force:
            print("   📥 加载图谱到内存...")
            self._entities = kb_database.get_all_entities()
            self._relationships = kb_database.get_all_relationships()
            
            # 构建实体关系索引
            self._entity_relations = {}
            for rel in self._relationships:
                # 发出关系
                if rel["from"] not in self._entity_relations:
                    self._entity_relations[rel["from"]] = {"out": [], "in": []}
                self._entity_relations[rel["from"]]["out"].append({
                    "to": rel["to"],
                    "type": rel["type"]
                })
                # 接收关系
                if rel["to"] not in self._entity_relations:
                    self._entity_relations[rel["to"]] = {"out": [], "in": []}
                self._entity_relations[rel["to"]]["in"].append({
                    "from": rel["from"],
                    "type": rel["type"]
                })
            
            print(f"   ✓ 已加载 {len(self._entities)} 实体, {len(self._relationships)} 关系")
    
    def get_entity(self, name):
        """快速获取实体"""
        return self._entities.get(name)
    
    def get_relations(self, entity_name):
        """快速获取实体关系"""
        return self._entity_relations.get(entity_name, {"out": [], "in": []})
    
    def find_paths(self, start, end, max_depth=3):
        """快速路径查找"""
        if start not in self._entities or end not in self._entities:
            return []
        
        # BFS
        queue = [(start, [start])]
        visited = {start}
        paths = []
        
        while queue and len(paths) < 10:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            if current == end:
                paths.append(path)
                continue
            
            # 扩展
            rels = self._entity_relations.get(current, {})
            
            for rel in rels.get("out", []):
                next_node = rel["to"]
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))
            
            for rel in rels.get("in", []):
                next_node = rel["from"]
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))
        
        return paths
    
    def get_neighbors(self, entity_name, depth=1):
        """获取N度关联节点"""
        if entity_name not in self._entities:
            return {}
        
        visited = {entity_name}
        result = {entity_name: {"type": self._entities[entity_name]["type"], "distance": 0}}
        
        current_level = {entity_name}
        
        for d in range(1, depth + 1):
            next_level = set()
            for current in current_level:
                rels = self._entity_relations.get(current, {})
                
                for rel in rels.get("out", []) + rels.get("in", []):
                    neighbor = rel.get("to") or rel.get("from")
                    if neighbor and neighbor not in visited:
                        visited.add(neighbor)
                        next_level.add(neighbor)
                        result[neighbor] = {
                            "type": self._entities.get(neighbor, {}).get("type", "未知"),
                            "distance": d,
                            "via": current
                        }
            
            current_level = next_level
        
        return result

# 全局索引实例
_graph_index = GraphIndex.get_instance()

def refresh_index():
    """刷新索引"""
    _graph_index.load(force=True)

def query_entity(entity_name):
    """查询实体详情"""
    # 使用内存索引
    entity = _graph_index.get_entity(entity_name)
    
    if not entity:
        # 尝试从数据库获取
        relations = kb_database.get_entity_relations(entity_name)
        if not relations:
            return None
        entity = relations["entity"]
    
    # 获取关联
    relations = _graph_index.get_relations(entity_name)
    
    return {
        "entity": entity,
        "outgoing": relations["out"],
        "incoming": relations["in"]
    }

def query_paths(start_name, end_name, max_depth=3):
    """查询实体间的路径"""
    paths = _graph_index.find_paths(start_name, end_name, max_depth)
    return paths

def query_neighbors(entity_name, depth=2):
    """查询N度关联"""
    return _graph_index.get_neighbors(entity_name, depth)

def list_entities(entity_type=None, limit=50):
    """列出实体"""
    _graph_index.load()
    
    entities = _graph_index._entities
    
    if entity_type:
        entities = {k: v for k, v in entities.items() if v.get("type") == entity_type}
    
    # 转为列表并排序
    result = [{"name": k, **v} for k, v in entities.items()]
    result.sort(key=lambda x: x.get("name", ""))
    
    return result[:limit]

def get_entity_types():
    """获取所有实体类型"""
    _graph_index.load()
    
    types = {}
    for name, info in _graph_index._entities.items():
        t = info.get("type", "未知")
        types[t] = types.get(t, 0) + 1
    
    return sorted(types.items(), key=lambda x: -x[1])

def format_entity_details(details):
    """格式化实体详情"""
    if not details:
        return "未找到实体"
    
    e = details["entity"]
    output = [
        "=" * 50,
        f"📌 实体: {e.get('name', '未知')}",
        f"   类型: {e.get('type', '未知')}",
        f"   描述: {e.get('description', '无')}",
        ""
    ]
    
    outgoing = details.get("outgoing", [])
    incoming = details.get("incoming", [])
    
    if outgoing:
        output.append(f"→ 发出关系 ({len(outgoing)}):")
        for r in outgoing[:10]:
            output.append(f"   --[{r['type']}]--> {r.get('to', r.get('target', ''))}")
    
    if incoming:
        output.append(f"← 接收关系 ({len(incoming)}):")
        for r in incoming[:10]:
            output.append(f"   <--[{r['type']}]-- {r.get('from', r.get('source', ''))}")
    
    return "\n".join(output)

def format_paths(paths, start, end):
    """格式化路径结果"""
    if not paths:
        return f"未找到 {start} 到 {end} 的路径"
    
    output = [f"🔍 路径查询结果:\n"]
    
    for i, path in enumerate(paths, 1):
        path_str = " → ".join(path)
        output.append(f"   路径{i}: {path_str}")
    
    return "\n".join(output)

def format_neighbors(neighbors, center):
    """格式化邻居结果"""
    if not neighbors:
        return "未找到关联实体"
    
    output = [f"🔗 {center} 的关联实体:\n"]
    
    # 按距离分组
    by_dist = {}
    for name, info in neighbors.items():
        if name == center:
            continue
        d = info.get("distance", 1)
        if d not in by_dist:
            by_dist[d] = []
        by_dist[d].append(f"{name} ({info.get('type', '')})")
    
    for dist in sorted(by_dist.keys()):
        output.append(f"\n   {dist}度关联 ({len(by_dist[dist])}个):")
        for n in by_dist[dist][:5]:
            output.append(f"      • {n}")
        if len(by_dist[dist]) > 5:
            output.append(f"      ... 还有{len(by_dist[dist])-5}个")
    
    return "\n".join(output)

def main():
    # 初始化加载索引
    _graph_index.load()
    
    if len(sys.argv) < 2:
        # 默认显示统计
        print("=" * 50)
        print("📊 知识图谱查询")
        print("=" * 50)
        
        stats = kb_database.get_stats()
        print(f"\n实体: {stats['entities']}")
        print(f"关系: {stats['relationships']}")
        
        types = get_entity_types()
        print(f"\n实体类型分布:")
        for t, c in types[:10]:
            print(f"    • {t}: {c}")
        
        return
    
    command = sys.argv[1]
    
    if command == "--entity" or command == "-e":
        # 查询实体
        if len(sys.argv) < 3:
            print("用法: graph_query.py -e <实体名>")
            return
        name = " ".join(sys.argv[2:])
        details = query_entity(name)
        print(format_entity_details(details))
    
    elif command == "--path":
        # 路径查询
        if len(sys.argv) < 4:
            print("用法: graph_query.py --path <起点> <终点> [最大深度]")
            return
        start = sys.argv[2]
        end = sys.argv[3]
        depth = int(sys.argv[4]) if len(sys.argv) > 4 else 3
        paths = query_paths(start, end, depth)
        print(format_paths(paths, start, end))
    
    elif command == "--neighbors":
        # 邻居查询
        if len(sys.argv) < 3:
            print("用法: graph_query.py --neighbors <实体> [深度]")
            return
        name = sys.argv[2]
        depth = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        neighbors = query_neighbors(name, depth)
        print(format_neighbors(neighbors, name))
    
    elif command == "--type" or command == "-t":
        # 按类型列出
        if len(sys.argv) < 3:
            types = get_entity_types()
            print("实体类型分布:")
            for t, c in types:
                print(f"    • {t}: {c}")
            return
        etype = sys.argv[2]
        entities = list_entities(etype)
        print(f"\n{etype} 实体 ({len(entities)}个):")
        for e in entities[:20]:
            print(f"    • {e['name']}")
    
    elif command == "--list" or command == "-l":
        # 列出所有
        entities = list_entities(limit=30)
        print(f"\n实体列表 (前{len(entities)}个):")
        for e in entities:
            print(f"    • {e['name']} ({e.get('type', '')})")
    
    elif command == "--refresh":
        # 刷新索引
        refresh_index()
        print("索引已刷新")
    
    else:
        # 默认当作实体名查询
        name = " ".join(sys.argv[1:])
        details = query_entity(name)
        print(format_entity_details(details))

if __name__ == "__main__":
    main()
