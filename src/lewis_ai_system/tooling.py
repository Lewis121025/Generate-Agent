"""Tool runtime and sandbox enforcement."""

from __future__ import annotations

import math
import textwrap
from dataclasses import dataclass
from threading import Lock
from types import MappingProxyType
from typing import Any, Callable, Dict

from .config import settings
from .instrumentation import TelemetryEvent, emit_event


@dataclass(slots=True)
class ToolRequest:
    name: str
    input: dict[str, Any]


@dataclass(slots=True)
class ToolResult:
    output: Any
    cost_usd: float = 0.0
    metadata: dict[str, Any] | None = None


class ToolExecutionError(RuntimeError):
    """Raised when a tool cannot be executed."""


class Tool:
    name: str
    description: str
    cost_estimate: float = 0.001

    def run(self, payload: dict[str, Any]) -> ToolResult:  # pragma: no cover - interface
        raise NotImplementedError

    @property
    def parameters(self) -> dict[str, Any]:
        """JSON Schema for the tool input parameters."""
        return {}


class PythonSandboxTool(Tool):
    """Enhanced sandbox for secure Python execution with resource limits."""

    name = "python_sandbox"
    description = "Executes Python code in a secure sandbox with CPU/memory limits."

    def __init__(self) -> None:
        from .providers import get_sandbox_provider
        self.provider = get_sandbox_provider()
        
        # Keep local fallback logic for now if provider is local
        self.allowed_builtins = MappingProxyType(
            {
                "abs": abs,
                "min": min,
                "max": max,
                "sum": sum,
                "len": len,
                "range": range,
                "round": round,
                "math": math,
            }
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Must be valid, complete Python code."
                }
            },
            "required": ["code"]
        }

    def run(self, payload: dict[str, Any]) -> ToolResult:
        import asyncio
        code = payload.get("code")
        if not isinstance(code, str):
            raise ToolExecutionError("python_sandbox requires 'code' string input")

        code = textwrap.dedent(code).strip()
        
        # If using E2B, delegate to provider
        if self.provider.name == "e2b":
            try:
                # If we're already inside an event loop (common in async workflows), run
                # the provider coroutine on a worker thread to avoid nested loop errors.
                try:
                    asyncio.get_running_loop()
                    loop_running = True
                except RuntimeError:
                    loop_running = False

                if loop_running:
                    import concurrent.futures

                    def _invoke() -> dict[str, Any]:
                        return asyncio.run(self.provider.run_code(code))

                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(_invoke)
                        result = future.result()
                else:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(self.provider.run_code(code))
            except Exception as exc:  # pragma: no cover - defensive
                raise ToolExecutionError(f"Sandbox execution failed: {exc}") from exc

            if result.get("error"):
                raise ToolExecutionError(f"Sandbox execution failed: {result['error']}")
            
            return ToolResult(output=result, cost_usd=0.01) # E2B cost estimate

        # 生产环境必须使用 E2B,不允许本地 fallback
        if settings.environment == "production":
            raise ToolExecutionError(
                "生产环境代码执行失败! E2B Provider 不可用。"
                "请确保已配置 E2B_API_KEY 环境变量。"
            )
        
        # 开发环境的本地 fallback (仅用于测试)
        logger.warning(
            "⚠️  使用本地沙箱执行代码 - 仅供开发使用! "
            "生产环境请务必配置 E2B_API_KEY。"
        )
        
        try:
            from .sandbox import get_sandbox
            sandbox = get_sandbox()
            execution_result = sandbox.execute_python(
                code,
                restricted_builtins=dict(self.allowed_builtins)
            )
            
            if execution_result["error"]:
                raise ToolExecutionError(f"Sandbox execution failed: {execution_result['error']}")
            
            output = {
                "result": execution_result["result"],
                "stdout": execution_result["stdout"],
                "execution_time": execution_result["execution_time"]
            }
            return ToolResult(output=output, cost_usd=self.cost_estimate)
            
        except Exception as exc:
            raise ToolExecutionError(f"本地沙箱执行失败: {exc}") from exc


class WebSearchTool(Tool):
    """Web search tool using configured provider."""

    name = "web_search"
    description = "Queries a web search API and returns summarized results."

    def __init__(self) -> None:
        from .providers import get_search_provider
        self._provider_factory = get_search_provider
        self.provider = self._provider_factory()

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string."
                },
                "provider": {
                    "type": "string",
                    "description": "Optional provider override (e.g. 'tavily', 'mock')."
                }
            },
            "required": ["query"]
        }

    def run(self, payload: dict[str, Any]) -> ToolResult:
        import asyncio
        query = payload.get("query", "")
        provider_override = payload.get("provider")
        if provider_override:
            self.provider = self._provider_factory(provider_override)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        result = loop.run_until_complete(self.provider.search(query))
        return ToolResult(output={"query": query, "result": result}, cost_usd=0.01)


