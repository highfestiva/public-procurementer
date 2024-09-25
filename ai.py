from groq import Groq
import os


client = Groq(api_key=os.environ.get('GROQ_API_KEY'))


def ask_question(system, question):
    chat_completion = client.chat.completions.create(
            messages=[
                {
                    'role': 'system',
                    'content': system,
                },
                {
                    'role': 'user',
                    'content': question,
                }
            ],
            model='llama3-8b-8192',
            temperature=0.01,
        )
    print(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content
