"""诊断500错误的详细脚本"""

import asyncio
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

BASE_URL = "http://localhost:8000"


async def diagnose():
    # 1. 创建一个新项目
    print("步骤1: 创建新项目...")
    async with httpx.AsyncClient(timeout=30) as client:
        create_payload = {
            "title": "诊断测试",
            "brief": "测试brief",
            "duration_seconds": 30,
        }
        
        response = await client.post(f"{BASE_URL}/creative/projects", json=create_payload)
        print(f"  状态码: {response.status_code}")
        if response.status_code == 201:
            project_id = response.json()["project"]["id"]
            print(f"  项目ID: {project_id}")
            
            # 2. 立即获取项目
            print("\n步骤2: 获取项目详情...")
            response = await client.get(f"{BASE_URL}/creative/projects/{project_id}")
            print(f"  状态码: {response.status_code}")
            print(f"  响应头: {dict(response.headers)}")
            
            if response.status_code == 500:
                print("\n错误详情:")
                try:
                    error_json = response.json()
                    print(f"  JSON响应: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                except:
                    print(f"  文本响应: {response.text}")
                    print(f"  响应长度: {len(response.text)}")
            elif response.status_code == 200:
                data = response.json()
                print(f"  成功！项目状态: {data['project']['state']}")
                print(f"  字段数: {len(data['project'])}")
        else:
            print(f"  创建失败: {response.text}")


if __name__ == "__main__":
    asyncio.run(diagnose())

