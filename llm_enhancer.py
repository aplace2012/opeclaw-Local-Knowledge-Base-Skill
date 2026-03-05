#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 精炼模块 - 制造业数字化版
使用 Minimax 大模型进行深度实体识别和关系抽取
"""

import json
import os
import sys
import hashlib
import re
import requests

# Minimax API 配置 - 运行时动态获取
def get_api_key():
    """动态获取API Key"""
    key = os.getenv('MINIMAX_API_KEY')
    if not key:
        try:
            import subprocess
            result = subprocess.run(
                ['powershell', '-Command', '[System.Environment]::GetEnvironmentVariable(\'MINIMAX_API_KEY\', \'User\')'],
                capture_output=True, text=True, timeout=10
            )
            key = result.stdout.strip()
        except:
            pass
    return key

# 初始化时获取
MINIMAX_API_KEY = get_api_key()
MINIMAX_BASE_URL = "https://api.minimaxi.com/v1"
MODEL_NAME = "MiniMax-M2.5"

# 知识库路径 - 动态获取
KB_DIR = os.path.expanduser("~/.openclaw/workspace/knowledge_base")
CACHE_DIR = os.path.join(KB_DIR, "llm_cache")

os.makedirs(CACHE_DIR, exist_ok=True)

# 制造业优化的LLM提示词
LLM_PROMPT_TEMPLATE = """你是一个制造业数字化知识图谱专家。

从以下文档中提取实体和关系。

## 实体类型
企业、组织、供应商、物料、产品、工序、设备、系统、技术、指标、方案、痛点、场景

## 关系类型
供应、用于、经过、使用、部署、采用、解决、核心功能、关联、负责、位于

## 输出格式（JSON）
{{
  "entities": [{{"name": "名称", "type": "类型"}}],
  "relationships": [{{"source": "实体A", "target": "实体B", "type": "关系"}}]
}}

文档内容：
{content}

直接输出JSON。"""

def get_cache_key(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def test_connection():
    """测试API连接"""
    if not MINIMAX_API_KEY:
        return {"error": "API Key未设置"}
    
    # 简单测试
    url = "{}/chat/completions".format(MINIMAX_BASE_URL)
    headers = {
        "Authorization": "Bearer {}".format(MINIMAX_API_KEY),
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "你好，请回复'LLM连接成功'"}
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return {"success": True, "response": result.get("choices", [{}])[0].get("message", {}).get("content", "")}
        else:
            return {"error": f"HTTP {response.status_code}", "detail": response.text[:200]}
    except Exception as e:
        return {"error": str(e)}

def describe_image_from_url(image_url, prompt="请详细描述这张图片的内容"):
    """
    使用LLM多模态能力描述图片
    image_url: 图片URL（需可访问）
    """
    if not MINIMAX_API_KEY:
        return {"error": "API Key未设置"}
    
    url = "{}/chat/completions".format(MINIMAX_BASE_URL)
    headers = {
        "Authorization": "Bearer {}".format(MINIMAX_API_KEY),
        "Content-Type": "application/json"
    }
    
    # MiniMax多模态格式
    payload = {
        "model": MODEL_NAME,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"success": True, "description": content}
        else:
            return {"error": f"HTTP {response.status_code}", "detail": response.text[:200]}
    except Exception as e:
        return {"error": str(e)}

def describe_image_from_bytes(image_bytes, prompt="请详细描述这张图片的内容"):
    """
    使用LLM多模态能力描述本地图片
    image_bytes: 图片二进制数据
    """
    import base64
    import io
    
    # 将图片转为base64
    b64_img = base64.b64encode(image_bytes).decode('utf-8')
    
    if not MINIMAX_API_KEY:
        return {"error": "API Key未设置"}
    
    url = "{}/chat/completions".format(MINIMAX_BASE_URL)
    headers = {
        "Authorization": "Bearer {}".format(MINIMAX_API_KEY),
        "Content-Type": "application/json"
    }
    
    # MiniMax多模态格式 - 使用base64
    payload = {
        "model": MODEL_NAME,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
            ]
        }],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"success": True, "description": content}
        else:
            return {"error": f"HTTP {response.status_code}", "detail": response.text[:200]}
    except Exception as e:
        return {"error": str(e)}

def load_from_cache(cache_key):
    cache_file = os.path.join(CACHE_DIR, "{}.json".format(cache_key))
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_to_cache(cache_key, data):
    cache_file = os.path.join(CACHE_DIR, "{}.json".format(cache_key))
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def call_minimax_llm(prompt):
    url = "{}/chat/completions".format(MINIMAX_BASE_URL)
    headers = {
        "Authorization": "Bearer {}".format(MINIMAX_API_KEY),
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "你是知识图谱专家，直接输出JSON。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            print("API Error: {} {}".format(response.status_code, response.text[:100]))
            return None
    except Exception as e:
        print("LLM Error: {}".format(str(e)[:100]))
        return None

def parse_llm_response(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except:
        pass
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return None

def llm_enhance(content, use_cache=True):
    truncated = content[:4000]
    prompt = LLM_PROMPT_TEMPLATE.format(content=truncated)
    cache_key = get_cache_key(prompt)
    
    if use_cache:
        cached = load_from_cache(cache_key)
        if cached:
            print("Use cached")
            return cached
    
    response = call_minimax_llm(prompt)
    if response:
        result = parse_llm_response(response)
        if result:
            if use_cache:
                save_to_cache(cache_key, result)
            print("LLM Done")
            return result
    
    return {"entities": [], "relationships": []}

def llm_enhance_batch(chunks, use_cache=True):
    combined = "\n\n".join([c[:600] if isinstance(c, str) else c.get("content", "")[:600] for c in chunks[:6]])
    return llm_enhance(combined, use_cache)

def llm_enhance_batch_manufacturing(chunks, use_cache=True):
    return llm_enhance_batch(chunks, use_cache)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        content = " ".join(sys.argv[1:])
        result = llm_enhance(content)
        print(json.dumps(result, ensure_ascii=False, indent=2))
