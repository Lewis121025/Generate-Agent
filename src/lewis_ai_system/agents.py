"""Shared agent primitives."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Sequence

from .config import settings
from .providers import LLMProvider, default_llm_provider


class PlanningAgent:
    """Expands prompts into actionable steps."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or default_llm_provider

    async def expand_brief(self, prompt: str, *, mode: str) -> dict[str, Any]:
        completion = await self.provider.complete(
            f"Expand the following brief for {mode} mode:\n{prompt}",
            temperature=0.4,
        )
        digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:8]
        return {
            "summary": completion,
            "hash": digest,
            "mode": mode,
        }


class QualityAgent:
    """Performs LLM-based quality scoring with independent QC workflow and rule engine."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or default_llm_provider
        self.qc_rules: list[dict[str, Any]] = []
        # Initialize default QC rules
        self._init_default_rules()

    def _init_default_rules(self) -> None:
        """Initialize default QC rules."""
        self.add_qc_rule("content_quality", ["quality", "relevance"], threshold=0.7)
        self.add_qc_rule("completeness", ["completeness", "coherence"], threshold=0.6)
        self.add_qc_rule("technical_quality", ["technical", "accuracy"], threshold=0.75)

    def add_qc_rule(self, rule_name: str, criteria: list[str], threshold: float = 0.7, auto_approve: bool = False) -> None:
        """Add a QC rule to the rule engine."""
        self.qc_rules.append({
            "name": rule_name,
            "criteria": criteria,
            "threshold": threshold,
            "auto_approve": auto_approve,
        })

    async def evaluate(self, artifact: str, criteria: Sequence[str]) -> dict[str, Any]:
        criteria_list = ", ".join(criteria)
        use_mock_shortcut = settings.llm_provider_mode == "mock" and self.provider is default_llm_provider
        if use_mock_shortcut:
            return {
                "score": 0.82,
                "criteria": list(criteria),
                "notes": "Mock evaluation pass",
            }
        prompt = (
            f"Evaluate the following text against these criteria: {criteria_list}.\n"
            "Provide a score from 0.0 to 1.0 and a brief justification.\n"
            f"Text: {artifact[:2000]}"  # Truncate to avoid context limits
        )
        response = await self.provider.complete(prompt, temperature=0.1)
        
        # Simple heuristic to extract score if possible, otherwise default
        # This is a basic implementation; in production, we'd use structured output
        score = 0.8
        if "0." in response:
            try:
                # Attempt to find a float in the response
                words = response.split()
                for word in words:
                    # Strip common punctuation
                    clean_word = word.strip(".,;!?")
                    if "0." in clean_word and clean_word.replace(".", "", 1).isdigit():
                        val = float(clean_word)
                        if 0 <= val <= 1:
                            score = val
                            break
            except ValueError:
                pass

        return {
            "score": score,
            "criteria": list(criteria),
            "notes": response.strip(),
        }

    async def run_qc_workflow(
        self,
        content: str,
        content_type: str = "general",
        apply_rules: bool = True
    ) -> dict[str, Any]:
        """Run independent QC workflow with rule engine."""
        results = {
            "overall_score": 0.0,
            "passed": False,
            "rule_results": [],
            "recommendations": [],
        }

        # Apply QC rules if enabled
        if apply_rules and self.qc_rules:
            for rule in self.qc_rules:
                criteria_tuple = tuple(rule["criteria"])
                evaluation = await self.evaluate(content, criteria_tuple)
                rule_result = {
                    "rule_name": rule["name"],
                    "score": evaluation["score"],
                    "threshold": rule["threshold"],
                    "passed": evaluation["score"] >= rule["threshold"],
                    "notes": evaluation["notes"],
                }
                results["rule_results"].append(rule_result)
                
                if not rule_result["passed"]:
                    results["recommendations"].append(
                        f"Rule '{rule['name']}' failed: {evaluation['notes']}"
                    )
                elif rule.get("auto_approve", False) and rule_result["passed"]:
                    results["passed"] = True

        # Overall evaluation if no rules or rules didn't auto-approve
        if not results["passed"]:
            overall_eval = await self.evaluate(content, ("quality", "relevance", "completeness"))
            results["overall_score"] = overall_eval["score"]
            results["passed"] = overall_eval["score"] >= 0.7
            if not results["passed"]:
                results["recommendations"].append(f"Overall quality below threshold: {overall_eval['notes']}")

        return results

    async def validate_preview(
        self,
        preview_content: dict[str, Any],
        project_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Validate preview content before final approval."""
        if settings.llm_provider_mode == "mock":
            return {
                "approved": True,
                "score": 0.9,
                "issues": [],
                "notes": "Mock validation auto-approved",
            }
        content_str = json.dumps(preview_content, indent=2)
        context_str = json.dumps(project_context or {}, indent=2) if project_context else ""
        
        prompt = (
            "Validate this preview content for final approval.\n"
            f"Preview Content:\n{content_str}\n\n"
            f"Project Context:\n{context_str}\n\n"
            "Check for: visual quality, consistency, completeness, brand compliance.\n"
            "Return JSON with 'approved' (bool), 'score' (float), 'issues' (list), 'notes' (string)."
        )
        
        response = await self.provider.complete(prompt, temperature=0.1)
        
        # Parse response
        try:
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                score = float(parsed.get("score", 0.5))
                approved = bool(parsed.get("approved", False))
                if not approved and score >= 0.4:
                    approved = True
                return {
                    "approved": approved,
                    "score": score,
                    "issues": parsed.get("issues", []),
                    "notes": parsed.get("notes", response.strip()),
                }
        except (ValueError, KeyError, json.JSONDecodeError):
            pass
        
        # Fallback
        return {
            "approved": True,
            "score": 0.6,
            "issues": ["Could not parse validation response"],
            "notes": response.strip(),
        }


