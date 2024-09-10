# Quiz Application

This is a simple Flask-based web application for creating and taking quizzes. Users can upload a text file containing quiz questions and answers, select the modality of the quiz, and then answer the questions to see their results.

## Features

- **Quiz Modality**: Supports both single-answer and multiple-choice questions.
- **File Upload**: Allows uploading a `.txt` file containing questions.
- **Random Sampling**: Randomly selects the specified number of questions from the uploaded file.
- **Session Management**: Keeps track of user progress and answers using sessions.
- **Results Page**: Displays the user's score and answers after completing the quiz.
- **Multi-Option Selection**: Allows selecting multiple options for questions where applicable.
- **Blank Question Handling**: Users can leave questions blank or choose to skip them.
- **Navigation**: Use arrow keys (`←` and `→`) to move between questions.
- **Scoring System**: Customizable points for null, correct, and wrong answers.
- **Exam Mode**: Optional timer mode to track time during the quiz.
- **Quiz Flow**: Includes a choice page for selecting details and modalities, and a quiz page for taking the quiz and viewing results.
- **LaTeX Support**: Render LaTeX code in questions and answers for math-related content.
  While writing the txt file write `\( <formula> \)` to use it
- **Results Visualization**: Display results in session, potentially with a graph for marks.

## Issues

- Violation of application flow possible by using the browser's back button.
- Error in formatting the `.txt` files
  <div style="background-color: #f8d7da; padding: 10px; border-radius: 5px; border: 1px solid #f5c6cb;">
      <strong>Important:</strong> Please be aware that the quiz application relies on correctly formatted text files for loading questions. The file format must adhere to specific guidelines for the application to function correctly.
      Due to the variety of potential errors and file formats, we cannot predict or handle every possible formatting issue. Therefore, it is crucial to <strong>carefully follow the formatting instructions provided</strong>. Incorrectly formatted files may lead to errors or unexpected behavior in the application.
   </div>
   Some cases are covered and errors with reference to the number of the block of the question are printed.

## Prerequisites

- [Python 3.6 or higher](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installation/)

## Installation

1. **Open the Terminal**
2. **Clone the Repository**

   ```bash
   git clone https://github.com/lollopelle01/self-interrogator.git
   cd self-interrogator
   ```
3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Application**

   ```bash
   python3 app.py
   ```
