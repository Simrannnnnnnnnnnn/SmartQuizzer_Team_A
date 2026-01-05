import json
from groq import Groq

class LLMClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
    def get_fun_fact(self):
      prompt = "Generate one short, mind-blowing fun fact about Artificial Intelligence or Computer Science. Keep it under 20 words and make it interesting for students."
      try:
        completion = self.client.chat.completions.create(
          messages=[{"role": "user", "content": prompt}],
          model="llama-3.3-70b-versatile",
        )
        return completion.choices[0].message.content
      except:
        print(f"Fact Error:{e}")
        return "Did you know? The first programmer was a woman named Ada Lovelace!"

    def generate_questions(self, content, count, quiz_format='mcq', source_type='text'):
        if not content: return []
        
        # 1. Define source-specific instructions
        if source_type == 'image':
            system_instruction = (
                "You are an expert at interpreting messy OCR text from handwritten notes. "
                "The text has typos like 'Mavhine' for 'Machine'. Fix these contextually "
                "before generating questions. Use professional terminology only."
            )
        elif source_type == 'topic':
            system_instruction = (
                "The user provided a broad topic. Use your own internal expert knowledge "
                "to generate comprehensive educational questions about this subject."
            )
        elif source_type == 'pdf':
            system_instruction = (
                "You are analyzing a formal PDF document. Stick strictly to the facts "
                "presented in the text and generate academic-style questions."
            )
        else: # Default for raw text
            system_instruction = "Generate educational questions based on the provided study notes."

        # 2. Define format instructions
        format_instruction = {
            'mcq': "Generate ONLY Multiple Choice Questions (4 options: A, B, C, D).",
            'tf': "Generate ONLY True/False questions (2 options: A: True, B: False).",
            'theory': "Generate Short Answer questions. Set 'options' to {} and provide a concise 'correct_answer'.",
            'mixed': "Generate a variety of MCQ, True/False, and Short Answer questions."
        }

        # 3. Build the final prompt
        prompt = f"""
        TASK: {format_instruction.get(quiz_format, format_instruction['mcq'])}
        
        SOURCE CONTENT:
        ---
        {content[:4000]}
        ---

        Generate {count} questions. 
        
        STRICT JSON STRUCTURE:
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
        """
        
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
            )
            data = json.loads(completion.choices[0].message.content)
            return data.get("questions", [])
        except Exception as e:
            print(f"LLM Error: {e}")
            return []