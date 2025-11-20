/**
 * Creative Canvas - 视频创作画布
 * 状态机驱动的块级编辑器: Drafting -> Scripting -> Visualizing -> Rendering
 */

'use client';

import { useState } from 'react';
import { useStudioStore, selectCurrentSession } from '@/lib/stores/studio';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import {
  Video,
  Wand2,
  Film,
  Image,
  Play,
  Download,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function CreativeCanvas() {
  const creativeStage = useStudioStore((state) => state.creativeStage);
  const setCreativeStage = useStudioStore((state) => state.setCreativeStage);
  const isStreaming = useStudioStore((state) => state.isStreaming);
  const currentSession = useStudioStore(selectCurrentSession);

  return (
    <div className="h-full flex flex-col bg-surface-1">
      {/* 进度指示器 */}
      <StageProgress currentStage={creativeStage || 'drafting'} />

      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto px-6 py-8 scrollbar-thin scrollbar-thumb-surface-3 scrollbar-track-transparent">
        <div className="max-w-4xl mx-auto">
          <AnimatePresence mode="wait">
            {creativeStage === 'drafting' && <DraftingStage />}
            {creativeStage === 'scripting' && <ScriptingStage />}
            {creativeStage === 'visualizing' && <VisualizingStage />}
            {creativeStage === 'rendering' && <RenderingStage />}
            {creativeStage === 'done' && <DoneStage />}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

// ==================== 进度指示器 ====================
const STAGES = [
  { id: 'drafting', label: '需求输入', icon: Wand2 },
  { id: 'scripting', label: '脚本生成', icon: Film },
  { id: 'visualizing', label: '分镜预览', icon: Image },
  { id: 'rendering', label: '视频渲染', icon: Video },
  { id: 'done', label: '完成', icon: CheckCircle2 },
] as const;

function StageProgress({ currentStage }: { currentStage: string }) {
  const currentIndex = STAGES.findIndex((s) => s.id === currentStage);

  return (
    <div className="border-b border-border/30 bg-surface-2/50 backdrop-blur-sm px-6 py-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between">
          {STAGES.map((stage, index) => {
            const Icon = stage.icon;
            const isActive = index === currentIndex;
            const isCompleted = index < currentIndex;

            return (
              <div key={stage.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center gap-2">
                  <div
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center transition-all',
                      isActive &&
                        'bg-primary text-primary-foreground shadow-lg scale-110',
                      isCompleted &&
                        'bg-primary/20 text-primary',
                      !isActive && !isCompleted && 'bg-surface-3 text-muted-foreground'
                    )}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <span
                    className={cn(
                      'text-xs font-medium transition-colors',
                      isActive && 'text-foreground',
                      isCompleted && 'text-primary',
                      !isActive && !isCompleted && 'text-muted-foreground'
                    )}
                  >
                    {stage.label}
                  </span>
                </div>

                {/* 连接线 */}
                {index < STAGES.length - 1 && (
                  <div className="flex-1 h-0.5 mx-2 mt-[-20px]">
                    <div
                      className={cn(
                        'h-full transition-colors',
                        isCompleted ? 'bg-primary' : 'bg-surface-3'
                      )}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ==================== 阶段 1: 需求输入 ====================
function DraftingStage() {
  const [prompt, setPrompt] = useState('');
  const setCreativeStage = useStudioStore((state) => state.setCreativeStage);
  const setStreaming = useStudioStore((state) => state.setStreaming);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    setStreaming(true);
    // TODO: 调用后端 API 生成脚本
    console.log('Generating script for:', prompt);

    // 模拟延迟
    setTimeout(() => {
      setStreaming(false);
      setCreativeStage('scripting');
    }, 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-foreground">
          描述你的视频创意
        </h2>
        <p className="text-sm text-muted-foreground">
          详细描述视频的内容、风格、情绪,AI 会为你生成专业的分镜脚本
        </p>
      </div>

      <div className="bg-surface-2 rounded-google-lg p-6 space-y-4">
        <Textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="例如: 制作一个30秒的科技感广告,展示 AI 助手帮助创作者完成工作的场景,采用未来主义风格,配合动感音乐..."
          className="min-h-[200px] bg-surface-1 border-border/50 rounded-google"
        />

        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">
            {prompt.length} / 2000 字符
          </div>
          <Button
            onClick={handleGenerate}
            disabled={!prompt.trim()}
            className="bg-primary hover:bg-primary/90 rounded-google"
          >
            <Wand2 className="w-4 h-4 mr-2" />
            生成脚本
          </Button>
        </div>
      </div>

      {/* 示例提示 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {[
          '一个温馨的家庭聚餐场景,金色的夕阳透过窗户...',
          '科幻风格的城市街景,霓虹灯闪烁,飞行器穿梭...',
          '大自然纪录片风格,展示森林中的野生动物...',
          '产品展示视频,突出手机的设计细节和功能...',
        ].map((example, index) => (
          <button
            key={index}
            onClick={() => setPrompt(example)}
            className="text-left p-4 bg-surface-3/30 hover:bg-surface-3 rounded-google border border-border/30 transition-colors"
          >
            <p className="text-sm text-foreground line-clamp-2">{example}</p>
          </button>
        ))}
      </div>
    </motion.div>
  );
}

// ==================== 阶段 2: 脚本生成 ====================
function ScriptingStage() {
  const setCreativeStage = useStudioStore((state) => state.setCreativeStage);

  // 模拟脚本数据
  const mockScript = [
    {
      scene: 1,
      duration: 5,
      description: '开场镜头: 城市天际线,日出时分',
      visualElements: ['天际线', '太阳', '建筑剪影'],
    },
    {
      scene: 2,
      duration: 5,
      description: '转场: 镜头下降到街道层面',
      visualElements: ['街道', '人群', '交通'],
    },
    {
      scene: 3,
      duration: 5,
      description: '特写: 主角使用手机的画面',
      visualElements: ['手机屏幕', '手部特写', 'UI界面'],
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">分镜脚本</h2>
          <p className="text-sm text-muted-foreground mt-1">
            AI 已为你生成专业的分镜脚本,可以编辑调整
          </p>
        </div>
        <Button
          onClick={() => setCreativeStage('visualizing')}
          className="bg-primary hover:bg-primary/90 rounded-google"
        >
          <Image className="w-4 h-4 mr-2" />
          生成分镜图
        </Button>
      </div>

      <div className="space-y-3">
        {mockScript.map((scene) => (
          <div
            key={scene.scene}
            className="bg-surface-2 rounded-google-lg p-5 border border-border/30"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-google flex items-center justify-center flex-shrink-0">
                <span className="text-lg font-bold text-primary">
                  {scene.scene}
                </span>
              </div>

              <div className="flex-1 space-y-3">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-medium text-muted-foreground">
                      时长: {scene.duration}s
                    </span>
                  </div>
                  <p className="text-sm text-foreground">
                    {scene.description}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {scene.visualElements.map((element, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-surface-3/50 text-xs text-muted-foreground rounded-md"
                    >
                      {element}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

// ==================== 阶段 3: 分镜预览 ====================
function VisualizingStage() {
  const setCreativeStage = useStudioStore((state) => state.setCreativeStage);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">分镜预览</h2>
          <p className="text-sm text-muted-foreground mt-1">
            查看每个场景的视觉效果
          </p>
        </div>
        <Button
          onClick={() => setCreativeStage('rendering')}
          className="bg-primary hover:bg-primary/90 rounded-google"
        >
          <Video className="w-4 h-4 mr-2" />
          开始渲染视频
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((index) => (
          <div
            key={index}
            className="group aspect-video bg-surface-3 rounded-google-lg overflow-hidden border border-border/30 relative cursor-pointer hover:scale-[1.02] transition-transform"
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-muted-foreground animate-spin" />
            </div>
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
              <p className="text-xs text-white">场景 {index}</p>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

// ==================== 阶段 4: 视频渲染 ====================
function RenderingStage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex flex-col items-center justify-center py-20 space-y-6"
    >
      <div className="w-20 h-20 bg-primary/10 rounded-google-lg flex items-center justify-center">
        <Video className="w-10 h-10 text-primary animate-pulse" />
      </div>
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-foreground">正在渲染视频</h2>
        <p className="text-sm text-muted-foreground">
          AI 正在合成最终视频,预计需要 2-5 分钟...
        </p>
      </div>

      {/* 进度条 */}
      <div className="w-full max-w-md">
        <div className="h-2 bg-surface-3 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-primary"
            initial={{ width: '0%' }}
            animate={{ width: '60%' }}
            transition={{ duration: 2, ease: 'easeInOut' }}
          />
        </div>
        <p className="text-xs text-muted-foreground text-center mt-2">
          60% 完成
        </p>
      </div>
    </motion.div>
  );
}

// ==================== 阶段 5: 完成 ====================
function DoneStage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      <div className="text-center space-y-2">
        <div className="w-16 h-16 bg-primary/10 rounded-google-lg flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">视频生成完成!</h2>
        <p className="text-sm text-muted-foreground">
          你的视频已准备就绪
        </p>
      </div>

      {/* 视频预览 */}
      <div className="bg-surface-2 rounded-google-lg p-6 space-y-4">
        <div className="aspect-video bg-surface-3 rounded-google overflow-hidden">
          <div className="w-full h-full flex items-center justify-center">
            <Play className="w-16 h-16 text-muted-foreground" />
          </div>
        </div>

        <div className="flex items-center justify-center gap-3">
          <Button className="bg-primary hover:bg-primary/90 rounded-google">
            <Play className="w-4 h-4 mr-2" />
            播放视频
          </Button>
          <Button variant="outline" className="rounded-google">
            <Download className="w-4 h-4 mr-2" />
            下载
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
