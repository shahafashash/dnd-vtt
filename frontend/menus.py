''' this module's responsibility is to create gui menus '''

import pygame
from frontend.gui import *

class MenuManager:
    def __init__(self, config=None):
        self.current_menu = None
        self.map_menu = None
        self.config = config

    def set_config(self, config):
        self.config = config

    def create_loading_screen(self, win):
        cm = StackPanel()
        label_title = Label("LOADING...", GUI.get_font_at(2))
        cm.append(label_title)
        cm.pos = (
            win.get_width() // 2 - cm.size[0] // 2,
            win.get_height() // 2 - cm.size[1] // 2,
        )
        self.current_menu = cm
        cm.frame = GUI.frames[0]

        GUI.append(self.current_menu)


    def create_main_menu(self, win):
        GUI.elements.remove(self.current_menu)

        self.current_menu = Elements()

        cm = StackPanel()
        label_title = Label("DND VIRTUAL TABLE TOP", GUI.get_font_at(2))
        cm.append(label_title)
        label_credits = Label("By Shahaf Ashash and Simon Labunsky", GUI.get_font_at(0))
        cm.append(label_credits)
        cm.set_pos(
            (
                win.get_width() // 2 - cm.size[0] // 2,
                win.get_height() // 2 - cm.size[1] // 2 - 100,
            )
        )
        cm.frame = GUI.frames[0]
        self.current_menu.append(cm)

        button = Button("Start", "start", GUI.get_font_at(0), GUI.get_font_at(1))
        button.set_pos(
            (
                win.get_width() // 2 - button.size[0] // 2,
                win.get_height() // 2 - button.size[1] // 2 + 100,
            )
        )
        self.current_menu.append(button)

        GUI.append(self.current_menu)


    def create_columns_maps(self, found_maps) -> Columns:
        """create columns based on found map and return columns object"""
        thumbnail_columns = Columns(3)
        for map in found_maps:
            map_obj = self.config.get_map(map)
            thumbnail = map_obj.thumbnail
            thumbnail_stackpanel = StackPanel()
            thumbnail_stackpanel.append(Picture(thumbnail))
            button = Button(
                map, "change_map", GUI.get_font_at(3), GUI.get_font_at(4), custom_width=400
            )
            thumbnail_stackpanel.linked_button = button
            thumbnail_stackpanel.append(button)
            thumbnail_columns.append(thumbnail_stackpanel)
            thumbnail_columns.scrollable = True
        return thumbnail_columns


    def create_menu_maps(self, maps: list[str]):
        if self.current_menu and self.current_menu in GUI.elements:
            GUI.remove(self.current_menu)

        if self.map_menu:
            GUI.append(self.map_menu)
            self.current_menu = self.map_menu
            return

        self.current_menu = Elements()

        search_textbox = TextBox("search", "search for maps", GUI.get_font_at(0))
        thumbnail_columns = self.create_columns_maps(maps)

        search_textbox.set_pos(
            (GUI.win.get_width() // 2 - search_textbox.size[0] // 2, 100)
        )
        thumbnail_columns.set_pos(
            (GUI.win.get_width() // 2 - thumbnail_columns.size[0] // 2, 200)
        )

        self.current_menu.append(thumbnail_columns)
        self.current_menu.append(search_textbox)
        self.map_menu = self.current_menu

        GUI.append(self.current_menu)


    def create_menu_game(self, win):
        if self.current_menu and self.current_menu in GUI.elements:
            GUI.remove(self.current_menu)
            if self.current_menu.name == "game_menu":
                self.current_menu = None
                return

        font1 = GUI.get_font_at(0)
        font2 = GUI.get_font_at(1)

        stackPanel = StackPanel()
        stackPanel.append(Button("Map Menu", "map_menu", font1, font2))
        stackPanel.append(Button("Toggle Darkness", "toggle_darkness", font1, font2))
        stackPanel.append(Button("Add Map Tags", "add_tag_menu", font1, font2))
        stackPanel.append(Button("Exit", "exit", font1, font2))

        stackPanel.set_pos(
            (
                win.get_width() // 2 - stackPanel.size[0] // 2,
                win.get_height() // 2 - stackPanel.size[1] // 2,
            )
        )
        self.current_menu = stackPanel
        self.current_menu.name = "game_menu"
        GUI.append(stackPanel)


    def create_menu_add_tag(self, win):
        if self.current_menu and self.current_menu in GUI.elements:
            GUI.remove(self.current_menu)

        font1 = GUI.get_font_at(0)
        font2 = GUI.get_font_at(1)

        stackPanel = StackPanel()
        stackPanel.append(TextBox("new_tag", "Insert Tags Here", GUI.get_font_at(0)))
        stackPanel.append(Button("Add", "add_tags", font1, font2))

        stackPanel.set_pos(
            (
                win.get_width() // 2 - stackPanel.size[0] // 2,
                win.get_height() // 2 - stackPanel.size[1] // 2,
            )
        )
        self.current_menu = stackPanel
        GUI.append(stackPanel)