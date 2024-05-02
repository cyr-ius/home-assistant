"""Creates a switch entity for the mower."""

from datetime import datetime, timedelta
import logging
from typing import Any, cast

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEntityFeature,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import AutomowerDataUpdateCoordinator
from .entity import AutomowerBaseEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up switch platform."""
    coordinator: AutomowerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerCalendarEntity(coordinator, mower_id) for mower_id in coordinator.data
    )


class AutomowerCalendarEntity(AutomowerBaseEntity, CalendarEntity):
    """Representation of the Automower Calendar element."""

    _attr_name: str | None = None
    _attr_supported_features = CalendarEntityFeature.UPDATE_EVENT

    def __init__(
        self, coordinator: AutomowerDataUpdateCoordinator, mower_id: str
    ) -> None:
        """Initialize AutomowerCalendar."""
        super().__init__(mower_id, coordinator)
        self._attr_unique_id = f"{self.mower_id}"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        _LOGGER.debug(self.mower_attributes.calendar.tasks)
        current_week_tasks = self.daterange(dt_util.start_of_local_day())
        for events in current_week_tasks:
            for event in events:
                start = cast(datetime, event["start"])
                end = cast(datetime, event["end"])
                if dt_util.now() > start and dt_util.now() < end:
                    return CalendarEvent(
                        start=start,
                        end=end,
                        summary=f'{event["work_area"]} - {event["cutting_height"]}%',
                        description=f'Mow the lawn in the {event["work_area"]} area',
                        location=event["work_area"],
                        uid=event["uid"],
                    )
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        calendar_events = []
        tasks = self.daterange(start_date, (end_date - start_date).days)
        for events in tasks:
            for event in events:
                start = cast(datetime, event["start"])
                end = cast(datetime, event["end"])
                calendar_events.append(
                    CalendarEvent(
                        start=start,
                        end=end,
                        summary=f'{event["work_area"]} - {event["cutting_height"]}%',
                        description=f'Mow the lawn in the {event["work_area"]} area',
                        location=event["work_area"],
                        uid=event["uid"],
                    )
                )
        return calendar_events

    def daterange(
        self, start_date: datetime, interval: int = 7
    ) -> list[list[dict[str, Any]]] | list:
        """Return current week."""
        periods: list[list[dict[str, Any]]] | list = []
        save_dt = start_date.date()
        attrs = self.mower_attributes
        for i, task in enumerate(attrs.calendar.tasks):
            work_area_id = int(task.work_area_id) if task.work_area_id else 0
            if isinstance(attrs.work_areas, dict):
                attrs_tsk = attrs.work_areas[work_area_id]
                period: list[dict[str, Any]] = []
                while start_date.date() < save_dt + timedelta(days=interval):
                    str_day = start_date.strftime("%A").lower()
                    if getattr(task, str_day) is True:
                        dt_start: datetime = start_date + timedelta(minutes=task.start)
                        dt_end: datetime = start_date + timedelta(
                            minutes=task.start + task.duration
                        )
                        period.append(
                            {
                                "day": start_date,
                                "start": dt_start,
                                "end": dt_end,
                                "work_area_id": work_area_id,
                                "work_area": attrs_tsk.name,
                                "cutting_height": attrs_tsk.cutting_height,
                                "uid": f"{i}#{work_area_id}#{str_day}",
                            }
                        )
                    start_date = start_date + timedelta(days=1)
                periods.append(period)
        return periods

    async def async_update_event(
        self,
        uid: str,
        event: dict[str, Any],
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        """Update an event on the calendar."""
        int_task, work_aera_id, _ = uid.split("#")
        int_work_aera_id = int(work_aera_id)

        # Force refresh  because mower_attributes not up to date
        self.coordinator.data = await self.coordinator.api.get_status()

        calendar = self.mower_attributes.calendar.tasks[int(int_task)]

        day = event["dtstart"].strftime("%A").lower()
        setattr(calendar, day, True)

        calendar.start = event["dtstart"].minute + event["dtstart"].hour * 60
        calendar.duration = int(
            (event["dtend"] - event["dtstart"]) / timedelta(seconds=60)
        )

        task_list = []
        for task in self.mower_attributes.calendar.tasks:
            my_task = task.to_dict().copy()
            my_task["workAreaId"] = my_task.pop("work_area_id", 0)
            task_list.append(my_task)

        await self.coordinator.api.set_calendar(
            self.mower_id, task_list, int_work_aera_id
        )
        await self.coordinator.async_request_refresh()