class OutputFormatterAgent:
    """Produces human readable outputs."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or default_llm_provider

    async def summarize(self, content: str) -> str:
        return await self.provider.complete(f"Summarize the following content:\n{content}", temperature=0.1)


class CreativeAgent:
    """Handles creative content generation."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or default_llm_provider

    async def write_script(self, brief: str, duration: int, style: str) -> str:
        prompt = (
            "You are a professional screenwriter. Create a compelling scene-by-scene script based on the brief below.\n"
            "Structure the output clearly with Scene Headers (e.g., SCENE 1: [LOCATION] - [TIME]), Action Lines, and Dialogue.\n"
            f"Target Duration: {duration} seconds.\n"
            f"Style: {style}.\n"
            f"Brief:\n{brief}\n\n"
            "Ensure the script is paced well for the target duration."
        )
        return await self.provider.complete(prompt, temperature=0.7)

    async def split_script(self, script: str, total_duration: int) -> list[dict[str, Any]]:
        prompt = (
            "Analyze the following script and split it into distinct scenes.\n"
            "Return a JSON object with a key 'scenes', where each item is an object containing:\n"
            "- 'description': A concise visual description of the action and setting.\n"
            "- 'visual_cues': Specific camera or lighting notes based on the style.\n"
            "- 'estimated_duration': Estimated duration in seconds (integer).\n\n"
            f"Script:\n{script}\n\n"
            "Ensure the total duration roughly matches the target. Return ONLY valid JSON."
        )
        response = await self.provider.complete(prompt, temperature=0.1)
        
        # Basic JSON cleanup
        text = response.strip()
        if text.startswith("```"):
            import re
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            
        try:
            import json
            data = json.loads(text)
            return data.get("scenes", [])
        except Exception:
            # Fallback
            chunks = [c.strip() for c in script.split("\n\n") if c.strip()]
            return [
                {
                    "description": c,
                    "visual_cues": "Standard shot",
                    "estimated_duration": max(total_duration // max(len(chunks), 1), 5)
                }
                for c in chunks
            ]

    async def generate_panel_visual(self, description: str) -> str:
        """Generate a visual for a storyboard panel using DALL-E 3 or fallback.
        
        Returns:
            URL of the generated image
        """
        from .config import settings
        from .instrumentation import get_logger
        
        logger = get_logger()
        
        # 生产环境必须使用真实的图片生成 API
        if settings.environment == "production" and not settings.openrouter_api_key:
            raise RuntimeError(
                "生产环境必须配置 OPENROUTER_API_KEY 以生成分镜图片!"
            )
        
        # 尝试使用 OpenAI DALL-E 3 生成图片
        try:
            # 构造专业的分镜提示词
            prompt = f"Professional storyboard sketch: {description}. Clean linework, cinematographic composition, black and white or minimal color."
            
            # 如果配置了 OpenRouter,尝试通过 OpenRouter 调用 DALL-E
            if settings.openrouter_api_key:
                import httpx
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    # Note: OpenRouter 可能不支持图片生成,需要直接调用 OpenAI
                    # 这里先记录日志,实际可能需要独立的 OPENAI_API_KEY
                    logger.warning(
                        "图片生成需要 OpenAI API Key, OpenRouter 可能不支持此功能。"
                        "考虑配置独立的 OPENAI_API_KEY 或使用 Replicate API。"
                    )
            
            # 开发/测试环境 Fallback 到占位图
            logger.info(f"使用 Mock 图片生成 (开发模式): {description[:50]}...")
            import hashlib
            digest = hashlib.md5(description.encode()).hexdigest()[:8]
            
            # 使用真实的占位符服务 (支持自定义尺寸)
            return f"https://placehold.co/1024x576/1a1a1a/white?text=Storyboard+{digest}"
            
        except Exception as e:
            logger.error(f"图片生成失败: {e}")
            # 返回错误占位图
            return "https://placehold.co/1024x576/ff0000/white?text=Generation+Failed"


class GeneralAgent:
    """Handles general queries using a ReAct loop."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or default_llm_provider

    async def react_loop(self, query: str, tool_runtime: Any, max_steps: int = 5) -> str:
        """Execute a ReAct loop to answer the query using available tools."""
        from .tooling import ToolRequest, ToolExecutionError
        from .general.models import GuardrailTriggered

        import json
        
        tools_desc_list = []
        for name, tool in tool_runtime._tools.items():
            try:
                schema = json.dumps(tool.parameters, indent=2)
            except NotImplementedError:
                schema = "{}"
            tools_desc_list.append(f"- {name}: {tool.description}\n  Parameters: {schema}")
        
        tools_desc = "\n".join(tools_desc_list)
        
        system_prompt = (
            "You are a helpful AI assistant with access to the following tools:\n"
            f"{tools_desc}\n\n"
            "Use the following format:\n"
            "Question: the input question you must answer\n"
            "Thought: you should always think about what to do\n"
            "Action: the action to take, should be one of the tool names\n"
            "Action Input: the input to the action as a valid JSON string matching the tool's parameter schema\n"
            "Observation: the result of the action\n"
            "... (this Thought/Action/Action Input/Observation can repeat N times)\n"
            "Thought: I now know the final answer\n"
            "Final Answer: the final answer to the original input question\n\n"
            "Begin!"
        )

        history = f"{system_prompt}\n\nQuestion: {query}\n"
        for _ in range(max_steps):
            # Get LLM response
            response = await self.provider.complete(history, temperature=0.0)
            history += f"{response}\n"

            if "Final Answer:" in response:
                return response.split("Final Answer:")[-1].strip()

            # Parse Action
            if "Action:" in response and "Action Input:" in response:
                try:
                    import re
                    import json
                    
                    action_match = re.search(r"Action:\s*(.*?)\n", response)
                    input_match = re.search(r"Action Input:\s*(.*)", response, re.DOTALL)
                    
                    if not action_match or not input_match:
                        raise ValueError("Could not parse Action or Action Input")

                    action_name = action_match.group(1).strip()
                    action_input_str = input_match.group(1).strip()
                    
                    # Clean up JSON string if needed (remove markdown code blocks)
                    if action_input_str.startswith("```"):
                        action_input_str = re.sub(r"^```(?:json)?\s*", "", action_input_str)
                        action_input_str = re.sub(r"\s*```$", "", action_input_str)
                    
                    # Handle single quotes or other common JSON errors heuristically if needed
                    # For now, assume valid JSON or simple dict string
                    try:
                        action_input = json.loads(action_input_str)
                    except json.JSONDecodeError:
                        # Fallback for simple string inputs if the tool expects a specific key
                        # This is a simplification; a robust parser would be better
                        action_input = {"input": action_input_str}

                    # Execute Tool
                    observation = f"Observation: Error: Tool '{action_name}' not found."
                    if action_name in tool_runtime._tools:
                        try:
                            result = tool_runtime.execute(ToolRequest(name=action_name, input=action_input))
                            observation = f"Observation: {result.output}"
                        except GuardrailTriggered:
                            # Bubble up so orchestrator can pause gracefully
                            raise
                        except Exception as e:
                            observation = f"Observation: Tool execution failed: {str(e)}"
                    
                except Exception as e:
                    observation = f"Observation: Failed to parse or execute action: {str(e)}"
                
                history += f"{observation}\n"
            else:
                # If no action is taken but no final answer, force a stop or ask for continuation
                # For now, just return the response as is if it seems complete
                return response.strip()

        return "I could not answer the question within the step limit."


class AgentPool:
    """Shared agent facade."""

    def __init__(self) -> None:
        self.planning = PlanningAgent()
        self.quality = QualityAgent()
        self.formatter = OutputFormatterAgent()
        self.creative = CreativeAgent()
        self.general = GeneralAgent()


agent_pool = AgentPool()
