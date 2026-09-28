from collections.abc import Mapping
from typing import Any, ClassVar

from worlds.AutoWorld import World

from . import items, locations, regions, rules, web_world
from . import options as mushroom_age_options

class MushroomAgeWorld(World):
    """
    Mushroom Age is an I-Spy Point-and-Click adventure game about time travel.
    """

    game = "Mushroom Age"

    web = web_world.MushroomAgeWebWorld()

    options_dataclass = mushroom_age_options.MushroomAgeOptions
    options: mushroom_age_options.MushroomAgeOptions

    location_name_to_id = locations.location_names_to_ids()
    item_name_to_id = items.item_names_to_ids()

    origin_region_name = "Title Screen"

    def create_regions(self) -> None:
        regions.create_and_connect_regions(self)
        locations.create_all_locations(self)
    
    def set_rules(self) -> None:
        rules.set_all_rules(self)

    def create_items(self) -> None:
        items.create_all_items(self)

    def create_item(self, name: str) -> items.MushroomAgeItem:
        return items.create_item_with_correct_classification(self, name)

    def get_filler_item_name(self) -> str:
        return items.get_random_filler_item_name(self)

    def fill_slot_data(self) -> Mapping[str, Any]:
        return {
            "gate_dict": rules.create_gate_dict(None)
        }