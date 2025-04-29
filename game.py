import pygame
import time
import random
import sys
import os


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
screen = pygame.display.set_mode((800, 600))
screen.fill((255, 255, 255))
pygame.display.set_caption("Guess Their Answer!")
input_block = TextInputBlock(50, 50, 700, 50, font_size=48, color=(0, 0, 0), bg_color=(200, 200, 200))
show_menu = True

if __name__ == "__main__":
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if not show_menu:
                input_block.handle_event(event)
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



        pygame.display.flip()

    pygame.quit()
    sys.exit()
