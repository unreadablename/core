"""YoLink BinarySensor."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from yolink.device import YoLinkDevice

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_COORDINATOR, ATTR_DEVICE_DOOR_SENSOR, DOMAIN
from .coordinator import YoLinkCoordinator
from .entity import YoLinkEntity


@dataclass
class YoLinkBinarySensorEntityDescription(BinarySensorEntityDescription):
    """YoLink BinarySensorEntityDescription."""

    exists_fn: Callable[[YoLinkDevice], bool] = lambda _: True
    value: Callable[[str], bool | None] = lambda _: None


SENSOR_DEVICE_TYPE = [ATTR_DEVICE_DOOR_SENSOR]

SENSOR_TYPES: tuple[YoLinkBinarySensorEntityDescription, ...] = (
    YoLinkBinarySensorEntityDescription(
        key="state",
        icon="mdi:door",
        device_class=BinarySensorDeviceClass.DOOR,
        name="state",
        value=lambda value: value == "open",
        exists_fn=lambda device: device.device_type in [ATTR_DEVICE_DOOR_SENSOR],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up YoLink Sensor from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][ATTR_COORDINATOR]
    sensor_devices = [
        device
        for device in coordinator.yl_devices
        if device.device_type in SENSOR_DEVICE_TYPE
    ]
    entities = []
    for sensor_device in sensor_devices:
        for description in SENSOR_TYPES:
            if description.exists_fn(sensor_device):
                entities.append(
                    YoLinkBinarySensorEntity(coordinator, description, sensor_device)
                )
    async_add_entities(entities)


class YoLinkBinarySensorEntity(YoLinkEntity, BinarySensorEntity):
    """YoLink Sensor Entity."""

    entity_description: YoLinkBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: YoLinkCoordinator,
        description: YoLinkBinarySensorEntityDescription,
        device: YoLinkDevice,
    ) -> None:
        """Init YoLink Sensor."""
        super().__init__(coordinator, device)
        self.entity_description = description
        self._attr_unique_id = f"{device.device_id} {self.entity_description.key}"
        self._attr_name = f"{device.device_name} ({self.entity_description.name})"

    @callback
    def update_entity_state(self, state: dict) -> None:
        """Update HA Entity State."""
        self._attr_is_on = self.entity_description.value(
            state[self.entity_description.key]
        )
        self.async_write_ha_state()