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
        except Exception as e:
            print(f"Fact Error: {e}")
            return "Did you know? The first programmer was a woman named Ada Lovelace!"

    def generate_questions(self, content, count, quiz_format='mcq', source_type='text'):
        if not content: return []
        
        # 1. Define source-specific instructions
        if source_type == 'image':
            system_instruction = (
                "You are an expert at interpreting messy OCR text from handwritten notes. "
                "Fix typos contextually before generating questions."
            )
        elif source_type == 'topic':
            system_instruction = "The user provided a broad topic. Use your own internal expert knowledge."
        elif source_type == 'pdf':
            system_instruction = "You are analyzing a formal PDF document. Stick strictly to the facts presented."
        else:
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
        SOURCE CONTENT: {content[:4000]}
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

    # --- YEHA DEKHO: Ye class ke andar hona chahiye (4 spaces ka gap) ---
    def generate_study_material(self, content):
        """Generates Shorthand Notes, Mnemonics, and Flashcards."""
        prompt = f"""
        Analyze this content: {content}
        You are a world-class tutor. Create a study bundle.
        Return ONLY a JSON object with this exact structure:
        {{
            "shorthand_notes": ["point 1", "point 2", "point 3", "point 4", "point 5"],
            "mnemonic_story": "A creative story or acronym to remember the main points",
            "flashcards": [
                {{"front": "Question/Concept 1", "back": "Answer/Explanation 1"}},
                {{"front": "Question/Concept 2", "back": "Answer/Explanation 2"}},
                {{"front": "Question/Concept 3", "back": "Answer/Explanation 3"}},
                {{"front": "Question/Concept 4", "back": "Answer/Explanation 4"}},
                {{"front": "Question/Concept 5", "back": "Answer/Explanation 5"}}
            ]
        }}
        Do not include any text before or after the JSON.
        """

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error in LLM Study Hub: {e}")
            return {
                "shorthand_notes": ["Could not generate notes. Please try again."],
                "mnemonic_story": "Mnemonic generation failed.",
                "flashcards": []
            }