from pathlib import Path
from backend.serializers import GameState, GameSerializer
from main import GameManager, Grid, GridColors, Event, GameEvent


class GameSaveHandler:
    def __init__(self) -> None:
        self.__save_dir = str(Path(__file__).parent.joinpath("saves").resolve())

    def __create_game_state(self) -> GameState:
        game = GameManager.get_instance()
        current_map = game.current_map
        grid_size = game.grid_size
        grid_state = game.grid_state
        grid_color = game.grid_color
        game_state = GameState(current_map, grid_size, grid_state, grid_color)
        return game_state

    def save(self, save_name: str) -> None:
        game_state = self.__create_game_state()
        data = GameSerializer.serialize(game_state)
        save_path = Path(self.__save_dir).joinpath(save_name).resolve()
        with open(save_path, "wb") as save_file:
            save_file.write(data)

    def load(self, save_name: str) -> None:
        game = GameManager.get_instance()
        save_path = Path(self.__save_dir).joinpath(save_name).resolve()
        with open(save_path, "rb") as save_file:
            data = save_file.read()
        game_state = GameSerializer.deserialize(data)

        # restore the grid size
        game.grid_size = game_state.grid_size
        # restore the grid state
        while game.grid_state != game_state.grid_state:
            game.grid_state = next(game.grid_states)
        # restore the grid color
        while game.grid_color != game_state.grid_color:
            game.grid_color = next(game.grid_colors)
        # restore the current map
        game.add_event(GameEvent(Event.CHANGE_MAP, game_state.current_map))
