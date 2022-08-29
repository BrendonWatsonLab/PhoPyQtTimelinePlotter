#!/usr/bin/python3
# -*- coding: utf-8 -*-
from base64 import b64encode
from datetime import datetime, timezone, timedelta

# DateTimeRenders.py

## IMPORTS:
# from phopyqttimelineplotter.GUI.Helpers.DateTimeRenders import DateTimeRenderMixin

class DateTimeRenderMixin(object):

    # Get time string from seconds
    # def get_time_string(self, seconds):
    #     drawTime = self.totalStartTime + timedelta(seconds=seconds)
    #     # return drawTime.strftime("%d-%m-%Y %I %p")
    #     # return drawTime.strftime("%#m/%#d \n%#I%p") # Works on windows
    #     return drawTime.strftime("X%m/X%d \nX%I%p").replace('X0', 'X').replace('X', '')

    #     # m, s = divmod(seconds, 60)
    #     # h, m = divmod(m, 60)
    #     # return "%02d:%02d:%02d" % (h, m, s)


    # Get "7/27" style timestring for the start of each day
    @staticmethod
    def get_start_of_day_time_string(start_of_day_date):
        return start_of_day_date.strftime("X%m/X%d").replace('X0', 'X').replace('X', '')


    # Get time string from seconds
    @staticmethod
    def get_hours_of_day_only_time_string(drawTime):
        return drawTime.strftime("X%I%p").replace('X0', 'X').replace('X', '')


    # Get "7/27 7:18am" style timestring for the start of each day
    @staticmethod
    def get_full_date_time_string(drawTime):
        return drawTime.strftime("X%m/X%d X%I:%m %p").replace('X0', 'X').replace('X', '')


    # "7/27/19 7:18:03am" style timestring Includes years and seconds.
    @staticmethod
    def get_full_long_date_time_string(drawTime):
        return drawTime.strftime("X%m/X%d/%y X%I:%m:%S %p").replace('X0', 'X').replace('X', '')


    # "7/27/19\n 7:18:03am" style timestring Includes years and seconds, with a line break between the date and time
    @staticmethod
    def get_full_long_date_time_twoLine_string(drawTime):
        return drawTime.strftime("X%m/X%d/%y\nX%I:%m:%S %p").replace('X0', 'X').replace('X', '')
