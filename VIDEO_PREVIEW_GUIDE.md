# 创作模式视频预览功能说明

## ✨ 功能概述

创作模式现在支持完整的视频预览功能！在项目完成后，你可以：

1. 📺 **预览主视频** - 查看合成后的完整视频
2. 🎬 **浏览所有镜头** - 单独查看每个生成的视频片段
3. 🔗 **在新窗口打开** - 全屏播放视频
4. 📊 **查看质量评分** - 了解AI的质量控制评估

## 🎯 工作流程

### 1. 创建项目
```bash
POST /creative/projects
{
  "title": "我的视频项目",
  "brief": "描述你想要创作的视频内容...",
  "duration_seconds": 30,
  "style": "cinematic"
}
```

### 2. 完成工作流
执行以下步骤（通过 `/advance` 端点）：
- ✅ Brief 扩展 → Script 生成
- ✅ Script 审批 → Storyboard 生成
- ✅ Storyboard → Shots 生成（生成实际视频）
- ✅ Shots → Render → Preview（生成预览）

### 3. 查看视频预览

访问项目详情页：`http://localhost:3000/creative/{project_id}`

页面将显示：

#### 📺 主预览播放器
- 完整的视频预览
- 质量评分和QC状态
- 视频控制（播放/暂停/跳转）
- 在新窗口打开按钮

#### 🎬 镜头画廊
- 网格布局展示所有生成的镜头
- 每个镜头的独立播放器
- 镜头状态标识
- 提示词（prompt）显示
- 单独打开每个镜头

## 📱 前端界面

### 视频预览卡片
```tsx
<Card>
  <video 
    src={preview_url} 
    controls 
    className="aspect-video"
  />
  <CardContent>
    <h3>视频预览</h3>
    <p>QC 评分: {quality_score} · {qc_status}</p>
    <Button>在新窗口打开</Button>
  </CardContent>
</Card>
```

### 镜头画廊
```tsx
<Card>
  <CardHeader>
    <CardTitle>生成的镜头</CardTitle>
  </CardHeader>
  <CardContent>
    <Grid>
      {shots.map(shot => (
        <div>
          <video src={shot.video_url} controls />
          <Badge>{shot.status}</Badge>
          <p>{shot.prompt}</p>
        </div>
      ))}
    </Grid>
  </CardContent>
</Card>
```

## 🔧 后端实现

### PreviewRecord 模型
```python
class PreviewRecord(BaseModel):
    preview_url: str | None = None        # 预览视频URL
    preview_path: str | None = None       # 本地路径
    quality_score: float | None = None    # 质量评分
    qc_status: Literal["pending", "approved", ...] = "pending"
    qc_notes: str | None = None
```

### 预览生成逻辑
```python
async def _generate_preview(self, project: CreativeProject) -> bool:
    # 1. 运行质量控制检查
    qc_result = await self._run_qc_workflow(project)
    
    # 2. 生成预览内容
    preview_content = {...}
    preview_path = self.storage.save_json(...)
    
    # 3. 从第一个完成的镜头获取预览URL
    preview_url = None
    if project.shots:
        for shot in project.shots:
            if shot.video_url:
                preview_url = shot.video_url
                break
    
    # 4. 保存预览记录
    project.preview_record = PreviewRecord(
        preview_path=preview_path,
        preview_url=preview_url,
        quality_score=qc_result["overall_score"],
        qc_status="approved" if qc_result["passed"] else "needs_revision"
    )
```

## 🧪 测试

### 快速测试
```bash
# 运行测试脚本
python test_video_preview.py
```

测试脚本将：
1. 创建一个新项目
2. 完成整个工作流
3. 生成视频预览
4. 输出预览URL和项目信息

### 手动测试

1. **启动后端**
   ```bash
   cd c:\Learn\Lewis_AI_System
   uvicorn lewis_ai_system.main:app --reload
   ```

2. **启动前端**
   ```bash
   cd frontend
   npm run dev
   ```

3. **创建项目**
   - 访问 http://localhost:3000
   - 选择 Creative Mode
   - 输入项目描述
   - 点击 Start

4. **查看预览**
   - 等待工作流完成
   - 自动跳转到项目详情页
   - 查看视频预览和镜头画廊

## 📊 API 响应示例

### 获取项目详情
```json
{
  "id": "proj_123",
  "title": "我的视频",
  "state": "preview_ready",
  "preview_record": {
    "preview_url": "https://example.com/video.mp4",
    "quality_score": 8.5,
    "qc_status": "approved",
    "qc_notes": null
  },
  "shots": [
    {
      "scene_number": 1,
      "video_url": "https://example.com/shot1.mp4",
      "status": "completed",
      "prompt": "Opening scene with AI concept"
    },
    {
      "scene_number": 2,
      "video_url": "https://example.com/shot2.mp4",
      "status": "completed",
      "prompt": "Showcase of AI tools"
    }
  ]
}
```

## 🎨 UI 特性

### 响应式设计
- ✅ 桌面端：2列镜头网格
- ✅ 移动端：1列镜头网格
- ✅ 自适应视频播放器

### 交互特性
- ✅ 原生 HTML5 视频控制
- ✅ 悬停效果和过渡动画
- ✅ 状态标识（完成/处理中）
- ✅ 一键在新窗口打开

### 视觉反馈
- ✅ 玻璃态卡片效果
- ✅ 质量评分显示
- ✅ 加载状态指示
- ✅ 镜头描述显示

## 🚀 未来增强

### 计划中的功能
- [ ] 视频编辑器集成
- [ ] 字幕/标题添加
- [ ] 背景音乐选择
- [ ] 多种导出格式
- [ ] 批量下载镜头
- [ ] 时间轴编辑
- [ ] 转场效果预设

### 性能优化
- [ ] 视频懒加载
- [ ] 缩略图预生成
- [ ] CDN 加速
- [ ] 流式播放支持

## 📝 注意事项

1. **视频生成**：实际视频生成需要配置相应的Provider（Runway、Pika等）
2. **存储**：视频文件较大，建议使用S3或类似的对象存储
3. **成本**：视频生成API调用会产生费用，请注意预算控制
4. **时间**：生成视频可能需要几分钟，请耐心等待

## 🔗 相关文件

- 前端页面：`frontend/src/app/creative/[id]/page.tsx`
- 后端工作流：`src/lewis_ai_system/creative/workflow.py`
- 数据模型：`src/lewis_ai_system/creative/models.py`
- API类型：`frontend/src/lib/api.ts`
- 测试脚本：`test_video_preview.py`

---

**更新时间**: 2025-11-20  
**功能状态**: ✅ 已实现并测试
