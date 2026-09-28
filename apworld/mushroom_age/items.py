from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification

from .game_constants import *

if TYPE_CHECKING:
    from .world import MushroomAgeWorld


class MushroomAgeItem(Item):
    game = "Mushroom Age"

def item_names_to_ids() -> dict[str, int]:
    items = {}

    items_to_check = KEY_ITEMS | KEY_QUESTS | KEY_PHONE_NUMBERS | TRAP_ITEMS
    for item in items_to_check.values():
        items[item["name"]] = item["id"]
    
    for i, item in enumerate(FILLER_ITEMS):
        items[item + FILLER_SUFFIX] = FILLER_ITEMS_ID + i

    return items


def get_random_filler_item_name(world: MushroomAgeWorld) -> str:
    if world.random.randint(0, 99) < world.options.trap_chance:
        trap = world.random.choice(list(TRAP_ITEMS.values()))["name"]
        return trap

    item = world.random.choice(FILLER_ITEMS)
    return item + FILLER_SUFFIX

def create_item_with_correct_classification(world: MushroomAgeWorld, name: str) -> MushroomAgeItem:
    classification = ItemClassification.filler
    item_id = FILLER_ITEMS_ID

    progress_items = KEY_ITEMS | KEY_QUESTS | KEY_PHONE_NUMBERS
    for item in progress_items.values():
        if name == item["name"]:
            if item.get("useful", False):
                classification = ItemClassification.useful
            else:
                classification = ItemClassification.progression
            item_id = item["id"]
    
    for item in TRAP_ITEMS.values():
        if name == item["name"]:
            classification = ItemClassification.trap
            item_id = item["id"]

    junk_name = name.removesuffix(FILLER_SUFFIX)
    if junk_name in FILLER_ITEMS:
        item_id += FILLER_ITEMS.index(junk_name)

    return MushroomAgeItem(name, classification, item_id, world.player)

def create_all_items(world: MushroomAgeWorld) -> None:
    item_pool = []

    all_items = KEY_ITEMS

    if world.options.phone_numbers: # if phone numbers are in the pool
        all_items |= KEY_PHONE_NUMBERS

    for item in all_items.values():
        item_pool.append(world.create_item(item["name"]))

    number_of_items = len(item_pool)
    number_of_unfilled_locations = len(world.multiworld.get_unfilled_locations(world.player))
    needed_number_of_filler_items = number_of_unfilled_locations - number_of_items
    item_pool.extend([world.create_filler() for _ in range(needed_number_of_filler_items)])

    world.multiworld.itempool += item_pool