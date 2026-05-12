import random
from typing import List, Optional, Sequence, Tuple

import pygame

from engine import GameController, GameSession, GameState, Tile
from settings import SETTINGS
from ui.assets import AssetManager
from ui.renderer import GameRenderer
from ui.audio import AudioManager
from ui.screen import Screen


Color = Tuple[int, int, int]


class BaseScreen(Screen):
    def __init__(self, assets: Optional[AssetManager] = None, audio_manager: Optional[AudioManager] = None) -> None:
        self.assets = assets
        self.audio_manager = audio_manager

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
        if self.audio_manager:
            self.audio_manager.play_bgm("menu")

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

    def __init__(self, assets: Optional[AssetManager] = None, audio_manager: Optional[AudioManager] = None) -> None:
        super().__init__(assets, audio_manager)
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
        if self.audio_manager:
            self.audio_manager.play_bgm("menu")

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
        if self.audio_manager:
            self.audio_manager.play_bgm("menu")

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
        audio_manager: Optional[AudioManager] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
        self.game_controller = game_controller
        self.session = session
        self.renderer: Optional[GameRenderer] = None

        self.ingame_tracks = ["score1", "score2", "score3"]
        self.current_track = random.choice(self.ingame_tracks)

        if self.audio_manager:
            self.audio_manager.register_events(self.game_controller)

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
                if self.audio_manager:
                    self.audio_manager.play_sfx("position")
            elif event.key == pygame.K_RIGHT:
                self.game_controller.move_right()
                if self.audio_manager:
                    self.audio_manager.play_sfx("position")
            elif event.key == pygame.K_DOWN:
                self.game_controller.move_down()
                if self.audio_manager:
                    self.audio_manager.play_sfx("position")
            elif event.key == pygame.K_UP:
                self.game_controller.rotate()
                if self.audio_manager:
                    self.audio_manager.play_sfx("rotate")
            elif event.key == pygame.K_SPACE:
                self.game_controller.hard_drop()
        return None

    def update(self, delta_time: float) -> None:
        if self.session.state == GameState.RUNNING:
            if self.audio_manager:
                if self.audio_manager.current_bgm not in self.ingame_tracks:
                    self.current_track = random.choice(self.ingame_tracks)
                self.audio_manager.play_bgm(self.current_track)
            self.game_controller.update(delta_time)

    def render(self, surface: pygame.Surface) -> None:
        if self.renderer is None:
            self.renderer = GameRenderer(
                surface,
                self.assets,
                self.game_controller,
                self.session,
            )

        self.renderer.render()

        if self.session.state == GameState.GAME_OVER:
            self._draw_text(
                surface,
                "GAME OVER",
                28,
                (255, 102, 102),
                (SETTINGS.SCREEN.GAME_WIDTH // 2, 285),
            )




class PauseScreen(BaseScreen):
    def __init__(
        self,
        game_screen: GameScreen,
        assets: Optional[AssetManager] = None,
        audio_manager: Optional[AudioManager] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
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
                if self.game_screen.audio_manager:
                    self.game_screen.audio_manager.stop_bgm()
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
