""" this module's responsibility is to create gui menus """

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
        label_title = Label("LOADING...", GUI.get_font_at(1))
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
        label_title = Label("DND VIRTUAL TABLE TOP", GUI.get_font_at(1))
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

        button = Button("Start", "start", GUI.get_font_at(0))
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

        # create columns
        thumbnail_columns = Columns(cols=3)
        for map in found_maps:
            map_obj = self.config.get_map(map)
            thumbnail = map_obj.thumbnail
            # inside columns: create stackpanel per map
            thumbnail_stackpanel = StackPanel()
            # inside stackpanel: elements
            elements = Elements()
            picture = Picture(thumbnail)
            picture.use_parents_size = True
            elements.append(picture)
            favorite_button = CheckBoxStar('favorited')
            favorite_button.event["map_name"] = map
            if map_obj.favorite:
                favorite_button.checked = True
            elements.append(favorite_button)

            elements.set_size(elements.elements[0].size)
            thumbnail_stackpanel.append(elements)
            button = Button(
                map,
                "change_map",
                GUI.get_font_at(2),
                custom_width=400,
            )
            thumbnail_stackpanel.linked_button = button
            thumbnail_stackpanel.append(button)
            thumbnail_columns.append(thumbnail_stackpanel)
            thumbnail_columns.scrollable = True
            thumbnail_columns.scroll_limit_upper = 200
        return thumbnail_columns

    def create_menu_maps(self, maps: list[str]):
        if self.current_menu and self.current_menu in GUI.elements:
            GUI.remove(self.current_menu)

        if self.map_menu:
            GUI.append(self.map_menu)
            self.current_menu = self.map_menu
            return

        self.current_menu = Elements()

        search_textbox = TextBox("search", "search for maps", GUI.get_font_at(0), 600)
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

        button_width = 450

        stackPanel = StackPanel()
        stackPanel.append(Button("Map Menu", "map_menu", font1, button_width))
        stackPanel.append(Button("Toggle Darkness", "toggle_darkness", font1, button_width))
        stackPanel.append(Button("Color Filters", "color_filter", font1, button_width))
        stackPanel.append(Button("Insert Token", "token_menu", font1, button_width))
        stackPanel.append(Button("Add Map Tags", "add_tag_menu", font1, button_width))
        stackPanel.append(Button("Rename Map", "add_rename_map_menu", font1, button_width))
        stackPanel.append(Button("Exit", "exit", font1, button_width))

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

        stackPanel = StackPanel()
        stackPanel.append(TextBox("new_tag", "Insert Tags Here", GUI.get_font_at(0)))
        stackPanel.append(Button("Add", "add_tags", font1))

        stackPanel.set_pos(
            (
                win.get_width() // 2 - stackPanel.size[0] // 2,
                win.get_height() // 2 - stackPanel.size[1] // 2,
            )
        )
        self.current_menu = stackPanel
        GUI.append(stackPanel)

    def create_menu_rename_map(self, win):
        if self.current_menu and self.current_menu in GUI.elements:
            GUI.remove(self.current_menu)

        font1 = GUI.get_font_at(0)

        stackPanel = StackPanel()
        stackPanel.append(
            TextBox("new_name", "Insert New Name Here", GUI.get_font_at(0))
        )
        stackPanel.append(Button("Confirm", "rename_map", font1))

        stackPanel.set_pos(
            (
                win.get_width() // 2 - stackPanel.size[0] // 2,
                win.get_height() // 2 - stackPanel.size[1] // 2,
            )
        )
        self.current_menu = stackPanel
        GUI.append(stackPanel)

    def create_filters_menu(self, win):
        if self.current_menu and self.current_menu in GUI.elements:
            GUI.remove(self.current_menu)

        font1 = GUI.get_font_at(0)

        stackPanel = StackPanel()
        button_stack = StackPanel(orientation=StackPanel.HORIZONTAL)
        check = CheckBox("fileter_check_avernus")
        label = Label("Avernus", font1)
        button_stack.append(check)
        button_stack.append(label)
        stackPanel.append(button_stack)

        button_stack = StackPanel(orientation=StackPanel.HORIZONTAL)
        check = CheckBox("fileter_check_mexico")
        label = Label("Mexico", font1)
        button_stack.append(check)
        button_stack.append(label)
        stackPanel.append(button_stack)

        button_stack = StackPanel(orientation=StackPanel.HORIZONTAL)
        check = CheckBox("fileter_check_matrix")
        label = Label("Matrix", font1)
        button_stack.append(check)
        button_stack.append(label)
        stackPanel.append(button_stack)

        stackPanel.set_pos(
            (
                win.get_width() // 2 - stackPanel.size[0] // 2,
                win.get_height() // 2 - stackPanel.size[1] // 2,
            )
        )
        self.current_menu = stackPanel
        GUI.append(stackPanel)

    def create_menu_tokens(self, win, available_tokens):
        if self.current_menu and self.current_menu in GUI.elements:
            GUI.remove(self.current_menu)

        # create columns
        token_columns = Columns(cols=3)

        for token in available_tokens:
            thumbnail = token['thumbnail']
            # inside columns: create stackpanel per map
            thumbnail_stackpanel = StackPanel()
            # inside stackpanel: elements
            picture = Picture(thumbnail)
            picture.use_parents_size = True
            thumbnail_stackpanel.append(picture)
            button = Button(
                token['name'],
                "insert_token",
                GUI.get_font_at(2),
                custom_width=400,
            )
            button.event['token'] = token
            thumbnail_stackpanel.linked_button = button
            thumbnail_stackpanel.append(button)
            token_columns.append(thumbnail_stackpanel)
            token_columns.scrollable = True
            token_columns.scroll_limit_upper = 200

        token_columns.set_pos(
            (
            win.get_width() // 2 - token_columns.size[0] // 2,
            win.get_height() // 2 - token_columns.size[1] // 2,
            )
        )
        self.current_menu = token_columns
        GUI.append(token_columns)
        