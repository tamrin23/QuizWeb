from flask import Flask, render_template, request, session
import json
import random

app = Flask(__name__)

app.secret_key = "quiz-secret-key"


def load_local_questions(topic):

    file_path = f"questions/{topic}.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


@app.route("/")
def home():

    return render_template("index.html")


@app.route("/start-quiz", methods=["POST"])
def start_quiz():

    topic = request.form["topic"]
    session["topic"] = topic

    number = int(request.form["number"])
    difficulty = request.form["difficulty"]
    if difficulty == "hard":
        return render_template("hard_unavailable.html")
    # Load questions for the selected topic
    questions = load_local_questions(topic)

    # Keep only questions matching the selected difficulty
    questions = [ q for q in questions if q["difficulty"] == difficulty ]

    # Make sure requested number doesn't exceed available questions
    number = min(number, len(questions))

    # Randomly select questions
    selected_questions = random.sample(questions, number)

    # Store questions for submission
    session["questions"] = selected_questions

    return render_template(
        "quiz.html",
        questions=selected_questions,
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
    app.run(host="0.0.0.0", port=5000)