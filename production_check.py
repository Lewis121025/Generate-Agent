#!/usr/bin/env python3
"""
Lewis AI System - 生产环境部署自检脚本
检查所有必需的配置和服务是否正确配置
"""

import asyncio
import sys
from typing import List, Tuple

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")

def print_check(name: str, passed: bool, message: str = ""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} {name}")
    if message:
        print(f"       {Colors.YELLOW}→ {message}{Colors.END}")

async def check_environment():
    """检查环境变量配置"""
    print_header("1. 环境变量检查")
    
    from lewis_ai_system.config import settings
    
    checks = []
    
    # 检查环境模式
    is_production = settings.environment == "production"
    checks.append(("环境模式", is_production, f"当前: {settings.environment} (应为 'production')"))
    
    # 检查核心 API Keys
    checks.append((
        "OpenRouter API Key",
        bool(settings.openrouter_api_key and settings.openrouter_api_key != "mock"),
        "未配置或使用 Mock"
    ))
    
    checks.append((
        "E2B API Key (代码沙箱)",
        bool(settings.e2b_api_key),
        "生产环境必须配置 E2B 以安全执行代码"
    ))
    
    # 检查数据库配置
    checks.append((
        "数据库连接",
        bool(settings.database_url and "postgresql" in settings.database_url),
        f"当前: {settings.database_url[:50] if settings.database_url else 'None'}..."
    ))
    
    checks.append((
        "Redis 连接",
        bool(settings.redis_url and settings.redis_enabled),
        f"当前: {settings.redis_url if settings.redis_url else 'None'}"
    ))
    
    # 检查 Secret Key
    checks.append((
        "Secret Key 安全性",
        settings.secret_key != "dev-secret-key-change-in-production",
        "使用了默认开发密钥,生产环境必须更换!"
    ))
    
    # 打印结果
    all_passed = True
    for name, passed, message in checks:
        print_check(name, passed, message if not passed else "")
        if not passed:
            all_passed = False
    
    return all_passed


async def check_database():
    """检查数据库连接和表结构"""
    print_header("2. 数据库检查")
    
    try:
        from lewis_ai_system.database import db_manager
        from lewis_ai_system.config import settings
        from sqlalchemy import text
        
        # 初始化数据库管理器
        if not db_manager.engine:
            db_manager.initialize(settings.database_url)
        
        async with db_manager.get_session() as session:
            # 测试连接
            result = await session.execute(text("SELECT 1"))
            print_check("数据库连接", True)
            
            # 检查表是否存在
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('users', 'creative_projects', 'scripts', 'storyboards')
            """)
            tables = (await session.execute(tables_query)).fetchall()
            table_names = [t[0] for t in tables]
            
            expected_tables = ['users', 'creative_projects', 'scripts', 'storyboards']
            missing_tables = [t for t in expected_tables if t not in table_names]
            
            if missing_tables:
                print_check(
                    "数据库表结构",
                    False,
                    f"缺少表: {', '.join(missing_tables)}。请运行: alembic upgrade head"
                )
                return False
            else:
                print_check("数据库表结构", True, f"已找到 {len(table_names)} 个表")
                return True
    
    except Exception as e:
        print_check("数据库连接", False, f"错误: {str(e)}")
        return False


async def check_redis():
    """检查 Redis 连接"""
    print_header("3. Redis 检查")
    
    try:
        import redis.asyncio as aioredis
        from lewis_ai_system.config import settings
        
        if not settings.redis_url:
            print_check("Redis 配置", False, "REDIS_URL 未配置")
            return False
        
        # 连接 Redis
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        
        # Ping 测试
        pong = await client.ping()
        print_check("Redis 连接", pong, f"连接到: {settings.redis_url}")
        
        # 测试读写
        await client.set("lewis_test_key", "hello", ex=10)
        value = await client.get("lewis_test_key")
        print_check("Redis 读写", value == "hello")
        
        await client.close()
        return pong and value == "hello"
    
    except Exception as e:
        print_check("Redis 连接", False, f"错误: {str(e)}")
        return False


async def check_api_providers():
    """检查外部 API Providers"""
    print_header("4. 外部 API 检查")
    
    from lewis_ai_system.config import settings
    import httpx
    
    checks = []
    
    # 检查 OpenRouter
    if settings.openrouter_api_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {settings.openrouter_api_key}"}
                )
                checks.append(("OpenRouter API", response.status_code == 200, f"状态码: {response.status_code}"))
        except Exception as e:
            checks.append(("OpenRouter API", False, f"错误: {str(e)}"))
    else:
        checks.append(("OpenRouter API", False, "未配置 API Key"))
    
    # 检查 E2B (代码沙箱)
    if settings.e2b_api_key:
        checks.append(("E2B API Key", True, "已配置"))
    else:
        checks.append(("E2B API Key", False, "未配置 - 生产环境必须配置!"))
    
    # 检查视频生成 Provider
    video_key_exists = bool(
        settings.runway_api_key or 
        settings.pika_api_key or 
        getattr(settings, 'runware_api_key', None)
    )
    checks.append((
        "视频生成 Provider",
        video_key_exists,
        f"当前: {settings.video_provider_default}"
    ))
    
    # 打印结果
    all_passed = True
    for name, passed, message in checks:
        print_check(name, passed, message if not passed else "")
        if not passed:
            all_passed = False
    
    return all_passed


async def check_security():
    """检查安全配置"""
    print_header("5. 安全配置检查")
    
    from lewis_ai_system.config import settings
    
    checks = []
    
    # CORS 检查
    cors_secure = "*" not in settings.cors_origins
    checks.append((
        "CORS 配置",
        cors_secure,
        f"当前: {settings.cors_origins} (生产环境不应使用 '*')"
    ))
    
    # Trusted Hosts 检查
    hosts_secure = "*" not in settings.trusted_hosts
    checks.append((
        "Trusted Hosts",
        hosts_secure,
        f"当前: {settings.trusted_hosts} (生产环境不应使用 '*')"
    ))
    
    # 速率限制检查
    checks.append((
        "速率限制",
        settings.rate_limit_enabled,
        "生产环境应启用速率限制"
    ))
    
    # 打印结果
    all_passed = True
    for name, passed, message in checks:
        print_check(name, passed, message if not passed else "")
        if not passed:
            all_passed = False
    
    return all_passed


async def main():
    print(f"\n{Colors.BOLD}Lewis AI System - 生产环境自检{Colors.END}")
    print(f"检查所有必需的配置和服务...")
    
    results = []
    
    # 运行所有检查
    results.append(("环境变量", await check_environment()))
    results.append(("数据库", await check_database()))
    results.append(("Redis", await check_redis()))
    results.append(("外部 API", await check_api_providers()))
    results.append(("安全配置", await check_security()))
    
    # 汇总结果
    print_header("检查结果汇总")
    
    all_passed = True
    for name, passed in results:
        status = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ 所有检查通过! 系统已准备好部署到生产环境。{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ 部分检查失败! 请修复上述问题后再部署。{Colors.END}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
