# -*- coding: utf-8 -*-
""" Hr Employee Attendance Sheet Inherit """

from datetime import timedelta
from dateutil.relativedelta import relativedelta
import pytz
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.hr_attendance_sheet.models.hr_attendance_sheet import interval_clean


class AttendanceSheet(models.Model):
    """Attendance Sheet Model
    
    calculate working intervals based on the rotational shifts.
    """
    _inherit = 'attendance.sheet'

    def get_work_intervals(self, day_start, day_end):
        """ Override to use the calender of the current month's employee's
        shift sheet not the default calender in the contract. """
        start_date = day_start.date()
        shift = self.employee_id.employee_shift_schedule_ids.\
            filtered(lambda record: fields.Date.from_string(record.date_from) <= start_date  <=
                             fields.Date.from_string(record.date_to))
                     # int(fields.Date.from_string(record.date_from).strftime("%m")) ==
                     # start_date.month)
        if not shift:
            raise ValidationError(_("There is no calendar include this day %s" % str(start_date)))
        calender = shift.resource_calendar_id
        tz_info = fields.Datetime.context_timestamp(self, day_start).tzinfo
        working_intervals = []
        for att in calender._get_day_attendances(
                day_start.date(), day_start.replace(hour=0, minute=0, second=0).time(),
                day_end.time()):
            if att.hour_to < att.hour_from:
                day_end = day_start + relativedelta(days=1)
            dt_f = day_start.replace(hour=0, minute=0, second=0) + \
                timedelta(seconds=(att.hour_from * 3600))
            dt_t = day_end.replace(hour=0, minute=0, second=0) + \
                timedelta(seconds=(att.hour_to * 3600))
            # adapt tz
            working_interval_tz = (
                dt_f.replace(tzinfo=tz_info).astimezone(pytz.UTC).replace(tzinfo=None),
                dt_t.replace(tzinfo=tz_info).astimezone(pytz.UTC).replace(tzinfo=None))
            working_intervals.append(working_interval_tz)
        clean_work_intervals = interval_clean(working_intervals)
        return clean_work_intervals
