#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库搜索脚本 - 重构版
支持: 混合搜索(关键词+实体关联)、SQLite存储
"""

import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入数据库模块
sys.path.insert(0, os.path.dirname(__file__))
import kb_database

def hybrid_search(query, top_k=5):
    """
    混合搜索: 关键词 + 实体关联
    1. 先在实体表中搜索相关实体
    2. 获取实体的关联关系
    3. 在文本块中搜索关键词
    4. 合并结果
    """
    results = []
    query_lower = query.lower()
    query_keywords = query_lower.split()
    
    # 第一步: 实体搜索
    print("   🔍 步骤1: 实体匹配")
    entities = kb_database.search_entities(query)
    print(f"      找到 {len(entities)} 个相关实体")
    
    entity_results = []
    for entity in entities:
        # 获取实体关联
        relations = kb_database.get_entity_relations(entity["name"])
        if relations:
            entity_results.append({
                "type": "entity",
                "entity": entity,
                "relations": relations,
                "score": len(query_keywords) * 2  # 实体匹配高分
            })
    
    # 第二步: 文本块搜索
    print("   🔍 步骤2: 文本搜索")
    chunks = kb_database.search_chunks(query, limit=top_k * 2)
    print(f"      找到 {len(chunks)} 个相关片段")
    
    chunk_results = []
    for chunk in chunks:
        # 计算关键词匹配得分
        score = 0
        matched = []
        for kw in query_keywords:
            if kw in chunk["content"].lower():
                score += 1
                matched.append(kw)
        
        chunk_results.append({
            "type": "chunk",
            "content": chunk["content"],
            "filename": chunk["filename"],
            "chunk_index": chunk["chunk_index"],
            "score": score,
            "matched": matched
        })
    
    # 合并结果
    all_results = []
    
    # 添加实体结果
    for er in entity_results:
        all_results.append({
            "result_type": "entity",
            "entity": er["entity"],
            "relations": er["relations"],
            "score": er["score"],
            "content": f"实体: {er['entity']['name']} ({er['entity']['type']})"
        })
    
    # 添加文本块结果
    for cr in chunk_results:
        all_results.append({
            "result_type": "chunk",
            "filename": cr["filename"],
            "content": cr["content"][:500],
            "score": cr["score"],
            "matched": cr["matched"]
        })
    
    # 按得分排序
    all_results.sort(key=lambda x: x["score"], reverse=True)
    
    return all_results[:top_k]

def search_knowledge_base(query, mode="hybrid", top_k=5):
    """
    搜索知识库
    mode: hybrid(混合) / entities(仅实体) / chunks(仅文本)
    """
    if mode == "hybrid":
        return hybrid_search(query, top_k)
    elif mode == "entities":
        entities = kb_database.search_entities(query)
        return [{"result_type": "entity", "entity": e} for e in entities]
    elif mode == "chunks":
        chunks = kb_database.search_chunks(query, top_k)
        return [{"result_type": "chunk", "content": c["content"], "filename": c["filename"]} for c in chunks]
    else:
        return []

def format_results(results):
    """格式化搜索结果"""
    if not results:
        return "未找到相关内容"
    
    output = []
    output.append(f"\n找到 {len(results)} 条相关结果:\n")
    
    for i, r in enumerate(results, 1):
        if r.get("result_type") == "entity":
            e = r["entity"]
            output.append(f"【实体 {i}】{e['name']}")
            output.append(f"   类型: {e['type']}")
            if e.get("description"):
                output.append(f"   描述: {e['description'][:100]}")
            
            # 显示关联
            relations = r.get("relations", {})
            if relations.get("outgoing"):
                outs = [f"{x['target']}({x['type']})" for x in relations['outgoing'][:3]]
                output.append(f"   → 关联: {', '.join(outs)}")
            if relations.get("incoming"):
                ins = [f"{x['source']}({x['type']})" for x in relations['incoming'][:3]]
                output.append(f"   ← 关联: {', '.join(ins)}")
            output.append("")
        else:
            output.append(f"【文档 {i}】来源: {r.get('filename', '未知')}")
            if r.get("matched"):
                output.append(f"   匹配词: {', '.join(r['matched'])}")
            content = r.get("content", "")
            output.append(f"   内容: {content[:300]}...")
            output.append("")
    
    return "\n".join(output)

def list_documents():
    """列出所有文档"""
    conn = kb_database.init_database()
    cursor = conn.cursor()
    
    cursor.execute('SELECT filename, file_path, chunk_count, processed_at FROM doc_index ORDER BY processed_at DESC')
    docs = cursor.fetchall()
    
    conn.close()
    
    if not docs:
        return "知识库中暂无文档"
    
    output = [f"\n知识库共有 {len(docs)} 个文档:\n"]
    for d in docs:
        output.append(f"  📄 {d[0]}")
        output.append(f"     切片: {d[2]} | 更新时间: {d[3]}")
        output.append("")
    
    return "\n".join(output)

def show_stats():
    """显示统计信息"""
    stats = kb_database.get_stats()
    
    # 获取实体类型分布
    conn = kb_database.init_database()
    cursor = conn.cursor()
    cursor.execute('SELECT type, COUNT(*) FROM entities GROUP BY type ORDER BY COUNT(*) DESC')
    type_dist = cursor.fetchall()
    conn.close()
    
    output = [
        "\n📊 知识库统计",
        "=" * 40,
        f"  实体: {stats['entities']}",
        f"  关系: {stats['relationships']}",
        f"  文档: {stats['documents']}",
        f"  切片: {stats['chunks']}",
        "",
        "📌 实体类型分布:"
    ]
    
    for t, c in type_dist:
        output.append(f"    • {t}: {c}")
    
    return "\n".join(output)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python search.py <query>           - 混合搜索")
        print("  python search.py --list           - 列出文档")
        print("  python search.py --stats          - 显示统计")
        print("  python search.py --entities <kw>  - 仅搜索实体")
        print("  python search.py --chunks <kw>    - 仅搜索文本")
        return
    
    command = sys.argv[1]
    
    if command == "--list":
        print(list_documents())
    elif command == "--stats":
        print(show_stats())
    elif command == "--entities":
        if len(sys.argv) < 3:
            print("请提供搜索关键词")
            return
        kw = " ".join(sys.argv[2:])
        results = search_knowledge_base(kw, mode="entities")
        print(format_results(results))
    elif command == "--chunks":
        if len(sys.argv) < 3:
            print("请提供搜索关键词")
            return
        kw = " ".join(sys.argv[2:])
        results = search_knowledge_base(kw, mode="chunks")
        print(format_results(results))
    else:
        query = " ".join(sys.argv[1:])
        results = search_knowledge_base(query, mode="hybrid")
        print(format_results(results))

if __name__ == "__main__":
    main()
