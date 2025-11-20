"""完整工作流测试 - 不获取最终结果"""

import asyncio
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

BASE_URL = "http://localhost:8000"


async def test_creative_full():
    """测试创作模式完整工作流"""
    print("\n" + "=" * 80)
    print("创作模式完整工作流测试")
    print("=" * 80 + "\n")
    
    async with httpx.AsyncClient(timeout=300) as client:
        # 1. 创建项目
        print("[1] 创建项目...")
        create_payload = {
            "title": "AI视频生成工具宣传视频",
            "brief": "创建一个30秒的产品宣传视频，展示AI视频生成工具的核心功能。",
            "duration_seconds": 30,
            "budget_usd": 10.0,
        }
        
        response = await client.post(f"{BASE_URL}/creative/projects", json=create_payload)
        if response.status_code != 201:
            print(f"[FAIL] 创建失败: {response.status_code} - {response.text}")
            return False
        
        project_data = response.json()
        project_id = project_data["project"]["id"]
        project = project_data["project"]
        
        print(f"[OK] 项目已创建: {project_id}")
        print(f"   状态: {project['state']}")
        
        # 2. 审批脚本
        if project["state"] == "script_review":
            print("\n[2] 审批脚本...")
            response = await client.post(f"{BASE_URL}/creative/projects/{project_id}/approve-script")
            if response.status_code != 200:
                print(f"[FAIL] 审批失败: {response.status_code} - {response.text}")
                return False
            project = response.json()["project"]
            print(f"[OK] 脚本已审批，状态: {project['state']}")
        
        # 3. 推进到分镜
        if project["state"] == "storyboard_ready":
            print("\n[3] 分镜已生成")
            if project.get("storyboard"):
                storyboard = project["storyboard"]
                if isinstance(storyboard, list):
                    print(f"   分镜数: {len(storyboard)}")
                elif isinstance(storyboard, dict) and storyboard.get("panels"):
                    print(f"   分镜数: {len(storyboard['panels'])}")
        
        # 4. 尝试获取项目（测试修复）
        print("\n[4] 测试获取项目...")
        response = await client.get(f"{BASE_URL}/creative/projects/{project_id}")
        if response.status_code == 200:
            print("[OK] 获取项目成功！")
            final_project = response.json()["project"]
            print(f"   最终状态: {final_project['state']}")
            print(f"   总成本: ${final_project.get('cost_usd', 0):.4f}")
            return True
        else:
            print(f"[FAIL] 获取项目失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误详情: {error_data}")
            except:
                print(f"   错误文本: {response.text[:200]}")
            return False


async def test_general_simple():
    """测试通用模式简单流程"""
    print("\n" + "=" * 80)
    print("通用模式测试")
    print("=" * 80 + "\n")
    
    async with httpx.AsyncClient(timeout=300) as client:
        # 1. 创建会话
        print("[1] 创建会话...")
        create_payload = {
            "goal": "简要说明AI视频生成的主要优势",
            "budget_usd": 2.0,
            "max_iterations": 3,
        }
        
        response = await client.post(f"{BASE_URL}/general/sessions", json=create_payload)
        if response.status_code != 201:
            print(f"[FAIL] 创建失败: {response.status_code} - {response.text}")
            return False
        
        session_data = response.json()
        session_id = session_data["session"]["id"]
        print(f"[OK] 会话已创建: {session_id}")
        
        # 2. 执行一次迭代
        print("\n[2] 执行迭代...")
        response = await client.post(f"{BASE_URL}/general/sessions/{session_id}/iterate")
        if response.status_code == 200:
            session = response.json()["session"]
            print(f"[OK] 迭代完成，状态: {session.get('status')}")
            print(f"   成本: ${session.get('spent_usd', 0):.4f}")
            return True
        else:
            print(f"[FAIL] 迭代失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误详情: {error_data}")
            except:
                print(f"   错误文本: {response.text[:200]}")
            return False


async def main():
    results = {}
    
    # 测试创作模式
    results["creative"] = await test_creative_full()
    
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    if results["creative"]:
        print("[OK] 创作模式测试通过")
    else:
        print("[FAIL] 创作模式测试失败")
    
    # 测试通用模式
    results["general"] = await test_general_simple()
    
    if results["general"]:
        print("[OK] 通用模式测试通过")
    else:
        print("[FAIL] 通用模式测试失败")
    
    print("\n" + "=" * 80)
    if all(results.values()):
        print("所有测试通过！")
    else:
        print("部分测试失败，请查看上述错误信息")


if __name__ == "__main__":
    asyncio.run(main())

