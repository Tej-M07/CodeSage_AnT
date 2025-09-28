
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import google.generativeai as genai
# ADD THIS LINE:
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import google.generativeai as genai
import json
import ast
import subprocess
import tempfile
import os
import PyPDF2
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'codesage_hackathon_2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# Your working Gemini API key
GEMINI_API_KEY = "AIzaSyC1pN-EiPov1ZElGmRiR0E8PU3x9heUs-A"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

class GeminiCodeSageInterviewer:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.interview_state = {
            "candidate_profile": None,
            "current_question": None,
            "question_count": 0,
            "questions": [],
            "conversation_history": []
        }
        
        self.default_problem = {
            "id": "default",
            "title": "Welcome to CodeSage",
            "description": "Upload your resume to start your personalized technical interview powered by Gemini AI.",
            "template": "# Welcome! Upload your resume to begin\n# Your personalized coding questions will appear here\nprint('Hello CodeSage!')"
        }
        
    def parse_resume(self, file_content, filename):
        """Parse resume content from uploaded file"""
        try:
            if filename.lower().endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            elif filename.lower().endswith('.txt'):
                return file_content.decode('utf-8')
            else:
                return "Error: Please upload PDF or TXT file."
        except Exception as e:
            return f"Error parsing resume: {str(e)}"

    def analyze_resume_with_gemini(self, resume_text):
        """Analyze resume using working Gemini"""
        prompt = f"""You are an expert technical recruiter analyzing a software engineer's resume. 

RESUME CONTENT:
{resume_text[:3000]}

Please analyze this resume and create a personalized interview plan with exactly 4 questions:

1. One behavioral question about their experience/projects
2. One technical discussion question about their skills  
3. One coding problem related to their project experience
4. One coding problem testing CS fundamentals

Provide your response in this JSON format:
{{
    "candidate_summary": "Brief analysis of experience level and key skills",
    "welcome_message": "Personalized welcome message referencing their background",
    "questions": [
        {{
            "id": 1,
            "type": "behavioral",
            "question": "Specific behavioral question about their background"
        }},
        {{
            "id": 2,
            "type": "technical",
            "question": "Technical discussion question about their skills"
        }},
        {{
            "id": 3,
            "type": "coding",
            "title": "Project-Related Coding Problem",
            "description": "Coding problem based on their experience",
            "template": "def solution():\\n    # Your code here\\n    pass\\n\\nprint('Test your solution')"
        }},
        {{
            "id": 4,
            "type": "coding", 
            "title": "CS Fundamentals Problem",
            "description": "Algorithm/data structure problem",
            "template": "def solution():\\n    # Your code here\\n    pass\\n\\nprint('Test your solution')"
        }}
    ]
}}

Make the questions highly relevant to their actual experience and background."""

        try:
            print("🤖 Analyzing resume with Gemini...")
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            print("✅ Gemini analysis received!")
            
            # Extract JSON from response
            try:
                # Look for JSON content
                if '{' in content and '}' in content:
                    start = content.find('{')
                    # Find the matching closing brace
                    brace_count = 0
                    end = start
                    for i, char in enumerate(content[start:], start):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i + 1
                                break
                    
                    json_content = content[start:end]
                    interview_data = json.loads(json_content)
                    print("✅ Successfully parsed Gemini JSON response!")
                    return interview_data
                else:
                    raise json.JSONDecodeError("No JSON found", content, 0)
                    
            except json.JSONDecodeError:
                print("⚠️ JSON parsing failed, using fallback")
                return self.create_fallback_interview_plan(resume_text)
                
        except Exception as e:
            print(f"❌ Gemini error: {str(e)}")
            return self.create_fallback_interview_plan(resume_text)

    def create_fallback_interview_plan(self, resume_text):
        """Fallback interview plan"""
        text_lower = resume_text.lower()
        
        if any(keyword in text_lower for keyword in ['senior', 'lead', 'architect', '5+ years']):
            level = "Senior"
        else:
            level = "Mid-level"
            
        return {
            "candidate_summary": f"{level} software engineer with technical experience",
            "welcome_message": f"Welcome! I've reviewed your background and see you're a {level.lower()} developer. Let's have a great technical interview!",
            "questions": [
                {
                    "id": 1,
                    "type": "behavioral",
                    "question": "Tell me about a challenging technical project you've worked on recently."
                },
                {
                    "id": 2,
                    "type": "technical",
                    "question": "What technologies do you feel most confident with and why?"
                },
                {
                    "id": 3,
                    "type": "coding",
                    "title": "Two Sum Problem",
                    "description": "Given an array of integers and a target sum, return the indices of two numbers that add up to the target.",
                    "template": "def two_sum(nums, target):\n    # Your solution here\n    pass\n\n# Test your function\nnums = [2, 7, 11, 15]\ntarget = 9\nresult = two_sum(nums, target)\nprint(f'Result: {result}')"
                },
                {
                    "id": 4,
                    "type": "coding",
                    "title": "Valid Parentheses",
                    "description": "Given a string containing brackets '()', '[]', '{}', determine if the brackets are valid.",
                    "template": "def is_valid(s):\n    # Your solution here\n    pass\n\n# Test your function\ntest_cases = ['()', '()[]{}', '([)]']\nfor test in test_cases:\n    result = is_valid(test)\n    print(f'is_valid(\"{test}\") = {result}')"
                }
            ]
        }

    def get_current_question(self):
        """Get current question"""
        if self.interview_state["question_count"] >= len(self.interview_state.get("questions", [])):
            return None
        return self.interview_state["questions"][self.interview_state["question_count"]]

    def advance_to_next_question(self):
        """Move to next question"""
        self.interview_state["question_count"] += 1
        return self.get_current_question()

    def get_gemini_response(self, prompt):
        """Get response from Gemini"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"I'm here to help! Let's continue with our interview."

    def analyze_code_with_gemini(self, code, analysis_type, profile_context=""):
        """Analyze code using Gemini"""
        context_prefix = f"Candidate background: {profile_context[:200]}...\n\n" if profile_context else ""
        
        prompts = {
            "hint": f"""{context_prefix}You are CodeSage, helping a candidate with their coding problem.

