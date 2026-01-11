import json
import os
from groq import Groq

class LLMClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.FAST_MODEL = "llama-3.1-8b-instant"
        self.POWER_MODEL = "llama-3.3-70b-versatile"

    def generate_questions(self, content, count, quiz_format='mcq', source_type='text'):
        if not content: return []

        # 1. STRICT Persona Setup
        system_prompt = (
            "You are a Strict Educational API. You ONLY output valid JSON. "
            "You NEVER include conversational text, greetings, or markdown code blocks (like ```json). "
            "Your goal is to create high-accuracy academic questions."
        )

        # 2. Format-Specific Example (Strict Instruction)
        if quiz_format == 'tf':
            format_example = '{"question_text": "Is the sky blue?", "options": {"A": "True", "B": "False"}, "correct_answer": "A", "explanation": "Sky appears blue due to scattering."}'
        elif quiz_format == 'theory':
            format_example = '{"question_text": "Define Gravity.", "options": {}, "correct_answer": "Gravity is a force...", "explanation": "It pulls objects toward the center.", "ideal_answer": "The force that attracts a body toward the center of the earth."}'
        else:
            format_example = '{"question_text": "Q", "options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "correct_answer": "A", "explanation": "Exp"}'

        # 3. Final Strict Prompt
        user_prompt = f"""
        STRICT TASK: Generate {count} {quiz_format} questions from the content below.
        
        CONTENT: {content[:4000]}

        JSON STRUCTURE MUST BE:
        {{
          "questions": [
             {format_example}
          ]
        }}

        STRICT RULES:
        1. If format is 'tf', always use A: True and B: False.
        2. If format is 'theory', 'options' must be an empty dictionary {{}}.
        3. All 'correct_answer' keys must match the option key (e.g., 'A') or the full answer string for theory.
        4. Return ONLY the JSON object.
        """

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.POWER_MODEL,
                response_format={"type": "json_object"}, # This forces Groq to return JSON
                temperature=0.1 # Low temperature = High accuracy/strictness
            )
            data = json.loads(completion.choices[0].message.content)
            return data.get("questions", [])
        except Exception as e:
            print(f"Strict Generation Error: {e}")
            return []

    # get_fun_fact, generate_study_material, simplify_content remains the same...
