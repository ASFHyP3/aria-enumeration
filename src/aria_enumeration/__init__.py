from importlib.metadata import version

from .aria import AriaFrame, AriaProductGroup, does_product_exist, get_frame, get_frames, get_slcs, get_stack


__version__ = version(__name__)

__all__ = [
    '__version__',
    'AriaFrame',
    'AriaProductGroup',
    'get_frames',
    'get_frame',
    'get_stack',
    'get_slcs',
    'does_product_exist',
]
