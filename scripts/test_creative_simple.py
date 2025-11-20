"""简单的创作模式测试"""

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


async def test_creative():
    """测试创作模式：创建30秒产品宣传视频"""
    print("\n" + "=" * 80)
    print("创作模式测试：产品宣传视频")
    print("=" * 80 + "\n")
    
    async with httpx.AsyncClient(timeout=300) as client:
        # 1. 创建项目
        print("[1] 创建视频项目...")
        create_payload = {
            "title": "AI视频生成工具宣传视频",
            "brief": "创建一个30秒的产品宣传视频，展示AI视频生成工具的核心功能。视频应该：1) 开头展示产品logo和slogan，2) 中间展示主要功能（文本生成视频、快速渲染、高质量输出），3) 结尾展示使用场景和客户见证。风格要求：现代、专业、科技感，色彩以蓝色和白色为主。",
            "duration_seconds": 30,
            "budget_usd": 10.0,
        }
        
        try:
            response = await client.post(f"{BASE_URL}/creative/projects", json=create_payload)
            response.raise_for_status()
            project_data = response.json()
            project_id = project_data["project"]["id"]
            project = project_data["project"]
            
            print(f"[OK] 项目已创建: {project_id}")
            print(f"   标题: {project['title']}")
            print(f"   状态: {project['state']}")
            print(f"   预算: ${create_payload['budget_usd']}")
            
            # 2. 推进到脚本阶段
            print("\n[2] 推进到脚本阶段...")
            response = await client.post(f"{BASE_URL}/creative/projects/{project_id}/advance")
            response.raise_for_status()
            project = response.json()["project"]
            print(f"   新状态: {project['state']}")
            
            if project.get("script"):
                script = project["script"]
                if isinstance(script, dict):
                    print(f"   脚本已生成，长度: {len(script.get('content', ''))} 字符")
                    if script.get("scenes"):
                        print(f"   场景数: {len(script['scenes'])}")
                else:
                    print(f"   脚本已生成: {str(script)[:100]}...")
            
            # 3. 审批脚本
            if project["state"] == "script_review":
                print("\n[3] 审批脚本...")
                response = await client.post(f"{BASE_URL}/creative/projects/{project_id}/approve-script")
                response.raise_for_status()
                project = response.json()["project"]
                print(f"   状态: {project['state']}")
            
            # 4. 推进到分镜阶段
            print("\n[4] 推进到分镜阶段...")
            response = await client.post(f"{BASE_URL}/creative/projects/{project_id}/advance")
            response.raise_for_status()
            project = response.json()["project"]
            print(f"   新状态: {project['state']}")
            
            if project.get("storyboard"):
                storyboard = project["storyboard"]
                if isinstance(storyboard, dict) and storyboard.get("panels"):
                    print(f"   分镜数: {len(storyboard['panels'])}")
                elif isinstance(storyboard, list):
                    print(f"   分镜数: {len(storyboard)}")
            
            # 5. 获取最终结果
            print("\n[5] 获取最终结果...")
            response = await client.get(f"{BASE_URL}/creative/projects/{project_id}")
            response.raise_for_status()
            final_project = response.json()["project"]
            
            print(f"\n最终状态: {final_project['state']}")
            print(f"总成本: ${final_project.get('cost_tracker', {}).get('spent_usd', 0):.4f}")
            
            if final_project.get("script"):
                script = final_project["script"]
                if isinstance(script, dict):
                    print(f"\n脚本预览:\n{script.get('content', '')[:300]}...")
                else:
                    print(f"\n脚本预览:\n{str(script)[:300]}...")
            
            return final_project
            
        except httpx.HTTPStatusError as e:
            print(f"[ERROR] HTTP错误: {e.response.status_code}")
            print(f"响应: {e.response.text}")
            return None
        except Exception as e:
            print(f"[ERROR] 错误: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    result = asyncio.run(test_creative())
    if result:
        print("\n[OK] 测试完成！")
    else:
        print("\n[FAIL] 测试失败！")

