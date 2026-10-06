from flask import Flask, render_template, request, session
from google import genai
from dotenv import load_dotenv
import json 
import time

load_dotenv()
client = genai.Client()
app = Flask(__name__)

app.secret_key ="quiz-secret-key"

def load_local_questions(topic):

    file_path = f"questions/{topic}.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
    
@app.route("/start-local-quiz", methods=["POST"])
def start_local_quiz():
    
    topic = request.form["topic"]
    session["topic"] = topic
    number = int(request.form["number"])
    difficulty = request.form["difficulty"]
    if difficulty == "hard":
        return render_template("hard_unavailable.html")
    questions = load_local_questions(topic)

    # Keep only questions matching the selected difficulty
    questions = [
        q for q in questions
        if q["difficulty"] == difficulty
    ]

    # Make sure we don't request more questions than available
    number = min(number, len(questions))

    # Randomly select questions
    import random
    selected_questions = random.sample(questions, number)

    session["questions"] = selected_questions

    return render_template(
        "quiz.html",
        questions=selected_questions,
        topic=topic,
    )
    
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start-quiz", methods=["POST"])
def start_quiz():
    
    topic = request.form["topic"]
    session["topic"] = topic
    number = int(request.form["number"])
    difficulty = request.form["difficulty"]

    prompt = f"""
    Create {number} multiple-choice English quiz questions.

    Topic: {topic}
    Difficulty: {difficulty}

    Requirements:
    - Each question must have exactly 4 options.
    - Each question must have exactly one correct answer.
    - Provide a short explanation for the correct answer.
    - Return only valid JSON.
    - Return a JSON array.
    
    Each question must have this structure:
    {{
        "question": "...",
        "options": ["...", "...", "...", "..."],
        "correct_answer": "...",
        "explanation": "..."
    }}
    """
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )
            break
        except Exception as e:
            print("Gemini error:", e)
            error_message = str(e)
            # API quota exceeded
            if "429" in error_message:
                return render_template(
                    "api_limit.html",
                    topic=topic,
                    number=number,
                    difficulty=difficulty
                )

            # Temporary server problem
            if "503" in error_message:

                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue

                return "Gemini is temporarily unavailable. Please try again."

            # Any other error
            return f"Gemini error: {error_message}"

    questions = json.loads(response.text)
    session["questions"] = questions
    return render_template(
        "quiz.html",
        questions=questions,
        topic=topic
    )
@app.route("/submit-quiz", methods=["POST"])
def submit_quiz():
    topic = session["topic"] 
    questions = session["questions"]
    answers = request.form

    score = 0
    results = []

    for i, question in enumerate(questions, start=1):

        user_answer = answers.get(f"q{i}")
        correct_answer = question["correct_answer"]

        is_correct = user_answer == correct_answer

        if is_correct:
            score += 1

        results.append({
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

    return render_template(
        "quiz.html",
        questions=questions,
        answers=answers,
        results=results,
        score=score,
        topic=topic,
        submitted=True
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)