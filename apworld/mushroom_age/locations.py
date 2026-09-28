from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import ItemClassification, Location

from . import items
from .game_constants import *

if TYPE_CHECKING:
    from .world import MushroomAgeWorld


class MushroomAgeLocation(Location):
    game = "Mushroom Age"

def location_names_to_ids() -> dict[str, int | None]:
    locations = get_location_names_with_ids([{"task_id": task_id, "offset": 0, "string": LOCATION_NAME_STRING} for task_id in TASK_IDS])
    locations |= get_location_names_with_ids([{"task_id": task_id, "offset": 1, "string": LOCATION_NAME_STRING_BONUS} for task_id in BONUS_ITEM_TASKS])

    return locations


def get_location_names_with_ids(location_dicts: list[dict]) -> dict[str, int | None]:
    return_dict = {}

    for location in location_dicts:
        location_id = (location["task_id"][0]) * 1000 + (location["task_id"][1] * 10)
        return_dict[location["string"].format(*location["task_id"])] = location_id + location["offset"]

    return return_dict


def create_all_locations(world: MushroomAgeWorld) -> None:
    create_regular_locations(world)
    create_events(world)

def create_regular_locations(world: MushroomAgeWorld) -> None:
    for time_period in TIME_PERIODS.values():
        region = world.get_region(time_period["name"])

        locations = get_location_names_with_ids(
            [{"task_id": task_id, "offset": 0, "string": LOCATION_NAME_STRING} for task_id in (
                t for t in TASK_IDS if t[0] in set(time_period["chapters"])
            )]
        )

        locations |= get_location_names_with_ids(
            [{"task_id": task_id, "offset": 1, "string": LOCATION_NAME_STRING_BONUS} for task_id in (
                t for t in BONUS_ITEM_TASKS if t[0] in set(time_period["chapters"])
            )]
        )

        region.add_locations(locations, MushroomAgeLocation)

def create_events(world: MushroomAgeWorld) -> None:
    for quest in KEY_QUESTS.values():
        quest_item = items.MushroomAgeItem(quest["name"], ItemClassification.progression, quest["id"], world.player)
        location = world.get_location(LOCATION_NAME_STRING.format(*quest["task"]))

        location.place_locked_item(quest_item)