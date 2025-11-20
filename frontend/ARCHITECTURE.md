# Lewis AI System Frontend - Google AI Studio 风格重构

## 🎯 架构概览

本次重构将 Lewis AI System 前端从传统的"网页导向"设计升级为**"工作区导向"的 IDE 级应用**,完美复刻 Google AI Studio 的专业体验。

## 📁 新架构目录结构

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # 全局 Root Layout
│   │   ├── page.tsx            # 重定向到 /studio
│   │   ├── globals.css         # Google AI Studio 配色系统
│   │   └── studio/             # 核心工作区
│   │       ├── layout.tsx      # React Query Provider
│   │       └── page.tsx        # Studio 主入口
│   │
│   ├── components/
│   │   ├── layout/             # 布局组件
│   │   │   ├── StudioShell.tsx     # 三栏式布局容器
│   │   │   ├── StudioHeader.tsx    # 顶部工具栏
│   │   │   ├── StudioSidebar.tsx   # 左侧导航与资产库
│   │   │   └── ConfigPanel.tsx     # 右侧配置面板
│   │   │
│   │   ├── workspace/          # 画布组件
│   │   │   ├── GeneralCanvas.tsx   # 通用对话引擎
│   │   │   └── CreativeCanvas.tsx  # 创作工作流引擎
│   │   │
│   │   └── ui/                 # Shadcn/UI 原子组件
│   │
│   └── lib/
│       ├── stores/             # Zustand 状态管理
│       │   ├── types.ts        # 类型定义
│       │   └── studio.ts       # 核心 Store
│       └── hooks/              # 自定义 Hooks
```

## 🏗️ 核心架构特性

### 1. 三栏式布局 (Three-Pane Layout)

使用 `react-resizable-panels` 实现可调整大小的专业工作区:

- **左侧栏**: 会话历史 + 资产库 (Creative 模式)
- **中间画布**: 双引擎动态渲染 (General/Creative)
- **右侧栏**: 上下文配置面板 (动态绑定到当前模式)

### 2. Zustand 全局状态管理

```typescript
interface StudioStore {
  // 核心状态
  mode: 'general' | 'creative';
  currentSessionId: string | null;
  sessions: Session[];
  
  // 布局状态
  layout: LayoutState;
  
  // 动态配置
  generalConfig: GeneralConfig;
  creativeConfig: CreativeConfig;
  
  // 运行时
  isStreaming: boolean;
  creativeStage: CreativeStage | null;
}
```

### 3. 双引擎画布系统

#### General Canvas (通用对话引擎)
- 传统 Chat UI + 流式输出
- Tool Invocation Cards (可折叠的工具调用展示)
- 自动滚动 + Framer Motion 动画

#### Creative Canvas (视频创作引擎)
- 状态机驱动: `Drafting → Scripting → Visualizing → Rendering → Done`
- 块级编辑器 (Block-Based Editor)
- 分镜网格预览 + 视频播放器

### 4. Google AI Studio 视觉系统

#### 配色方案 (Dark Theme)
```css
--surface-1: #1E1F20  /* 主背景 */
--surface-2: #28292A  /* 卡片/面板 */
--surface-3: #3C4043  /* 悬浮/激活 */
--primary: #A8C7FA    /* Google Blue */
```

#### 设计原则
- **大圆角**: `rounded-google` (16px), `rounded-google-lg` (24px)
- **无边框输入**: Focus 时使用 Ring
- **Backdrop Blur**: 半透明面板 + 毛玻璃效果
- **平滑过渡**: `cubic-bezier(0.4, 0, 0.2, 1)`

## 🛠️ 技术栈

### 核心依赖
- **Next.js 14**: App Router + Server Components
- **Zustand**: 轻量级全局状态管理
- **TanStack Query**: 服务端数据缓存
- **Vercel AI SDK**: 流式 AI 响应处理
- **React Resizable Panels**: 可调整大小的布局
- **Framer Motion**: 流畅动画系统
- **Shadcn/UI**: 基于 Radix 的组件库

### 设计工具
- **Tailwind CSS 3.4**: 实用工具类
- **date-fns**: 时间格式化
- **lucide-react**: 图标库

## 🚀 核心功能

### 1. 无缝模式切换
- 顶部 Tab 切换 General/Creative 模式
- Store 自动同步 URL 参数
- 配置面板动态重渲染

### 2. 会话管理
- Optimistic UI (乐观更新)
- 本地持久化 (localStorage)
- 按模式分组展示

### 3. 响应式流处理
- Server-Sent Events (SSE)
- 逐 Token 渲染
- 停止生成按钮

### 4. 资产库 (Creative 模式)
- 视频/图片缩略图预览
- Lazy Loading
- Layout ID 动画 (点击放大)

## 📝 使用指南

### 启动开发服务器

```bash
cd frontend
npm install
npm run dev
```

访问: `http://localhost:3000` (自动重定向到 `/studio`)

