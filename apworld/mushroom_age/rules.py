from __future__ import annotations

import operator
from functools import reduce
from typing import TYPE_CHECKING

from rule_builder.options import OptionFilter
from rule_builder.rules import Has, HasAll, Rule

from .game_constants import *

if TYPE_CHECKING:
    from .world import MushroomAgeWorld


def set_all_rules(world: MushroomAgeWorld) -> None:
    set_all_location_rules(world)
    set_completion_condition(world)

def set_all_location_rules(world: MushroomAgeWorld) -> None:
    create_gate_dict(world)

def create_gate_dict(world = None):
    gatekeepers = KEY_ITEMS | KEY_QUESTS | KEY_PHONE_NUMBERS
    gate_dict = {}
    name_or_id = "name" if world is not None else "id"

    for period in TIME_PERIODS.values():
        gates = []
        for chapter in period["chapters"]:
            for task in TASK_IDS:
                if chapter != task[0]: continue

                for gatekeeper_key, gatekeeper_dict in gatekeepers.items():
                    if task in gatekeeper_dict["gates"]:
                        pool_name = gatekeeper_dict.get("pool_name")
                        if pool_name is not None:
                            count = PROGRESSION_ITEMS[pool_name].index(gatekeeper_key) + 1
                            gates.append([gatekeeper_dict[name_or_id], count])
                        else:
                            gates.append([gatekeeper_dict[name_or_id], 1])

                rules_list = []

                if len(gates) == 0:
                    if world is not None:
                        continue

                if world is not None: # if setting locations for world
                    for rule in gates:
                        rules_list.append(Has(rule[0], count = rule[1]))
                else: # if returning a dict
                    gate_dict[(task[0] - 1) * 100 + (task[1] - 1)] = list(gates)
                    continue

                rule = reduce(operator.and_, rules_list)

                location = world.get_location(LOCATION_NAME_STRING.format(*task))
                world.set_rule(location, rule)

                if task in BONUS_ITEM_TASKS:
                    location = world.get_location(LOCATION_NAME_STRING_BONUS.format(*task))
                    world.set_rule(location, rule)
    
    if world is None:
        return gate_dict

def set_completion_condition(world: MushroomAgeWorld) -> None:
    world.set_completion_rule(Has(KEY_QUESTS["victory"]["name"]))