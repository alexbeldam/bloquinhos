from dataclasses import dataclass
from enum import Enum
from queue import Queue
from typing import TYPE_CHECKING

from engine.tile import Tetromino
from settings import SETTINGS
from ui.assets import AssetManager

if TYPE_CHECKING:
    from service_container import ServiceContainer


class AssetType(Enum):
    MIXER_INIT = "mixer_init"
    IMAGE = "image"
    SFX = "sfx"
    MUSIC = "music"
    FONT = "font"
    TILE = "tile"


@dataclass
class WorkItem:
    asset_type: AssetType
    data: str | int | Tetromino | None
    progress_value: int


class LoadingPipeline:
    def __init__(
        self,
        skip_font_sizes: set[int] | None = None,
        skip_image_files: set[str] | None = None,
    ) -> None:
        self._work_queue: Queue[WorkItem] = Queue()
        self._skip_font_sizes = skip_font_sizes or set()
        self._skip_image_files = skip_image_files or set()

    def has_pending_work(self) -> bool:
        return not self._work_queue.empty()

    def get_next_work_item(self) -> WorkItem:
        return self._work_queue.get_nowait()

    def prepare_asset_work_items(self, assets: AssetManager) -> int:
        asset_files = assets.list_asset_files()
        img_files = asset_files["images"]
        wav_files = asset_files["sfx"]
        ogg_files = asset_files["music"]
        font_sizes = asset_files["fonts"]
        tiles = asset_files["tiles"]

        queued_img_files = [filename for filename in img_files if filename not in self._skip_image_files]
        queued_font_sizes = [size for size in font_sizes if size not in self._skip_font_sizes]

        total_assets = 1 + len(queued_img_files) + len(wav_files) + len(ogg_files) + len(queued_font_sizes) + len(tiles)

        current_item = 0

        current_item += 1
        progress = 45 + int((current_item / total_assets) * 55)
        self._work_queue.put(WorkItem(AssetType.MIXER_INIT, None, progress))

        for img in queued_img_files:
            current_item += 1
            progress = 45 + int((current_item / total_assets) * 55)
            self._work_queue.put(WorkItem(AssetType.IMAGE, img, progress))

        for wav in wav_files:
            current_item += 1
            progress = 45 + int((current_item / total_assets) * 55)
            self._work_queue.put(WorkItem(AssetType.SFX, wav, progress))

        for ogg in ogg_files:
            current_item += 1
            progress = 45 + int((current_item / total_assets) * 55)
            self._work_queue.put(WorkItem(AssetType.MUSIC, ogg, progress))

        for size in queued_font_sizes:
            current_item += 1
            progress = 45 + int((current_item / total_assets) * 55)
            self._work_queue.put(WorkItem(AssetType.FONT, size, progress))

        for tile in tiles:
            current_item += 1
            progress = 45 + int((current_item / total_assets) * 55)
            self._work_queue.put(WorkItem(AssetType.TILE, tile, progress))

        return total_assets

    @staticmethod
    def process_work_item(item: WorkItem, services: 'ServiceContainer', assets: AssetManager) -> None:
        if item.asset_type == AssetType.MIXER_INIT:
            services.audio_manager.initialize_mixer()
        elif item.asset_type == AssetType.IMAGE:
            assets.load_and_register_image(item.data)
        elif item.asset_type == AssetType.SFX:
            assets.load_and_register_sfx(item.data)
        elif item.asset_type == AssetType.MUSIC:
            assets.register_music_path(item.data)
        elif item.asset_type == AssetType.FONT:
            assets.load_and_register_font(item.data)
        elif item.asset_type == AssetType.TILE:
            assets.load_and_register_tile(item.data)
