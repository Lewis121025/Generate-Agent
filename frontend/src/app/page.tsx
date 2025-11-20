/**
 * Home Page - 重定向到 Studio 工作区
 * Lewis AI System v1.0.0 - IDE 级 AI 工作台
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // 自动重定向到 Studio
    router.push('/studio');
  }, [router]);

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-surface-1">
      <div className="text-center space-y-4">
        <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto" />
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-foreground">
            Lewis AI Studio
          </h2>
          <p className="text-sm text-muted-foreground">
            正在启动工作区...
          </p>
        </div>
      </div>
    </div>
  );
}
