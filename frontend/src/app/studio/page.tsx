/**
 * Studio Page - 主工作区入口
 * 统一的 IDE 级工作台,通过 mode 参数切换 General/Creative 视图
 */

'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { useStudioStore } from '@/lib/stores/studio';
import { Loader2 } from 'lucide-react';

// 加载骨架屏组件
function LoadingScreen() {
  return (
    <div className="h-screen w-screen flex items-center justify-center bg-surface-1">
      <div className="text-center space-y-4">
        <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto" />
        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">正在加载工作区...</p>
          <p className="text-xs text-muted-foreground">请稍候</p>
        </div>
      </div>
    </div>
  );
}

// 动态导入主内容组件,完全避免 SSR
const StudioWorkspace = dynamic(
  () => import('@/components/workspace/StudioWorkspace'),
  { 
    ssr: false,
    loading: () => <LoadingScreen />
  }
);

export default function StudioPage() {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    // 确保 Zustand store hydration 完成
    useStudioStore.persist.rehydrate();
    setIsClient(true);
  }, []);

  // 完全阻止 SSR 渲染
  if (!isClient) {
    return <LoadingScreen />;
  }

  return <StudioWorkspace />;
}
