import openai
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from decouple import config

# Set your API key (recommended to use environment variable)
openai.api_key = config("OPENAI_API_KEY")

@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")

            if not user_message:
                return JsonResponse({"response": "Please enter a message."})

            # New v1.x SDK structure
            client = openai.OpenAI(api_key=config("OPENAI_API_KEY"))

            chat_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are StudyBot, a helpful assistant for students. Answer questions about university courses, exams, study tips, and help users navigate the MyStudy_App platform."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                max_tokens=500,
                temperature=0.7,
            )

            reply = chat_response.choices[0].message.content.strip()
            return JsonResponse({"response": reply})

        except Exception as e:
            print("Chatbot Error:", str(e))
            traceback.print_exc()
            return JsonResponse({"response": "⚠️ Chatbot error: " + str(e)})

    return JsonResponse({"response": "Invalid request method."})
