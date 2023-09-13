import json
import pygame

class Font:
    def __init__(self, dic):
        self.atlas = pygame.image.load(dic['path'])
        self.dic = dic
    def render(self, text, antialiasing, color):
        text = text.upper()
        height = self.atlas.get_height()
        space_between_characters = height / 16
        size = [0, height]
        cords = self.dic['cords']
        for c in text:
            if c == ' ':
                char_size = height / 2
            else:
                index = ord(c) - ord('A')
                char_size = cords[index][1] - cords[index][0]
            
            size[0] += char_size + space_between_characters
        
        surf = pygame.Surface(size, pygame.SRCALPHA)
        offset = 0
        for c in text:
            if c == ' ':
                char_size = height / 2
            else:
                index = ord(c) - ord('A')
                char_size = cords[index][1] - cords[index][0]
                surf.blit(self.atlas, (offset, 0), ((cords[index][0], 0), (char_size, height)))
            offset += char_size + space_between_characters
        return surf
        
        
if __name__ == '__main__':
    pygame.init()
    win = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    
    with open(r'assets/Font/Fonts.json', "r") as f:
        fonts_json = json.load(f)
    
    font77 = Font(fonts_json[0])
    
    text = font77.render('hello world'.upper(), True, None)
    text2 = font77.render('the quick brown fox jumps over the lazy dog'.upper(), True, None)
    
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
    
        win.fill((0,0,0))
        win.blit(text, (100,100))
        win.blit(text2, (100,500))
            
        pygame.display.flip()