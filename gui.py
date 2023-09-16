import pygame
from enum import Enum
from typing import Any
import json


def draw_rect(surface, color, rect):
    shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
    surface.blit(shape_surf, rect)

class NoFonts(Exception):
    pass

class GUI:
    win = None
    fonts = []

    elements = []
    focused_element = None
    gui_events = []

    gui_event_handler = None
    gui_scroll_event = (0, 0)

    frames = []

    debug = False

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

        # pygame right click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            for element in GUI.elements:
                element.no_click()

        # pygame scroll
        if event.type == pygame.MOUSEWHEEL:
            GUI.gui_scroll_event = (event.x, event.y)
        
    def get_font_at(index):
        if len(GUI.fonts) == 0:
            raise NoFonts
        if len(GUI.fonts) > index:
            return GUI.fonts[index]
        else:
            return GUI.fonts[0]
        
    def step():
        GUI.focused_element = None
        for element in GUI.elements:
            element.step()
        GUI.gui_scroll_event = (0, 0)

    def draw():
        for element in GUI.elements:
            element.draw()

    def append(element):
        GUI.elements.append(element)


class Element:
    """Gui Element base class"""

    def __init__(self):
        self.pos = (0, 0)
        self.size = (0, 0)
        self.parent = None
        self.frame = None
        self.debug_color = (255,255,255)
    def step(self):
        pass

    def draw(self):
        if GUI.debug:
            pygame.draw.rect(GUI.win, self.debug_color, (self.get_abs_pos(), self.size), 1)
        if self.frame:
            self.frame.draw(self)

    def click(self):
        pass

    def no_click(self):
        pass

    def set_size(self, size):
        self.size = size

    def get_abs_pos(self):
        if self.parent is None:
            return self.pos
        parent_pos = self.parent.get_abs_pos()
        return (parent_pos[0] + self.pos[0], parent_pos[1] + self.pos[1])


class Label(Element):
    def __init__(self, text, font=None):
        super().__init__()
        self.text = text
        self.font = font
        if not self.font:
            self.font = GUI.fonts[0]
        self.surf = self.font.render(self.text)
        self.size = self.surf.get_size()
        
        self.debug_color = (0,255,0)

    def draw(self):
        super().draw()
        pos = self.get_abs_pos()
        center = (
                    pos[0] + self.size[0] // 2 - self.surf.get_width() // 2,
                    pos[1] + self.size[1] // 2 - self.surf.get_height() // 2,
                 )
        GUI.win.blit(self.surf, center)


class Button(Label):
    def __init__(self, text, key, font=None, selected_font=None):
        super().__init__(text)
        self.text = text
        self.font = font
        self.selected_font = selected_font
        if not self.font:
            self.font = GUI.fonts[0]
        if not self.selected_font:
            self.selected_font = GUI.fonts[0]

        self.surf = self.font.render(text)
        self.surf_selected = self.selected_font.render(text)
        self.key = key
        self.size = self.surf.get_size()

    def step(self):
        super().step()
        mouse_pos = pygame.mouse.get_pos()
        # if mouse on button
        pos = self.get_abs_pos()
        if (
            mouse_pos[0] > pos[0]
            and mouse_pos[0] < pos[0] + self.size[0]
            and mouse_pos[1] > pos[1]
            and mouse_pos[1] < pos[1] + self.size[1]
        ):
            GUI.focused_element = self

    def draw(self):
        super().draw()
        pos = self.get_abs_pos()
        center = (
                    pos[0] + self.size[0] // 2 - self.surf.get_width() // 2,
                    pos[1],
                 )

        if self is GUI.focused_element:
            GUI.win.blit(self.surf_selected, center)
        else:
            GUI.win.blit(self.surf, center)

    def click(self):
        if self.parent:
            self.parent.click()


