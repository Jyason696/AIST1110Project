import pygame
import time
import random
import sys
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
'''
def get_questions(theme: str = None) -> list[dict]:
    """
    Generate questions and answers based on a specified theme

    Args:
        theme (str, optional): Theme for the questions. Defaults to None.

    Returns:
        list[dict]: A list of 3 question dictionaries, each containing:
            - question (str): The question
            - answer (list[str]): List of the 6 answers in lowercase
            - points (list[int]): Corresponding points for each answer
    """
    load_dotenv()
    AZURE_API_KEY = os.getenv("AZURE_API_KEY")

    # Initialize the client
    client = AzureOpenAI(
        azure_endpoint="https://cuhk-apip.azure-api.net",
        api_version="2024-06-01",
        api_key=AZURE_API_KEY,
    )

    theme_prompt = ""
    if theme != None:
        theme_prompt = "related to the theme " + theme

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": (
                    "Create 3 questions for playing the 'Guess Their Answer' game "
                    + theme_prompt
                    + ","
                    "each question has 10 answers with the first 6 answers being the most popular ones. "
                    "Restrict your answer to only single word only"
                    "Do not use any text formatting in your response."
                    "Use 'Question 1: ','Question 2: ','Question 3: ' to indicate each question, "
                    "then use a numbered list for the answers"
                    "Assign a total of 100 points to the first 6 answers, put them in a bracket after each answer, "
                    "do not include anything else in the brackets"
                ),
            },
        ],
        temperature=0.9,
    )
    res = response.choices[0].message.content
    res = res.split("\n")

    ret = list()
    temp = dict()  # store current question
    for line in res:
        if line.find("Question") != -1:
            temp = dict()  # start a new question
            text = line[12:]
            temp["question"] = text
        else:
            answer = ""
            points = 0
            text = line.split()
            for word in text:
                if word.isalpha():
                    if answer != "":
                        answer += " "
                    answer += word
                elif word[0] == "(":
                    points = int(word[1:-1])
            answer = answer.lower()
            if not "answer" in temp:
                temp["answer"] = list()
                temp["points"] = list()
            if len(temp["answer"]) == 5:
                temp["answer"].append(answer)
                temp["points"].append(points)
                ret.append(temp)
            elif len(temp["answer"]) < 5:
                temp["answer"].append(answer)
                temp["points"].append(points)
    return ret
'''

