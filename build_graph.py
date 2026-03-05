#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱构建器 - 重构版
支持: SQLite存储、增量更新、实体消歧、环境变量配置、领域定制
"""

import os
import sys
import io
import re
import json

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入数据库模块
sys.path.insert(0, os.path.dirname(__file__))
import kb_database

# 获取API Key（从环境变量）
def get_api_key():
    """从环境变量获取API Key"""
    return os.environ.get('MINIMAX_API_KEY', '')

# ==================== 动态加载领域配置 ====================
def load_domain_config():
    """加载用户配置的领域设置"""
    kb_dir = os.path.expanduser("~/.openclaw/workspace/knowledge_base")
    config_file = os.path.join(kb_dir, "domain_config.json")
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f" 使用领域: {config.get('domain', '通用')}")
            return config.get('entity_types', {})
    return None

# ==================== 默认实体类型定义 ====================
# 如果用户未配置领域，使用默认的通用定义
DEFAULT_ENTITY_SCHEMAS = {
    "组织": ["公司", "部门", "团队", "小组", "工厂"],
    "人物": ["经理", "总监", "主管", "负责人"],
    "项目": ["项目", "任务", "里程碑"],
    "文档": ["报告", "计划", "合同", "方案"],
    "工具": ["软件", "系统", "平台", "工具"],
    "时间": ["日期", "时间", "截止日期"]
}
ENTITY_SCHEMAS = {
    "组织": ["部", "车间", "科室", "部门", "团队", "小组", "工厂"],
    "供应商": ["供应商", "厂商", "服务商", "制造商"],
    "物料": ["物料", "原材料", "零部件", "配件", "元器件", "芯片", "屏幕", "电池", "PCB"],
    "产品": ["手机", "平板", "手表", "终端", "成品", "产品"],
    "工序": ["工序", "工艺", "流程", "SMT", "贴片", "组装", "测试", "包装", "贴合"],
    "设备": ["设备", "机器", "仪器", "治具", "贴片机", "AOI", "点胶机", "焊接机"],
    "系统": ["系统", "平台", "软件", "MES", "WMS", "ERP", "PLM", "SRM", "APS", "QMS"],
    "技术": ["技术", "算法", "AI", "机器视觉", "数字孪生", "边缘计算", "物联网", "5G"],
    "指标": ["指标", "KPI", "OEE", "良率", "产能", "利用率", "周转率"],
    "方案": ["方案", "规划", "建议", "策略"],
    "痛点": ["问题", "困难", "挑战", "痛点", "瓶颈", "风险", "异常"],
    "场景": ["场景", "应用", "业务", "检验", "入库", "出库", "报工", "追溯"],
}

# AI/ML 实体类型
ML_ENTITY_SCHEMAS = {
    "领域": ["机器学习", "深度学习", "人工智能", "AI", "ML", "DL"],
    "方法论": ["监督学习", "无监督学习", "强化学习", "半监督学习", "迁移学习"],
    "任务": ["回归", "分类", "聚类", "降维", "目标检测", "语义分割", "自然语言处理", "计算机视觉"],
    "算法": ["神经网络", "卷积神经网络", "循环神经网络", "Transformer", "决策树", "随机森林", "支持向量机", "线性回归", "逻辑回归", "K-means", "XGBoost"],
    "组件": ["编码器", "解码器", "嵌入层", "全连接层", "卷积层", "池化层", "注意力层"],
    "优化器": ["Adam", "SGD", "RMSprop", "AdaGrad"],
    "平台": ["Sentosa", "RapidMiner", "Altair", "DataSphere", "ModelArts"],
    "概念": ["过拟合", "欠拟合", "超参数", "激活函数", "损失函数"],
}

# ==================== 实体消歧映射 ====================
ENTITY_NORMALIZATION = {
    # 系统别名
    "MES系统": "MES",
    "WMS系统": "WMS",
    "ERP系统": "ERP",
    "MES平台": "MES",
    "WMS平台": "WMS",
    "ERP平台": "ERP",
    # 技术别名
    "人工智能技术": "人工智能",
    "机器学习技术": "机器学习",
    "深度学习技术": "深度学习",
    "机器视觉技术": "机器视觉",
    # 产品别名
    "手机产品": "手机",
    # 行业术语
    "5G通信": "5G",
    "工业互联网平台": "工业互联网",
}

# 合并所有实体模式
ALL_ENTITY_SCHEMAS = {**ENTITY_SCHEMAS, **ML_ENTITY_SCHEMAS}

# ==================== 关系模式 ====================
RELATIONSHIP_PATTERNS = [
    (r"([^\s，。,\.]+?供应商|[^\s，。,\.]+?厂商)(供应|提供|生产)([^\s，。,\.]+?物料)", "供应"),
    (r"([^\s，。,\.]+?物料)(用于|装配于|组成)([^\s，。,\.]+?手机|[^\s，。,\.]+?平板|[^\s，。,\.]+?手表)", "用于"),
    (r"([^\s，。,\.]+?产品)(经过|通过|需要)([^\s，。,\.]+?SMT|[^\s，。,\.]+?贴片|[^\s，。,\.]+?组装|[^\s，。,\.]+?测试)", "经过"),
    (r"([^\s，。,\.]+?MES|[^\s，。,\.]+?WMS|[^\s，。,\.]+?ERP)(部署|应用|支撑)([^\s，。,\.]+?生产|[^\s，。,\.]+?仓储|[^\s，。,\.]+?车间)", "部署"),
    (r"([^\s，。,\.]+?方案)(采用|使用|应用)([^\s，。,\.]+?AI|[^\s，。,\.]+?机器视觉|[^\s，。,\.]+?AGV)", "采用"),
    (r"([^\s，。,\.]+?AI|[^\s，。,\.]+?机器视觉)(解决|改善|优化)([^\s，。,\.]+?效率|[^\s，。,\.]+?成本|[^\s，。,\.]+?质量)", "解决"),
]

def normalize_entity(entity_name):
    """实体名称规范化 - 消歧"""
    # 去除常见后缀
    for pattern, canonical in ENTITY_NORMALIZATION.items():
        if entity_name.endswith(pattern) or entity_name == pattern:
            return canonical
    
    # 去除"系统"、"平台"等后缀（保留MES/WMS/ERP）
    if entity_name not in ["MES", "WMS", "ERP", "APS", "SRM", "PLM", "QMS"]:
        if entity_name.endswith("系统") or entity_name.endswith("平台"):
            base = entity_name[:-2]
            if base in ["MES", "WMS", "ERP"]:
                return base
    
    return entity_name

def extract_entities_rule_based(text):
    """规则匹配提取实体"""
    found = {}  # {规范化名称: 原始名称}
    
    for entity_type, keywords in ALL_ENTITY_SCHEMAS.items():
        for keyword in keywords:
            if keyword in text:
                # 规范化
                normalized = normalize_entity(keyword)
                if normalized not in found:
                    found[normalized] = {"name": keyword, "type": entity_type, "original": normalized}
    
    return list(found.values())

def extract_relationships_rule_based(text, entity_names):
    """规则匹配提取关系"""
    relationships = []
    
    for pattern, rel_type in RELATIONSHIP_PATTERNS:
        try:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) >= 2:
                    source = normalize_entity(match[0].strip())
                    target = normalize_entity(match[2].strip()) if len(match) > 2 else None
                    
                    if source in entity_names and target in entity_names and target:
                        relationships.append({
                            "source": source,
                            "target": target,
                            "type": rel_type
                        })
        except:
            continue
    
    return relationships

def import_document(file_path, mode="rule-only"):
    """
    导入文档到知识库
    1. 检查是否需要更新（增量）
    2. 读取文件
    3. 提取实体和关系
    4. 存储到数据库
    """
    print(f"\n📥 开始导入: {os.path.basename(file_path)}")
    print(f"   模式: {mode}")
    
    # 1. 检查是否需要更新
    needs_update, existing_doc_id = kb_database.check_doc_needs_update(file_path)
    
    if not needs_update:
        print("   ⏭️  文档未变更，跳过")
        stats = kb_database.get_stats()
        print(f"   📊 当前: {stats['entities']} 实体, {stats['relationships']} 关系")
        return {"status": "skipped", "doc_id": existing_doc_id}
    
    if existing_doc_id:
        print("   🔄 检测到文档已更新，将重新处理")
    
    # 2. 读取文件
    from read_file import read_file, chunk_text
    content = read_file(file_path)
    
    if content.startswith("Error"):
        print(f"   ❌ 读取失败: {content}")
        return {"status": "error", "message": content}
    
    # 3. 语义切片
    chunks = chunk_text(content, chunk_size=800, overlap=100)
    print(f"   ✓ 已读取，共 {len(chunks)} 个切片")
    
    # 4. 提取实体
    full_text = "\n".join(chunks)
    extracted_entities = extract_entities_rule_based(full_text)
    
    entity_names = set()
    new_entities_count = 0
    
    print(f"   🔍 发现 {len(extracted_entities)} 个候选实体")
    
    for entity in extracted_entities:
        name = entity["original"]
        if name not in entity_names:
            entity_names.add(name)
            
            # 添加到数据库
            entity_id = kb_database.add_entity(
                name=name,
                etype=entity["type"],
                description=f"从{os.path.basename(file_path)}提取",
                source="rule",
                source_doc=os.path.basename(file_path)
            )
            
            if entity_id:
                new_entities_count += 1
    
    print(f"   + 新增实体: {new_entities_count}")
    
    # 5. 提取关系
    extracted_relations = extract_relationships_rule_based(full_text, entity_names)
    new_rels_count = 0
    
    for rel in extracted_relations:
        rel_id = kb_database.add_relationship(
            source_name=rel["source"],
            target_name=rel["target"],
            rel_type=rel["type"]
        )
        if rel_id:
            new_rels_count += 1
    
    print(f"   + 新增关系: {new_rels_count}")
    
    # 6. 存储文档和切片
    doc_id = kb_database.add_document(
        filename=os.path.basename(file_path),
        file_path=file_path,
        content=content,
        chunks=chunks
    )
    
    # 7. 输出统计
    stats = kb_database.get_stats()
    print(f"\n   📊 图谱统计: {stats['entities']} 实体, {stats['relationships']} 关系")
    
    return {
        "status": "success",
        "doc_id": doc_id,
        "chunks": len(chunks),
        "new_entities": new_entities_count,
        "new_relations": new_rels_count,
        "total_entities": stats["entities"],
        "total_relations": stats["relationships"]
    }

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python build_graph.py <file_path> [mode]")
        print("")
        print("Modes:")
        print("  --rule-only    仅使用规则匹配 (0 Token) [默认]")
        print("  --llm-enhanced 使用 LLM 精炼 (消耗 Token)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    mode = "rule-only"
    if len(sys.argv) > 2 and "--llm-enhanced" in sys.argv:
        mode = "llm-enhanced"
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        sys.exit(1)
    
    # 检查API Key
    api_key = get_api_key()
    if mode == "llm-enhanced" and not api_key:
        print("⚠️ 警告: 未设置 MINIMAX_API_KEY 环境变量，将使用规则匹配模式")
        mode = "rule-only"
    
    result = import_document(file_path, mode)
    
    print("\n" + "=" * 50)
    if result["status"] == "success":
        print("✅ 文档导入成功!")
    elif result["status"] == "skipped":
        print("⏭️  文档已存在且未变更")
    else:
        print("❌ 导入失败")
    print("=" * 50)

if __name__ == "__main__":
    main()
