# DurationRepresentationHelpers.py


## IMPORTS:
# from GUI.Helpers.DurationRepresentationHelpers import DurationRepresentationMixin

class DurationRepresentationMixin(object):

    """
        Object must have the following instance properties:
        self.width()
        self.height()

        self.totalStartTime
        self.totalEndTime
        self.activeScaleMultiplier
    """

    def get_total_start_time(self):
        return self.totalStartTime

    def get_total_end_time(self):
        return self.totalEndTime

    def get_total_duration(self):
        return (self.get_total_end_time() - self.get_total_start_time())

    def get_active_scale_multiplier(self):
        return self.activeScaleMultiplier

    # Get scale from length
    def getScale(self):
        return float(self.get_total_duration())/float(self.width())


    # Timeline position/time converion functions:
    def offset_to_percent(self, event_x, event_y):
        percent_x = event_x / (self.width() * self.get_active_scale_multiplier())
        percent_y = event_y / self.height()
        return (percent_x, percent_y)

    def offset_to_duration(self, event_x):
        (percent_x, percent_y) = self.offset_to_percent(event_x, 0.0)
        return (self.get_total_duration() * percent_x)

    def offset_to_datetime(self, event_x):
        duration_offset = self.offset_to_duration(event_x)
        return (self.get_total_start_time() + duration_offset)

    def percent_to_offset(self, percent_offset):
        event_x = percent_offset * (self.width() * self.get_active_scale_multiplier())
        return event_x

    def duration_to_offset(self, duration_offset):
        percent_x = duration_offset / self.get_total_duration()
        event_x = self.percent_to_offset(percent_x)
        return event_x

    def datetime_to_offset(self, newDatetime):
        duration_offset = newDatetime - self.get_total_start_time()
        event_x = self.duration_to_offset(duration_offset)
        return event_x