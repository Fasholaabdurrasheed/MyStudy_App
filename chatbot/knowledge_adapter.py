from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement
import re

class KnowledgeAdapter(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)
        # Expanded knowledge base aligned with training data
        self.knowledge = {
            r"what is the capital of france": "The capital of France is Paris.",
            r"what is the capital of germany": "The capital of Germany is Berlin.",
            r"what is the capital of\s+([\w\s]+)": lambda x: f"The capital of {x.strip()} is not in my knowledge base. Try a known country like France or Germany.",
            r"who (?:discovered|is the father of) gravity": "Sir Isaac Newton is credited with discovering gravity.",
            r"what is the boiling point of water": "The boiling point of water is 100 degrees Celsius at standard pressure.",
            r"what is photosynthesis": "Photosynthesis is the process by which green plants use sunlight to convert carbon dioxide and water into glucose and oxygen, using chlorophyll.",
            r"what is the formula for water": "The chemical formula for water is H2O.",
            r"who wrote (?:hamlet|romeo and juliet)": "William Shakespeare wrote Hamlet and Romeo and Juliet.",
            r"what is python": "Python is a high-level, interpreted programming language known for its readability and versatility.",
            r"what is the theory of relativity": "The theory of relativity, developed by Albert Einstein, includes special relativity and general relativity, describing the relationship between space, time, and gravity."
        }

    def can_process(self, statement):
        text = statement.text.lower()
        # Exclude math-related queries
        if re.search(r'\d+\s*[\+\-\*/=]\s*\d+', text) or 'solve' in text:
            return False
        return any(keyword in text for keyword in ["what is", "who", "capital", "boiling point", "discovered", "formula", "wrote"]) or any(
            re.match(pattern, text) for pattern in self.knowledge.keys()
        )

    def process(self, statement, additional_response_selection_parameters=None):
        text = statement.text.lower()
        response_text = "I don't know the answer to that."
        confidence = 0.1

        for pattern, answer in self.knowledge.items():
            match = re.match(pattern, text)
            if match:
                if callable(answer):
                    response_text = answer(match.group(1) if match.groups() else "")
                else:
                    response_text = answer
                confidence = 0.95
                break

        response = Statement(text=response_text)
        response.confidence = confidence
        print(f"KnowledgeAdapter: Text: {text}, Response: {response_text}, Confidence: {confidence}")
        return response