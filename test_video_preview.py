"""
测试创作模式的视频预览功能

这个脚本演示如何：
1. 创建一个创作项目
2. 完成整个工作流（Brief -> Script -> Storyboard -> Shots -> Preview）
3. 查看生成的视频预览
"""

import asyncio
import httpx

API_BASE = "http://localhost:8000"


async def test_video_preview():
    """测试完整的视频预览工作流"""
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("🎬 创建创作项目...")
        # 1. 创建项目
        response = await client.post(
            f"{API_BASE}/creative/projects",
            json={
                "title": "AI视频生成演示",
                "brief": "创建一个30秒的视频，展示AI如何改变内容创作。包含：开场介绍、AI工具展示、未来展望。风格要现代、专业、有科技感。",
                "duration_seconds": 30,
                "style": "cinematic",
                "budget_limit_usd": 50.0,
                "tenant_id": "demo",
            },
        )
        response.raise_for_status()
        project = response.json()
        project_id = project["id"]
        print(f"✅ 项目创建成功: {project_id}")
        print(f"   状态: {project['state']}")

        # 2. 推进到脚本生成
        print("\n📝 生成脚本...")
        response = await client.post(f"{API_BASE}/creative/projects/{project_id}/advance")
        response.raise_for_status()
        project = response.json()
        print(f"✅ 脚本生成完成")
        print(f"   状态: {project['state']}")
        if project.get("script"):
            print(f"   脚本预览: {project['script'][:100]}...")

        # 3. 审批脚本
        print("\n✔️  审批脚本...")
        response = await client.post(
            f"{API_BASE}/creative/projects/{project_id}/approve-script"
        )
        response.raise_for_status()
        project = response.json()
        print(f"✅ 脚本已审批")
        print(f"   状态: {project['state']}")

        # 4. 生成分镜
        print("\n🎨 生成分镜...")
        response = await client.post(f"{API_BASE}/creative/projects/{project_id}/advance")
        response.raise_for_status()
        project = response.json()
        print(f"✅ 分镜生成完成")
        print(f"   状态: {project['state']}")
        if project.get("storyboard"):
            print(f"   分镜数量: {len(project['storyboard'])}")

        # 5. 生成视频镜头（这一步会调用实际的视频生成API）
        print("\n🎥 生成视频镜头（可能需要几分钟）...")
        response = await client.post(f"{API_BASE}/creative/projects/{project_id}/advance")
        response.raise_for_status()
        project = response.json()
        print(f"✅ 镜头生成完成")
        print(f"   状态: {project['state']}")
        if project.get("shots"):
            print(f"   镜头数量: {len(project['shots'])}")
            for idx, shot in enumerate(project["shots"], 1):
                print(f"   镜头 {idx}: {shot.get('status')} - {shot.get('video_url', '无URL')}")

        # 6. 生成预览
        print("\n🎬 生成预览...")
        response = await client.post(f"{API_BASE}/creative/projects/{project_id}/advance")
        response.raise_for_status()
        project = response.json()
        print(f"✅ 预览生成完成")
        print(f"   状态: {project['state']}")

        # 7. 检查预览记录
        if project.get("preview_record"):
            preview = project["preview_record"]
            print(f"\n📺 视频预览信息:")
            print(f"   预览URL: {preview.get('preview_url', '无')}")
            print(f"   质量评分: {preview.get('quality_score', '无')}")
            print(f"   QC状态: {preview.get('qc_status', '无')}")
            
            if preview.get("preview_url"):
                print(f"\n🌐 在浏览器中打开: http://localhost:3000/creative/{project_id}")
                print(f"   或直接访问视频: {preview['preview_url']}")
        else:
            print("\n⚠️  预览记录未生成")

        # 8. 获取完整项目信息
        print("\n📊 项目完整信息:")
        response = await client.get(f"{API_BASE}/creative/projects/{project_id}")
        response.raise_for_status()
        project = response.json()
        
        print(f"   项目ID: {project['id']}")
        print(f"   标题: {project['title']}")
        print(f"   状态: {project['state']}")
        print(f"   预算: ${project['budget_limit_usd']}")
        print(f"   已花费: ${project['cost_usd']:.2f}")
        print(f"   脚本: {'✓' if project.get('script') else '✗'}")
        print(f"   分镜: {len(project.get('storyboard', []))} 个")
        print(f"   镜头: {len(project.get('shots', []))} 个")
        print(f"   预览: {'✓' if project.get('preview_record', {}).get('preview_url') else '✗'}")

        return project_id


if __name__ == "__main__":
    print("=" * 60)
    print("创作模式视频预览功能测试")
    print("=" * 60)
    print("\n确保后端服务正在运行: http://localhost:8000")
    print("确保前端服务正在运行: http://localhost:3000")
    print("\n开始测试...\n")
    
    try:
        project_id = asyncio.run(test_video_preview())
        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print(f"🌐 在浏览器中查看项目: http://localhost:3000/creative/{project_id}")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
