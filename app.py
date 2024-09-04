from flask import Flask, render_template, request, redirect, url_for, session
import random
import logging
# from flask_debugtoolbar import DebugToolbarExtension


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # TODO: change it

def load_questions(file, modality):
    """
    Load questions from a file based on the modality.
    
    :param file: A file-like object containing question data.
    :param modality: The type of quiz ('single' for single answer, 'multiple' for multiple choice).
    :return: A list of questions with options and correct answers.
    """
    # Read the file content
    content = file.read().decode('utf-8').strip()
    blocks = content.split('\n\n')
    
    questions = []
    
    for block in blocks:
        parts = block.split('\n')
        question = parts[0]
        
        if modality == 'single':
            correct_answer = parts[1]
            questions.append((question, None, correct_answer))
        
        elif modality == 'multiple':
            options = parts[1:-1]
            correct_answers = parts[-1].split(': ')[1].split(', ')
            questions.append((question, options, correct_answers))
        
        else:
            raise ValueError("Invalid modality. Must be 'single' or 'multiple'.")
    
    return questions


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        modality = request.form['modality']
        question_file = request.files['file_upload']
        num_questions = int(request.form['num_questions'])
        
        # Ensure the file is of the correct type
        if not question_file or not question_file.filename.endswith('.txt'):
            return "Invalid file type. Please upload a .txt file.", 400
        
        # Load questions from the file
        questions = load_questions(question_file, modality)
        
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
        correct_answer = current_question[2].strip().lower()

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
    # Print or return the session data for debugging
    return f"""
        <h1>Session Data</h1>
        <pre>{session}</pre>
    """

if __name__ == '__main__':
    app.run(debug=True)