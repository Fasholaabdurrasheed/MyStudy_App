from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement
import wikipedia
import re
from bs4 import BeautifulSoup

class WikipediaAdapter(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)
        wikipedia.set_lang("en")

    def can_process(self, statement):
        text = statement.text.lower()
        # Process only if it's a question, not math or time-related
        return (
            ("what is" in text or "who is" in text or "where is" in text or "when did" in text)
            and not re.search(r'\d+\s*[\+\-\*/=]\s*\d+', text)
            and not re.search(r'\b(time|clock|now)\b', text)
            and "solve" not in text
        )

    def process(self, statement, additional_response_selection_parameters=None):
        text = statement.text.lower()
        try:
            # Extract and normalize query (e.g., "what is python" -> "Python")
            query = re.sub(r'^(what is|who is|where is|when did)\s+', '', text).strip()
            query = query.title()  # Capitalize for Wikipedia
            if not query:
                response_text = "Please provide a specific topic to look up."
                confidence = 0.1
            else:
                # Fetch Wikipedia summary (limit to 2 sentences)
                summary = wikipedia.summary(query, sentences=2, auto_suggest=True, parser='lxml')
                response_text = summary
                confidence = 0.9
        except wikipedia.exceptions.DisambiguationError as e:
            response_text = f"Multiple results found for '{query}'. Try being more specific, e.g., '{e.options[0]}'."
            confidence = 0.5
        except wikipedia.exceptions.PageError:
            response_text = f"I couldn't find information on '{query}' in Wikipedia. Try another topic."
            confidence = 0.5
        except Exception as e:
            response_text = "Sorry, I couldn't fetch that information. Try a different question."
            confidence = 0.1

        response = Statement(text=response_text)
        response.confidence = confidence
        print(f"WikipediaAdapter: Text: {text}, Response: {response_text}, Confidence: {confidence}")
        return response