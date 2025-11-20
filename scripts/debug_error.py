"""调试500错误的脚本"""

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


async def test():
    async with httpx.AsyncClient(timeout=30) as client:
        # 创建一个新项目
        print("创建项目...")
        create_payload = {
            "title": "测试项目",
            "brief": "测试brief",
            "duration_seconds": 30,
            "budget_usd": 10.0,
        }
        
        response = await client.post(f"{BASE_URL}/creative/projects", json=create_payload)
        print(f"创建响应状态: {response.status_code}")
        if response.status_code != 201:
            print(f"错误: {response.text}")
            return
        
        project_data = response.json()
        project_id = project_data["project"]["id"]
        print(f"项目ID: {project_id}")
        
        # 立即获取项目
        print("\n获取项目...")
        response = await client.get(f"{BASE_URL}/creative/projects/{project_id}")
        print(f"获取响应状态: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
        
        if response.status_code == 500:
            try:
                error_data = response.json()
                print(f"\n错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"\n原始错误: {response.text}")


if __name__ == "__main__":
    asyncio.run(test())

