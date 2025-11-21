"""Enhanced sandbox execution with resource limits and isolation."""

from __future__ import annotations

import multiprocessing
import signal
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

# Import resource module only on Unix systems
if sys.platform != "win32":
    import resource
else:
    resource = None

from .config import settings
from .instrumentation import get_logger

logger = get_logger()


class SandboxTimeoutError(Exception):
    """Raised when sandbox execution exceeds time limit."""
    pass


class SandboxResourceError(Exception):
    """Raised when sandbox exceeds resource limits."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise SandboxTimeoutError("Execution timeout exceeded")


@contextmanager
def resource_limits(
    max_memory_mb: int = 512,
    max_cpu_seconds: int = 60,
    max_file_size_mb: int = 10
):
    """
    Context manager to set resource limits (Unix only).
    
    Note: Windows does not support resource.setrlimit, so limits
    are only enforced on Unix systems.
    """
    if sys.platform == "win32" or resource is None:
        # Windows: no resource limits available via resource module
        logger.debug("Resource limits not enforced on Windows")
        yield
        return
    
    # Save current limits
    old_limits = {}
    
    try:
        # Set memory limit (RLIMIT_AS = address space)
        if hasattr(resource, 'RLIMIT_AS'):
            old_limits['RLIMIT_AS'] = resource.getrlimit(resource.RLIMIT_AS)
            resource.setrlimit(
                resource.RLIMIT_AS,
                (max_memory_mb * 1024 * 1024, max_memory_mb * 1024 * 1024)
            )
        
        # Set CPU time limit
        if hasattr(resource, 'RLIMIT_CPU'):
            old_limits['RLIMIT_CPU'] = resource.getrlimit(resource.RLIMIT_CPU)
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (max_cpu_seconds, max_cpu_seconds)
            )
        
        # Set file size limit
        if hasattr(resource, 'RLIMIT_FSIZE'):
            old_limits['RLIMIT_FSIZE'] = resource.getrlimit(resource.RLIMIT_FSIZE)
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (max_file_size_mb * 1024 * 1024, max_file_size_mb * 1024 * 1024)
            )
        
        yield
        
    finally:
        # Restore old limits
        for limit_name, limit_value in old_limits.items():
            if hasattr(resource, limit_name):
                resource.setrlimit(getattr(resource, limit_name), limit_value)


@contextmanager
def execution_timeout(seconds: int):
    """
    Context manager for execution timeout.
    
    Uses signal.alarm on Unix, or a simple timer on Windows.
    """
    if sys.platform == "win32":
        # Windows: use threading timeout (less reliable but available)
        import threading
        
        timer = None
        timed_out = [False]
        
        def timeout_func():
            timed_out[0] = True
        
        timer = threading.Timer(seconds, timeout_func)
        timer.start()
        
        try:
            yield
            if timed_out[0]:
                raise SandboxTimeoutError("Execution timeout exceeded")
        finally:
            if timer:
                timer.cancel()
    else:
        # Unix: use signal.alarm
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(seconds)
        
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


class EnhancedSandbox:
    """Enhanced sandbox with resource limits and isolation."""
    
    def __init__(
        self,
        max_memory_mb: int = 512,
        max_cpu_seconds: int = 60,
        max_file_size_mb: int = 10,
        timeout_seconds: int = 60,
        working_dir: Path | None = None
    ):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_seconds = max_cpu_seconds
        self.max_file_size_mb = max_file_size_mb
        self.timeout_seconds = timeout_seconds
        self.working_dir = working_dir or settings.sandbox.working_directory
        
        # Create working directory if it doesn't exist
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def execute_python(
        self,
        code: str,
        allowed_modules: list[str] | None = None,
        restricted_builtins: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute Python code - 已废弃!
        
        ⚠️ 此方法仅供开发环境使用,生产环境必须使用 E2B 云沙箱。
        本地 exec() 存在严重安全风险,不应在生产环境中使用。
        
        如果在生产环境调用此方法,将抛出异常。
        """
        # 生产环境强制禁用本地 exec()
        if settings.environment == "production":
            raise RuntimeError(
                "生产环境禁止使用本地 exec() 执行代码! "
                "请配置 E2B_API_KEY 并使用云端沙箱。"
            )
        
        logger.warning(
            "⚠️  使用本地 exec() 执行代码 - 此方法仅供开发/测试使用! "
            "生产环境请务必配置 E2B 云沙箱。"
        )
        
        import io
        import sys
        
        # Default restricted builtins
        if restricted_builtins is None:
            import math
            restricted_builtins = {
                "abs": abs,
                "min": min,
                "max": max,
                "sum": sum,
                "len": len,
                "range": range,
                "round": round,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "print": print,
                "math": math,
            }
        
        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        result = {
            "result": None,
            "stdout": "",
            "stderr": "",
            "error": None,
            "execution_time": 0.0
        }
        
        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            import time
            start_time = time.time()
            
            with execution_timeout(self.timeout_seconds):
                with resource_limits(
                    self.max_memory_mb,
                    self.max_cpu_seconds,
                    self.max_file_size_mb
                ):
                    local_vars = {}
                    exec(
                        code,
                        {"__builtins__": restricted_builtins},
                        local_vars
                    )
                    result["result"] = local_vars.get("result", local_vars)
            
            result["execution_time"] = time.time() - start_time
            
        except SandboxTimeoutError as e:
            result["error"] = f"Timeout: {str(e)}"
            logger.warning(f"Sandbox timeout: {e}")
        except MemoryError as e:
            result["error"] = f"Memory limit exceeded: {str(e)}"
            logger.warning(f"Sandbox memory error: {e}")
        except Exception as e:
            result["error"] = f"Execution error: {str(e)}"
            logger.warning(f"Sandbox execution error: {e}")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            result["stdout"] = stdout_capture.getvalue()
            result["stderr"] = stderr_capture.getvalue()
        
        return result
    
    def execute_in_process(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function in a separate process with resource limits.
        
        This provides better isolation than thread-based execution.
        """
        def wrapper(result_queue):
            try:
                with resource_limits(
                    self.max_memory_mb,
                    self.max_cpu_seconds,
                    self.max_file_size_mb
                ):
                    result = func(*args, **kwargs)
                    result_queue.put({"success": True, "result": result})
            except Exception as e:
                result_queue.put({"success": False, "error": str(e)})
        
        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=wrapper, args=(result_queue,))
        process.start()
        process.join(timeout=self.timeout_seconds)
        
        if process.is_alive():
            process.terminate()
            process.join()
            raise SandboxTimeoutError("Process execution timeout")
        
        if result_queue.empty():
            raise SandboxResourceError("Process terminated without result")
        
        result_data = result_queue.get()
        if not result_data["success"]:
            raise RuntimeError(result_data["error"])
        
        return result_data["result"]
    
    def create_temp_file(self, suffix: str = ".tmp") -> Path:
        """Create a temporary file in the sandbox working directory."""
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.working_dir)
        import os
        os.close(fd)
        return Path(path)
    
    def cleanup(self):
        """Clean up sandbox working directory."""
        import shutil
        
        if self.working_dir.exists():
            try:
                shutil.rmtree(self.working_dir)
                logger.info(f"Cleaned up sandbox directory: {self.working_dir}")
            except Exception as e:
                logger.error(f"Failed to cleanup sandbox: {e}")


# Global sandbox instance
_default_sandbox = None


def get_sandbox() -> EnhancedSandbox:
    """Get or create the default sandbox instance."""
    global _default_sandbox
    
    if _default_sandbox is None:
        _default_sandbox = EnhancedSandbox(
            max_memory_mb=512,
            max_cpu_seconds=settings.sandbox.execution_timeout_seconds,
            max_file_size_mb=10,
            timeout_seconds=settings.sandbox.execution_timeout_seconds,
            working_dir=settings.sandbox.working_directory
        )
    
    return _default_sandbox