### 创建新会话

```typescript
import { useStudioStore } from '@/lib/stores/studio';

const { createSession, switchSession } = useStudioStore();

// 创建 General 模式会话
const session = createSession('general', '我的新对话');
switchSession(session.id);
```

### 更新配置

```typescript
const { updateGeneralConfig, updateCreativeConfig } = useStudioStore();

// 调整 Temperature
updateGeneralConfig('temperature', 0.9);

// 切换视频 Provider
updateCreativeConfig('videoProvider', 'runway');
```

### 切换模式

```typescript
const { setMode } = useStudioStore();

// 切换到创作模式
setMode('creative');
```

## 🎨 自定义主题

### 修改颜色变量

编辑 `src/app/globals.css`:

```css
.dark {
  --primary: 214 95% 76%;  /* 修改主色调 */
  --surface-1: 220 15% 11%; /* 修改背景色 */
}
```

### 添加自定义动画

在 `tailwind.config.ts` 中扩展:

```typescript
keyframes: {
  myCustomAnimation: {
    '0%': { transform: 'scale(1)' },
    '100%': { transform: 'scale(1.1)' },
  },
},
animation: {
  'my-custom': 'myCustomAnimation 0.3s ease-out',
},
```

## 🔗 后端集成 (待实现)

### General 模式 API

```typescript
// TODO: 集成 Vercel AI SDK
import { useChat } from 'ai/react';

const { messages, input, handleSubmit, isLoading } = useChat({
  api: '/api/general/chat',
  body: {
    config: generalConfig,
  },
});
```

### Creative 模式 API

```typescript
// TODO: 调用视频生成 API
const generateScript = async (prompt: string) => {
  const response = await fetch('/api/creative/script', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  });
  return response.json();
};
```

## 📊 性能优化

### 1. 代码分割
- 画布组件使用 `dynamic import`
- 按模式懒加载引擎

### 2. 虚拟化列表
- 历史会话列表考虑使用 `react-window`
- 分镜网格使用 Intersection Observer

### 3. 图片优化
- 缩略图使用 `next/image`
- 视频 Poster 预加载

## 🐛 已知问题

- [ ] 需要集成真实的 SSE 流式响应
- [ ] Creative 模式状态持久化逻辑待完善
- [ ] 视频预览组件需要优化加载策略
- [ ] 移动端响应式布局需要调整

## 🚧 下一步计划

### Phase 1: 数据集成 (1-2天)
- [ ] 对接后端 General API
- [ ] 对接后端 Creative Workflow API
- [ ] 实现 SSE 流式响应

### Phase 2: 功能完善 (2-3天)
- [ ] 实现会话编辑/删除
- [ ] 添加键盘快捷键
- [ ] 实现搜索过滤功能

### Phase 3: 体验优化 (1-2天)
- [ ] 添加骨架屏加载
- [ ] 优化动画性能
- [ ] 完善错误处理

### Phase 4: 测试与部署
- [ ] 编写单元测试
- [ ] E2E 测试
- [ ] 生产环境优化

## 📚 参考资源

- [Google AI Studio](https://aistudio.google.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Zustand Documentation](https://docs.pmnd.rs/zustand)
- [Framer Motion](https://www.framer.com/motion/)
- [Shadcn/UI](https://ui.shadcn.com/)

---

**Lewis AI System v1.0.0** - Production Ready Frontend Architecture
Built with ❤️ following Google AI Studio's design philosophy
