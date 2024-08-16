import eggsample


@eggsample.hookimpl
def eggsample_add_ingredients() -> list[str]:
    spices = ["salt", "pepper"]
    you_can_never_have_enough_eggs = ["egg", "egg"]
    ingredients = spices + you_can_never_have_enough_eggs
    return ingredients


@eggsample.hookimpl
def eggsample_prep_condiments(condiments: dict[str, int]) -> None:
    condiments["mint sauce"] = 1
