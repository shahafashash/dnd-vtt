from typing import Tuple
import pygame
from random import randint
from backend.settings import Controls


class Effects(list):
    def handle_events(self, event):
        for effect in self:
            effect.handle_events(event)

    def step(self):
        for effect in self:
            effect.step()

    def draw(self):
        for effect in self:
            effect.draw()


class Effect:
    def __init__(self, win: pygame.Surface, controls: Controls) -> None:
        self.name = ""
        self.win = win
        self.surf = None
        self.controls = controls

    def handle_events(self, event):
        pass

    def step(self):
        pass

    def draw(self):
        self.win.blit(self.surf, (0, 0))


class DarknessEffect(Effect):
    def __init__(self, win: pygame.Surface, controls: Controls) -> None:
        super().__init__(win, controls)
        self.name = "darkness"
        self.amount = 200
        self.light_sources = []
        self.surf = pygame.Surface(self.win.get_size(), pygame.SRCALPHA)
        self.surf.fill((0, 0, 0, self.amount))

        self.light_surf_base = pygame.image.load(r"./assets/images/light.png")

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
                if self.focused_light[1] <= 0:
                    self.focused_light[1] = 1
        elif event.type == pygame.KEYDOWN:
            if event.key == self.controls.get("light"):
                mouse_pos = pygame.mouse.get_pos()
                self.create_light_source(mouse_pos, 50)
            elif event.key == pygame.K_DELETE:
                if self.focused_light:
                    self.light_sources.remove(self.focused_light)
                    self.focused_light = None

    def step(self):
        self.focused_light = None
        self.surf.fill((0, 0, 0, self.amount))
        # update lights
        mouse_pos = pygame.mouse.get_pos()
        for light in self.light_sources:
            pos, radius = light
            factor = radius * 3 / self.light_surf_base.get_width()

            light_surf = pygame.transform.smoothscale_by(self.light_surf_base, factor)
            self.surf.blit(
                light_surf,
                (
                    pos[0] - light_surf.get_width() // 2,
                    pos[1] - light_surf.get_height() // 2,
                ),
                special_flags=pygame.BLEND_RGBA_SUB,
            )

            if (mouse_pos[0] - pos[0]) * (mouse_pos[0] - pos[0]) + (
                mouse_pos[1] - pos[1]
            ) * (mouse_pos[1] - pos[1]) < 2500:
                self.focused_light = light

    def draw(self):
        super().draw()
        if self.focused_light:
            pygame.draw.circle(self.win, (255, 255, 255), self.focused_light[0], 50, 1)


class ColorFilter(Effect):
    def __init__(
        self, win: pygame.Surface, color: Tuple[int, int, int], controls: Controls
    ) -> None:
        super().__init__(win, controls)
        self.color = color

    def draw(self):
        self.win.fill(self.color, special_flags=pygame.BLEND_MULT)
        self.win.fill((255, 100, 100), special_flags=pygame.BLEND_MULT)


class Rain(Effect):
    def __init__(self, win: pygame.Surface, controls: Controls) -> None:
        super().__init__(win, controls)
        self.particles = []
        self.max_particles = 100

    def step(self):
        if len(self.particles) < self.max_particles:
            if randint(1, 100) > 10:
                # create a new particle
                x = 5

    def draw(self):
        for particle in self.particles:
            pass