Current code:
{code}

Provide a helpful hint that guides them toward a better solution without giving it away. Be encouraging and specific about what to consider next.""",

            "feedback": f"""{context_prefix}You are CodeSage reviewing this code solution during a technical interview.

Code:
{code}

Provide constructive feedback covering:
1. Correctness and approach
2. Time/space complexity analysis
3. Code quality and readability  
4. Specific improvement suggestions

Be encouraging but thorough, like a senior engineer conducting a code review.""",

            "general": f"""{context_prefix}Analyze this code solution:

{code}

Provide brief, helpful feedback focusing on the approach and any key improvements."""
        }

        try:
            prompt = prompts.get(analysis_type, prompts["general"])
            return self.get_gemini_response(prompt)
        except:
            fallbacks = {
                "hint": "💡 Great start! Consider the problem step-by-step. What data structure might help optimize your approach?",
                "feedback": "🔍 Good effort! Your solution shows solid problem-solving thinking. Consider edge cases and optimization opportunities.",
                "general": "✅ Nice work! Keep thinking about efficiency and edge cases."
            }
            return fallbacks.get(analysis_type, fallbacks["general"])

    def execute_code(self, code):
        """Execute code safely"""
        if not code.strip():
            return {"success": False, "output": "No code to execute"}
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(['python', temp_file], capture_output=True, text=True, timeout=10)
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip() or "✅ Code executed successfully"}
            else:
                return {"success": False, "output": f"❌ Runtime Error:\n{result.stderr.strip()}"}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "⏱️ Execution timed out (10s limit)"}
        except Exception as e:
            return {"success": False, "output": f"💥 Execution Error: {str(e)}"}

    def analyze_complexity(self, code):
        """Real-time complexity analysis"""
        if not code.strip():
            return {"complexity": "O(1)", "details": "No code", "warning": "", "syntax": "Ready"}
        
        try:
            tree = ast.parse(code)
            loops = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While)))
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            
            complexity = "O(n²)" if loops > 1 else ("O(n)" if loops > 0 else "O(1)")
            warning = "⚠️ Consider optimization" if loops > 1 else ""
            
            return {
                "complexity": complexity,
                "details": f"Functions: {functions}, Loops: {loops}",
                "warning": warning,
                "syntax": "✅ Valid Python syntax"
            }
            
        except SyntaxError:
            return {"complexity": "N/A", "details": "❌ Syntax Error", "warning": "", "syntax": "❌ Syntax error"}

# Initialize the Gemini-powered interviewer
interviewer = GeminiCodeSageInterviewer()


@app.route('/api/ai-proctoring-violation', methods=['POST'])
def ai_proctoring_violation():
    data = request.json
    print(f"🤖 AI Proctoring violation: Multiple persons detected")
    print(f"📊 Violations: {len(data.get('violations', []))}")
    return jsonify({"status": "logged"})

@app.route('/')
def index():
    return render_template('index.html', problem=interviewer.default_problem)

@app.route('/api/analyze-resume', methods=['POST'])
def analyze_resume():
    if 'resume' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"})
    
    try:
        print(f"📄 Processing resume: {file.filename}")
        file_content = file.read()
        resume_text = interviewer.parse_resume(file_content, file.filename)
        
        if "Error" in resume_text:
            return jsonify({"success": False, "error": resume_text})
        
        print("🚀 Creating personalized interview with Gemini...")
        interview_data = interviewer.analyze_resume_with_gemini(resume_text)
        
        # Store interview plan
        interviewer.interview_state["questions"] = interview_data["questions"]
        interviewer.interview_state["question_count"] = 0
        interviewer.interview_state["candidate_profile"] = interview_data["candidate_summary"]
        
        # Get first question
        first_question = interviewer.get_current_question()
        
        # Update current question if it's coding type
        if first_question and first_question["type"] == "coding":
            interviewer.interview_state["current_question"] = {
                "id": f"q{first_question['id']}",
                "title": first_question["title"],
                "description": first_question["description"],
                "template": first_question["template"]
            }
        
        return jsonify({
            "success": True,
            "profile": interview_data["candidate_summary"],
            "summary": interview_data["candidate_summary"],
            "welcome_message": interview_data["welcome_message"],
            "first_question": first_question,
            "personalized_problem": interviewer.interview_state.get("current_question", interviewer.default_problem),
            "progress": {"current": 1, "total": len(interview_data["questions"])}
        })
        
    except Exception as e:
        print(f"❌ Resume processing error: {str(e)}")
        return jsonify({"success": False, "error": f"Processing error: {str(e)}"})

@app.route('/api/next-question', methods=['POST'])
def get_next_question():
    next_question = interviewer.advance_to_next_question()
    
    if next_question:
        # Update current question if it's coding type
        if next_question["type"] == "coding":
            interviewer.interview_state["current_question"] = {
                "id": f"q{next_question['id']}",
                "title": next_question["title"],
                "description": next_question["description"],
                "template": next_question["template"]
            }
        
        return jsonify({
            "success": True,
            "question": next_question,
            "problem": interviewer.interview_state.get("current_question"),
            "progress": {
                "current": interviewer.interview_state["question_count"], 
                "total": len(interviewer.interview_state.get("questions", []))
            }
        })
    else:
        return jsonify({
            "interview_complete": True,
            "message": "🎉 Congratulations! You've completed your technical interview. You demonstrated strong problem-solving skills and technical knowledge. Thank you for your time!"
        })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    prompt = f"""You are CodeSage, a friendly AI technical interviewer. 

