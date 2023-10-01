""" module for adding and managing tokens on screen """

import pygame

class TokenManager:
    _single = None
    def __init__(self, win=None):
        TokenManager._single = self
        self.tokens = []
        self.win = win

        self.selected_token = None
        self.dargged_token = None
        self.mouse_offset = None

    @staticmethod
    def get_instance():
        return TokenManager._single
    
    def append(self, token):
        self.tokens.append(token)

    def handle_pygame_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.selected_token:
                self.mouse_offset = (event.pos[0] - self.selected_token.pos[0], event.pos[1] - self.selected_token.pos[1])
                self.dargged_token = self.selected_token
            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dargged_token = None 
        elif event.type == pygame.MOUSEMOTION:
            if self.dargged_token:
                self.dargged_token.pos = (event.pos[0] - self.mouse_offset[0], event.pos[1] - self.mouse_offset[1])
        elif event.type == pygame.MOUSEWHEEL:
            if self.selected_token:
                sign = 1 if event.y > 0 else -1
                print(sign)

                scale_factor = 1 + (event.y / 10)
                print(scale_factor)
                self.selected_token.scale(scale_factor)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_COMMA:
                if self.selected_token:
                    self.selected_token.rotate(10)
            elif event.key == pygame.K_PERIOD:
                if self.selected_token:
                    self.selected_token.rotate(-10)
            elif event.key == pygame.K_DELETE:
                if self.selected_token:
                    self.tokens.remove(self.selected_token)
                    self.selected_token = None

    def step(self):
        self.selected_token = None
        for token in self.tokens:
            token.step()

    def draw(self):
        for token in self.tokens:
            token.draw()

class Token:
    ''' object on screen that can be moved, scaled, rotated by the user '''
    def __init__(self):
        # position on screen
        self.pos = (0,0)
        # scale factor
        self.scale_factor = 1.0
        # rotation degrees
        self.rotation = 0

        # size of surf
        self.radius = 0

    def step(self):
        token_man = TokenManager.get_instance()
        mouse_pos = pygame.mouse.get_pos()
        if (mouse_pos[0] > self.pos[0] - self.radius and mouse_pos[0] < self.pos[0] + self.radius and
            mouse_pos[1] > self.pos[1] - self.radius and mouse_pos[1] < self.pos[1] + self.radius):
            token_man.selected_token = self

    def draw(self):
        pass


class TokenSurf(Token):
    ''' token is pygame surface '''
    def __init__(self, surf: pygame.Surface, diameter=None):
        super().__init__()
        
        # original surf for calculations
        self.org_surf = surf

        # surf for drawing
        self.surf = surf

        if diameter:
            radius = diameter / 2
            mean = (surf.get_width() + surf.get_height()) / 2
            self.scale_factor = (radius * 2) / mean
            self.recalculate_surf()
            self.radius = radius
        else:
            self.radius = (surf.get_width() + surf.get_height()) / 4

        self.lower_limit_factor = 0.3 * self.scale_factor

    def recalculate_surf(self):
        # scale
        self.surf = pygame.transform.smoothscale_by(self.org_surf, self.scale_factor)

        # rotate
        self.surf = pygame.transform.rotate(self.surf, self.rotation)
        self.radius = (self.surf.get_width() + self.surf.get_height()) / 4

    def scale(self, factor):
        # if self.scale_factor + factor < self.lower_limit_factor:
        #     factor = 0
        self.scale_factor *= factor
        
        self.recalculate_surf()
        
    def rotate(self, angle_degrees):
        self.rotation += angle_degrees
        self.recalculate_surf()

    def draw(self):
        token_man = TokenManager.get_instance()
        pos = (self.pos[0] - self.surf.get_width() // 2, self.pos[1] - self.surf.get_height() // 2)
        token_man.win.blit(self.surf, pos)

        if self is token_man.selected_token:
            pygame.draw.circle(token_man.win, (255,255,255), self.pos, self.radius, 1)
