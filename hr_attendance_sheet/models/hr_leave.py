# -*- coding: utf-8 -*-
""" init object """

from pytz import timezone, UTC, utc
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import  api, fields, models, _
from odoo.addons.resource.models.resource import float_to_time
from odoo.exceptions import ValidationError

import logging

LOGGER = logging.getLogger(__name__)


class Leave(models.Model):
    _inherit = 'hr.leave'

    request_date_from_period = fields.Selection([
        ('am', 'First Half'), ('pm', 'Second Half')],
        string="Date Period Start", default='am')

    @api.onchange('request_date_from_period', 'request_hour_from', 'request_hour_to',
                  'request_date_from', 'request_date_to',
                  'employee_id')
    def _onchange_request_parameters(self):
        super(Leave, self)._onchange_request_parameters()
        if self.request_unit_half:
            calendar = self.employee_id.resource_calendar_id or self.env.user.company_id.resource_calendar_id
            attendances = calendar.attendance_ids.filtered(
                lambda att:
                int(att.dayofweek) == self.request_date_from.weekday() and
                not (att.date_from and fields.Date.from_string(att.date_from) > self.request_date_from) and
                not (att.date_to and fields.Date.from_string(att.date_to) < self.request_date_to))
            attendance = attendances and attendances[0]
            diff_hours = (attendance.hour_to - attendance.hour_from) / 2

            if self.request_date_from_period == 'am':
                hour_from = float_to_time(attendance.hour_from)
                hour_to = float_to_time(attendance.hour_from + diff_hours)
            else:
                hour_from = float_to_time(attendance.hour_from + diff_hours)
                hour_to = float_to_time(attendance.hour_to)

            tz = self.env.user.tz if self.env.user.tz and not self.request_unit_custom else 'UTC'  # custom -> already in UTC
            self.date_from = timezone(tz).localize(datetime.combine(self.request_date_from, hour_from)).astimezone(
                UTC).replace(tzinfo=None)
            self.date_to = timezone(tz).localize(datetime.combine(self.request_date_to, hour_to)).astimezone(UTC).replace(
                tzinfo=None)
            self._onchange_leave_dates()

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        result = super(Leave, self)._get_number_of_days(date_from=date_from, date_to=date_to, employee_id=employee_id)
        if self.leave_type_request_unit == 'hour':
            res = self._compute_leave_flexible_hours(employee_id, date_from, date_to)
            if res:
                hours, days = res
                result = days and days or result
        return result

    @api.multi
    @api.depends('number_of_days')
    def _compute_number_of_hours_display(self):
        super(Leave, self)._compute_number_of_hours_display()
        for leave in self:
            if leave.leave_type_request_unit == 'hour':
                result = leave._compute_leave_flexible_hours(leave.employee_id, leave.date_from , leave.date_to)
                if result:
                    hours, days = result
                    if hours:
                        leave.number_of_hours_display = hours

    def _compute_leave_flexible_hours(self, employee, date_from , date_to):
        hours, days = 0, 0
        date_from = fields.Datetime.from_string(date_from)
        date_to = fields.Datetime.from_string(date_to)
        tz = self.env.user.tz if self.env.user.tz and not self.request_unit_custom else 'UTC'  # custom -> already in UTC
        tz = timezone(tz)
        resource = employee.resource_calendar_id
        flexible_hours = resource.flexible_hours
        holiday_date = utc.localize(fields.Datetime.from_string(self.date_from)).astimezone(tz)
        holiday_date_end = utc.localize(fields.Datetime.from_string(self.date_to)).astimezone(tz)
        day_start = holiday_date.replace(hour=0, minute=0, second=0)
        day_end = holiday_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        day_hours = resource. \
            get_work_hours_count(day_start, day_end, False)

        if date_from and date_to:
            day_start = day_start.replace(tzinfo=None)
            if self.request_unit_hours and \
                    not (self.request_hour_from and self.request_hour_to):
                return 0
            if flexible_hours:
                intervals = resource._get_day_attendances(holiday_date.date(),
                                                          holiday_date.replace(hour=0,
                                                                               minute=0,
                                                                               second=0).time(),
                                                          day_end.time())

                if intervals:
                    working_interval = intervals[0]
                    flexible_m_interval_start = holiday_date.replace(hour=0, minute=0, second=0) + timedelta(
                        seconds=(working_interval.hour_from * 3600))
                    flexible_m_interval_end = flexible_m_interval_start + relativedelta(hours=flexible_hours)
                    flexible_e_interval_start = holiday_date.replace(hour=0, minute=0, second=0) + timedelta(
                        seconds=(working_interval.hour_to * 3600))
                    # flexible_e_interval_end = flexible_e_interval_start + relativedelta(hours=flexible_hours)

                    if flexible_e_interval_start <= holiday_date_end:

                        attendance = self.env['hr.attendance'].search(
                            [('employee_id.id', '=', employee.id),
                             ('check_in', '>=', str(day_start)),
                             ('check_in', '<=', str(flexible_e_interval_start.replace(tzinfo=None)))],
                            order="check_in desc", limit=1)
                        if attendance:
                        #     raise war(_("You should check in first"))
                            check_in = utc.localize(
                                fields.Datetime.from_string(attendance.check_in)).astimezone(tz).replace(
                                tzinfo=None)
                            flexible_m_interval_start = flexible_m_interval_start.replace(tzinfo=None)
                            flexible_m_interval_end = flexible_m_interval_end.replace(tzinfo=None)
                            holiday_date = holiday_date.replace(tzinfo=None)
                            holiday_date_end = holiday_date_end.replace(tzinfo=None)
                            if check_in < flexible_m_interval_start:
                                check_in = flexible_m_interval_start
                            #
                            if check_in > flexible_m_interval_end:
                                check_in = flexible_m_interval_end

                            planned_check_out = check_in + relativedelta(hours=day_hours)

                            if holiday_date < planned_check_out:
                                check_out = planned_check_out
                                if holiday_date_end < planned_check_out:
                                   check_out = holiday_date_end
                                hours = (check_out - holiday_date).seconds
                                hours = round(hours / 3600.0, 1)
                                days = round(hours / day_hours, 2)

        return hours, days
