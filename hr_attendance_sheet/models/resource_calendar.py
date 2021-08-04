# -*- coding: utf-8 -*-
""" Flexible  Attendance """

from odoo import api, fields, models
from odoo.addons.hr_attendance_sheet.models.hr_attendance_sheet import float_to_time


class ResourceCalendar(models.Model):

    _inherit = 'resource.calendar'

    flexible_hours = fields.Float()


    @api.multi
    def _get_day_attendances(self, day_date, start_time=None, end_time=None):
        """ Given a day date, return matching attendances. Those can be limited
        by starting and ending time objects. """
        self.ensure_one()
        weekday = day_date.weekday()
        attendances = self.env['resource.calendar.attendance']

        for attendance in self.attendance_ids.filtered(
                lambda att:
                int(att.dayofweek) == weekday and
                not (att.date_from and fields.Date.from_string(att.date_from) > day_date) and
                not (att.date_to and fields.Date.from_string(att.date_to) < day_date)):
            if start_time and float_to_time(attendance.hour_to) < start_time:
                continue
            if end_time and float_to_time(attendance.hour_from) > end_time:
                continue
            attendances |= attendance
        return attendances
