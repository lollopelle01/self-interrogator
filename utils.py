# TODO: filter only necessary imports
from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import logging
import webbrowser
import threading
import time
import socket
from threading import Timer

def load_questions(file, modality):
    # TODO: add extraction for multiple questions with multiple answers
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
            options = [opt.strip() for opt in parts[1:-1]]  # Pulisci e rimuovi spazi bianchi dalle opzioni
            correct_answer_line = parts[-1].strip()

            if not correct_answer_line.startswith('Correct answer: '):
                raise ValueError(f"Error at block {block_line_number}: The last line for 'multiple' modality should start with 'Correct answers: '")
        
            correct_answers = correct_answer_line[len('Correct answer: '):].split(', ')  # Split delle risposte corrette

            if not all(option for option in options):  # Verifica che nessuna opzione sia vuota
                raise ValueError(f"Error at block {block_line_number}: One or more options are empty.")
            
            if not correct_answers:  # Verifica che ci siano risposte corrette
                raise ValueError(f"Error at block {block_line_number}: Correct answers are missing or empty.")
            
            # Assicurati che ogni risposta corretta sia tra le opzioni fornite
            valid_options = [opt[0] for opt in options]  # Estrai i caratteri delle opzioni (a, b, c, ...)
            if not all(ans in valid_options for ans in correct_answers):  
                raise ValueError(f"Error at block {block_line_number}: One or more correct answers are not among the provided options.")
            
            questions.append((question, options, correct_answers))

        else:
            raise ValueError(f"Error at block {block_line_number}: Invalid modality. Must be 'single' or 'multiple'.")

    return questions

def format_time(seconds_remaining):
    """Format the remaining time in Hh Mm Ss."""
    hours = seconds_remaining // 3600
    minutes = (seconds_remaining % 3600) // 60
    seconds = seconds_remaining % 60
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def get_remaining_time(start_time, duration_secs):
    """Calculate the remaining time from the start time and duration."""
    elapsed_time = (time.time() - start_time)
    remaining_time = duration_secs - elapsed_time
    return max(remaining_time, 0)  # Ensure remaining time is not negative

def to_lower_case(val):
    if isinstance(val, list):
        return [v.lower() for v in val]
    elif isinstance(val, str):
        return val.lower()
    return val

def compute_points(options, user_answer, solution_answer, T, F, N):
    question_points = 0
    # Caso in cui la risposta è vuota o non fornita
    if user_answer is None or user_answer == "" or user_answer == []:
        question_points += N
    
    # Caso in cui ci sono delle opzioni multiple (risposte come liste)
    elif options and isinstance(user_answer, list) and isinstance(solution_answer, list):
        
        # Distribute points
        T = T/len(solution_answer)
        F = F/(len(options)-len(solution_answer))
                
        correct_answers = set(solution_answer)  # Set di risposte corrette
        user_answers = set(user_answer)         # Set di risposte fornite dall'utente
        
        # Risposte corrette date dall'utente
        correct_given = user_answers.intersection(correct_answers)
        wrong_given = user_answers - correct_answers  # Risposte sbagliate date dall'utente
        blank_given = correct_answers - user_answers  # Risposte corrette non date dall'utente (considerate vuote)
        
        # print(f"correct_given = {correct_given}")
        # print(f"wrong_given = {wrong_given}")
        # print(f"blank_given = {blank_given}")
        
        # Assegna punti per ogni risposta corretta
        question_points += len(correct_given) * T
        
        # Assegna punti negativi per le risposte sbagliate
        question_points += len(wrong_given) * F
        
        # Assegna punti neutri per le risposte lasciate in bianco (non fornite dall'utente)
        question_points += len(blank_given) * F
        
        # print(f"points for correct = {len(correct_given) * T}")
        # print(f"points for wrong = {len(wrong_given) * F}")
        # print(f"points for blank = {len(blank_given) * F}")
    
    # Caso in cui non ci sono opzioni (domande a risposta aperta)
    else:
        if user_answer == solution_answer:
            question_points += T  # Risposta corretta
        else:
            question_points += F  # Risposta sbagliata
    
    # Round the result
    question_points = round(question_points, 2)
    
    return question_points

def unpac(quiz_questions, scores, user_answers):
    # all_questions = list of tuple (question, [options]/None, real_answer)
    # scores = {"correct": x.xx, "blank": x.xx, "wrong": x.xx}
    # user_answers = list of answers provided by the user
    
    N, T, F = scores.values()  # Punteggi per corretto, vuoto e sbagliato
    # print(scores)
    # print(T, N, F)
    
    questions_points = []  # Lista per memorizzare i punti per ogni domanda
    questions = []  # Lista per memorizzare le domande
    
    for i, question in enumerate(quiz_questions):
        # print("\n"*3)
        # print(f"### Question {i+1} " + "#"*30)
        
        q_text, options, real_answer = question
        questions.append(q_text)  # Aggiunge la domanda
        
        user_answer = user_answers[i] if i < len(user_answers) else None  # Risposta dell'utente
        user_answer = to_lower_case(user_answer)
        real_answer = to_lower_case(real_answer)
        
        question_points = compute_points(options, user_answer, real_answer, T, F, N)
        questions_points.append(question_points)
        
        # DEBUG
        # print(question)
        # print(user_answer)
        # print(real_answer)
        # print(questions_points[i])
        # print("\n"*3)

    return questions, questions_points
