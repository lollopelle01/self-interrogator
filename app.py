from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import logging
import webbrowser
import threading
import time
import socket
from threading import Timer

app = Flask(__name__)
app.secret_key = 'idice'  # TODO: change it

PORT = 5000

def load_questions(file, modality):
    """
    Load questions from a file based on the modality.

    :param file: A file-like object containing question data.
    :param modality: The type of quiz ('single' for single answer, 'multiple' for multiple choice).
    :return: A list of questions with options and correct answers.
    :raises ValueError: If the file content is invalid or does not match the modality.
    """
    try:
        content = file.read().decode('utf-8').strip()
    except UnicodeDecodeError:
        raise ValueError("The file could not be decoded. Please ensure it is a valid UTF-8 encoded text file.")

    lines = content.split('\n')
    
    blocks = []
    current_block = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line:
            current_block.append(stripped_line)
        else:
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
    if current_block:
        blocks.append('\n'.join(current_block))  # Append the last block if not empty

    if not blocks:
        raise ValueError("The file is empty or incorrectly formatted. Each question should be separated by two newlines.")

    questions = []
    
    for block_line_number, block in enumerate(blocks, 1):
        parts = block.strip().split('\n')
        
        if not parts or len(parts) < 2:
            raise ValueError(f"Error at block {block_line_number}: Each block must contain at least a question and an answer or options.")
        
        question = parts[0].strip()
        
        if not question:
            raise ValueError(f"Error at block {block_line_number}: A question is missing in one of the blocks.")
        
        if modality == 'single':
            if len(parts) != 2:
                raise ValueError(f"Error at block {block_line_number}: For 'single' modality, each question block should contain exactly two lines.")
            correct_answer = parts[1].strip()
            if not correct_answer:
                raise ValueError(f"Error at block {block_line_number}: The correct answer is missing or empty.")
            questions.append((question, None, correct_answer))
        
        elif modality == 'multiple':
            options = parts[1:-1]
            correct_answer_line = parts[-1].strip()
            if not correct_answer_line.startswith('Correct answer: '):
                raise ValueError(f"Error at block {block_line_number}: The last line for 'multiple' modality should start with 'Correct answer: '")
            
            correct_answer = correct_answer_line[len('Correct answer: '):].split(', ')
            
            if not all(option.strip() for option in options):
                raise ValueError(f"Error at block {block_line_number}: One or more options are empty.")
            
            if not correct_answer:
                raise ValueError(f"Error at block {block_line_number}: Correct answers are missing or empty.")
            
            # Ensure that each correct answer is among the options
            if not all(ans[0] in [o[0] for o in options] for ans in correct_answer):
                raise ValueError(f"Error at block {block_line_number}: One or more correct answers are not among the provided options.")
            
            questions.append((question, options, correct_answer))
        
        else:
            raise ValueError(f"Error at block {block_line_number}: Invalid modality. Must be 'single' or 'multiple'.")

    return questions


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session["modality"] = request.form['modality']
        question_file = request.files['file_upload']
        num_questions = int(request.form['num_questions'])
        
        # Ensure the file is of the correct type
        if not question_file or not question_file.filename.endswith('.txt'):
            flash("Invalid file type. Please upload a .txt file.", 'error')
            return redirect(url_for('index'))
        
        try:
            # Load questions from the file
            questions = load_questions(question_file, session["modality"])
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('index'))
        
        # Randomly sample the required number of questions
        session['num_questions'] = num_questions
        session['questions'] = random.sample(questions, num_questions)
        session['current_question'] = 0
        session['correct_answers'] = 0
        session['user_answers'] = []
        return redirect(url_for('quiz'))
    
    return render_template('index.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    
    if session['current_question'] >= session['num_questions']:
        return redirect(url_for('results'))
    
    current_question = session['questions'][session['current_question']]

    if request.method == 'POST':
        user_answer = request.form['answer'].strip().lower()
        if type(current_question[2])==list :
            correct_answer = current_question[2][0].strip().lower()
        else :
            correct_answer = current_question[2].strip().lower()

        if session["modality"] == "multiple" : user_answer = user_answer[0]
        
        if user_answer == correct_answer:
            session['correct_answers'] += 1

        session['user_answers'].append({
            'question': current_question[0],
            'correct_answer': correct_answer,
            'user_answer': user_answer,
            'options': current_question[1]
        })

        session['current_question'] += 1
        return redirect(url_for('quiz'))

    return render_template('quiz.html', question=current_question[0], options=current_question[1])
    
@app.route('/results', methods=['GET'])
def results():
    return render_template('results.html', score=session['correct_answers'], total=session['num_questions'], user_answers=session['user_answers'])
 
@app.route('/debug')
def debug():
    # DEBUG only
    return f"""
        <h1>Session Data</h1>
        <pre>{session}</pre>
    """

def open_browser():
    webbrowser.open_new(f"http://127.0.0.1:{PORT}")

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    PORT = sock.getsockname()[1]
    sock.close()
    Timer(1, open_browser).start()
    app.run(port=PORT)