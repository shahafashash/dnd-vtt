import pygame

class Effect:
    def __init__(self, win):
        self.win = win
        self.surf = None

    def handle_events(self, event):
        pass

    def step(self):
        pass

    def draw(self):
        self.win.blit(self.surf, (0,0))
    

class DarknessEffect(Effect):
    def __init__(self, win):
        super().__init__(win)
        self.amount = 200
        self.light_sources = []
        self.surf = pygame.Surface(self.win.get_size(), pygame.SRCALPHA)
        self.surf.fill((0, 0, 0, self.amount))

        self.light_surf_base = pygame.image.load(r'./assets/images/light.png')

        self.focused_light = None
        self.dragged_light = None
    
    def create_light_source(self, pos, radius):
        light = [pos, radius]
        self.light_sources.append(light)

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.focused_light:
                self.dragged_light = self.focused_light
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragged_light = None
        elif event.type == pygame.MOUSEMOTION:
            if self.dragged_light:
                self.dragged_light[0] = event.pos
        elif event.type == pygame.MOUSEWHEEL:
            if self.focused_light:
                self.focused_light[1] += event.y * 5
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_l:
                mouse_pos = pygame.mouse.get_pos()
                self.create_light_source(mouse_pos, 50)

    def step(self):
        self.focused_light = None
        self.surf.fill((0, 0, 0, self.amount))
        # update lights
        mouse_pos = pygame.mouse.get_pos()
        for light in self.light_sources:
            pos, radius = light
            factor = radius * 3 / self.light_surf_base.get_width()
            
            light_surf = pygame.transform.smoothscale_by(self.light_surf_base, factor)
            self.surf.blit(light_surf, (pos[0] - light_surf.get_width()//2, pos[1] - light_surf.get_height()//2), special_flags=pygame.BLEND_RGBA_SUB)

            if (mouse_pos[0] - pos[0])*(mouse_pos[0] - pos[0]) + (mouse_pos[1] - pos[1])*(mouse_pos[1] - pos[1]) < 2500:
                self.focused_light = light

    def draw(self):
        super().draw()
        if self.focused_light:
            pygame.draw.circle(self.win, (255,255,255), self.focused_light[0], 50, 1)


class ColorFilter:
    def __init__(self):
        pass
