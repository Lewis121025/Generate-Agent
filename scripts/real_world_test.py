"""真实世界任务测试脚本

测试两个真实场景：
1. General Mode: 研究2025年AI视频生成市场趋势
2. Creative Mode: 创建一个30秒的产品宣传视频
"""

import asyncio
import json
import sys
from pathlib import Path
from pprint import pprint

import httpx

# Add src to path
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

BASE_URL = "http://localhost:8000"
TIMEOUT = 300  # 5分钟超时


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


async def test_general_mode():
    """测试通用模式：研究2025年AI视频生成市场趋势"""
    print_section("通用模式测试：AI视频生成市场研究")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # 1. 创建会话
        print("[1] 创建研究会话...")
        create_payload = {
            "goal": "研究2025年AI视频生成市场的最新趋势，包括主要供应商、价格对比、技术突破和市场规模预测。生成一份包含关键发现和建议的研究报告。",
            "budget_usd": 5.0,
            "max_iterations": 10,
            "tool_whitelist": ["web_search", "web_scrape", "python_code"],
        }
        
        response = await client.post(f"{BASE_URL}/general/sessions", json=create_payload)
        response.raise_for_status()
        session_data = response.json()
        session_id = session_data["session"]["id"]
        
        print(f"[OK] 会话已创建: {session_id}")
        print(f"   目标: {create_payload['goal'][:60]}...")
        print(f"   预算: ${create_payload['budget_usd']}")
        
        # 2. 执行迭代
        print("\n[2] 开始执行研究任务...")
        iteration_count = 0
        max_iterations = create_payload["max_iterations"]
        
        while iteration_count < max_iterations:
            iteration_count += 1
            print(f"\n--- 迭代 {iteration_count}/{max_iterations} ---")
            
            try:
                response = await client.post(f"{BASE_URL}/general/sessions/{session_id}/iterate")
                response.raise_for_status()
                result = response.json()
                session = result["session"]
                
                # 显示当前状态
                print(f"状态: {session.get('status', 'unknown')}")
                print(f"成本: ${session.get('cost_tracker', {}).get('spent_usd', 0):.4f}")
                
                # 显示最后一步的工具调用
                if session.get("turns"):
                    last_turn = session["turns"][-1]
                    if last_turn.get("tool_calls"):
                        tool_call = last_turn["tool_calls"][-1]
                        print(f"工具: {tool_call.get('tool_name', 'unknown')}")
                        if tool_call.get("output"):
                            output = tool_call["output"]
                            if isinstance(output, dict):
                                output_str = json.dumps(output, ensure_ascii=False, indent=2)[:200]
                            else:
                                output_str = str(output)[:200]
                            print(f"输出: {output_str}...")
                
                # 检查是否完成
                if session.get("status") in ["completed", "failed", "paused"]:
                    print(f"\n[OK] 任务完成，状态: {session.get('status')}")
                    break
                    
            except httpx.HTTPStatusError as e:
                print(f"[ERROR] HTTP错误: {e.response.status_code}")
                print(f"响应: {e.response.text}")
                break
            except Exception as e:
                print(f"[ERROR] 错误: {e}")
                break
        
        # 3. 获取最终结果
        print("\n[3] 获取最终结果...")
        response = await client.get(f"{BASE_URL}/general/sessions/{session_id}")
        response.raise_for_status()
        final_result = response.json()
        session = final_result["session"]
        
        print(f"\n最终状态: {session.get('status')}")
        print(f"总成本: ${session.get('cost_tracker', {}).get('spent_usd', 0):.4f}")
        print(f"迭代次数: {len(session.get('turns', []))}")
        
        if session.get("final_summary"):
            print(f"\n最终摘要:\n{session['final_summary']}")
        
        return session