class StackPanel(Element):
    def __init__(self, pos=(0,0)):
        super().__init__()
        self.pos = pos
        self.elements = []
        self.margin = 10
        self.scrollable = False
        self.linked_button = None
        self.debug_color = (255,0,0)

    def append(self, element):
        element.parent = self
        self.elements.append(element)
        self.size = (max(self.size[0], element.size[0]), self.size[1] + element.size[1] + self.margin)

        height_offset = 0
        for element in self.elements:
            element.pos = (self.pos[0], self.pos[1] + height_offset)
            element.set_size((self.size[0], element.size[1]))
            height_offset += element.size[1] + self.margin

        self.size = (self.size[0], height_offset - self.margin)

    def set_size(self, size):
        self.size = size
        for e in self.elements:
            e.set_size((size[0], e.size[1]))

    def set_pos(self, pos):
        self.pos = pos

    def step(self):
        super().step()
        if self.scrollable and GUI.gui_scroll_event[1] != 0:
            self.pos = (self.pos[0], self.pos[1] + GUI.gui_scroll_event[1] * 20) 
        if self.linked_button:
            mouse_pos = pygame.mouse.get_pos()
            # if mouse on button
            pos = self.get_abs_pos()
            if (
                mouse_pos[0] > pos[0]
                and mouse_pos[0] < pos[0] + self.size[0]
                and mouse_pos[1] > pos[1]
                and mouse_pos[1] < pos[1] + self.size[1]
            ):
                GUI.focused_element = self.linked_button
        for element in self.elements:
            element.step()

    def draw(self):
        for element in self.elements:
            element.draw()
        super().draw()


class Columns(StackPanel):
    def __init__(self, cols):
        super().__init__()
        self.cols = cols
        self.current_index = [0,0]
        self.hor_margin = 10
        self.ver_margin = 10

        self.element_size = (0,0)
        self.debug_color = (255,255,0)
    def append(self, element):
        self.element_size = (max(self.element_size[0], element.size[0]), max(self.element_size[1], element.size[1]))
        self.elements.append(element)
        element.parent = self

        x = 0
        y = 0

        size_x = 0
        size_y = 0
        for i, e in enumerate(self.elements):
            e.pos = ((x, y))
            e.set_size(self.element_size)
            x += self.element_size[0] + self.hor_margin
            size_x = max(x, size_x)
            if (i + 1) % self.cols == 0:
                x = 0
                y += self.element_size[1] + self.ver_margin
                size_y = max(y, size_y)
        self.size = (size_x - self.hor_margin, size_y - self.ver_margin)


class ContextMenu(StackPanel):
    def __init__(self, pos=(0,0)):
        super().__init__()
        self.pos = pos
        self.elements = []
        self.size = (0, 0)

    def add_button(self, text, key):
        button = Button(text, key)
        self.append(button)
        
    def click(self):
        GUI.elements.remove(self)

    def no_click(self):
        GUI.elements.remove(self)


