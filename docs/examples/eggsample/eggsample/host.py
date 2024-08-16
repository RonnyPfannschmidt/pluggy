import itertools
import random

from eggsample import hookspecs
from eggsample import lib

import pluggy


condiments_tray = {"pickled walnuts": 13, "steak sauce": 4, "mushy peas": 2}


def main() -> None:
    pm = get_plugin_manager()
    cook = EggsellentCook(pm.hook)
    cook.add_ingredients()
    cook.prepare_the_food()
    cook.serve_the_food()


def get_plugin_manager() -> pluggy.PluginManager:
    pm = pluggy.PluginManager("eggsample")
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints("eggsample")
    pm.register(lib)
    return pm


class EggsellentCook:
    FAVORITE_INGREDIENTS = ("egg", "egg", "egg")
    ingredients : list[str]
    def __init__(self, hook: pluggy.HookRelay) -> None:
        self.hook = hook
        self.ingredients = []

    def add_ingredients(self) -> None:
        results = self.hook.eggsample_add_ingredients(
            ingredients=self.FAVORITE_INGREDIENTS
        )
        my_ingredients = list(self.FAVORITE_INGREDIENTS)
        # Each hook returns a list - so we chain this list of lists
        other_ingredients = list(itertools.chain(*results))
        self.ingredients = my_ingredients + other_ingredients

    def prepare_the_food(self) -> None:
        random.shuffle(self.ingredients)

    def serve_the_food(self) -> None:
        condiment_comments = self.hook.eggsample_prep_condiments(
            condiments=condiments_tray
        )
        print(f"Your food. Enjoy some {', '.join(self.ingredients)}")
        print(f"Some condiments? We have {', '.join(condiments_tray.keys())}")
        if any(condiment_comments):
            print("\n".join(condiment_comments))


if __name__ == "__main__":
    main()
