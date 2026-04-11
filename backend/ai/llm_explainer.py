"""
Code Archaeologist - LLM Function Explainer
Week 3: AI-powered function documentation using GPT-3.5-Turbo
"""

import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass

# Optional OpenAI import
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class FunctionExplanation:
    """AI-generated function explanation"""
    function_name: str
    explanation: str
    key_points: List[str]
    parameters: List[str]
    return_value: str
    model_used: str
    confidence: str


class LLMFunctionExplainer:
    """
    Week 3: LLM-based function documentation
    
    Uses GPT-3.5-Turbo to explain what functions do
    and extract key insights from code.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize explainer
        
        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"
        self.has_openai = HAS_OPENAI
        
        if self.api_key and self.has_openai:
            openai.api_key = self.api_key
    
    def is_available(self) -> bool:
        """Check if LLM is available"""
        return self.has_openai and self.api_key is not None
    
    def explain_function(
        self,
        function_name: str,
        code_snippet: str,
        context: Optional[str] = None,
        language: str = "python"
    ) -> FunctionExplanation:
        """
        Explain a function using LLM
        
        Args:
            function_name: Name of the function
            code_snippet: The actual code
            context: Optional surrounding code context
            language: Programming language
            
        Returns:
            FunctionExplanation with AI analysis
        """
        if not self.is_available():
            # Fallback when LLM not available
            return self._fallback_explanation(function_name, code_snippet, language)
        
        try:
            # Build prompt
            prompt = self._build_prompt(function_name, code_snippet, context, language)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a code analysis expert. Explain functions concisely."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            explanation_text = response.choices[0].message.content
            
            # Extract structured info
            return self._parse_explanation(
                function_name,
                explanation_text,
                code_snippet,
                self.model
            )
            
        except Exception as e:
            print(f"⚠️ LLM error: {e}")
            return self._fallback_explanation(function_name, code_snippet, language)
    
    def _build_prompt(
        self,
        function_name: str,
        code: str,
        context: Optional[str],
        language: str
    ) -> str:
        """Build prompt for LLM"""
        prompt = f"""Analyze this {language} function:

Function: {function_name}
Code:
```
{code}
```
"""
        if context:
            prompt += f"""
Context:
```
{context}
```
"""
        
        prompt += """
