from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Entrance, Region

from .game_constants import *

if TYPE_CHECKING:
    from .world import MushroomAgeWorld


def create_and_connect_regions(world: MushroomAgeWorld) -> None:
    create_all_regions(world)
    connect_regions(world)

def create_all_regions(world: MushroomAgeWorld) -> None:
    time_period_names = [time_period["name"] for time_period in TIME_PERIODS.values()]
    regions = [Region(name, world.player, world.multiworld) for name in ["Title Screen"] + time_period_names]

    world.multiworld.regions += regions

def connect_regions(world: MushroomAgeWorld) -> None:
    title_screen = world.get_region("Title Screen")

    for time_period in TIME_PERIODS.values():
        time_period_name = time_period["name"]
        title_screen.connect(world.get_region(time_period_name), f"Title Screen to {time_period_name}")