class WebScrapeTool(Tool):
    """Web scraping tool using Firecrawl."""
    
    name = "web_scrape"
    description = "Extracts content from a URL as markdown."
    
    def __init__(self) -> None:
        from .providers import get_scrape_provider
        self._provider_factory = get_scrape_provider
        self.provider = self._provider_factory()
        
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to scrape content from."
                },
                "provider": {
                    "type": "string",
                    "description": "Optional provider override (e.g. 'firecrawl', 'mock')."
                }
            },
            "required": ["url"]
        }
        
    def run(self, payload: dict[str, Any]) -> ToolResult:
        import asyncio
        url = payload.get("url")
        if not url:
            raise ToolExecutionError("web_scrape requires 'url' string input")

        provider_override = payload.get("provider")
        if provider_override:
            self.provider = self._provider_factory(provider_override)
            
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        content = loop.run_until_complete(self.provider.scrape(url))
        return ToolResult(output={"url": url, "content": content[:5000]}, cost_usd=0.005)


class VideoGenerationTool(Tool):
    """Tool for generating videos via provider APIs (Runway/Pika/Runware)."""

    name = "generate_video"
    description = "Generates video from text prompt using configured provider."
    cost_estimate = 2.5  # Average cost per 5-second video

    def __init__(self, provider_name: str | None = None) -> None:
        from .providers import get_video_provider

        self._provider_factory = get_video_provider
        self.provider_name = provider_name or settings.video_provider_default
        self.provider = self._provider_factory(self.provider_name)

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description of the video to generate."
                },
                "duration_seconds": {
                    "type": "integer",
                    "description": "Duration in seconds (default 5).",
                    "default": 5
                },
                "aspect_ratio": {
                    "type": "string",
                    "description": "Aspect ratio (e.g., '16:9', '9:16').",
                    "default": "16:9"
                },
                "quality": {
                    "type": "string",
                    "enum": ["preview", "final"],
                    "default": "preview"
                },
                "provider": {
                    "type": "string",
                    "description": "Optional provider override."
                }
            },
            "required": ["prompt"]
        }

    def _resolve_provider(self, override: str | None) -> tuple[str, Any]:
        if not override or override == self.provider_name:
            return self.provider_name, self.provider
        resolved = self._provider_factory(override)
        return override, resolved

    def run(self, payload: dict[str, Any]) -> ToolResult:
        import asyncio

        prompt = payload.get("prompt")
        if not isinstance(prompt, str):
            raise ToolExecutionError("generate_video requires 'prompt' string input")

        duration = payload.get("duration_seconds", 5)
        aspect_ratio = payload.get("aspect_ratio", "16:9")
        quality = payload.get("quality", "preview")
        provider_override = payload.get("provider")
        provider_name, provider = self._resolve_provider(provider_override)

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            provider.generate_video(
                prompt,
                duration_seconds=duration,
                aspect_ratio=aspect_ratio,
                quality=quality,
            )
        )

        cost_multiplier = 1.5 if quality == "final" else 0.3
        cost = self.cost_estimate * (duration / 5) * cost_multiplier

        return ToolResult(output=result, cost_usd=cost, metadata={"provider": provider_name})


class TTSTool(Tool):
    """Tool for text-to-speech synthesis."""

    name = "text_to_speech"
    description = "Converts text to speech audio using TTS provider."
    cost_estimate = 0.15  # Per 1000 characters

    def __init__(self, provider_name: str = "elevenlabs") -> None:
        from .providers import get_tts_provider
        self.provider = get_tts_provider(provider_name)
        self.provider_name = provider_name

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to convert to speech."
                },
                "voice": {
                    "type": "string",
                    "description": "Voice ID or name.",
                    "default": "default"
                }
            },
            "required": ["text"]
        }

    def run(self, payload: dict[str, Any]) -> ToolResult:
        import asyncio
        
        text = payload.get("text")
        if not isinstance(text, str):
            raise ToolExecutionError("text_to_speech requires 'text' string input")
        
        voice = payload.get("voice", "default")
        
        # Run async provider call
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(self.provider.synthesize(text, voice=voice))
        
        # Calculate cost based on character count
        cost = (len(text) / 1000) * self.cost_estimate
        
        return ToolResult(output=result, cost_usd=cost, metadata={"provider": self.provider_name})


class ToolRuntime:
    """Shared registry handling execution and telemetry."""

    def __init__(self, sandbox_timeout: int = settings.sandbox.execution_timeout_seconds) -> None:
        self._tools: Dict[str, Tool] = {}
        self._lock = Lock()
        self.sandbox_timeout = sandbox_timeout

    def register(self, tool: Tool) -> None:
        with self._lock:
            self._tools[tool.name] = tool

    def execute(self, request: ToolRequest) -> ToolResult:
        tool = self._tools.get(request.name)
        if not tool:
            raise ToolExecutionError(f"Unknown tool '{request.name}'")

        emit_event(TelemetryEvent(name="tool_start", attributes={"tool": request.name}))
        result = tool.run(request.input)
        emit_event(TelemetryEvent(name="tool_complete", attributes={"tool": request.name, "cost": result.cost_usd}))
        return result


default_tool_runtime = ToolRuntime()
default_tool_runtime.register(PythonSandboxTool())
default_tool_runtime.register(WebSearchTool())
default_tool_runtime.register(WebScrapeTool())
default_tool_runtime.register(VideoGenerationTool(provider_name=settings.video_provider_default))
default_tool_runtime.register(TTSTool(provider_name="elevenlabs"))