Candidate's message: {message}

Context: You're conducting a technical interview. The candidate has shared their thoughts or asked a question. Respond as a supportive interviewer would - be encouraging, ask follow-ups when appropriate, and guide the conversation naturally.

Keep your response conversational and helpful."""
    
    response = interviewer.get_gemini_response(prompt)
    return jsonify({"response": response})

@app.route('/api/execute', methods=['POST'])
def execute_code():
    data = request.json
    code = data.get('code', '')
    result = interviewer.execute_code(code)
    return jsonify(result)

@app.route('/api/analyze', methods=['POST'])
def analyze_code():
    data = request.json
    code = data.get('code', '')
    analysis_type = data.get('type', 'general')
    profile = interviewer.interview_state.get("candidate_profile", "")
    
    complexity = interviewer.analyze_complexity(code)
    ai_analysis = interviewer.analyze_code_with_gemini(code, analysis_type, profile)
    
    return jsonify({"complexity": complexity, "ai_analysis": ai_analysis})
# NEW: ANTI-CHEAT ENDPOINTS
@app.route('/api/log-violation', methods=['POST'])
def log_violation():
    data = request.json
    print(f"🚨 Security violation: {data.get('type')} - {data.get('description')}")
    return jsonify({"status": "logged"})

@app.route('/api/terminate-interview', methods=['POST'])
def terminate_interview():
    data = request.json
    print(f"🚫 Interview terminated: {data.get('reason')}")
    print(f"📊 Final strikes: {data.get('strikes')}")
    return jsonify({"status": "terminated", "report_generated": True})
@app.route('/api/ai-violation', methods=['POST'])
def ai_violation():
    data = request.json
    print(f"🤖 AI VIOLATION: {data.get('count')} people detected by {data.get('model')}")
    print(f"📊 Detection timestamp: {data.get('timestamp')}")
    return jsonify({"status": "logged", "action": "interview_terminated"})

# Make sure static files are served (add if missing)
from flask import send_from_directory

@app.route('/api/ai-proctoring', methods=['POST'])
def ai_proctoring():
    data = request.json
    print(f"🤖 AI PROCTORING: {data.get('count')} people detected by {data.get('model')}")
    print(f"📊 Violation type: {data.get('type')}")
    return jsonify({"status": "logged", "action": "terminated"})


@socketio.on('code_change')
def handle_code_change(data):
    code = data.get('code', '')
    complexity = interviewer.analyze_complexity(code)
    emit('analysis_update', complexity)

@app.route('/api/voice-chat', methods=['POST'])
def voice_chat():
    data = request.json
    speech = data.get('speech', '')
    code = data.get('code', '')
    profile = data.get('profile', '')
    
    # Enhanced prompt for voice interaction
    prompt = f"""You are CodeSage conducting a LIVE VOICE technical interview. The candidate just said: "{speech}"

