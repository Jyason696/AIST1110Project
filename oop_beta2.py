import pygame
import time
import random
import sys
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

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
    def __init__(self, x, y, width, height, font_size=30, color=(0, 0, 0), bg_color=(200, 200, 200)):
        super().__init__(x, y, width, height, bg_color)
        self.font_size = font_size
        self.color = color
        self.font = pygame.font.Font(None, self.font_size)
        self.text = ""
        self.active = False
        self.output_text = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle active state if clicked inside the input box
            self.active = self.rect.collidepoint(event.pos)
        
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.output_text = self.text
                self.text = ""
                return self.output_text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
        return None

    def render(self, screen, color=(0, 0, 0), width=2):
        # Draw the background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        # Draw the border
        border_color = (100, 100, 255) if self.active else color
        pygame.draw.rect(screen, border_color, self.rect, width)
        # Render the text
        rendered_text = self.font.render(self.text, True, self.color)
        screen.blit(rendered_text, (self.rect.x + 5, self.rect.y + 5))

class ImageSprite:              
    """Sprite class that supports image update and displaying speech bubble"""
    def __init__( self, x, y, img ):     
        pygame.sprite.Sprite.__init__(self)      
        self.image = img
        self.rect  = self.image.get_rect()
        self.rect.center = ( x, y )
        self.textbox = None     
        self.text_duration = 0   # Time left until speech bubble disappear (in miliseconds)
        self.text_offset = 15   # Space between sprite and speech bubble

    def talk( self, text, duration = 120, dir_right=True, bg_color = (160, 160, 160), txt_color = (0, 0, 0)):
        """
        Display a speech bubble near the sprite

        text: The text to display
        duration: How many frames to show the text 
        dir_right: True indicates the speech bubble is displayed on the right hand side of the sprite, False indicates left hand side
        txt_color: RGB color of the text
        bg_color: RGB color of the text box background
        """
        test_font = pygame.font.Font(None, 28)
        text_width, text_height = test_font.size(text)
        text_width += 50
        text_height += 30   # Padding of speech bubble
        
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

