from typing import List, Optional, Sequence, Tuple

import pygame

from engine import GameController, GameSession, GameState, Tile
from settings import SETTINGS
from ui.assets import AssetManager
from ui.screen import Screen


Color = Tuple[int, int, int]


class BaseScreen(Screen):
    def __init__(self, assets: Optional[AssetManager] = None) -> None:
        self.assets = assets

    def _font(self, size: int) -> pygame.font.Font:
        if self.assets is not None:
            try:
                return self.assets.get_font(size)
            except (KeyError, FileNotFoundError, pygame.error):
                pass
        return pygame.font.Font(None, size)

    def _draw_text(
        self,
        surface: pygame.Surface,
        text: str,
        size: int,
        color: Color,
        center: Tuple[int, int],
    ) -> None:
        rendered = self._font(size).render(text, True, color)
        surface.blit(rendered, rendered.get_rect(center=center))


class TitleScreen(BaseScreen):
    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                return "menu"
        return None

    def update(self, delta_time: float) -> None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((14, 18, 28))
        logo_drawn = False

        if self.assets is not None:
            try:
                logo = self.assets.get_image("logo")
                logo_rect = logo.get_rect(center=(surface.get_width() // 2, 170))
                surface.blit(logo, logo_rect)
                logo_drawn = True
            except (KeyError, FileNotFoundError, pygame.error):
                logo_drawn = False

        if not logo_drawn:
            self._draw_text(
                surface,
                SETTINGS.APP_NAME,
                32,
                (242, 244, 248),
                (surface.get_width() // 2, 170),
            )

        self._draw_text(
            surface,
            "PRESS START",
            24,
            (255, 221, 87),
            (surface.get_width() // 2, 360),
        )


class MenuScreen(BaseScreen):
    OPTIONS: Sequence[Tuple[str, str]] = (
        ("Jogar", "game"),
        ("Ranking", "ranking"),
        ("Sair", "quit"),
    )

    def __init__(self, assets: Optional[AssetManager] = None) -> None:
        super().__init__(assets)
        self.selected_index = 0

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.OPTIONS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.OPTIONS[self.selected_index][1]
            elif event.key == pygame.K_ESCAPE:
                return "quit"
        return None

    def update(self, delta_time: float) -> None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((18, 22, 31))
        self._draw_text(
            surface,
            SETTINGS.APP_NAME,
            32,
            (242, 244, 248),
            (surface.get_width() // 2, 120),
        )

        start_y = 260
        for index, (label, _) in enumerate(self.OPTIONS):
            color = (255, 221, 87) if index == self.selected_index else (205, 213, 224)
            prefix = "> " if index == self.selected_index else "  "
            self._draw_text(
                surface,
                f"{prefix}{label}",
                24,
                color,
                (surface.get_width() // 2, start_y + index * 58),
            )


class RankingScreen(BaseScreen):
    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                return "menu"
        return None

    def update(self, delta_time: float) -> None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((18, 22, 31))
        self._draw_text(
            surface,
            "RANKING",
            32,
            (242, 244, 248),
            (surface.get_width() // 2, 150),
        )
        self._draw_text(
            surface,
            "Em breve",
            20,
            (205, 213, 224),
            (surface.get_width() // 2, 270),
        )


class GameScreen(BaseScreen):
    def __init__(
        self,
        game_controller: GameController,
        session: GameSession,
        assets: Optional[AssetManager] = None,
    ) -> None:
        super().__init__(assets)
        self.game_controller = game_controller
        self.session = session

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                self.session.pause()
                return "pause"
            if self.session.state != GameState.RUNNING:
                continue
            if event.key == pygame.K_LEFT:
                self.game_controller.move_left()
            elif event.key == pygame.K_RIGHT:
                self.game_controller.move_right()
            elif event.key == pygame.K_DOWN:
                self.game_controller.move_down()
            elif event.key == pygame.K_UP:
                self.game_controller.rotate()
            elif event.key == pygame.K_SPACE:
                self.game_controller.hard_drop()
        return None

    def update(self, delta_time: float) -> None:
        if self.session.state == GameState.RUNNING:
            self.game_controller.update(delta_time)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((10, 14, 22))
        self._draw_board(surface)
        self._draw_active_piece(surface)
        self._draw_hud(surface)

        if self.session.state == GameState.GAME_OVER:
            self._draw_text(
                surface,
                "GAME OVER",
                28,
                (255, 102, 102),
                (SETTINGS.SCREEN.GAME_WIDTH // 2, 285),
            )

    def _draw_board(self, surface: pygame.Surface) -> None:
        tile_size = SETTINGS.SCREEN.TILE_SIZE
        board_rect = pygame.Rect(
            0,
            0,
            SETTINGS.SCREEN.GAME_WIDTH,
            SETTINGS.SCREEN.GAME_HEIGHT,
        )
        pygame.draw.rect(surface, (24, 30, 42), board_rect)

        for y, row in enumerate(self.game_controller.board.grid):
            for x, tile in enumerate(row):
                self._draw_tile(surface, tile, x, y)

        for x in range(SETTINGS.SCREEN.GRID_WIDTH + 1):
            pygame.draw.line(
                surface,
                (37, 45, 61),
                (x * tile_size, 0),
                (x * tile_size, SETTINGS.SCREEN.GAME_HEIGHT),
            )
        for y in range(SETTINGS.SCREEN.GRID_HEIGHT + 1):
            pygame.draw.line(
                surface,
                (37, 45, 61),
                (0, y * tile_size),
                (SETTINGS.SCREEN.GAME_WIDTH, y * tile_size),
            )

    def _draw_active_piece(self, surface: pygame.Surface) -> None:
        piece = self.game_controller.current_piece
        if piece is None:
            return

        for x, y in piece.get_occupied_places():
            if y >= 0:
                self._draw_tile(surface, piece.tile, x, y)

    def _draw_tile(self, surface: pygame.Surface, tile: Tile, x: int, y: int) -> None:
        if tile == Tile.EMPTY:
            return

        tile_size = SETTINGS.SCREEN.TILE_SIZE
        rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)

        if self.assets is not None:
            try:
                surface.blit(self.assets.get_tile_surface(tile), rect)
                return
            except (KeyError, FileNotFoundError, pygame.error):
                pass

        color = SETTINGS.TILE_COLORS.get_tile_info(tile).color
        pygame.draw.rect(surface, color, rect.inflate(-2, -2), border_radius=3)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        left = SETTINGS.SCREEN.GAME_WIDTH + 24
        self._draw_text(surface, "SCORE", 16, (159, 173, 189), (left + 76, 70))
        self._draw_text(surface, str(self.session.score), 20, (242, 244, 248), (left + 76, 105))
        self._draw_text(surface, "LEVEL", 16, (159, 173, 189), (left + 76, 170))
        self._draw_text(surface, str(self.session.level), 20, (242, 244, 248), (left + 76, 205))
        self._draw_text(surface, "LINES", 16, (159, 173, 189), (left + 76, 270))
        self._draw_text(surface, str(self.session.total_lines), 20, (242, 244, 248), (left + 76, 305))


class PauseScreen(BaseScreen):
    def __init__(
        self,
        game_screen: GameScreen,
        assets: Optional[AssetManager] = None,
    ) -> None:
        super().__init__(assets)
        self.game_screen = game_screen

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                self.game_screen.session.resume()
                return "game"
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.game_screen.session.resume()
                return "game"
            if event.key == pygame.K_q:
                self.game_screen.session.reset()
                return "menu"
        return None

    def update(self, delta_time: float) -> None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        self.game_screen.render(surface)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        self._draw_text(
            surface,
            "PAUSE",
            32,
            (242, 244, 248),
            (surface.get_width() // 2, 250),
        )
        self._draw_text(
            surface,
            "ENTER para voltar",
            16,
            (255, 221, 87),
            (surface.get_width() // 2, 315),
        )
