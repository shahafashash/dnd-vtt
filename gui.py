import pygame
from enum import Enum
from typing import Any
from tools.profilers import time_profiler
import json


class NoFonts(Exception):
    pass


class GUI:
    win = None
    fonts = []

    elements = []
    focused_element = None
    active_element = None
    gui_events = []

    gui_event_handler = None
    gui_scroll_event = (0, 0)

    frames = []

    debug = False

    def event_handle(event):
        # pygame left click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if GUI.focused_element:
                for element in GUI.elements:
                    if element is GUI.focused_element:
                        continue
                    else:
                        element.no_click()
                GUI.focused_element.click()

                if isinstance(GUI.focused_element, TextBox):
                    textBox = GUI.focused_element
                    GUI.active_element = textBox
                    textBox.start_typing()
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

        # keyboard on click
        if event.type == pygame.KEYDOWN:
            if GUI.active_element:
                character = event.unicode
                GUI.active_element.type_character(character)

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

    def remove(element):
        GUI.elements.remove(element)


class Element:
    """Gui Element base class"""

    def __init__(self):
        self.pos = (0, 0)
        self.size = (0, 0)
        self.parent = None
        self.frame = None
        self.debug_color = (255, 255, 255)
        self.name = ''

    def step(self):
        pass

    def draw(self):
        if GUI.debug:
            pygame.draw.rect(
                GUI.win, self.debug_color, (self.get_abs_pos(), self.size), 1
            )
        if self.frame:
            self.frame.draw(self)

    def click(self):
        pass

    def no_click(self):
        pass

    def set_pos(self, pos):
        self.pos = pos

    def set_size(self, size):
        self.size = size

    def get_abs_pos(self):
        if self.parent is None:
            return self.pos
        parent_pos = self.parent.get_abs_pos()
        return (parent_pos[0] + self.pos[0], parent_pos[1] + self.pos[1])


class Elements(Element):
    def __init__(self):
        super().__init__()
        self.elements = []
    
    def append(self, element):
        self.elements.append(element)

    def draw(self):
        super().draw()
        for element in self.elements:
            element.draw()

    def step(self):
        super().step()
        for element in self.elements:
            element.step()

    def click(self):
        for element in self.elements:
            element.click()

    def no_click(self):
        for element in self.elements:
            element.no_click()


class Label(Element):
    """A free label with no events"""

    def __init__(self, text, font=None):
        super().__init__()
        self.text = text
        self.font = font
        if not self.font:
            self.font = GUI.fonts[0]
        self.surf = self.font.render(self.text, True, (0, 0, 0))
        self.size = self.surf.get_size()

        self.debug_color = (0, 255, 0)

    def draw(self):
        super().draw()
        pos = self.get_abs_pos()
        center = (
            pos[0] + self.size[0] // 2 - self.surf.get_width() // 2,
            pos[1] + self.size[1] // 2 - self.surf.get_height() // 2,
        )
        GUI.win.blit(self.surf, center)


class Button(Element):
    """a button, send event: {'key': _, 'text': _}"""

    def __init__(self, text, key, font=None, selected_font=None, custom_width=-1):
        super().__init__()
        self.text = text
        self.font = font
        self.selected_font = selected_font
        if not self.font:
            self.font = GUI.fonts[0]
        if not self.selected_font:
            self.selected_font = GUI.fonts[0]

        self.surf = self.font.render(text, True, (0, 0, 0))
        self.custom_width = custom_width
        self.surf = self.render(self.text, self.font, (0, 0, 0))
        self.surf_selected = self.render(text, self.selected_font, (100, 100, 100))

        self.key = key
        self.size = self.surf.get_size()

    def render(self, text, font, color):
        rendered_text = font.render(text, True, color)
        self.text_width = rendered_text.get_width()
        if self.custom_width != -1:
            self.text_width = min(rendered_text.get_width(), self.custom_width)
            surf = pygame.Surface(
                (self.custom_width, rendered_text.get_height()), pygame.SRCALPHA
            )
            surf.blit(rendered_text, (0, 0))
        else:
            surf = rendered_text
        return surf

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
            pos[0] + self.size[0] // 2 - self.text_width // 2,
            pos[1],
        )

        if self is GUI.focused_element:
            GUI.win.blit(self.surf_selected, center)
        else:
            GUI.win.blit(self.surf, center)

    def click(self):
        GUI.gui_event_handler({"key": self.key, "text": self.text})


