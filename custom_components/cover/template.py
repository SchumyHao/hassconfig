"""
Support for cover which integrates with other components.
"""
import asyncio
import logging

from homeassistant.components.cover import (
    CoverDevice, SUPPORT_OPEN, SUPPORT_CLOSE, SUPPORT_SET_POSITION,
    ENTITY_ID_FORMAT)
from homeassistant.const import (
    ATTR_FRIENDLY_NAME, CONF_VALUE_TEMPLATE, STATE_OPEN, STATE_CLOSED,
    ATTR_ENTITY_ID, CONF_COVERS, EVENT_HOMEASSISTANT_START,
    CONF_DEVICE_CLASS)
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.script import Script
from homeassistant.helpers.entity import async_generate_entity_id

_LOGGER = logging.getLogger(__name__)

CLOSE_ACTION = 'close'
OPEN_ACTION = 'open'
SET_POSITION_ACTION = 'set_pos'

_VALID_POS = Range(min=0, max=100)

@asyncio.coroutine
# pylint: disable=unused-argument
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the Template covers."""
    covers = []

    for device, device_config in config[CONF_COVERS].items():
        friendly_name = device_config.get(ATTR_FRIENDLY_NAME, device)
        pos_template = device_config[CONF_VALUE_TEMPLATE]
        close_action = device_config[CLOSE_ACTION]
        open_action = device_config[OPEN_ACTION]
        set_pos_action = device_config[SET_POSITION_ACTION]
        device_class = device_config[CONF_DEVICE_CLASS]
        entity_ids = (device_config.get(ATTR_ENTITY_ID) or
                      state_template.extract_entities())

        supported_features = 0
        if close_action is not None:
            supported_features |= SUPPORT_CLOSE
        if open_action is not None:
            supported_features |= SUPPORT_OPEN
        if set_pos_action is not None:
            supported_features |= SUPPORT_SET_POSITION

        pos_template.hass = hass

        if supported_features is 0:
            _LOGGER.error("Got an invalid cover")
        else:
            covers.append(
                CoverTemplate(
                    hass, device, friendly_name,
                    close_action, open_action, set_pos_action,
                    pos_template,
                    device_class, supported_features, entity_ids)
                )

    if not covers:
        _LOGGER.error("No covers added")
        return False

    async_add_devices(covers, True)
    return True

class CoverTemplate(CoverDevice):
    """Representation of a template cover."""

    # pylint: disable=no-self-use
    def __init__(self, hass, device_id, name,
                 close_action, open_action, set_pos_action,
                 pos_template,
                 device_class=None, supported_features=None, entity_ids):
        """Initialize the cover."""
        self.hass = hass
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, device_id, hass=hass)
        self._name = name
        self._pos_template = pos_template
        self._device_class = device_class
        self._supported_features = supported_features
        if supported_features & SUPPORT_CLOSE:
            self._close = Script(hass, close_action)
        if supported_features & SUPPORT_OPEN:
            self._open = Script(hass, open_action)
        if supported_features & SUPPORT_SET_POSITION:
            self._set_position = Script(hass, set_pos_action)
        self._entities = entity_ids

        self._position = 50

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed for a demo cover."""
        return False

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        try:
            pos = self._pos_template.async_render().lower()

            if pos in _VALID_POS:
                self._position = pos
            else:
                _LOGGER.error(
                    'Received invalid cover position value: %d.',
                    pos)
                self._position = None

        except TemplateError as ex:
            _LOGGER.error(ex)
            self._position = None

        return self._position

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self.current_cover_position is not None:
            if self.current_cover_position > 0:
                return False
            else:
                return True

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._device_class

    @property
    def supported_features(self):
        """Flag supported features."""
        if self._supported_features is not None:
            return self._supported_features
        else:
            return super().supported_features

    def close_cover(self, **kwargs):
        """Close the cover."""
        if self._position == 0:
            return
        else:
            self._close.run()
            self.schedule_update_ha_state()
            return

    def open_cover(self, **kwargs):
        """Open the cover."""
        if self._position == 100:
            return
        else:
            self._open.run()
            self.schedule_update_ha_state()
            return

    def set_cover_position(self, position, **kwargs):
        """Move the cover to a specific position."""
        if self._position == position:
            return
        else:
            self._set_position.run()
            self.schedule_update_ha_state()
            return
