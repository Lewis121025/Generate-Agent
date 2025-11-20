"""测试序列化问题"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lewis_ai_system.creative.repository import creative_repository
from lewis_ai_system.creative.models import CreativeProjectCreateRequest, CreativeProjectResponse


async def test():
    print("创建项目...")
    req = CreativeProjectCreateRequest(title="测试", brief="测试brief")
    proj = await creative_repository.create(req)
    print(f"创建成功: {proj.id}, 状态: {proj.state}")
    
    print("\n获取项目...")
    retrieved = await creative_repository.get(proj.id)
    print(f"获取成功: {retrieved.id}, 状态: {retrieved.state}")
    
    print("\n测试序列化...")
    try:
        response = CreativeProjectResponse(project=retrieved)
        serialized = response.model_dump(mode="json")
        print(f"序列化成功，字段数: {len(serialized.get('project', {}))}")
        print(f"项目ID: {serialized['project']['id']}")
        print(f"状态: {serialized['project']['state']}")
        print("✅ 所有测试通过！")
    except Exception as e:
        print(f"❌ 序列化失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())