async def test_creative_mode():
    """测试创作模式：创建30秒产品宣传视频"""
    print_section("创作模式测试：产品宣传视频")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # 1. 创建项目
        print("[1] 创建视频项目...")
        create_payload = {
            "title": "AI视频生成工具宣传视频",
            "brief": "创建一个30秒的产品宣传视频，展示AI视频生成工具的核心功能。视频应该：1) 开头展示产品logo和slogan，2) 中间展示主要功能（文本生成视频、快速渲染、高质量输出），3) 结尾展示使用场景和客户见证。风格要求：现代、专业、科技感，色彩以蓝色和白色为主。",
            "duration_seconds": 30,
            "budget_usd": 10.0,
        }
        
        response = await client.post(f"{BASE_URL}/creative/projects", json=create_payload)
        response.raise_for_status()
        project_data = response.json()
        project_id = project_data["project"]["id"]
        project = project_data["project"]
        
        print(f"[OK] 项目已创建: {project_id}")
        print(f"   标题: {project['title']}")
        print(f"   状态: {project['state']}")
        print(f"   预算: ${create_payload['budget_usd']}")
        
        # 2. 推进工作流
        print("\n[2] 推进工作流...")
        stages = [
            ("Brief", "brief_pending"),
            ("Script", "script_pending"),
            ("Storyboard", "storyboard_pending"),
            ("Render", "render_pending"),
        ]
        
        for stage_name, target_state in stages:
            print(f"\n--- {stage_name} 阶段 ---")
            
            # 检查当前状态
            response = await client.get(f"{BASE_URL}/creative/projects/{project_id}")
            response.raise_for_status()
            current_project = response.json()["project"]
            current_state = current_project["state"]
            
            print(f"当前状态: {current_state}")
            
            # 如果是脚本阶段，需要审批
            if current_state == "script_review":
                print("[审批] 审批脚本...")
                response = await client.post(f"{BASE_URL}/creative/projects/{project_id}/approve-script")
                response.raise_for_status()
                print("[OK] 脚本已审批")
                continue
            
            # 如果是预览阶段，需要审批
            if current_state == "preview_ready":
                print("[审批] 审批预览...")
                response = await client.post(f"{BASE_URL}/creative/projects/{project_id}/approve-preview")
                response.raise_for_status()
                print("[OK] 预览已审批")
                continue
            
            # 推进到下一阶段
            if current_state == target_state or current_state.endswith("_pending"):
                print(f"推进到下一阶段...")
                response = await client.post(f"{BASE_URL}/creative/projects/{project_id}/advance")
                response.raise_for_status()
                updated_project = response.json()["project"]
                print(f"新状态: {updated_project['state']}")
                
                # 显示阶段特定信息
                if stage_name == "Script" and updated_project.get("script"):
                    script = updated_project["script"]
                    print(f"脚本长度: {len(script.get('content', ''))} 字符")
                    if script.get("scenes"):
                        print(f"场景数: {len(script['scenes'])}")
                
                if stage_name == "Storyboard" and updated_project.get("storyboard"):
                    storyboard = updated_project["storyboard"]
                    if storyboard.get("panels"):
                        print(f"分镜数: {len(storyboard['panels'])}")
                
                if stage_name == "Render" and updated_project.get("render_manifest"):
                    manifest = updated_project["render_manifest"]
                    if manifest.get("shots"):
                        print(f"已生成镜头数: {len(manifest['shots'])}")
                        total_cost = sum(shot.get("cost_usd", 0) for shot in manifest["shots"])
                        print(f"渲染成本: ${total_cost:.4f}")
            
            # 检查是否完成或失败
            if updated_project["state"] in ["completed", "failed"]:
                print(f"\n[OK] 项目完成，最终状态: {updated_project['state']}")
                break
        
        # 3. 获取最终结果
        print("\n[3] 获取最终结果...")
        response = await client.get(f"{BASE_URL}/creative/projects/{project_id}")
        response.raise_for_status()
        final_result = response.json()
        project = final_result["project"]
        
        print(f"\n最终状态: {project['state']}")
        print(f"总成本: ${project.get('cost_tracker', {}).get('spent_usd', 0):.4f}")
        
        if project.get("script"):
            print(f"\n脚本: {project['script'].get('content', '')[:200]}...")
        
        if project.get("storyboard") and project["storyboard"].get("panels"):
            print(f"\n分镜数: {len(project['storyboard']['panels'])}")
        
        if project.get("render_manifest") and project["render_manifest"].get("shots"):
            shots = project["render_manifest"]["shots"]
            print(f"\n已生成镜头: {len(shots)}")
            for i, shot in enumerate(shots[:3], 1):  # 只显示前3个
                print(f"  镜头{i}: {shot.get('prompt', 'N/A')[:50]}...")
                if shot.get("video_url"):
                    print(f"    视频URL: {shot['video_url']}")
        
        return project


async def main():
    """主函数"""
    print_section("Lewis AI System 真实世界测试")
    print("测试两个真实场景：")
    print("1. General Mode: 研究2025年AI视频生成市场趋势")
    print("2. Creative Mode: 创建30秒产品宣传视频")
    print("\n确保服务已启动: docker compose up 或 python -m uvicorn lewis_ai_system.main:app")
    print("\n开始测试...\n")
    
    results = {}
    
    try:
        # 测试通用模式
        results["general"] = await test_general_mode()
    except Exception as e:
        print(f"\n[FAIL] 通用模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        results["general"] = None
    
    print("\n\n等待5秒后继续测试创作模式...\n")
    await asyncio.sleep(5)
    
    try:
        # 测试创作模式
        results["creative"] = await test_creative_mode()
    except Exception as e:
        print(f"\n[FAIL] 创作模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        results["creative"] = None
    
    # 总结
    print_section("测试总结")
    
    if results["general"]:
        print("[OK] 通用模式测试完成")
        print(f"   状态: {results['general'].get('status')}")
        print(f"   成本: ${results['general'].get('cost_tracker', {}).get('spent_usd', 0):.4f}")
    else:
        print("[FAIL] 通用模式测试失败")
    
    if results["creative"]:
        print("\n[OK] 创作模式测试完成")
        print(f"   状态: {results['creative'].get('state')}")
        print(f"   成本: ${results['creative'].get('cost_tracker', {}).get('spent_usd', 0):.4f}")
    else:
        print("\n[FAIL] 创作模式测试失败")
    
    print("\n测试完成！")


if __name__ == "__main__":
    asyncio.run(main())

