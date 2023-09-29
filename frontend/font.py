import json
import pygame

class Font:
    def __init__(self, json_config):
        with open(json_config, "r") as f:
            dic = json.load(f)
        self.atlas = pygame.image.load(dic['path'])
        self.cords = dic['coords']
    def resize(self, height):
        ratio = height / self.atlas.get_height()
        new_width = ratio * self.atlas.get_width()
        self.atlas = pygame.transform.smoothscale(self.atlas, (new_width, height))
        new_cords = []
        for rect in self.cords:
            new_rect = []
            for pair in rect:
                new_rect.append((pair[0] * ratio, pair[1] * ratio))
            new_cords.append(new_rect)
        self.cords = new_cords
    def render(self, text, antialiasing=False, color=None):
        height = self.cords[0][1][1]
        space_size = height / 4
        tracking = 0
        size = [0, height]
        for c in text:
            if c == ' ':
                char_size = space_size
            else:
                index = ord(c) - ord('!')
                char_size = self.cords[index][1][0]
            
            size[0] += char_size + tracking
        
        surf = pygame.Surface(size, pygame.SRCALPHA)
        offset = 0
        for c in text:
            if c == ' ':
                char_size = space_size
            else:
                index = ord(c) - ord('!')
                char_size = self.cords[index][1][0]
                surf.blit(self.atlas, (offset, 0), self.cords[index])
            offset += char_size + tracking
        return surf
        
        
if __name__ == '__main__':
    pygame.init()
    win = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    
    with open(r'./CriticalRolePlay72.json', "r") as f:
        fonts_json = json.load(f)
    
    font77 = Font(fonts_json)
    
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