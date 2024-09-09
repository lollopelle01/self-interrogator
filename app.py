from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import logging
import webbrowser
import threading
import time
import socket

import matplotlib
matplotlib.use('agg')

import matplotlib.pyplot as plt
import io
import base64
from threading import Timer
from utils import load_questions, format_time, get_remaining_time, unpac

app = Flask(__name__)
app.secret_key = 'idice'  # TODO: change it

PORT = 5000 # default

# Avoid caching
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        
        # Initialize data structures
        session["settings"] = {}
        session["values"] = {}
        
        # FILE
        question_file = request.files['file_upload']
        if not question_file or not question_file.filename.endswith('.txt'):
            flash("Invalid file type. Please upload a .txt file.", 'error')
            return redirect(url_for('index'))
        
        # SETTINGS
        session["settings"]["timer"] = int(request.form['timer'])*60 # mins -> secs
        session["settings"]["modality"] = request.form['modality']
        session["settings"]["num_questions"] = int(request.form['num_questions'])
        session["settings"]["results"] = []
        session["settings"]["scores"] = {
            "correct" : float(request.form['correct_score']),
            "blank" : float(request.form['blank_score']),
            "wrong" : float(request.form['wrong_score'])
        }

        try:
            # Load questions from the file
            session["settings"]["all_questions"] = load_questions(question_file, session["settings"]["modality"])
        except ValueError as e:
            print(e) # flashe seems as it doesn't work
            flash(str(e), 'error')
            return redirect(url_for('index'))
        
        # Check
        questions = session["settings"]["all_questions"]
        num_questions = session["settings"]["num_questions"]
        if len(questions) < num_questions :
            flash(f"You ask for {num_questions} question but in the file i count {len(questions)} question", 'error')
            return redirect(url_for('index'))
        
        return redirect(url_for('start'))
    
    return render_template('index.html')

@app.route('/start', methods=['GET', 'POST'])
def start():
    
    if request.method == 'POST':
        # VALUES
        session["values"]['questions'] = random.sample(session["settings"]['all_questions'], session["settings"]['num_questions']) 
        session["values"]['current_question'] = 1
        session["values"]['answers'] = [""]*session["settings"]["num_questions"]
        session["values"]['start_time'] = session["settings"]["timer"]
        session.modified = True
    
        return redirect(url_for('quiz'))

    # Format the timer to display
    formatted_time = format_time(session["settings"]["timer"])

    return render_template('start.html', timer=formatted_time)
    
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():

    # Read from session
    q = session["values"]['current_question']
    questions = session["values"]['questions']
    
    # Read the request
    question_num = request.args.get('question_num')
    remaining_time = request.args.get('remaining_time')
    if question_num:
        q = int(question_num)
        session["values"]["current_question"] = q
        session.modified = True
    if remaining_time :
        session["values"]['start_time'] = int(remaining_time)
        session.modified = True
    
    current_question = questions[q-1]
    
    if request.method == 'POST':
        
        # If it's not in time
        if ("expired" in request.form) and (request.form['expired']=="True") :
            # Show banner and go to result
            flash("Time's up!", 'error')
            return redirect(url_for('result'))
        else :
            # Take the time for the next quiz
            session["values"]['start_time'] = int(request.form['remaining_time'])
            
            # Take the answer 
            # TODO: forse faccio lower() anche dopo in result, vedere se inutile
            match session["settings"]["modality"]:
                case "single":
                    user_answer = request.form['answer'].strip().lower()
                case "multiple" :
                    user_answer = request.form.getlist('answer[]')
                    user_answer = [ans[0] for ans in user_answer] # extract only the first letter (a-z)
                    
            session["values"]['answers'][q-1] = user_answer
            session.modified = True
            return redirect(url_for('quiz'))
        
    # If already answered report the last answer ==> simulate a memory while moving along questions
    if session["values"]['answers'][q-1] != "" :
        match session["settings"]["modality"]:
            case "single":
                    prev_answer = session["values"]['answers'][q-1] 
            case "multiple" :
                    prev_answer = session["values"]['answers'][q-1] 
                    prev_answer = [answer for answer in current_question[1] if answer[0] in prev_answer]
    else :
        prev_answer = ""
    
    return render_template('quiz.html', question=current_question[0], 
                                        options=current_question[1], 
                                        prev_answer=prev_answer)
    
@app.route('/result', methods=['GET'])
def result():
    
    # Read from session
    total=session['settings']['num_questions'] 
    user_answers=session["values"]['answers']
    quiz_questions=session["values"]["questions"]
    scores=session["settings"]["scores"]
    
    questions, questions_points = unpac(quiz_questions, scores, user_answers)
    best_score = total * scores["correct"]
    score=sum(questions_points)

    # Update only when you completed the quiz
    referer = request.headers.get('Referer')
    if referer and '/quiz' in referer:
        session["settings"]["results"].append(score)
        session.modified = True
    
    return render_template('result.html',   score=score,
                                            total=best_score, 
                                            user_answers=user_answers,
                                            questions=questions,
                                            questions_points=questions_points,
                                            quiz_questions=quiz_questions)
 
@app.route('/results', methods=['GET'])
def results():
    # Sample data: Replace this with your session data
    scores = session["settings"]["results"]

    # Create the graph
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(1, 1, 1)
    x_values = range(1, len(scores) + 1)
    ax.plot(x_values, scores, marker='o')
    ax.set_title('Quiz Results')
    ax.set_xlabel('Attempt')
    ax.set_ylabel('Score')

    # Set x-axis to only show integer ticks
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.set_xticks(x_values)

    # Save the graph to a bytes buffer
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Convert the image to base64 string
    graph_url = base64.b64encode(img.getvalue()).decode()

    # Pass the graph to the template
    return render_template('results.html', graph_url=graph_url)

def open_browser():
    webbrowser.open_new(f"http://127.0.0.1:{PORT}")

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    PORT = sock.getsockname()[1]
    sock.close()
    Timer(1, open_browser).start()
    app.run(port=PORT)