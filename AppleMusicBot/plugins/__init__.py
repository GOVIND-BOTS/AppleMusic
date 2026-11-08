import glob
from os.path import dirname, isfile


def __list_all_modules():
    work_dir = dirname(__file__)
    mod_paths = glob.glob(work_dir + "/**/*.py", recursive=True)
    all_modules = [
        (
            f.replace(work_dir, "AppleMusicBot.plugins")
            .replace("/", ".")
            .replace("\\", ".")
            .replace(".py", "")
        )
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]
    return all_modules


ALL_MODULES = sorted(__list_all_modules())
__all__ = ALL_MODULES + ["ALL_MODULES"]
