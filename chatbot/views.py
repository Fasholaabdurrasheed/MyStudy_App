from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import traceback
import re
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from .equation_solver_adapter import EquationSolverAdapter
from .knowledge_adapter import KnowledgeAdapter
from .wikipedia_adapter import WikipediaAdapter
from sympy import symbols, Eq, solve, sympify
import base64
import io
import traceback

# Define the variable symbol globally
x = symbols('x')

# 🔧 Helper: Insert * for implicit multiplication like 2x → 2*x
def insert_multiplication_symbols(expr):
    expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)  # 2x → 2*x
    expr = re.sub(r'([a-zA-Z])(\d)', r'\1*\2', expr)  # x2 → x*2 (rare case)
    return expr

# 🔍 Extract equations like "2x+3 = 7"
def extract_math_expression(text):
    text = text.lower().strip()
    text = insert_multiplication_symbols(text)
    
    # Check if it looks like a math equation involving x and '='
    if '=' in text and 'x' in text:
        return text
    return None

# 🧠 Basic NLP preprocessing (for fallback chatbot logic)
def preprocess_message(message):
    message = message.lower().strip()
    message = re.sub(r"\s+", " ", message)
    message = message.replace("’", "'")
    return message


# Initialize the chatbot
chatbot = ChatBot(
    'StudyBot',
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    logic_adapters=[
        {
            'import_path': 'chatbot.equation_solver_adapter.EquationSolverAdapter'
        },
        'chatterbot.logic.MathematicalEvaluation',
        {
            'import_path': 'chatbot.knowledge_adapter.KnowledgeAdapter'
        },
        {
            'import_path': 'chatbot.wikipedia_adapter.WikipediaAdapter'
        },
        'chatterbot.logic.TimeLogicAdapter',
        {
            'import_path': 'chatterbot.logic.SpecificResponseAdapter',
            'input_text': 'What time is it?',
            'output_text': 'I can tell you the time! However, I need to know your current date and time context. Please provide that information.'
        },
        {
            'import_path': 'chatterbot.logic.BestMatch',
            'default_response': "I'm not sure how to answer that. Could you ask something about studying, university courses, or academic topics? For example, try 'What are some study tips?' or 'Solve 2x + 3 = 7'.",
            'maximum_similarity_threshold': 0.95  # Lowered to balance precision
        }
    ],
    database_uri='sqlite:///database.sqlite3'
)

# Train the chatbot with cleaned study and academic data
trainer = ListTrainer(chatbot)
training_data = [
    "Hello, I'm StudyBot, a helpful assistant for students. How can I assist you today?",
    "Hi StudyBot, what are some study tips?",
    "What are the tips for study?",
    "Here are some study tips: 1. Create a study schedule and stick to it. 2. Take regular breaks using the Pomodoro technique. 3. Use active recall by testing yourself. 4. Study in a distraction-free environment. 5. Summarize key points in your own words.",
    "How do I study?",
    "To study effectively, create a schedule, use active recall, take breaks, and study in a quiet environment. Try the Pomodoro technique and summarize key points.",
    "Can you give me more study tips?",
    "Of course! Here are more study tips: 1. Form study groups to discuss topics. 2. Use flashcards for quick reviews. 3. Teach concepts to someone else to reinforce your understanding. 4. Stay organized with a planner. 5. Get enough sleep to improve focus.",
    "How do I prepare for exams?",
    "What are good ways to prepare for exams?",
    "To prepare for exams, create a study plan, review past papers, focus on key topics, and practice time management during the exam. Also, make sure to take breaks and stay hydrated.",
    "How do I navigate the MyStudy_App platform?",
    "To navigate MyStudy_App, use the sidebar to access features like the dashboard, inbox, and study resources. You can also toggle the chatbot using the button at the bottom right.",
    "What are university courses like?",
    "University courses vary depending on your major, but they typically involve lectures, tutorials, assignments, and exams. Expect to spend time reading, researching, and collaborating with peers.",
    "What is university?",
    "A university is an institution of higher education where students pursue undergraduate and postgraduate degrees.",
    "How can I improve my focus while studying?",
    "To improve your focus while studying, try these tips: 1. Eliminate distractions by turning off notifications. 2. Set specific goals for each study session. 3. Use noise-canceling headphones or white noise. 4. Take short breaks to recharge. 5. Stay hydrated and eat healthy snacks.",
    # Arithmetic training data
    "What is 2 + 2?",
    "The result is 4.",
    "What of 3 + 5?",
    "The result is 8.",
    "Calculate 5 * 3",
    "The result is 15.",
    "What is 10 - 4?",
    "The result is 6.",
    "What’s 7 + 2?",
    "The result is 9.",
    "What is 6 + 6?",
    "The result is 12.",
    "What is 2 * 3?",
    "The result is 6.",
    "Calculate 8 / 2",
    "The result is 4.",
    "Calculate 6 / 2",
    "The result is 3.",
    "What is 2 * 4?",
    "The result is 8.",
    "What is 4 * 4?",
    "The result is 16.",
    "What is 250 * 250?",
    "The result is 62500.",
    "What is 3 / 2?",
    "The result is 1.5.",
    "What is 4 / 2?",
    "The result is 2.",
    # Equation training data
    "Solve 2x + 3 = 7",
    "The solution is x = 2.",
    "Solve 3x + 2 = 7",
    "The solution is x = 5/3.",
    "Solve x + 5 = 10",
    "The solution is x = 5.",
    "Solve 2x + 3 = 5",
    "The solution is x = 1.",
    # Academic training data
    "What is the capital of France?",
    "The capital of France is Paris.",
    "What is the capital of Germany?",
    "The capital of Germany is Berlin.",
    "Who discovered gravity?",
    "Sir Isaac Newton is credited with discovering gravity.",
    "What is the boiling point of water?",
    "The boiling point of water is 100 degrees Celsius at standard pressure.",
    "What is photosynthesis?",
    "Photosynthesis is the process by which green plants use sunlight to convert carbon dioxide and water into glucose and oxygen, using chlorophyll.",
    "Who wrote Hamlet?",
    "William Shakespeare wrote Hamlet.",
    "Who wrote Romeo and Juliet?",
    "William Shakespeare wrote Romeo and Juliet.",
    "what is python?",
    "Python is a high-level, interpreted programming language known for its readability and versatility.",
    "What is quantum mechanics?",
    "Quantum mechanics is a fundamental theory in physics that describes the behavior of matter and energy on microscopic scales, such as atoms and subatomic particles."
]
trainer.train(training_data)

