import json
import pygame

class Font:
    def __init__(self, dic):
        self.atlas = pygame.image.load(dic['path'])
        self.cords = dic['cords'].copy()
    def resize(self, height):
        ratio = height / self.atlas.get_height()
        new_width = ratio * self.atlas.get_width()
        self.atlas = pygame.transform.smoothscale(self.atlas, (new_width, height))
        new_cords = []
        for t in self.cords:
            new_cords.append((t[0] * ratio, t[1] * ratio))
        self.cords = new_cords
    def render(self, text, antialiasing, color):
        text = text.upper()
        height = self.atlas.get_height()
        space_size = height / 4
        tracking = height / 16
        size = [0, height]
        for c in text:
            if c == ' ':
                char_size = space_size
            else:
                index = ord(c) - ord('A')
                char_size = self.cords[index][1] - self.cords[index][0]
            
            size[0] += char_size + tracking
        
        surf = pygame.Surface(size, pygame.SRCALPHA)
        offset = 0
        for c in text:
            if c == ' ':
                char_size = space_size
            else:
                index = ord(c) - ord('A')
                char_size = self.cords[index][1] - self.cords[index][0]
                surf.blit(self.atlas, (offset, 0), ((self.cords[index][0], 0), (char_size, height)))
            offset += char_size + tracking
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