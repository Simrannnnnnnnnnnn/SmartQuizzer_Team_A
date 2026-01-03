import json
from groq import Groq

class LLMClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def generate_questions(self, content, count, quiz_format='mcq'):
        if not content: return []
        
        # Mapping logic to ensure the AI understands the user's intent
        format_instruction = {
            'mcq': "Generate ONLY Multiple Choice Questions with exactly 4 options (A, B, C, D).",
            'tf': "Generate ONLY True/False questions with exactly 2 options (A: True, B: False).",
            'theory': "Generate ONLY Short Answer questions. Set the 'options' to {} and provide a concise answer in 'correct_answer'.",
            'mixed': "Generate a VARIETY of Multiple Choice(4 options), True/False (2 options), and Short Answer (options:{}) questions."
        }

        prompt = f"""
        {format_instruction.get(quiz_format, format_instruction['mcq'])}
        
        Generate {count} questions from the following content: {content[:3000]}
        
        STRICT JSON STRUCTURE:
        Return ONLY a JSON object:
        {{
          "questions": [
            {{
              "question_text": "...",
              "options": {{"A": "...", "B": "..."}}, 
              "correct_answer": "...",
              "explanation": "...",
              "difficulty": "Medium" 
            }}
          ]
        }}
        
        RULES:
        - For MCQ: "options" must have A, B, C, D.
        - For TF: "options" must have A, B.
        - For Theory : "options" must be {{}}.
        - Always provide a clear "explanation".
        """
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
            )
            data = json.loads(completion.choices[0].message.content)
            return data.get("questions", [])
        except Exception as e:
            print(f"LLM Error: {e}")
            return []