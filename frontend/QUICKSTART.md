# Lewis AI Studio - 快速启动指南

## 🎯 架构升级完成!

Lewis AI System 前端已成功重构为 **Google AI Studio 风格的 IDE 级工作区**。

## ✨ 核心特性

### 🏗️ 工作区导向架构
- **三栏式布局**: 左侧导航 + 中间画布 + 右侧配置
- **可调整大小**: 拖动分隔条自定义布局
- **模式切换**: General (通用对话) ↔ Creative (视频创作)

### 🎨 Google AI Studio 风格
- **深色主题**: 专业的 Surface 层级系统
- **Google Blue**: `#A8C7FA` 主色调
- **大圆角设计**: 16-24px 圆角
- **流畅动画**: Framer Motion 驱动

### 🧠 智能状态管理
- **Zustand Store**: 全局状态协调
- **会话持久化**: 自动保存到 localStorage
- **动态配置**: 根据模式切换参数面板

### 🚀 双引擎画布
- **General Canvas**: Chat UI + Tool Invocation Cards
- **Creative Canvas**: 状态机工作流 (5个阶段)

## 📦 已安装依赖

```json
{
  "dependencies": {
    "zustand": "^4.x",                  // 状态管理
    "@tanstack/react-query": "^5.x",   // 服务端缓存
    "ai": "^3.x",                       // Vercel AI SDK
    "react-resizable-panels": "^2.x",  // 可调整布局
    "framer-motion": "^12.x",          // 动画系统
    "date-fns": "^4.x"                 // 时间格式化
  }
}
```

## 🚀 启动步骤

### 1. 启动开发服务器

```powershell
cd frontend
npm run dev
```

访问: `http://localhost:3000` (自动跳转到 `/studio`)

### 2. 界面布局

```
┌─────────────────────────────────────────────────────────────┐
│  🎨 Studio Header                                           │
│  [≡ General | Creative]           Lewis AI Studio      [⚙️] │
├─────────┬───────────────────────────────────────┬───────────┤
│         │                                       │           │
│ 📂 左侧栏 │           🎯 中间画布                 │ ⚙️ 右侧栏 │
│         │                                       │           │
│ · 历史   │  General: Chat UI                    │ · 模型参数│
│ · 资产   │  Creative: Block Editor              │ · 工具开关│
│         │                                       │ · 视频设置│
│         │                                       │           │
└─────────┴───────────────────────────────────────┴───────────┘
```

### 3. 基本操作

#### 创建新会话
1. 点击左侧栏顶部的 **"新对话"** 或 **"新项目"** 按钮
2. 或使用快捷键: `Ctrl+N` (待实现)

#### 切换模式
- 点击顶部的 **General** 或 **Creative** 标签
- Store 自动切换配置面板

#### 调整布局
- 拖动分隔条调整三栏宽度
- 点击图标折叠/展开侧边栏

#### 输入对话 (General 模式)
- 在底部输入框输入问题
- `Enter`: 发送消息
- `Shift+Enter`: 换行

#### 创作视频 (Creative 模式)
1. **Drafting**: 输入视频创意描述
2. **Scripting**: AI 生成分镜脚本 (可编辑)
3. **Visualizing**: 查看分镜图片预览
4. **Rendering**: 等待视频渲染
5. **Done**: 播放/下载视频

## 🎨 颜色系统

### Surface Layers (背景层级)
```css
--surface-1: #1E1F20  /* 主背景 - 最深 */
--surface-2: #28292A  /* 卡片/面板 */
--surface-3: #3C4043  /* 悬浮/激活 - 最亮 */
```

### Primary Color (强调色)
```css
--primary: #A8C7FA           /* Google Blue */
--primary-container: #0842A0  /* 容器背景 */
```

### Usage Examples
```tsx
// 背景
className="bg-surface-1"  // 主背景
className="bg-surface-2"  // 卡片
className="bg-surface-3"  // Hover 状态

// 圆角
className="rounded-google"     // 16px
className="rounded-google-lg"  // 24px
className="rounded-google-xl"  // 32px

// 按钮
className="bg-primary hover:bg-primary/90"
```

