"""
Support philips eyecare lamp.

Thank rytilahti for his great work
"""
import logging
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS,
    Light, PLATFORM_SCHEMA)

from homeassistant.const import CONF_NAME, CONF_HOST, CONF_TOKEN

REQUIREMENTS = ['python-miio==0.0.9']

_LOGGER = logging.getLogger(__name__)

SUPPORT_FEATURE = (SUPPORT_BRIGHTNESS)

LAMP_DEFAULT_NAME = 'philips_eyecare'

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the philips eyecare lamp platform."""
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME) or LAMP_DEFAULT_NAME
    token = config.get(CONF_TOKEN)

    add_devices([
        PhilipsEyecareLamp(hass, name, host, token),
    ])

class PhilipsEyecareLamp(Light):
    """A philips eyecare lamp component."""

    def __init__(self, hass, name: str, host, token) -> None:
        """Initialize the entity."""
        self.hass = hass
        self._name = name
        self._supported_features = SUPPORT_FEATURE
        self._brightness = None
        self._is_on = False
        self.host = host
        self.token = token
        self._lamp = None

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._supported_features

    @property
    def name(self) -> str:
        """Get entity name."""
        return self._name

    @property
    def should_poll(self) -> bool:
        """Polling needed for fan."""
        return True

    @property
    def is_on(self) -> bool:
        """Return true if the entity is on."""
        return self._is_on

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 1..255."""
        return self._brightness

    @property
    def lamp(self):
        import miio
        if not self._lamp:
            _LOGGER.info("initializing with host %s token %s" % (self.host, self.token))
            self._lamp = miio.device(self.host, self.token)
        return self._lamp

    @property
    def lamp_power(self) -> str:
        """lamp is power on or not."""
        prop = self.lamp.send("get_prop", ["power"])
        
        return prop[0]

    @property
    def lamp_bright(self) -> int:
        """lamp is power on or not."""
        prop = self.lamp.send("get_prop", ["bright"])
        
        return prop[0]

    def update(self) -> None:
        """Update properties from the lamp."""
        self._is_on = (getattr(self, 'lamp_power') == 'on')
        bright = getattr(self, 'lamp_bright')
        if bright:
            self._brightness = 255 * (bright / 100)

    def set_brightness(self, brightness, duration) -> None:
        """Set bulb brightness."""
        if brightness:
            _LOGGER.debug("Setting brightness: %s", brightness)
            bright = int(brightness / 255 * 100)
            self.lamp.send("set_bright", [bright])


    def turn_on(self, **kwargs) -> None:
        """Turn on the entity."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        self.lamp.send("set_power", ["on"])
        self.set_brightness(brightness, 0)
        self._is_on = True

    def turn_off(self, **kwargs) -> None:
        """Turn off."""
        self.lamp.send("set_power", ["off"])
