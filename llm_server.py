# llm_server.py
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from groq import Groq

# Load API key from environment
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class LLMHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/chat':
            length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(length)
            data = json.loads(post_data)
            question = data.get('question', '')
            context = data.get('context', {})

            prompt = f"""You are Jaguar, an institutional trading assistant.
Current state: {json.dumps(context, indent=2)}
User question: {question}
Answer concisely and professionally."""

            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",  # or qwen/qwen3.6-27b
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=300
                )
                reply = response.choices[0].message.content
            except Exception as e:
                reply = f"⚠️ LLM error: {e}"

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server = HTTPServer(('localhost', 8082), LLMHandler)
    print("🧠 LLM server running on port 8082")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