class Frame:
    def __init__(self, json_path):
        with open(json_path, "r") as f:
            frame_dict = json.load(f)
        self.surf = pygame.image.load(frame_dict['path'])
        self.coords = frame_dict['coords']
    def draw(self, element):
        top_left = self.coords["top_left"]
        top_right = self.coords["top_right"]
        bottom_right = self.coords["bottom_right"]
        bottom_left = self.coords["bottom_left"]
        left = self.coords["left"]
        right = self.coords["right"]
        top = self.coords["top"]
        bottom = self.coords["bottom"]

        deco_left = self.coords["left_decoration"]
        deco_right = self.coords["right_decoration"]
        deco_top = self.coords["top_decoration"]
        deco_bottom = self.coords["bottom_decoration"]

        top_left_pos = (element.pos[0] - top_left[1][0], element.pos[1] - top_left[1][1])
        top_right_pos = (element.pos[0] + element.size[0], element.pos[1] - top_right[1][1])
        bottom_left_pos = (element.pos[0] - bottom_left[1][0], element.pos[1] + element.size[1])
        bottom_right_pos = (element.pos[0] + element.size[0], element.pos[1] + element.size[1])

        left_rect = (
            (element.pos[0] - left[1][0], element.pos[1]),
            (left[1][0], element.size[1]),
        )
        right_rect = (
            (element.pos[0] + element.size[0], element.pos[1]),
            (right[1][0], element.size[1]),
        )
        top_rect = (
            (element.pos[0], element.pos[1] - top[1][1]),
            (element.size[0], top[1][1])
        )
        bottom_rect = (
            (element.pos[0], element.pos[1] + element.size[1]),
            (element.size[0], bottom[1][1]),
        )

        deco_left_pos = (element.pos[0] - deco_left[1][0], element.pos[1] + element.size[1] // 2 - deco_left[1][1] // 2)
        deco_right_pos = (element.pos[0] + element.size[0], element.pos[1] + element.size[1] // 2 - deco_left[1][1] // 2)
        deco_top_pos = (element.pos[0] + element.size[0] // 2 - deco_top[1][0] // 2, element.pos[1] - deco_top[1][1])
        deco_bottom_pos = (element.pos[0] + element.size[0] // 2 - deco_bottom[1][0] // 2, element.pos[1] + element.size[1])

        left_surf = pygame.Surface(left[1], pygame.SRCALPHA)
        left_surf.blit(self.surf, (0, 0), left)
        left_surf = pygame.transform.scale(left_surf, left_rect[1])

        right_surf = pygame.Surface(right[1], pygame.SRCALPHA)
        right_surf.blit(self.surf, (0, 0), right)
        right_surf = pygame.transform.scale(right_surf, right_rect[1])

        top_surf = pygame.Surface(top[1], pygame.SRCALPHA)
        top_surf.blit(self.surf, (0, 0), top)
        top_surf = pygame.transform.scale(top_surf, top_rect[1])

        bottom_surf = pygame.Surface(bottom[1], pygame.SRCALPHA)
        bottom_surf.blit(self.surf, (0, 0), bottom)
        bottom_surf = pygame.transform.scale(bottom_surf, bottom_rect[1])

        win = GUI.win

        win.blit(self.surf, top_left_pos, top_left)
        win.blit(self.surf, top_right_pos, top_right)
        win.blit(self.surf, bottom_left_pos, bottom_left)
        win.blit(self.surf, bottom_right_pos, bottom_right)

        win.blit(left_surf, left_rect[0])
        win.blit(right_surf, right_rect[0])
        win.blit(top_surf, top_rect[0])
        win.blit(bottom_surf, bottom_rect[0])

        win.blit(self.surf, deco_left_pos, deco_left)
        win.blit(self.surf, deco_right_pos, deco_right)
        win.blit(self.surf, deco_top_pos, deco_top)
        win.blit(self.surf, deco_bottom_pos, deco_bottom)

        if GUI.debug:
            pygame.draw.rect(GUI.win, (255,255,255), (top_left_pos, top_left[1]), 1)
            pygame.draw.rect(GUI.win, (255,255,255), (top_right_pos, top_right[1]), 1)
            pygame.draw.rect(GUI.win, (255,255,255), (bottom_left_pos, bottom_left[1]), 1)
            pygame.draw.rect(GUI.win, (255,255,255), (bottom_right_pos, bottom_right[1]), 1)


class Picture(Element):
    def __init__(self, surf):
        super().__init__()
        self.surf = surf
        self.size = self.surf.get_size()
    def draw(self):
        pos = self.get_abs_pos()
        super().draw()
        GUI.win.blit(self.surf, (pos[0] + self.size[0] // 2 - self.surf.get_width() // 2, pos[1]))



def test():
    pass


if __name__ == "__main__":
    pygame.init()

    winWidth = 1280
    winHeight = 720
    win = pygame.display.set_mode((winWidth, winHeight))

    ### setup
    GUI.win = win
    GUI.fonts.append(pygame.font.SysFont("Calibri", 16))
    GUI.fonts.append(pygame.font.SysFont("Calibri", 17))
    GUI.gui_event_handler = test

    cm = ContextMenu((400, 400))
    cm.frame = True
    cm.add_button("test1", "t1")
    cm.add_button("test2", "t2")
    cm.add_button("this is label", "t3")
    cm.add_button("test4", "t4")
    cm.add_button("test5", "t5")
    GUI.elements.append(cm)

    GUI.frame_surf = pygame.image.load(
        r"./assets/images/frame.png"
    )
    GUI.frame_coords["top_right"] = ((1000 - 125, 0), (125, 140))
    GUI.frame_coords["top_left"] = ((0, 0), (125, 140))
    GUI.frame_coords["bottom_left"] = ((0, 1000 - 140), (125, 140))
    GUI.frame_coords["bottom_right"] = ((1000 - 125, 1000 - 140), (125, 140))
    GUI.frame_coords["right"] = ((1000 - 125, 150), (125, 10))
    GUI.frame_coords["left"] = ((0, 150), (125, 10))
    GUI.frame_coords["top"] = ((125, 0), (10, 140))
    GUI.frame_coords["bottom"] = ((125, 1000 - 140), (10, 140))

    ### main loop

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            run = False

        win.fill((255, 255, 255))
        GUI.step()

        GUI.draw()

        pygame.display.update()