class TextBox(Element):
    """editable textbox, send event: {'key': _, 'text': _, 'state': ['typing', 'done']}"""

    def __init__(self, key, initial_text, font=None, alignment="c"):
        super().__init__()
        self.key = key
        self.initial_text = initial_text
        self.text = ""
        self.font = font
        if not self.font:
            self.font = GUI.fonts[0]
        self.surf = self.font.render(initial_text, True, (0, 0, 0))
        self.size = self.surf.get_size()
        self.typing = False
        self.timer = 0
        self.cursor_on = False
        self.alignment = alignment

    def start_typing(self):
        self.typing = True
        self.timer = 20
        self.refresh()

    def stop_typing(self):
        self.typing = False
        self.timer = 0
        self.cursor_on = False
        self.refresh()
        if GUI.active_element is self:
            GUI.active_element = None
        GUI.gui_event_handler({"key": self.key, "text": self.text, "state": "done"})

    def type_character(self, char):
        if char == "\x08":
            if len(self.text) > 0:
                self.text = self.text[:-1]
        if char.isprintable():
            self.text += char
        GUI.gui_event_handler({"key": self.key, "text": self.text, "state": "typing"})
        self.refresh()

    def click(self):
        self.no_click()

    def no_click(self):
        if self.typing:
            self.stop_typing()

    def refresh(self):
        if not self.typing:
            text = ""
            if self.text != "":
                text = self.text
            else:
                text = self.initial_text
            self.surf = self.font.render(text, True, (0, 0, 0))
            return
        text = self.text
        if self.cursor_on:
            text += "|"
        self.surf = self.font.render(text, True, (0, 0, 0))

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

        if self.typing:
            self.timer -= 1
            if self.timer == 0:
                self.cursor_on = not self.cursor_on
                self.timer = 20
                self.refresh()

    def draw(self):
        super().draw()
        pos = self.get_abs_pos()
        alignment = (pos[0], pos[1])
        if self.alignment == "c":
            alignment = (
                pos[0] + self.size[0] // 2 - self.surf.get_width() // 2,
                pos[1],
            )
        elif self.alignment == "l":
            alignment = (
                pos[0],
                pos[1],
            )
        GUI.win.blit(self.surf, alignment)


class StackPanel(Element):
    """container for elements. elements are stacked vertically"""

    def __init__(self, pos=(0, 0)):
        super().__init__()
        self.pos = pos
        self.elements = []
        self.margin = 10
        self.scrollable = False
        # linked button: if stackpanel is focused, the button will be the focused_element
        self.linked_button = None
        self.debug_color = (255, 0, 0)

    def append(self, element):
        element.parent = self
        self.elements.append(element)
        self.size = (
            max(self.size[0], element.size[0]),
            self.size[1] + element.size[1] + self.margin,
        )

        height_offset = 0
        for element in self.elements:
            element.pos = (0, height_offset)
            element.set_size((self.size[0], element.size[1]))
            height_offset += element.size[1] + self.margin

        self.size = (self.size[0], height_offset - self.margin)

    def set_size(self, size):
        self.size = size
        for e in self.elements:
            e.set_size((size[0], e.size[1]))

    def step(self):
        super().step()
        if self.scrollable and GUI.gui_scroll_event[1] != 0:
            self.pos = (self.pos[0], self.pos[1] + GUI.gui_scroll_event[1] * 50)
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

    def click(self):
        for element in self.elements:
            element.click()

    def no_click(self):
        for element in self.elements:
            element.no_click()


class Columns(StackPanel):
    """container for elements, elements are placed in a grid"""

    def __init__(self, cols):
        super().__init__()
        self.cols = cols
        self.current_index = [0, 0]
        self.hor_margin = 10
        self.ver_margin = 10

        self.element_size = (0, 0)
        self.debug_color = (255, 255, 0)

    def append(self, element):
        self.element_size = (
            max(self.element_size[0], element.size[0]),
            max(self.element_size[1], element.size[1]),
        )
        self.elements.append(element)
        element.parent = self

        x = 0
        y = 0

        size_x = 0
        size_y = 0
        for i, e in enumerate(self.elements):
            e.pos = (x, y)
            e.set_size(self.element_size)
            x += self.element_size[0] + self.hor_margin
            size_x = max(x, size_x)
            if (i + 1) % self.cols == 0:
                x = 0
                y += self.element_size[1] + self.ver_margin
                size_y = max(y, size_y)
        self.size = (size_x - self.hor_margin, size_y - self.ver_margin)

    def set_size(self, size):
        self.size = size


class ContextMenu(StackPanel):
    """container for elements, context menu will vanish after click"""

    def __init__(self, pos=(0, 0)):
        super().__init__()
        self.pos = pos
        self.elements = []
        self.size = (0, 0)

    def add_button(self, text, key):
        button = Button(text, key)
        button.parent = self
        self.append(button)

    def click(self):
        GUI.elements.remove(self)

    def no_click(self):
        GUI.elements.remove(self)


