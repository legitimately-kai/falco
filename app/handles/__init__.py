from os import listdir
from . import *

# i know this isn't the right way to do it but it works
__all__ = [p.split(".")[0] for p in listdir("./app/handles") if not p.startswith("__")]
__modules__ = [p.split(".")[0] for p in listdir("./app/handles") if not p.startswith("__")]