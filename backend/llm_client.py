import json
import os
from groq import Groq

class LLMClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def get_fun_fact(self):
        prompt = "Generate one short, mind-blowing fun fact about Artificial Intelligence. Under 20 words."
        try:
            # Using compound-mini for the fastest response
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="groq/compound-mini",
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Fact Error: {e}")
            return "Did you know? The first programmer was a woman named Ada Lovelace!"

    def generate_questions(self, content, count, quiz_format='mcq', source_type='text'):
        if not content: return []
        
        # System instructions based on source
        instructions = {
            'image': "Expert at interpreting messy OCR. Fix typos contextually.",
            'topic': "User provided a topic. Use internal expert knowledge.",
            'pdf': "Analyze formal PDF. Stick strictly to provided facts."
        }
        system_instruction = instructions.get(source_type, "Generate educational questions from notes.")

        prompt = f"""
        TASK: Generate {count} {quiz_format} questions.
        SOURCE: {content[:4000]}
        Return ONLY a JSON object with a "questions" list containing:
        question_text, options (dict), correct_answer, explanation, difficulty.
        """

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                model="groq/compound-mini", # Fast and reliable for JSON
                response_format={"type": "json_object"}
            )
            data = json.loads(completion.choices[0].message.content)
            return data.get("questions", [])
        except Exception as e:
            print(f"LLM Error: {e}")
            return []

    def generate_study_material(self, content):
        prompt = f"""
        Analyze: {content}
        Return ONLY a JSON object:
        {{
            "shorthand_notes": ["list"],
            "detailed_revision": "paragraph",
            "mnemonic_story": "story",
            "flashcards": [{{"front": "...", "back": "..."}}]
        }}
        """
        try:
            response = self.client.chat.completions.create(
                model="groq/compound", # 'compound' is better for detailed reasoning
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Study Hub Error: {e}")
            return {
                "shorthand_notes": ["Note generation failed."],
                "detailed_revision": "Service temporarily unavailable.",
                "mnemonic_story": "Failed to generate mnemonic.",
                "flashcards": []
            }

    def simplify_content(self, text):
        prompt = f"Explain this like I'm 10 years old with analogies: {text}"
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="groq/compound-mini",
                temperature=0.8
            )
            return completion.choices[0].message.content
        except Exception as e:
            return "My brain froze trying to simplify this!"
