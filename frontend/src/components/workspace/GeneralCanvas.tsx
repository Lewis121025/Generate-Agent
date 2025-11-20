/**
 * General Canvas - 通用对话画布
 * 传统的 Chat UI + Tool Invocation Cards
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { useStudioStore, selectCurrentSession } from '@/lib/stores/studio';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import {
  Send,
  Loader2,
  User,
  Bot,
  Search,
  Code,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function GeneralCanvas() {
  const currentSessionId = useStudioStore((state) => state.currentSessionId);
  const isStreaming = useStudioStore((state) => state.isStreaming);
  const setStreaming = useStudioStore((state) => state.setStreaming);
  const currentSession = useStudioStore(selectCurrentSession);
  const [input, setInput] = useState('');
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  const scrollRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [currentSession?.messages]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    // TODO: 集成 Vercel AI SDK 处理流式响应
    console.log('Sending message:', input);
    setInput('');
    setStreaming(true);

    // 模拟延迟
    setTimeout(() => {
      setStreaming(false);
    }, 2000);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleToolExpansion = (toolId: string) => {
    setExpandedTools((prev) => {
      const next = new Set(prev);
      if (next.has(toolId)) {
        next.delete(toolId);
      } else {
        next.add(toolId);
      }
      return next;
    });
  };

  return (
    <div className="h-full flex flex-col bg-surface-1">
      {/* 消息列表 */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {!currentSession || currentSession.messages.length === 0 ? (
            <EmptyState />
          ) : (
            <AnimatePresence mode="popLayout">
              {currentSession.messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                >
                  <MessageBubble message={message} />

                  {/* Tool Invocations */}
                  {message.toolInvocations &&
                    message.toolInvocations.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {message.toolInvocations.map((tool, toolIndex) => (
                          <ToolInvocationCard
                            key={`${message.id}-tool-${toolIndex}`}
                            tool={tool}
                            isExpanded={expandedTools.has(
                              `${message.id}-${toolIndex}`
                            )}
                            onToggle={() =>
                              toggleToolExpansion(`${message.id}-${toolIndex}`)
                            }
                          />
                        ))}
                      </div>
                    )}
                </motion.div>
              ))}
            </AnimatePresence>
          )}

          {/* 流式加载指示器 */}
          {isStreaming && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-start gap-3"
            >
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1 bg-surface-2 rounded-google-lg p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>AI 正在思考...</span>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* 输入区域 */}
      <div className="border-t border-border/30 bg-surface-2/50 backdrop-blur-sm p-4">
        <div className="max-w-3xl mx-auto">
          <div className="relative">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入你的问题或任务... (Shift + Enter 换行)"
              className="min-h-[80px] max-h-[200px] pr-12 rounded-google-lg bg-surface-1 border-border/50 focus-visible:ring-primary resize-none"
              disabled={isStreaming}
            />
            <Button
              size="icon"
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className="absolute right-2 bottom-2 rounded-full bg-primary hover:bg-primary/90"
            >
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>

          <div className="mt-2 text-xs text-muted-foreground text-center">
            Lewis AI 可能会出错,请核查重要信息
          </div>
        </div>
      </div>
    </div>
  );
}

// ==================== 消息气泡 ====================
function MessageBubble({ message }: { message: any }) {
  const isUser = message.role === 'user';

  return (
    <div className={cn('flex items-start gap-3', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-primary/20' : 'bg-surface-3'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-primary" />
        ) : (
          <Bot className="w-4 h-4 text-primary" />
        )}
      </div>

      {/* Content */}
      <div
        className={cn(
          'flex-1 rounded-google-lg p-4 max-w-[85%]',
          isUser
            ? 'bg-primary-container text-primary-foreground ml-auto'
            : 'bg-surface-2 text-foreground'
        )}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {message.content}
        </div>
      </div>
    </div>
  );
}

// ==================== 工具调用卡片 ====================
function ToolInvocationCard({
  tool,
  isExpanded,
  onToggle,
}: {
  tool: any;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const getToolIcon = () => {
    if (tool.toolName.includes('search')) return Search;
    if (tool.toolName.includes('code') || tool.toolName.includes('python'))
      return Code;
    return Code;
  };

  const Icon = getToolIcon();

  return (
    <div className="ml-11 bg-surface-3/30 border border-border/30 rounded-google overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 hover:bg-surface-3/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-foreground">
            {tool.toolName}
          </span>
          {tool.status === 'pending' && (
            <Loader2 className="w-3 h-3 animate-spin text-muted-foreground" />
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        )}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="p-3 border-t border-border/30 bg-surface-2/50">
              <pre className="text-xs text-muted-foreground overflow-x-auto">
                {JSON.stringify(tool.args, null, 2)}
              </pre>
              {tool.result && (
                <div className="mt-2 pt-2 border-t border-border/20">
                  <div className="text-xs font-medium text-foreground mb-1">
                    结果:
                  </div>
                  <pre className="text-xs text-muted-foreground overflow-x-auto">
                    {JSON.stringify(tool.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ==================== 空状态 ====================
function EmptyState() {
  const suggestions = [
    '解释量子计算的基本原理',
    '帮我写一个 Python 爬虫',
    '搜索最新的 AI 新闻',
    '分析这段代码的时间复杂度',
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-12">
      <div className="w-16 h-16 bg-primary/10 rounded-google-lg flex items-center justify-center mb-4">
        <Bot className="w-8 h-8 text-primary" />
      </div>
      <h2 className="text-xl font-semibold text-foreground mb-2">
        开始新对话
      </h2>
      <p className="text-sm text-muted-foreground mb-6 max-w-md">
        我可以帮你编程、搜索、分析数据,还能运行 Python 代码
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            className="text-left p-4 bg-surface-2 hover:bg-surface-3 rounded-google border border-border/30 transition-colors"
          >
            <p className="text-sm text-foreground">{suggestion}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
