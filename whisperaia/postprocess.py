import ollama

BASE_SYSTEM_PROMPT = """你是语音转文字后处理助手，专门处理中英文混合的技术内容。

规则：
1. 保留英文技术术语原样，不翻译（agent、orchestration、LLM、API、layer、pipeline 等）
2. 修正明显的同音字错误和语音识别偏差（如"编排层"→"orchestration layer"）
3. 不添加任何标点符号，保持口语原貌
4. 最小化改动，不改变语义
5. 直接输出修正后的文字，不要任何解释

示例：
输入：我们今天来聊一下agent system中 ochestration layer的设计模式
输出：我们今天来聊一下agent system中orchestration layer的设计模式"""


class OllamaPostProcessor:
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model

    def process(self, text: str, corrections: list[tuple[str, str]] | None = None) -> str:
        if not text:
            return text
        system = BASE_SYSTEM_PROMPT
        if corrections:
            examples = "\n".join(f"- {orig} → {corr}" for orig, corr in corrections)
            system += f"\n\n用户历史纠错（优先参考）：\n{examples}"
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text},
                ],
                options={"temperature": 0.1},
            )
            result = response["message"]["content"].strip()
            if len(result) > len(text) * 2:
                return text
            return result
        except Exception:
            return text
