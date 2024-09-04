# Quiz Application

This is a simple Flask-based web application for creating and taking quizzes. Users can upload a text file containing quiz questions and answers, select the modality of the quiz, and then answer the questions to see their results.

## Features

- **Quiz Modality**: Supports both single-answer and multiple-choice questions.
- **File Upload**: Allows uploading a `.txt` file containing questions.
- **Random Sampling**: Randomly selects the specified number of questions from the uploaded file.
- **Session Management**: Keeps track of user progress and answers using sessions.
- **Results Page**: Displays the user's score and answers after completing the quiz.

## Prerequisites

- Python 3.6 or higher
- Flask

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/lollopelle01/self-interrogator.git
   cd self-interrogator
   ```
2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Application**

```bash
python3 app.py
```