class Block:
    def __init__(self, x, y, width, height, bg_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = self.curr_color = bg_color

    def update_color(self, hover, new_color = (192, 192, 192)):
        if hover:
            self.curr_color = new_color
        else:
            self.curr_color = self.bg_color

    def blk_render(self, screen):
        pygame.draw.rect(screen, self.curr_color, self.rect)


class TextBlock(Block):  # Ensure TextBlock inherits from Block
    def __init__(self, x, y, width, height, text, bg_color=(160, 160, 160), fontname=None, font_size=36, txt_color=(0, 0, 0)):
        super().__init__(x, y, width, height, bg_color)  # Pass required arguments to Block's __init__
        self.font = pygame.font.Font(fontname, font_size)
        self.text = text  # Store the text
        self.txt_color = txt_color  # Store the text color
        self.rendered_text = self.font.render(text, True, txt_color)

    def update_text(self, new_text):
        self.text = new_text  # Update the stored text
        self.rendered_text = self.font.render(self.text, True, self.txt_color)

    def txt_render(self, screen, x, y):
        self.text_rect = self.rendered_text.get_rect(center=self.rect.center)  # Update text position
        screen.blit(self.rendered_text, self.text_rect)

class Button(Block):
    def __init__(self, x, y, width, height, color=(160, 160, 160)):
        super().__init__(x, y, width, height, color)
        self.activated = True

    def check_hover(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed == 1 and self.activated
    
    def state(self):
        return self.activated


class TextInputBlock(Block):
    def __init__(self, x, y, width, height, font_size=30, color=(255, 255, 255), bg_color=(0, 0, 0)):
        super().__init__(x, y, width, height, bg_color)
        self.font_size = font_size
        self.color = color
        self.font = pygame.font.Font(None, self.font_size)
        self.text = "Hi"
        self.rendered_text = self.font.render(self.text, True, self.color)
        self.active = False

    def render(self, screen, color, width=2):
        pygame.draw.rect(screen, color, self.rect, width)
        

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if the click is inside the block
            print("Mouse clicked at:", event.pos)
            print("Block rect:", self.rect)
            print("Block active state:", self.active)
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.output_text = self.text  # Set output text
                self.text = ''  # Clear input field
                return self.output_text
            else:
                self.text += event.unicode

    def render(self, screen, color, width=2):
        # Draw the block
        pygame.draw.rect(screen, color, self.rect, 2)
        # Render the text
        rendered_text = self.font.render(self.text, True, self.color)
        screen.blit(rendered_text, (self.rect.topleft[0] + 5, self.rect.topleft[1] + 5))

# Initialization
pygame.init()
clock = pygame.time.Clock()
FPS = 60  # Frame rate
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen.fill((255, 255, 255))
pygame.display.set_caption("Guess Their Answer!")
input_block = TextInputBlock(50, 50, 700, 50, font_size=48, color=(0, 0, 0), bg_color=(200, 200, 200))
show_menu = True
questions = [{'question': 'Name something you bring to a picnic  ', 'answer': ['blanket', 'food', 'drinks', 'basket', 'plates', 'napkins'], 'points': [30, 25, 20, 15, 5, 5]}, {'question': 'Name something people do when they wake up  ', 'answer': ['shower', 'brush', 'eat', 'stretch', 'check', 'yawn'], 'points': [30, 20, 15, 15, 10, 10]}, {'question': 'Name something you find in a kitchen  ', 'answer': ['stove', 'fridge', 'sink', 'oven', 'knives', 'dishes'], 'points': [30, 20, 20, 15, 10, 5]}] 
print(questions)

# Game state
current_question = 0
player_score = 0
oppo_score = 0
answer_used = [0 for i in range(6)]

# Functions
feedback_text = ""
feedback_timer = 0
feedback_duration = 60  # frames to display feedback (1 second at 60 FPS)

def draw_answer_hints():
    # Show how many answers remain (but not what they are)
    remaining = len(questions[current_question]["answer"]) - sum(answer_used[i] for i in range(6))
    hint_text = f"Answers remaining: {remaining}"
    
    hint_block = TextBlock(
        275, 142, 250, 30,
        hint_text,
        bg_color=(240, 240, 240),
        font_size=24,
        txt_color=(100, 100, 100))
    
    hint_block.blk_render(screen)
    hint_block.txt_render(screen, 275, 142)

def check_answer(player_input: str):
    global questions, current_question, player_score, answer_used, feedback_text, feedback_timer
    player_input = player_input.lower().strip()
    
    if not player_input:
        feedback_text = "Please enter an answer!"
        feedback_timer = feedback_duration
        return False
    
    if player_input in questions[current_question]["answer"]:
        index = questions[current_question]["answer"].index(player_input)
        if answer_used[index] != 1:
            player_score += questions[current_question]["points"][index]
            answer_used[index] = 1
            feedback_text = f"Correct! +{questions[current_question]['points'][index]} points"
            feedback_timer = feedback_duration
            return True
        else:
            feedback_text = "Repeated answer!"
            feedback_timer = feedback_duration
            return False
    else:
        feedback_text = "Wrong answer!"
        feedback_timer = feedback_duration
        return False

def draw_answers():
    # Draw only the answers that have been revealed
    a_text_list = questions[current_question]["answer"]
    a_points_list = questions[current_question]["points"]
    
    answer_y = 180
    for i in range(len(questions[current_question]["answer"])):
        if answer_used[i] == 1:
            answer = a_text_list[i]
            points = a_points_list[i]
            
            answer_block = TextBlock(
                100, answer_y, 600, 40,
                f"{answer.capitalize()} ({points} pts)",
                bg_color=(200, 255, 200),  # Light green background
                font_size=24,
                txt_color=(0, 100, 0))  # Dark green text
            
            answer_block.blk_render(screen)
            answer_block.txt_render(screen, 100, answer_y)
            answer_y += 45

def draw_feedback():
    global feedback_text, feedback_timer
    if feedback_timer > 0:
        # Create a temporary text block for the feedback
        feedback_block = TextBlock(
            SCREEN_WIDTH // 2 - 150, 20, 300, 40,
            feedback_text,
            bg_color=(240, 240, 240),
            font_size=32,
            txt_color=(0, 0, 0)
        )
        # Draw with different colors based on feedback type
        if "Correct" in feedback_text:
            feedback_block.txt_color = (0, 128, 0)  # Green
        elif "Wrong" in feedback_text:
            feedback_block.txt_color = (255, 0, 0)  # Red
        else:
            feedback_block.txt_color = (255, 165, 0)  # Orange
        
        feedback_block.blk_render(screen)
        feedback_block.txt_render(screen, SCREEN_WIDTH // 2 - 150, 20)
        feedback_timer -= 1

def draw_scores():
    # draw text for player and opponent scores
    player_text = f"You: {player_score}"
    oppo_text = f"Opponent: {oppo_score}"
    Progress_bar = Block(80, 600 - 80, 800 - 80 - 80, 50, (160, 160, 160))
    player_bar = Block(80, 600 - 80, (800 - 80 - 80)*player_score/100, 50, (255, 0, 0))
    opponent_bar = Block(800 - (800 - 80 - 80)*oppo_score/100 - 80, 600 - 80, (800 - 80 - 80)*oppo_score/100, 50, (0, 0, 255))
    player_sign = TextBlock(80, 600 - 80, 250, 50, player_text)
    oppo_sign = TextBlock(800 - 250 - 80, 600 - 80, 250, 50, oppo_text)
    Progress_bar.blk_render(screen)
    player_bar.blk_render(screen)
    opponent_bar.blk_render(screen)
    player_sign.txt_render(screen, 80 + 10, 600 - 80 + 10)
    oppo_sign.txt_render(screen, 800 - 250 - 80 + 10, 600 - 80 + 10)

def draw_question():
    # draw text for question and answers
    q_text = questions[current_question]["question"]
    a_text_list = questions[current_question]["answer"]

    cur_x = (800-250)//2
    cur_y = 100
    question_sign = TextBlock(cur_x, cur_y, 250, 50, q_text)
    question_sign.txt_render(screen, cur_x, cur_y)



if __name__ == "__main__":
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if not show_menu:
                player_input = input_block.handle_event(event)
                if player_input != None:
                    check_answer(player_input)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PvE_button.is_clicked(event.pos, event.button == 1):  # Left mouse button
                    print("Button clicked!")
                    PvE_button.activated = False
                    show_menu = False
                    # Start the game

        if show_menu:
            """
            button_rect = pygame.Rect((800 - 250) // 2, 600 - 80, 250, 50)
            pygame.draw.rect(screen, pygame.Color("grey"), button_rect)
            font = pygame.font.Font(None, 36)
            button_text = font.render('PvE mode', True, (0, 0, 0))
            screen.blit(button_text, (button_rect.x + 10, button_rect.y + 10))"""
            PvE_sign = TextBlock((800 - 250) // 2, 600 - 80, 250, 50, "PvE mode")
            PvE_button = Button((800 - 250) // 2, 600 - 80, 250, 50)
            PvE_sign.update_color(PvE_button.check_hover(pygame.mouse.get_pos()))
            PvE_sign.blk_render(screen)
            PvE_sign.txt_render(screen, (800 - 250) // 2 + 10, 600 - 80 + 10)
        else:
            # Game Start
            screen.fill((255, 255, 255))
            input_block.render(screen, (0, 0, 0), 2)
            draw_scores()
            draw_question()
            draw_answers()
            draw_answer_hints()
            draw_feedback()

        pygame.display.flip()

    pygame.quit()
    sys.exit()
