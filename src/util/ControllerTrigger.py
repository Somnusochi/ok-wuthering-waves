import ctypes
from ctypes import wintypes

from ok import Logger

logger = Logger.get_logger(__name__)

XINPUT_GAMEPAD_RIGHT_THUMB = 0x0080


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", wintypes.DWORD),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


class XInputStateReader:

    def __init__(self):
        self.xinput = self._load_xinput()

    def _load_xinput(self):
        if not hasattr(ctypes, "WinDLL"):
            logger.warning("XInput is only available on Windows; controller trigger is unavailable")
            return None
        for dll_name in ("xinput1_4.dll", "xinput9_1_0.dll", "xinput1_3.dll"):
            try:
                return ctypes.WinDLL(dll_name)
            except OSError:
                continue
        logger.warning("XInput dll not found; controller trigger is unavailable")
        return None

    def __call__(self):
        if self.xinput is None:
            return 0
        state = XINPUT_STATE()
        for user_index in range(4):
            result = self.xinput.XInputGetState(user_index, ctypes.byref(state))
            if result == 0:
                return int(state.Gamepad.wButtons)
        return 0


class ControllerTrigger:

    button_masks = {
        "R3": XINPUT_GAMEPAD_RIGHT_THUMB,
    }

    def __init__(self, state_reader=None):
        self.state_reader = state_reader
        self.last_buttons = 0

    def consume_pressed(self, trigger_name):
        mask = self.button_masks.get(trigger_name)
        if not mask:
            return False
        if self.state_reader is None:
            self.state_reader = XInputStateReader()
        buttons = self.state_reader()
        pressed = bool(buttons & mask)
        was_pressed = bool(self.last_buttons & mask)
        self.last_buttons = buttons
        return pressed and not was_pressed
