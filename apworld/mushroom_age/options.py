from dataclasses import dataclass

from Options import Choice, OptionGroup, PerGameCommonOptions, Range, Toggle, DefaultOnToggle


class PhoneNumbers(DefaultOnToggle):
    """
    Whether certain areas are gated behind phone number items that need to be collected before reaching those areas.
    """

    display_name = "Use Phone Numbers"


class TrapChance(Range):
    """
    Percentage chance that any given filler item will be replaced by a trap item.
    """

    display_name = "Trap Chance"

    range_start = 0
    range_end = 100
    default = 0


@dataclass
class MushroomAgeOptions(PerGameCommonOptions):
    phone_numbers: PhoneNumbers
    trap_chance: TrapChance

option_groups = [
    OptionGroup(
        "Gameplay Options",
        [PhoneNumbers, TrapChance],
    ),
]