# Debug: Print the number of trained statements
print(f"Number of trained statements: {chatbot.storage.count()}")

# 🧮 Solve equation and return HTML image of the plot
def solve_equation_with_plot(equation_str):
    
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    try:
        equation_str = insert_multiplication_symbols(equation_str)
        lhs_str, rhs_str = equation_str.split('=')
        lhs = sympify(lhs_str)
        rhs = sympify(rhs_str)
        equation = Eq(lhs, rhs)

        solution = solve(equation, x)
        if not solution:
            return "⚠️ No solution found."

        # Plot (lhs - rhs) = 0
        x_vals = [i for i in range(-10, 11)]
        y_vals = [lhs.subs(x, val) - rhs.subs(x, val) for val in x_vals]

        fig = plt.figure()
        plt.axhline(0, color='gray', linestyle='--')
        plt.plot(x_vals, y_vals, label=f'{lhs_str} - ({rhs_str}) = 0', color='blue')
        plt.title("Equation Plot")
        plt.xlabel("x")
        plt.ylabel("y")
        plt.legend()

        # Convert plot to base64 image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close(fig)

        encoded_image = base64.b64encode(image_png).decode('utf-8')
        image_html = f'<img src="data:image/png;base64,{encoded_image}" alt="Equation plot"/>'

        return f"✅ Solution: x = {solution[0]} [[IMAGE:{encoded_image}]]"

    
    except Exception as e:
        return f"❌ Error solving equation: {e}"

# 💬 Main Chatbot Response View
@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").lower().strip()

            if not user_message:
                return JsonResponse({"response": "Please enter a message."})

            # 1. Try to extract and solve a math expression
            math_expression = extract_math_expression(user_message)
            if math_expression:
                reply = solve_equation_with_plot(math_expression)

            # 🧠 Add custom checks BEFORE calling the chatbot
            elif any(greet in user_message for greet in ["hello", "hi", "hey", "good morning", "good afternoon"]):
                reply = "👋 Hello! How can I help you today?"

            elif "time" in user_message:
                from datetime import datetime
                now = datetime.now().strftime("%I:%M %p")
                reply = f"🕒 The current time is {now}"

            else:
                temp_message = preprocess_message(user_message)
                response = chatbot.get_response(temp_message)
                reply = str(response)

            return JsonResponse({"response": reply})

        except Exception as e:
            print("Chatbot Error:", str(e))
            traceback.print_exc()
            return JsonResponse({"response": "⚠️ Chatbot error: " + str(e)})

    return JsonResponse({"response": "Invalid request method."})
