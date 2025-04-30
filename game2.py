import pygame
import time
import random
import sys
import os
from dotenv import load_dotenv
from openai import AzureOpenAI


def get_questions(theme: str = None) -> tuple[ list[dict], list[list[str]] ]:
    """
    Generate questions and answers based on a specified theme(optional)

    Arg: theme, Theme for the questions. Defaults to None.

    Returns tuple of two elements:

        list[dict]: A list of 3 question dictionaries, each containing:
            - question (str): The question
            - answer (list[str]): List of the 6 answers in lowercase
            - points (list[int]): Corresponding points for each answer

        list[list[str]]: 3 lists of strings, they are the list of guesses used by the AI opponent
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
                    "Restrict your question to at most 60 characters long. "
                    "Do not use any text formatting in your response, "
                    "In the answers, do not include any numbers or symbols. "
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
    ret2 = list()
    temp = dict()  # Store current question
    oppo_list = list()  # Store all answers of current question
    for line in res:
        if line.find("Question") != -1:
            if len(oppo_list)>0:
                ret2.append(oppo_list)
            oppo_list = list()
            temp = dict()  # start a new question
            text = line[12:]
            temp["question"] = text
        else:
            line = line.strip()
            if len(line) < 1:  # empty line
                continue
            answer = ""
            points = 0
            text = line.split()
            for word in text:
                if word.isalpha():
                    answer += word  # note that there are no spaces between words
                elif word[0] == "(":
                    points = int(word[1:-1])
            answer = answer.lower()  # convert to lowercase
            
            if not "answer" in temp:
                temp["answer"] = list()
                temp["points"] = list()

            if len(temp["answer"]) == 6: # handle oppo_list, keep original case and spaces
                oppo_list.append(line[line.find(" ")+1:])
            else:
                oppo_list.append(line[line.find(" ")+1:line.rfind(" ")])
            
            if len(temp["answer"]) == 5:
                temp["answer"].append(answer)
                temp["points"].append(points)
                ret.append(temp)
            elif len(temp["answer"]) < 5:
                temp["answer"].append(answer)
                temp["points"].append(points)

    ret2.append(oppo_list)
    return (ret, ret2)


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
        self.activated = True  # activated when declared

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
        self.text = ""
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

class ImageSprite( pygame.sprite.Sprite ):              
    """Sprite class that supports image update and displaying textbox"""
    def __init__( self, x, y, img ):     
        pygame.sprite.Sprite.__init__(self)      
        self.image = img
        self.rect  = self.image.get_rect()
        self.rect.center = ( x, y )
        self.textbox = None     
        self.text_duration = 0   # Time left until textbox disappear (in miliseconds)
        self.text_offset = 15   # Space between sprite and textbox

    def talk( self, text, duration = 120, dir_right=True, bg_color = (160, 160, 160), txt_color = (0, 0, 0)):
        """
        """
        test_font = pygame.font.Font(None, 28)
        text_width, text_height = test_font.size(text)
        text_width += 50
        text_height += 30
        
        if dir_right:
            x_pos = self.rect.right + self.text_offset
        else:
            x_pos = self.rect.left - text_width - self.text_offset
            
        y_pos = self.rect.top + text_height//2
        
        self.textbox = TextBlock(
            x=x_pos,
            y=y_pos,
            width=text_width,
            height=text_height,
            text=text,
            bg_color=bg_color,
            txt_color=txt_color
        )
        self.text_duration = duration
        self.text_dir_right = dir_right

    def update( self, screen, img=None ):   
        if img != None:
            self.image = img
        screen.blit(self.image, self.rect)
        if self.textbox and self.text_duration > 0:
            self.textbox.blk_render(screen)
            self.textbox.txt_render(screen, self.textbox.rect.centerx, self.textbox.rect.centery)
            self.text_duration -= 1
            if self.text_duration <= 0:
                self.textbox = None

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
show_scoreboard = False

# Game state
questions = dict()
oppo_answers = list()
current_question = -1  # Game not yet started

player_score = 0
oppo_score = 0
answer_used = [0 for i in range(6)]  # Which answers in currect question is used already

feedback_text = ""
feedback_timer = 0
feedback_duration = 60

player_hist = list() #  list of scores in previous rounds
oppo_hist = list()
QUESTION_TIME_LIMIT = 20  # seconds for each question
question_start_time = 0
QUESTIONS_TOTAL = 3
OPPO_TIME_LIMIT = 3

# Declare buttons
PvE_sign = TextBlock((800 - 250) // 2, 600 - 80, 250, 50, "PvE mode")
PvE_button = Button((800 - 250) // 2, 600 - 80, 250, 50)
to_menu_sign = TextBlock((800 - 250) // 2, 500, 250, 50, "Return to Menu")
to_menu_button = Button((800 - 250) // 2 // 2, 500, 250, 50)
to_menu_button.activated = False

# Declare sprites
player_image   = pygame.image.load( 'testsprite.png' ).convert()
player_sprite = ImageSprite(100, 400, player_image)
oppo_image   = pygame.image.load( 'testsprite.png' ).convert()
oppo_sprite = ImageSprite(700, 400, oppo_image)

# Declare colors
LIGHT_BLUE = (50, 160, 250)
BLUE = (10, 10, 250)
LIGHT_RED = (255, 125, 125)
RED = (250, 10, 10)

# Functions
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

def longest_common_substring(s1: str, s2: str) -> str:
    """Find the longest common substring between two strings"""
    # Create a matrix to store lengths of longest common suffixes
    m = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
    longest = 0
    end_pos = 0
    
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i-1].lower() == s2[j-1].lower():
                m[i][j] = m[i-1][j-1] + 1
                if m[i][j] > longest:
                    longest = m[i][j]
                    end_pos = i
            else:
                m[i][j] = 0
                
    return s1[end_pos-longest:end_pos] if longest > 0 else ""

def check_answer(player_input: str):
    global questions, current_question, player_score, answer_used, feedback_text, feedback_timer
    player_input = player_input.lower().replace(" ", "")    
    if not player_input:
        feedback_text = "Please enter an answer!"
        return False
    
    max_score = -1
    for i in range(len(questions[current_question]["answer"])):
        substring = longest_common_substring(player_input, questions[current_question]["answer"][i])
        score = len(substring)/len(questions[current_question]["answer"][i])
        if score > max_score:
            max_score = score
            index = i  # Store the index of the best match

    if max_score >= 0.8:
        if answer_used[index] != 1:
            player_score += questions[current_question]["points"][index]
            answer_used[index] = 1
            feedback_text = f"Correct! +{questions[current_question]['points'][index]} points"
            return True
        else:
            feedback_text = "Repeated answer!"
            return False
    else:
        feedback_text = "Wrong answer!"
        return False


def draw_answers():
    global oppo_answers, current_question
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
                oppo_answers[current_question][i] + f" ({points} pts)",
                bg_color=(200, 255, 200),  # Light green background
                font_size=24,
                txt_color=(0, 100, 0))  # Dark green text
            
            answer_block.blk_render(screen)
            answer_block.txt_render(screen, 100, answer_y)
            answer_y += 45

def draw_feedback():
    global feedback_text, feedback_timer, user_input
    if feedback_timer > 0:
        # Create a temporary text block for the feedback
        feedback_block = TextBlock(
            SCREEN_WIDTH // 2 - 150, 20, 300, 40,
            feedback_text,
            bg_color=(240, 240, 240),
            font_size=32,
            txt_color=(0, 0, 0)
        )
        answer_block = TextBlock(
            80, 450, 100, 30,
            f"Your answer: {user_input}",
            bg_color=(240, 240, 240),
            font_size=32,
            txt_color=(0, 0, 0)
        )
        answer_block.blk_render(screen)
        answer_block.txt_render(screen, 80, 450)

        # Draw with different colors based on feedback type
        if "Correct" in feedback_text:
            feedback_block.txt_color = (0, 128, 0)  # Green
        elif "Wrong" in feedback_text:
            feedback_block.txt_color = (255, 0, 0)  # Red
        else:
            feedback_block.txt_color = (255, 165, 0)  # Orange
        
        feedback_block.blk_render(screen)
        feedback_block.txt_render(screen, SCREEN_WIDTH // 2 - 150, 20)
        feedback_timer -= 1  # Decrease the timer

    
    if feedback_timer > 0:
        # Create a temporary text block for the feedback
        feedback_block = TextBlock(
            SCREEN_WIDTH // 2 - 150, 20, 300, 40,
            feedback_text,
            bg_color=(240, 240, 240),
            font_size=32,
            txt_color=(0, 0, 0)
        )
        
        feedback_block.blk_render(screen)
        feedback_block.txt_render(screen, SCREEN_WIDTH // 2 - 150, 20)
        feedback_timer -= 1  # Decrease the timer

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
    # draw text for question and used answers
    q_text = questions[current_question]["question"]
    a_text_list = questions[current_question]["answer"]

    cur_x = (800-250)//2
    cur_y = 100
    question_sign = TextBlock(cur_x, cur_y, 250, 50, q_text)
    question_sign.txt_render(screen, cur_x, cur_y)

def draw_timer():
    global current_question, question_start_time
    current_time = pygame.time.get_ticks()
    elapsed_seconds = (current_time - question_start_time) // 1000  
    time_left = QUESTION_TIME_LIMIT - elapsed_seconds
    time_sign = TextBlock((SCREEN_WIDTH-250)//2, SCREEN_HEIGHT - 160, 250, 50, f"Time left: {time_left}")
    time_sign.txt_render(screen, (SCREEN_WIDTH-250)//2, SCREEN_HEIGHT - 160)

def start_new_question():
    global current_question, question_start_time, player_score, oppo_score, player_hist, oppo_hist
    global answer_used, show_scoreboard, input_block
    
    # Reset question-related states
    question_start_time = pygame.time.get_ticks()  # Record start time in milliseconds
    if current_question>=0:
        player_hist.append(player_score)
        oppo_hist.append(oppo_score)
    player_score = 0
    oppo_score = 0
    answer_used = [0 for i in range(6)]
    current_question += 1
    input_block.text = ""
    if current_question >= QUESTIONS_TOTAL: # last question ended, proceed to scoreboard
        show_scoreboard = True

def check_timer():
    current_time = pygame.time.get_ticks()
    elapsed_seconds = (current_time - question_start_time) // 1000  # Get time elapsed since question started
    if elapsed_seconds >= QUESTION_TIME_LIMIT:
        start_new_question()

def render_menu():
    global PvE_sign, PvE_button
    """
    button_rect = pygame.Rect((800 - 250) // 2, 600 - 80, 250, 50)
    pygame.draw.rect(screen, pygame.Color("grey"), button_rect)
    font = pygame.font.Font(None, 36)
    button_text = font.render('PvE mode', True, (0, 0, 0))
    screen.blit(button_text, (button_rect.x + 10, button_rect.y + 10))
    """
    screen.fill((255, 255, 255))
    PvE_button.activated = True
    PvE_sign.update_color(PvE_button.check_hover(pygame.mouse.get_pos()))
    PvE_sign.blk_render(screen)
    PvE_sign.txt_render(screen, (800 - 250) // 2 + 10, 600 - 80 + 10)

def render_game():
    screen.fill((255, 255, 255))
    input_block.render(screen, (0, 0, 0), 2)
    draw_scores()
    draw_question()
    draw_timer()
    draw_answers()
    draw_answer_hints()
    draw_feedback()

def render_scoreboard():
    global player_hist, oppo_hist, QUESTIONS_TOTAL
    global show_menu, show_scoreboard
    global to_menu_sign, to_menu_button

    def draw_text(text: str, x, y):
        temp = TextBlock(x, y, 250, 50, text)
        temp.txt_render(screen, x, y)

    screen.fill((255, 255, 255))
    str_list = ["Question 1","Question 2","Question 3","Total"]
    y_list = [100, 200, 300, 400]
    x_left = (800-250) // 4
    x_mid = (800-250) // 4 * 2
    x_right = (800-250) // 4 * 3
    for i in range(QUESTIONS_TOTAL+1):
        if i==QUESTIONS_TOTAL: # show total score
            draw_text(str(sum(player_hist)), x_left, y_list[i])
            draw_text(str_list[i], x_mid, y_list[i])
            draw_text(str(sum(oppo_hist)), x_right, y_list[i])
        else:
            draw_text(str(player_hist[i]), x_left, y_list[i])
            draw_text(str_list[i], x_mid, y_list[i])
            draw_text(str(oppo_hist[i]), x_right, y_list[i])
    to_menu_button.activated = True
    to_menu_sign.update_color(to_menu_button.check_hover(pygame.mouse.get_pos()))
    to_menu_sign.blk_render(screen)
    to_menu_sign.txt_render(screen, (800 - 250) // 2 + 10, 600 - 80 + 10)

def render_sprites():
    global screen, player_sprite, oppo_sprite
    player_sprite.update(screen)
    oppo_sprite.update(screen)
    
def reset_game():
    global questions, current_question, player_hist, oppo_hist, oppo_answers
    screen.fill((0,0,0))
    temp = TextBlock((800-250)//2, (600-50)//2, 250, 50, "Game Loading... Please wait", txt_color=(255,255,255))
    temp.txt_render(screen, (800-250)//2, (600-50)//2) # loading screen not working?
    pygame.display.flip()
    (questions, oppo_answers) = get_questions()
    print(questions)
    print(oppo_answers)
    current_question = -1  
    player_hist = list() 
    oppo_hist = list()

if __name__ == "__main__":
    running = True
    reset_game()
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if not show_menu and not show_scoreboard:  # during game
                player_input = input_block.handle_event(event)
                if player_input != None:
                    user_input = player_input  # Get the input text
                    check_answer(player_input)
                    feedback_timer = feedback_duration
                    player_sprite.talk(player_input, bg_color=LIGHT_BLUE, txt_color=BLUE)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PvE_button.is_clicked(event.pos, event.button == 1):  # Left mouse button
                    PvE_button.activated = False
                    show_menu = False
                    show_scoreboard = False
                    start_new_question()
                if to_menu_button.is_clicked(event.pos, event.button == 1): 
                    to_menu_button.activated = False
                    show_scoreboard = False
                    show_menu = True
                    reset_game()
        
        check_timer()

        if show_menu:
            render_menu()
        elif show_scoreboard:
            render_scoreboard()
        else:
            render_game()
        render_sprites()

        pygame.display.flip()

    pygame.quit()
    sys.exit()