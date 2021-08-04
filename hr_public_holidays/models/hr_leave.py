# -*- coding: utf-8 -*-
""" Hr public Holidays """

from pytz import timezone, utc
from datetime import timedelta
from odoo import api, fields, models

import logging

LOGGER = logging.getLogger(__name__)
HOURS_PER_DAY = 8


class Holidays(models.Model):
    _inherit = 'hr.leave'

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        result = super(Holidays, self)._get_number_of_days(date_from=date_from, date_to=date_to,
                                                           employee_id=employee_id)
        if result and employee_id and date_from and date_to:
            holidays = self.env['hr.public.holiday'].sudo().search(
                [('date_from', '<=', date_to), ('date_to', '>=', date_from), ('state', '=', 'active')])
            if holidays:
                employee = self.env['hr.employee'].browse(employee_id)
                tz = employee.user_id and employee.employee_id.user_id.env.user.tz  or 'UTC'
                tz = timezone(tz)
                date_from = utc.localize(fields.Datetime.from_string(self.date_from)).astimezone(tz)
                date_to = utc.localize(fields.Datetime.from_string(self.date_to)).astimezone(tz) + timedelta(days=1)
                work_intervals = employee.resource_calendar_id._work_intervals(date_from, date_to)
                holiday_days = list(list(interval)[0].date() for interval in work_intervals)
                days_count = 0
                for holiday in holidays:
                    date_from = fields.Date.from_string(holiday.date_from)
                    date_to = fields.Date.from_string(holiday.date_to)
                    delta = date_to - date_from  # as timedelta
                    days = [date_from + timedelta(days=i) for i in range(delta.days + 1)]
                    days_count += sum(day in holiday_days for day in days)
                result = result - days_count
                if result < 0.0: result = 0.0
        return result

    @api.multi
    @api.depends('number_of_days')
    def _compute_number_of_hours_display(self):
        super(Holidays, self)._compute_number_of_hours_display()
        for record in self:
            if record.leave_type_request_unit == 'hour':
                tz = record.employee_id.user_id and record.employee_id.user_id.env.user.tz  or 'UTC'
                tz = timezone(tz)
                date_from = utc.localize(fields.Datetime.from_string(record.date_from)).astimezone(tz)
                date_to = utc.localize(fields.Datetime.from_string(record.date_to)).astimezone(tz) + timedelta(days=1)

                holidays = self.env['hr.public.holiday'].sudo().search(
                    [('date_from', '<=', date_to.date()), ('date_to', '>=', date_from.date()), ('state', '=', 'active')])
                if holidays:
                    employee = record.employee_id
                    resource = employee.resource_calendar_id
                    work_intervals = resource._work_intervals(date_from, date_to)

                    holiday_days = list(list(interval)[0].date() for interval in work_intervals)
                    hours_count = 0
                    for holiday in holidays:
                        date_from = fields.Date.from_string(holiday.date_from)
                        date_to = fields.Date.from_string(holiday.date_to)
                        delta = date_to - date_from  # as timedelta
                        days = [date_from + timedelta(days=i) for i in range(delta.days + 1)]
                        matched_days = [day in holiday_days and day for day in days]
                        for day in matched_days:
                            day = fields.Datetime.from_string(day)
                            day_start = day.replace(hour=0, minute=0, second=0).replace(tzinfo=None)
                            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
                            print(day_start, day_end)
                            hours_count += resource.get_work_hours_count(day_start, day_end, False)
                    result = record.number_of_hours_display - hours_count
                    if result < 0.0: result = 0.0
                    record.number_of_hours_display = result
