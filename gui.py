import pygame
from enum import Enum
from typing import Any

def draw_rect(surface, color, rect):
    shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
    surface.blit(shape_surf, rect)

class GUI:
    win = None
    font = None
    font2 = None

    elements = []
    focused_element = None
    gui_events = []

    gui_event_handler = None
    gui_scroll_event = (0,0)

    def event_handle(event):
        # pygame left click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if GUI.focused_element:
                GUI.gui_event_handler(
                    {"key": GUI.focused_element.key, "text": GUI.focused_element.text}
                )
                GUI.focused_element.click()

            else:
                for element in GUI.elements:
                    element.no_click()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            for element in GUI.elements:
                element.no_click()
                
        if event.type == pygame.MOUSEWHEEL:
            GUI.gui_scroll_event = (event.x, event.y)

    def step():
        GUI.focused_element = None
        for element in GUI.elements:
            element.step()
        GUI.gui_scroll_event = (0,0)

    def draw():
        for element in GUI.elements:
            element.draw()


class Element:
    def step(self):
        pass
    def draw(self):
        pass
    def click(self):
        pass
    def no_click(self):
        pass
    def move(self, offset):
        pass

class Button(Element):
    def __init__(self, text, key):
        self.text = text
        self.surf = GUI.font.render(text, True, (0, 0, 0))
        self.surf_selected = GUI.font2.render(text, True, (0, 0, 0))
        self.key = key

        self.pos = (0, 0)
        self.size = self.surf.get_size()
        self.parent = None

    def step(self):
        mouse_pos = pygame.mouse.get_pos()
        # if mouse on button
        if (
            mouse_pos[0] > self.pos[0]
            and mouse_pos[0] < self.pos[0] + self.size[0]
            and mouse_pos[1] > self.pos[1]
            and mouse_pos[1] < self.pos[1] + self.size[1]
        ):
            GUI.focused_element = self

    def draw(self):
        # draw_rect(
            # GUI.win,
            # (0, 0, 0, 100),
            # (self.pos[0], self.pos[1], self.size[0], self.size[1])
        # )
        if self is GUI.focused_element:
            GUI.win.blit(self.surf_selected, (self.pos[0] + self.size[0] // 2 - self.surf.get_width() // 2, self.pos[1]))
        else:
            GUI.win.blit(self.surf, (self.pos[0] + self.size[0] // 2 - self.surf.get_width() // 2, self.pos[1]))

    def click(self):
        if self.parent:
            self.parent.click()
            
    def move(self, offset):
        self.pos = (self.pos[0] + offset[0], self.pos[1] + offset[1])


class ContextMenu(Element):
    def __init__(self, pos):
        self.pos = pos
        self.elements = []
        self.width = 0

    def add_button(self, text, key):
        button = Button(text, key)
        button.parent = self
        self.elements.append(button)
        self.width = max(self.width, button.size[0])
        for i, element in enumerate(self.elements):
            element.pos = (self.pos[0], self.pos[1] + i * element.size[1])
            element.size = (self.width, element.size[1])

    def click(self):
        GUI.elements.remove(self)

    def no_click(self):
        GUI.elements.remove(self)

    def step(self):
        for element in self.elements:
            element.step()

    def draw(self):
        for element in self.elements:
            element.draw()
            
    def move(self, offset):
        self.pos = (self.pos[0] + offset[0], self.pos[1] + offset[1])
        for element in self.elements:
            element.move(offset)


class ScrollContainer(Element):
    def __init__(self):
        self.elements = []
        self.offset = 0
    def add_element(self, element):
        self.elements.append(element)
        element.parent = self
    def scroll(self, offset: int):
        self.offset += offset
        for element in self.elements:
            element.move((0, offset))
    def step(self):
        if GUI.gui_scroll_event[1] != 0:
            self.scroll(GUI.gui_scroll_event[1] * 15)
        for element in self.elements:
            element.step()
    def draw(self):
        for element in self.elements:
            element.draw()