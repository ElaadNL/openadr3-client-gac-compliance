"""Module which implements GAC compliance validators for the event OpenADR3 types."""

from openadr3_client.models.model import ValidatorRegistry, Model as ValidatorModel
from openadr3_client.models.event.event import Event

@ValidatorRegistry.register(Event, ValidatorModel())
def continuous_or_seperated(self: Event) -> Event:
    """Enforces that events either have consistent interval definitions compliant with GAC.
    
    the Grid aware charging (GAC) specification allows for two types of (mutually exclusive)
    interval definitions:

    1. Continuous
    2. Seperated

    The continious implementation can be used when all intervals have the same duration.
    In this case, only the top-level intervalPeriod of the event can be used, and the intervalPeriods
    of the individual intervals must be None.

    In the seperated intervalDefinition approach, the intervalPeriods must be set on each individual intervals,
    and the top-level intervalPeriod of the event must be None. This seperated approach is used when events have differing
    durations.
    """
    intervals = self.intervals or ()

    if self.interval_period is None:
        # interval period not set at top level of the event.
        # Ensure that all intervals have the interval_period defined, to comply with the GAC specification.
        undefined_intervals_period = [
            i for i in intervals if i.interval_period is None
        ]
        if undefined_intervals_period:
            raise ValueError(
                "Either 'interval_period' must be set on the event once, or every interval must have its own 'interval_period'."
            )
    else:
        # interval period set at top level of the event.
        # Ensure that all intervals do not have the interval_period defined, to comply with the GAC specification.
        duplicate_interval_period = [
            i for i in intervals if i.interval_period is not None
        ]
        if duplicate_interval_period:
            raise ValueError(
                "Either 'interval_period' must be set on the event once, or every interval must have its own 'interval_period'."
            )

    return self