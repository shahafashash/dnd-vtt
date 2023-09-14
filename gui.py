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
    gui_scroll_event = (0, 0)

    frame_surf = None
    frame_coords = {}

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

    def step():
        GUI.focused_element = None
        for element in GUI.elements:
            element.step()
        GUI.gui_scroll_event = (0, 0)

    def draw():
        for element in GUI.elements:
            element.draw()


class Element:
    """Gui Element base class"""

    def __init__(self):
        self.pos = (0, 0)
        self.size = (0, 0)
        self.parent = None

    def step(self):
        pass

    def draw(self):
        pass

    def click(self):
        pass

    def no_click(self):
        pass

    def set_pos(self, offset):
        self.pos = (self.pos[0] + offset[0], self.pos[1] + offset[1])


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
            GUI.win.blit(
                self.surf_selected,
                (
                    self.pos[0] + self.size[0] // 2 - self.surf.get_width() // 2,
                    self.pos[1],
                ),
            )
        else:
            GUI.win.blit(
                self.surf,
                (
                    self.pos[0] + self.size[0] // 2 - self.surf.get_width() // 2,
                    self.pos[1],
                ),
            )

    def click(self):
        if self.parent:
            self.parent.click()


class ContextMenu(Element):
    def __init__(self, pos):
        self.pos = pos
        self.elements = []
        self.size = (0, 0)

    def add_button(self, text, key):
        button = Button(text, key)
        button.parent = self
        self.elements.append(button)
        self.size = (max(self.size[0], button.size[0]), self.size[1] + button.size[1])
        for i, element in enumerate(self.elements):
            element.pos = (self.pos[0], self.pos[1] + i * element.size[1])
            element.size = (self.size[0], element.size[1])

            # self.size = (self.size[0], self.size[1] + element.size[1])
            # print(self.size)

    def click(self):
        GUI.elements.remove(self)

    def no_click(self):
        GUI.elements.remove(self)

    def step(self):
        for element in self.elements:
            element.step()

    def draw(self):
        # pygame.draw.rect(GUI.win, (150, 150, 150), (self.pos, self.size))
        for element in self.elements:
            element.draw()

    def set_pos(self, offset):
        super().set_pos(offset)
        for element in self.elements:
            element.set_pos(offset)


class ContextMenuFrame(ContextMenu):
    def draw(self):
        # pygame.draw.rect(win, (150,150,150), (self.pos, self.size))
        super().draw()

        top_left = GUI.frame_coords["top_left"]
        top_right = GUI.frame_coords["top_right"]
        bottom_right = GUI.frame_coords["bottom_right"]
        bottom_left = GUI.frame_coords["bottom_left"]
        left = GUI.frame_coords["left"]
        right = GUI.frame_coords["right"]
        top = GUI.frame_coords["top"]
        bottom = GUI.frame_coords["bottom"]

        top_left_pos = (self.pos[0] - top_left[1][0], self.pos[1] - top_left[1][1])
        top_right_pos = (self.pos[0] + self.size[0], self.pos[1] - top_right[1][1])
        bottom_left_pos = (self.pos[0] - bottom_left[1][0], self.pos[1] + self.size[1])
        bottom_right_pos = (self.pos[0] + self.size[0], self.pos[1] + self.size[1])

        left_rect = (
            (self.pos[0] - left[1][0], self.pos[1]),
            (left[1][0], self.size[1]),
        )
        right_rect = (
            (self.pos[0] + self.size[0], self.pos[1]),
            (right[1][0], self.size[1]),
        )
        top_rect = ((self.pos[0], self.pos[1] - top[1][1]), (self.size[0], top[1][1]))
        bottom_rect = (
            (self.pos[0], self.pos[1] + self.size[1]),
            (self.size[0], bottom[1][1]),
        )

        left_surf = pygame.Surface(left[1], pygame.SRCALPHA)
        left_surf.blit(GUI.frame_surf, (0, 0), left)
        left_surf = pygame.transform.scale(left_surf, left_rect[1])

        right_surf = pygame.Surface(right[1], pygame.SRCALPHA)
        right_surf.blit(GUI.frame_surf, (0, 0), right)
        right_surf = pygame.transform.scale(right_surf, right_rect[1])

        top_surf = pygame.Surface(top[1], pygame.SRCALPHA)
        top_surf.blit(GUI.frame_surf, (0, 0), top)
        top_surf = pygame.transform.scale(top_surf, top_rect[1])

        bottom_surf = pygame.Surface(bottom[1], pygame.SRCALPHA)
        bottom_surf.blit(GUI.frame_surf, (0, 0), bottom)
        bottom_surf = pygame.transform.scale(bottom_surf, bottom_rect[1])

        win.blit(GUI.frame_surf, top_left_pos, top_left)
        win.blit(GUI.frame_surf, top_right_pos, top_right)
        win.blit(GUI.frame_surf, bottom_left_pos, bottom_left)
        win.blit(GUI.frame_surf, bottom_right_pos, bottom_right)

        win.blit(left_surf, left_rect[0])
        win.blit(right_surf, right_rect[0])
        win.blit(top_surf, top_rect[0])
        win.blit(bottom_surf, bottom_rect[0])


class ContextMenuScrollable(ContextMenu):
    def __init__(self, pos):
        super().__init__(pos)
        self.offset = 0

    def scroll(self, offset: int):
        self.offset += offset
        for element in self.elements:
            element.set_pos((0, offset))

    def step(self):
        if GUI.gui_scroll_event[1] != 0:
            self.scroll(GUI.gui_scroll_event[1] * 15)
        super().step()


def test():
    pass


if __name__ == "__main__":
    pygame.init()

    winWidth = 1280
    winHeight = 720
    win = pygame.display.set_mode((winWidth, winHeight))

    ### setup
    GUI.win = win
    GUI.font = pygame.font.SysFont("Calibri", 16)
    GUI.font2 = pygame.font.SysFont("Calibri", 17)
    GUI.gui_event_handler = test

    cm = ContextMenuFrame((100, 100))
    cm.add_button("test1", "t1")
    cm.add_button("test2", "t2")
    cm.add_button("this is label", "t3")
    cm.add_button("test4", "t4")
    cm.add_button("test5", "t5")
    GUI.elements.append(cm)

    GUI.frame_surf = pygame.image.load(
        r"C:\Git\savedfiles\fontBuilder\ReadyFonts\Arial_18.png"
    )
    GUI.frame_coords["top_right"] = ((256 - 50, 0), (50, 50))
    GUI.frame_coords["top_left"] = ((0, 0), (50, 50))
    GUI.frame_coords["bottom_left"] = ((0, 256 - 50), (50, 50))
    GUI.frame_coords["bottom_right"] = ((256 - 50, 256 - 50), (50, 50))
    GUI.frame_coords["right"] = ((256 - 50, 50), (50, 50))
    GUI.frame_coords["left"] = ((0, 50), (50, 50))
    GUI.frame_coords["top"] = ((50, 0), (50, 50))
    GUI.frame_coords["bottom"] = ((50, 50), (50, 50))

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