## 📁 项目结构速览

```
frontend/src/
├── app/
│   ├── studio/page.tsx          # 👈 主入口
│   └── globals.css              # 🎨 主题配置
├── components/
│   ├── layout/
│   │   ├── StudioShell.tsx      # 三栏容器
│   │   ├── StudioHeader.tsx     # 顶部工具栏
│   │   ├── StudioSidebar.tsx    # 左侧导航
│   │   └── ConfigPanel.tsx      # 右侧配置
│   └── workspace/
│       ├── GeneralCanvas.tsx    # 通用对话
│       └── CreativeCanvas.tsx   # 视频创作
└── lib/
    └── stores/
        ├── types.ts             # 类型定义
        └── studio.ts            # Zustand Store
```

## 🔧 开发调试

### 1. Zustand DevTools

打开 Redux DevTools 扩展,可以看到:
- Store 名称: `StudioStore`
- 实时状态更新
- 时间旅行调试

### 2. React Query DevTools

```tsx
// 在 studio/layout.tsx 中启用
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

<QueryClientProvider client={queryClient}>
  {children}
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

### 3. 常用调试命令

```typescript
// 在浏览器控制台中
import { useStudioStore } from '@/lib/stores/studio';

// 查看当前状态
console.log(useStudioStore.getState());

// 手动切换模式
useStudioStore.getState().setMode('creative');

// 查看所有会话
console.log(useStudioStore.getState().sessions);
```

## 🐛 问题排查

### 问题: 页面空白
**原因**: 状态初始化失败
**解决**: 
```powershell
# 清除 localStorage
# 在浏览器控制台执行:
localStorage.removeItem('lewis-studio-storage')
# 刷新页面
```

### 问题: 布局错位
**原因**: CSS 变量未加载
**解决**: 检查 `globals.css` 中的 `.dark` 类

### 问题: 动画卡顿
**原因**: Framer Motion 配置
**解决**: 
```tsx
// 减少动画复杂度
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.2 }} // 缩短时间
/>
```

## 📝 下一步集成

### 1. 对接后端 API (优先级: 高)

```typescript
// lib/api/general.ts
export async function sendGeneralMessage(
  sessionId: string,
  message: string,
  config: GeneralConfig
) {
  const response = await fetch('/api/general/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, message, config }),
  });
  
  // 处理 SSE 流
  const reader = response.body?.getReader();
  // ...
}
```

### 2. 实现键盘快捷键

```typescript
// hooks/useKeyboardShortcuts.ts
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.ctrlKey || e.metaKey) {
      if (e.key === 'n') createSession(mode);
      if (e.key === 'k') toggleSidebar();
    }
  };
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, []);
```

### 3. 添加搜索功能

```tsx
// components/layout/StudioSidebar.tsx
const [searchQuery, setSearchQuery] = useState('');

const filteredSessions = sessions.filter(s =>
  s.title.toLowerCase().includes(searchQuery.toLowerCase())
);
```

## 🎉 功能清单

- [x] 三栏式布局系统
- [x] Zustand 状态管理
- [x] 模式切换 (General/Creative)
- [x] 会话历史管理
- [x] 动态配置面板
- [x] Google AI Studio 主题
- [x] Framer Motion 动画
- [x] 响应式设计
- [ ] SSE 流式输出 (待集成后端)
- [ ] 工具调用展示 (待集成后端)
- [ ] 视频生成工作流 (待集成后端)
- [ ] 键盘快捷键
- [ ] 搜索过滤
- [ ] 移动端适配

## 📚 参考资源

- **架构文档**: `frontend/ARCHITECTURE.md`
- **组件文档**: `frontend/src/components/README.md` (待创建)
- **API 文档**: `docs/api.md` (待创建)

---

**🎨 Lewis AI Studio v1.0.0**  
Production-Ready Frontend Architecture  
Build Date: 2025-11-20