Provide a JSON response with:
{
    "explanation": "One sentence describing what this function does",
    "key_points": ["List of 2-3 key behaviors or effects"],
    "parameters": ["Parameter name and purpose"],
    "return_value": "What the function returns"
}
"""
        return prompt
    
    def _parse_explanation(
        self,
        function_name: str,
        text: str,
        code: str,
        model: str
    ) -> FunctionExplanation:
        """Parse LLM response into structured format"""
        try:
            # Try to extract JSON from response
            # Look for JSON block
            if '```json' in text:
                json_str = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                json_str = text.split('```')[1].split('```')[0].strip()
            else:
                # Try to find JSON object
                start = text.find('{')
                end = text.rfind('}') + 1
                json_str = text[start:end] if start >= 0 and end > start else text
            
            data = json.loads(json_str)
            
            return FunctionExplanation(
                function_name=function_name,
                explanation=data.get('explanation', text[:200]),
                key_points=data.get('key_points', ['Analyzes code structure']),
                parameters=data.get('parameters', self._extract_params(code)),
                return_value=data.get('return_value', 'Unknown'),
                model_used=model,
                confidence="high"
            )
            
        except json.JSONDecodeError:
            # Use text directly
            return FunctionExplanation(
                function_name=function_name,
                explanation=text[:300],
                key_points=["See full explanation above"],
                parameters=self._extract_params(code),
                return_value="Unknown",
                model_used=model,
                confidence="medium"
            )
    
    def _extract_params(self, code: str) -> List[str]:
        """Extract parameter names from code (simple regex)"""
        import re
        
        # Match function definition
        match = re.search(r'def\s+\w+\s*\(([^)]*)\)', code)
        if match:
            params = match.group(1).split(',')
            return [p.strip().split(':')[0].split('=')[0].strip() 
                    for p in params if p.strip()]
        return []
    
    def _fallback_explanation(
        self,
        function_name: str,
        code: str,
        language: str
    ) -> FunctionExplanation:
        """Generate explanation without LLM"""
        # Simple analysis based on code patterns
        explanation = f"Function '{function_name}' in {language}"
        key_points = ["Static analysis fallback"]
        
        # Detect patterns
        if 'return' in code:
            key_points.append("Returns a value")
        if 'for ' in code or 'while ' in code:
            key_points.append("Contains loops")
        if 'if ' in code:
            key_points.append("Has conditional logic")
        if 'def ' in code or 'class ' in code:
            key_points.append("Defines nested functions/classes")
        
        return FunctionExplanation(
            function_name=function_name,
            explanation=explanation,
            key_points=key_points,
            parameters=self._extract_params(code),
            return_value="See code" if 'return' in code else "None/void",
            model_used="rule-based-fallback",
            confidence="low"
        )
    
    def batch_explain(
        self,
        functions: List[Dict[str, str]],
        max_concurrent: int = 5
    ) -> List[FunctionExplanation]:
        """
        Explain multiple functions
        
        Args:
            functions: List of dicts with 'name', 'code', 'context', 'language'
            max_concurrent: Max parallel requests
            
        Returns:
            List of FunctionExplanation objects
        """
        results = []
        
        for func in functions:
            explanation = self.explain_function(
                function_name=func['name'],
                code_snippet=func['code'],
                context=func.get('context'),
                language=func.get('language', 'python')
            )
            results.append(explanation)
        
        return results
    
    def generate_summary(
        self,
        functions: List[FunctionExplanation],
        project_name: str = "Code Analysis"
    ) -> str:
        """
        Generate project summary from function explanations
        
        Args:
            functions: List of function explanations
            project_name: Project name
            
        Returns:
            Markdown summary string
        """
        summary = f"# {project_name} - Code Analysis Summary\n\n"
        summary += f"**Generated**: {len(functions)} functions analyzed\n\n"
        
        for i, func in enumerate(functions, 1):
            summary += f"## {i}. `{func.function_name}`\n\n"
            summary += f"{func.explanation}\n\n"
            
            if func.key_points:
                summary += "**Key Points:**\n"
                for point in func.key_points:
                    summary += f"- {point}\n"
                summary += "\n"
            
            if func.parameters:
                summary += f"**Parameters:** {', '.join(func.parameters)}\n\n"
            
            summary += f"**Returns:** {func.return_value}\n\n"
            summary += f"*Model: {func.model_used} (confidence: {func.confidence})*\n\n"
            summary += "---\n\n"
        
        return summary


# Convenience function
def explain_function(
    function_name: str,
    code: str,
    api_key: Optional[str] = None,
    context: Optional[str] = None
) -> FunctionExplanation:
    """
    Quick explain function
    
    Usage:
        explanation = explain_function("process", "def process(): return 1")
        print(explanation.explanation)
    """
    explainer = LLMFunctionExplainer(api_key)
    return explainer.explain_function(function_name, code, context)


if __name__ == '__main__':
    # Test
    print("LLM Function Explainer - Week 3")
    print("=" * 50)
    
    # Test with sample code
    test_code = """
def process(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
"""
    
    explainer = LLMFunctionExplainer()
    
    if explainer.is_available():
        print("✅ OpenAI API available")
        explanation = explainer.explain_function("process", test_code)
        print(f"\nFunction: {explanation.function_name}")
        print(f"Explanation: {explanation.explanation}")
        print(f"Key Points: {explanation.key_points}")
    else:
        print("⚠️ OpenAI not available (set OPENAI_API_KEY)")
        print("Using fallback mode...")
        explanation = explainer.explain_function("process", test_code)
        print(f"\nFunction: {explanation.function_name}")
        print(f"Explanation: {explanation.explanation}")
        print(f"Key Points: {explanation.key_points}")
