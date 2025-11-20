from lewis_ai_system.config import settings
import os

def check_key(name, value):
    status = "✅ Present" if value else "❌ Missing"
    print(f"{name}: {status}")

print("Checking API Keys Configuration:")
print("-" * 30)
check_key("TAVILY_API_KEY", settings.tavily_api_key)
check_key("FIRECRAWL_API_KEY", settings.firecrawl_api_key)
check_key("E2B_API_KEY", settings.e2b_api_key)
check_key("OPENROUTER_API_KEY", settings.openrouter_api_key)
print("-" * 30)
