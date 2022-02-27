"""The onkyo constants."""
from homeassistant.components.media_player.const import (
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_SELECT_SOUND_MODE,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)

DOMAIN = "onkyo"

ATTR_AUDIO_INFORMATION = "audio_information"
ATTR_HDMI_OUTPUT = "hdmi_output"
ATTR_PRESET = "preset"
ATTR_VIDEO_INFORMATION = "video_information"
ATTR_VIDEO_OUT = "video_out"
PLATFORMS = ["media_player"]
CONF_MAX_VOLUME = "max_volume"
CONF_RECEIVER_MAX_VOLUME = "receiver_max_volume"
CONF_SOURCES = "sources"
CONF_SOUNDS_MODE = "sounds_mode"
DEFAULT_NAME = "Onkyo Receiver"
DEFAULT_PLAYABLE_SOURCES = ("fm", "am", "tuner")
DEFAULT_RECEIVER_MAX_VOLUME = 80
SERVICE_SELECT_HDMI_OUTPUT = "select_hdmi_output"
SUPPORTED_MAX_VOLUME = 100
TIMEOUT_MESSAGE = "Timeout waiting for response."
UNKNOWN_MODEL = "unknown-model"
SUPPORT_ONKYO = (
    SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_VOLUME_STEP
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_PLAY
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_SELECT_SOUND_MODE
)
SUPPORT_ONKYO_WO_VOLUME = (
    SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_PLAY
    | SUPPORT_PLAY_MEDIA
)
DEFAULT_SOURCES_SELECTED: list[str] = []
DEFAULT_SOUNDS_MODE_SELECTED: list[str] = []
ACCEPTED_VALUES = [
    "no",
    "analog",
    "yes",
    "out",
    "out-sub",
    "sub",
    "hdbaset",
    "both",
    "up",
]