class QuestionGenerator:
    @staticmethod
    def get_questions(theme: str = None) -> tuple[list[dict], list[list[str]] ]:
        """
        Generate questions and answers based on a specified theme

        Args:
            theme (str, optional): Theme for the questions. Defaults to None.

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
                        "Restrict each answer to at most 2 words"
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
                for i in range(1,len(text)):
                    word = text[i]
                    if(word[0]=='('):
                        points = int(word[1:-1])
                    else:
                        answer += word  # note that there are no spaces between words
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

class Bot:
    def __init__(self, oppo_answers, oppo_sprite):
        self.oppo_answers = oppo_answers
        self.oppo_sprite = oppo_sprite
        self.current_question = -1
        self.answer_timer = 0
        self.answer_delay = 0
        self.answers_used = []
        self.timer = 0
    
    def start_question(self, question_index):
        """Reset bot state for new question"""
        self.current_question = question_index
        self.answers_used = []
        self.answer_timer = 0
        self.answer_delay = random.randint(8, 15) * 1000  # Convert to milliseconds
        self.last_answer_time = pygame.time.get_ticks()
    
    def update(self, current_time):
        """Check if bot should answer now and return answer if ready"""
        if self.current_question == -1 or len(self.answers_used) >= len(self.oppo_answers[self.current_question]):
            return None
        
        # Check if delay time has passed
        if current_time - self.last_answer_time > self.answer_delay:
            # Get random unused answer
            available_answers = [
                i for i in range(len(self.oppo_answers[self.current_question])) 
                if i not in self.answers_used
            ]
            
            if available_answers:
                chosen_index = random.choice(available_answers)
                self.answers_used.append(chosen_index) # Mark answer as used
                self.last_answer_time = current_time # Reset last answer time
                self.answer_delay = random.randint(8, 15) * 1000 # Reset delay
                return chosen_index
        
        return None
    
    def draw_output(self, screen, output):
        if self.timer > 0 or output is not None:
            self.timer = 60
            if output is not None:
                self.last_output = self.oppo_answers[self.current_question][output]
            answer_block = TextBlock(
                800 - 180, 450, 100, 30,
                f"Opponent: {self.last_output}",
                bg_color=(240, 240, 240),
                font_size=25,
                txt_color=(0, 0, 0)
            )
            answer_block.blk_render(screen)
            answer_block.txt_render(screen, 80, 450)
        self.timer -= 1

class GameUI:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.SCREEN_WIDTH = 800
        self.SCREEN_HEIGHT = 600
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Guess Their Answer!")
        
        # UI Elements
        self.input_block = TextInputBlock(50, 50, 700, 50, font_size=48)
        self.PvE_button = Button((self.SCREEN_WIDTH - 250) // 2, self.SCREEN_HEIGHT - 80, 250, 50)
        self.PvE_sign = TextBlock((self.SCREEN_WIDTH - 250) // 2, self.SCREEN_HEIGHT - 80, 250, 50, "PvE mode")
        self.to_menu_button = Button((self.SCREEN_WIDTH - 250) // 4, 500, 250, 50)
        self.to_menu_sign = TextBlock((self.SCREEN_WIDTH - 250) // 2, 500, 250, 50, "Return to Menu")

        player_image   = pygame.image.load( 'testsprite.png' ).convert_alpha()
        self.player_sprite = ImageSprite(100, 400, player_image)
        oppo_image   = pygame.image.load( 'testsprite.png' ).convert_alpha()
        self.oppo_sprite = ImageSprite(700, 400, oppo_image)

        # Game state
        self.reset_game()


    def reset_game(self):
        """Reset all game state variables"""
        self.screen.fill((0, 0, 0))
        loading_text = TextBlock(
            (self.SCREEN_WIDTH-250)//2, (self.SCREEN_HEIGHT-50)//2, 
            250, 50, 
            "Game Loading... Please wait", 
            txt_color=(255, 255, 255)
        )
        loading_text.txt_render(self.screen, (self.SCREEN_WIDTH-250)//2, (self.SCREEN_HEIGHT-50)//2)
        pygame.display.flip()
        
        self.questions, self.oppo_answers = QuestionGenerator.get_questions()
        print(self.questions)
        print(self.oppo_answers)
        self.current_question = -1
        self.player_score = 0
        self.oppo_score = 0
        self.answer_used = [0] * 6
        self.player_hist = []
        self.oppo_hist = []
        self.feedback_text = ""
        self.feedback_timer = 0
        self.show_menu = True
        self.show_scoreboard = False
        self.question_start_time = 0
        self.user_input = ""
        self.bot = Bot(self.oppo_answers, self.oppo_sprite)


    def run(self):
        """Main game loop"""
        running = True
        while running:
            self.clock.tick(self.FPS)
            running = self.handle_events()
            self.update()
            self.render()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def handle_events(self) -> bool:
        """Handle all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle input block events
            if not self.show_menu and not self.show_scoreboard:
                result = self.input_block.handle_event(event)
                if result is not None:
                    self.user_input = result
                    self.check_answer(result)
                    self.feedback_timer = 60
                    self.player_sprite.talk(result, bg_color=(255, 125, 125), txt_color=(250, 10, 10)) # pink, red
            
            # Handle button clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.show_menu and self.PvE_button.is_clicked(event.pos, True):
                    self.start_game()
                elif self.show_scoreboard and self.to_menu_button.is_clicked(event.pos, True):
                    self.return_to_menu()
        
        return True

    def start_game(self):
        """Start a new game"""
        self.PvE_button.activated = False
        self.show_menu = False
        self.show_scoreboard = False
        self.start_new_question()

    def return_to_menu(self):
        """Return to main menu"""
        self.to_menu_button.activated = False
        self.show_scoreboard = False
        self.show_menu = True
        self.reset_game()

    def update(self):
        """Update game state"""
        if not self.show_menu and not self.show_scoreboard:
            self.check_timer()
            
    def check_bot_answer(self):        # Let bot answer
        current_time = pygame.time.get_ticks()
        bot_answer = self.bot.update(current_time)
        if bot_answer:
            self.bot.oppo_sprite.talk(self.oppo_answers[self.current_question][bot_answer], bg_color=(50, 160, 250), txt_color=(10, 10, 250), dir_right=False) # cyan, blue
            if bot_answer < 6 and self.answer_used[bot_answer] != 1:
                points = self.questions[self.current_question]["points"][bot_answer]
                self.oppo_score += points
                self.answer_used[bot_answer] = 1
        return bot_answer
                
            

    def render(self):
        """Render the current game state"""
        self.screen.fill((255, 255, 255))
        
        if self.show_menu:
            self.render_menu()
        elif self.show_scoreboard:
            self.render_scoreboard()
        else:
            self.render_game()
        self.render_sprites()

    def render_menu(self):
        """Render the main menu"""
        self.PvE_button.activated = True
        self.PvE_sign.update_color(self.PvE_button.check_hover(pygame.mouse.get_pos()))
        self.PvE_sign.blk_render(self.screen)
        self.PvE_sign.txt_render(self.screen, (self.SCREEN_WIDTH - 250) // 2 + 10, self.SCREEN_HEIGHT - 80 + 10)

    def render_game(self):
        """Render the game screen"""
        self.input_block.render(self.screen, (0, 0, 0), 2)
        self.draw_scores()
        self.draw_question()
        self.draw_timer()
        Bot.draw_output(self.bot, self.screen, self.check_bot_answer())
        self.draw_answers()
        self.draw_output()
        self.draw_answer_hints()
        self.draw_feedback()
        self.feedback_timer -= 1

    def render_scoreboard(self):
        """Render the scoreboard screen"""
        def draw_text(text: str, x, y):
            temp = TextBlock(x, y, 250, 50, text)
            temp.txt_render(self.screen, x, y)

        str_list = ["Question 1", "Question 2", "Question 3", "Total"]
        y_list = [100, 200, 300, 400]
        x_left = (self.SCREEN_WIDTH-250) // 4
        x_mid = (self.SCREEN_WIDTH-250) // 4 * 2
        x_right = (self.SCREEN_WIDTH-250) // 4 * 3
        
        for i in range(4):
            if i == 3:  # Show total score
                draw_text(str(sum(self.player_hist)), x_left, y_list[i])
                draw_text(str_list[i], x_mid, y_list[i])
                draw_text(str(sum(self.oppo_hist)), x_right, y_list[i])
            else:
                draw_text(str(self.player_hist[i]), x_left, y_list[i])
                draw_text(str_list[i], x_mid, y_list[i])
                draw_text(str(self.oppo_hist[i]), x_right, y_list[i])
        
        self.to_menu_button.activated = True
        self.to_menu_sign.update_color(self.to_menu_button.check_hover(pygame.mouse.get_pos()))
        self.to_menu_sign.blk_render(self.screen)
        self.to_menu_sign.txt_render(self.screen, (self.SCREEN_WIDTH - 250) // 2 + 10, self.SCREEN_HEIGHT - 80 + 10)

    def render_sprites(self):
        self.player_sprite.update(self.screen)
        self.bot.oppo_sprite.update(self.screen)

    # Game logic methods (kept similar to original but adapted for OOP)
    def draw_answer_hints(self):
        remaining = len(self.questions[self.current_question]["answer"]) - sum(self.answer_used)
        hint_text = f"Answers remaining: {remaining}"
        hint_block = TextBlock(275, 142, 250, 30, hint_text, bg_color=(240, 240, 240), font_size=24)
        hint_block.blk_render(self.screen)
        hint_block.txt_render(self.screen, 275, 142)

    def check_answer(self, player_input: str):
        player_input = player_input.lower().replace(" ", "")
        if not player_input:
            self.feedback_text = "Please enter an answer!"
            return False

        max_score = -1
        for i, answer in enumerate(self.questions[self.current_question]["answer"]):
            substring = longest_common_substring(player_input, answer)
            score = len(substring)/len(answer)
            if score > max_score:
                max_score = score
                index = i

        if max_score >= 0.8:
            if self.answer_used[index] != 1:
                points = self.questions[self.current_question]["points"][index]
                self.player_score += points
                self.answer_used[index] = 1
                self.feedback_text = f"Correct! +{points} points"
                return True
            else:
                self.feedback_text = "Repeated answer!"
                return False
        else:
            self.feedback_text = "Wrong answer!"
            return False

    def draw_answers(self):
        answer_y = 180
        for i, (answer, points) in enumerate(zip(
            self.questions[self.current_question]["answer"],
            self.questions[self.current_question]["points"]
        )):
            if self.answer_used[i] == 1:
                answer_block = TextBlock(
                    100, answer_y, 600, 40,
                    f"{self.oppo_answers[self.current_question][i]} ({points} pts)",
                    bg_color=(200, 255, 200),
                    font_size=24
                )
                answer_block.blk_render(self.screen)
                answer_block.txt_render(self.screen, 100, answer_y)
                answer_y += 45

    def draw_feedback(self):
        if self.feedback_timer > 0:
            feedback_block = TextBlock(
                self.SCREEN_WIDTH // 2 - 150, 20, 300, 40,
                self.feedback_text,
                bg_color=(240, 240, 240),
                font_size=32,
                txt_color=(
                    (0, 128, 0) if "Correct" in self.feedback_text else
                    (255, 0, 0) if "Wrong" in self.feedback_text else
                    (255, 165, 0)
                )
            )
            feedback_block.blk_render(self.screen)
            feedback_block.txt_render(self.screen, self.SCREEN_WIDTH // 2 - 150, 20)


    def draw_output(self):
        if self.feedback_timer > 0:
            answer_block = TextBlock(
                80, 450, 100, 30,
                f"Your answer: {self.user_input}",
                bg_color=(240, 240, 240),
                font_size=32,
                txt_color=(0, 0, 0)
            )
            answer_block.blk_render(self.screen)
            answer_block.txt_render(self.screen, 80, 450)

    def draw_scores(self):
        player_text = f"You: {self.player_score}"
        oppo_text = f"Opponent: {self.oppo_score}"
        
        Progress_bar = Block(80, self.SCREEN_HEIGHT - 80, self.SCREEN_WIDTH - 160, 50, (160, 160, 160))
        player_bar = Block(80, self.SCREEN_HEIGHT - 80, (self.SCREEN_WIDTH - 160)*self.player_score/100, 50, (255, 0, 0))
        opponent_bar = Block(
            self.SCREEN_WIDTH - (self.SCREEN_WIDTH - 160)*self.oppo_score/100 - 80, 
            self.SCREEN_HEIGHT - 80, 
            (self.SCREEN_WIDTH - 160)*self.oppo_score/100, 
            50, (0, 0, 255)
        )
        
        Progress_bar.blk_render(self.screen)
        player_bar.blk_render(self.screen)
        opponent_bar.blk_render(self.screen)
        
        player_sign = TextBlock(80, self.SCREEN_HEIGHT - 80, 250, 50, player_text)
        oppo_sign = TextBlock(self.SCREEN_WIDTH - 330, self.SCREEN_HEIGHT - 80, 250, 50, oppo_text)
        player_sign.txt_render(self.screen, 80 + 10, self.SCREEN_HEIGHT - 80 + 10)
        oppo_sign.txt_render(self.screen, self.SCREEN_WIDTH - 330 + 10, self.SCREEN_HEIGHT - 80 + 10)

    def draw_question(self):
        q_text = self.questions[self.current_question]["question"]
        question_sign = TextBlock((self.SCREEN_WIDTH-250)//2, 100, 250, 50, q_text)
        question_sign.txt_render(self.screen, (self.SCREEN_WIDTH-250)//2, 100)

    def draw_timer(self):
        elapsed_seconds = (pygame.time.get_ticks() - self.question_start_time) // 1000
        time_left = 20 - elapsed_seconds
        time_sign = TextBlock((self.SCREEN_WIDTH-250)//2, self.SCREEN_HEIGHT - 160, 250, 50, f"Time left: {time_left}")
        time_sign.txt_render(self.screen, (self.SCREEN_WIDTH-250)//2, self.SCREEN_HEIGHT - 160)

    def start_new_question(self):
        if self.current_question >= 0:
            self.player_hist.append(self.player_score)
            self.oppo_hist.append(self.oppo_score)
        
        self.question_start_time = pygame.time.get_ticks()
        self.player_score = 0
        self.oppo_score = 0
        self.answer_used = [0] * 6
        self.current_question += 1
        self.input_block.text = ""
        self.player_sprite.text_duration = 0
        self.bot.oppo_sprite.text_duration = 0
        self.bot.start_question(self.current_question)
        if self.current_question >= 3:
            self.show_scoreboard = True

    def check_timer(self):
        elapsed_seconds = (pygame.time.get_ticks() - self.question_start_time) // 1000
        if elapsed_seconds >= 20:
            self.start_new_question()


def longest_common_substring(s1: str, s2: str) -> str:
    """Find the longest common substring between two strings"""
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


if __name__ == "__main__":
    game = GameUI()
    game.run()