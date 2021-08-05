# -*- coding: utf-8 -*-
"""HR Employee Shifts Report"""

import pytz
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrEmployeeShiftsReport(models.AbstractModel):
    _name = 'report.hr_attendance_rotational_shifts.report_employee_shifts'

    def _get_employee_shifts(self, emp, dates):
        working_intervals = []
        for start_date in dates:
            start_date = datetime.datetime.combine(start_date, datetime.time())
            day_end = start_date.replace(hour=23, minute=59, second=59)
            shift = emp.employee_shift_schedule_ids. \
                filtered(lambda record: fields.Date.from_string(record.date_from) <=
                                        start_date.date() <=
                             fields.Date.from_string(record.date_to))
                         # int(fields.Date.from_string(record.date_from).strftime("%m")) == start_date.date().month)
            if shift:
                calender = shift.resource_calendar_id
                for att in calender._get_day_attendances(start_date.date(), start_date.time(),
                                                         day_end.time()):
                    if att.hour_to < att.hour_from:
                        day_end = start_date + relativedelta(days=1)
                    dt_f = start_date.replace(hour=0, minute=0, second=0) + \
                           timedelta(seconds=(att.hour_from * 3600))
                    dt_t = day_end.replace(hour=0, minute=0, second=0) + \
                           timedelta(seconds=(att.hour_to * 3600))
                    working_intervals.append([dt_f, dt_t])
        return working_intervals

    def _get_shifts_data(self, data):
        res = []
        Employee = self.env['hr.employee']
        date_from = fields.Date.from_string(data['date_from'])
        date_to = fields.Date.from_string(data['date_to'])
        all_dates = [(date_from + timedelta(days=i)) for i in range((date_to - date_from).days + 1)]
        for emp in Employee.browse(data['emp']):
                res.append({
                    'emp': emp.name,
                    'shifts': self._get_employee_shifts(emp, all_dates),
                })
        return res

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        shifts_report = self.env['ir.actions.report']. \
            _get_report_from_name('hr_attendance_rotational_shifts.report_employee_shifts')
        employees = self.env['hr.employee'].browse(data['form']['emp'])
        return {
            'doc_ids': self.ids,
            'doc_model': shifts_report.model,
            'docs': employees,
            'dates': [data['form']['date_from'], data['form']['date_to']],
            'get_shifts': self._get_shifts_data(data['form']),
        }