class Frame:
    """decorative frame for elements. envelops elements based on their size"""

    def __init__(self, json_path):
        with open(json_path, "r") as f:
            frame_dict = json.load(f)
        self.surf = pygame.image.load(frame_dict["path"])
        self.coords = frame_dict["coords"]

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

        top_left_pos = (
            element.pos[0] - top_left[1][0],
            element.pos[1] - top_left[1][1],
        )
        top_right_pos = (
            element.pos[0] + element.size[0],
            element.pos[1] - top_right[1][1],
        )
        bottom_left_pos = (
            element.pos[0] - bottom_left[1][0],
            element.pos[1] + element.size[1],
        )
        bottom_right_pos = (
            element.pos[0] + element.size[0],
            element.pos[1] + element.size[1],
        )

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
            (element.size[0], top[1][1]),
        )
        bottom_rect = (
            (element.pos[0], element.pos[1] + element.size[1]),
            (element.size[0], bottom[1][1]),
        )

        deco_left_pos = (
            element.pos[0] - deco_left[1][0],
            element.pos[1] + element.size[1] // 2 - deco_left[1][1] // 2,
        )
        deco_right_pos = (
            element.pos[0] + element.size[0],
            element.pos[1] + element.size[1] // 2 - deco_left[1][1] // 2,
        )
        deco_top_pos = (
            element.pos[0] + element.size[0] // 2 - deco_top[1][0] // 2,
            element.pos[1] - deco_top[1][1],
        )
        deco_bottom_pos = (
            element.pos[0] + element.size[0] // 2 - deco_bottom[1][0] // 2,
            element.pos[1] + element.size[1],
        )

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
            pygame.draw.rect(GUI.win, (255, 255, 255), (top_left_pos, top_left[1]), 1)
            pygame.draw.rect(GUI.win, (255, 255, 255), (top_right_pos, top_right[1]), 1)
            pygame.draw.rect(
                GUI.win, (255, 255, 255), (bottom_left_pos, bottom_left[1]), 1
            )
            pygame.draw.rect(
                GUI.win, (255, 255, 255), (bottom_right_pos, bottom_right[1]), 1
            )


class Picture(Element):
    """present surface"""

    def __init__(self, surf):
        super().__init__()
        self.surf = surf
        self.size = self.surf.get_size()

    def draw(self):
        pos = self.get_abs_pos()
        super().draw()
        GUI.win.blit(
            self.surf, (pos[0] + self.size[0] // 2 - self.surf.get_width() // 2, pos[1])
        )

class Drawer(Element):
    def __init__(self):
        super().__init__()
        # default to right
        width = 50
        self.pos = (GUI.win.get_width() - width, 0)
        self.size = (width, GUI.win.get_height())
        self.open = False
        self.element = None
        self.element_target_pos = (GUI.win.get_width(),0)
    def set_element(self, element):
        self.element = element
        self.element.set_pos(self.element_target_pos)
    def step(self):
        super().step()
        mouse_pos = pygame.mouse.get_pos()
        pos = self.get_abs_pos()
        if (
            mouse_pos[0] > pos[0]
            and mouse_pos[0] < pos[0] + self.size[0]
            and mouse_pos[1] > pos[1]
            and mouse_pos[1] < pos[1] + self.size[1]
        ):
            self.open = True
        if self.open:
            pass
        self.element.step()
    def draw(self):
        self.element.draw()



def test(event):
    print(event)


if __name__ == "__main__":
    pygame.init()

    winWidth = 1280
    winHeight = 720
    win = pygame.display.set_mode((winWidth, winHeight))

    ### setup
    GUI.win = win
    GUI.fonts.append(pygame.font.SysFont("Calibri", 16))
    # GUI.fonts.append(pygame.font.SysFont("Calibri", 16))
    GUI.gui_event_handler = test

    b = Button("free button", "free button")
    b.set_pos((400, 100))
    GUI.elements.append(b)
    b = TextBox("free button", "free textbox")
    b.set_pos((400, 120))
    GUI.elements.append(b)

    cm = StackPanel((200, 300))
    cm.append(Button("Enter First Name", "Enter First Name"))
    cm.append(Button("test2", "t2"))
    cm.append(Button("this is button", "t3"))
    cm.append(Button("test4", "t4"))
    cm.append(Button("test5", "t5"))
    GUI.elements.append(cm)

    cm = StackPanel((500, 200))
    cm.append(TextBox("name", "Enter First Name"))
    cm.append(TextBox("last", "Enter Last Name"))
    cm.append(TextBox("phone", "Enter Phone"))
    cm.append(TextBox("address", "Enter Address"))
    GUI.elements.append(cm)

    ### main loop

    run = True
    while run:
        for event in pygame.event.get():
            GUI.event_handle(event)
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                mouse_pos = pygame.mouse.get_pos()
                cm = ContextMenu(mouse_pos)
                cm.append(Button("test1", "t1"))
                cm.append(Button("test2", "t2"))
                cm.append(Button("this is button", "t3"))
                cm.append(Button("test4", "t4"))
                cm.append(Button("test5", "t5"))
                GUI.elements.append(cm)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            run = False

        win.fill((255, 255, 255))
        GUI.step()

        GUI.draw()

        pygame.display.update()