Current code they're working on:
{code}

Candidate background: {profile}

Respond as if you're having a natural conversation. Be encouraging, ask follow-ups, and provide guidance. Keep responses conversational and under 40 words for speech synthesis.

Guidelines:
- If they're thinking aloud about code, acknowledge their thought process
- If they ask a question, answer helpfully and concisely  
- If they seem stuck, offer a gentle hint
- Be encouraging and natural like a friendly interviewer

Response:"""
    
    try:
        response = interviewer.get_gemini_response(prompt)
        # Keep response concise for speech
        if len(response) > 200:
            response = response[:200] + "..."
        return jsonify({"response": response})
    except Exception as e:
        print(f"Voice chat error: {e}")
        return jsonify({"response": "I hear you thinking through this! That's a great approach. Tell me more about your solution."})

if __name__ == '__main__':
    print("🚀 Starting GEMINI-POWERED CodeSage...")
    print("🔗 Access at: http://localhost:5000")
    print("💎 AI Engine: Google Gemini 2.0 Flash (WORKING!)")
    print("📝 Features: Resume Analysis + Personalized Interviews")
    print("🎯 Interview Flow: Upload → Analyze → 4 Custom Questions")
    print("⚡ Response Time: Lightning fast with Gemini!")
    print("🔑  Status: ACTIVE AND WORKING PERFECTLY!")
    print("🎤 NEW: Voice Interview Feature!")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

