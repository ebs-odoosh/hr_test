# -*- coding: utf-8 -*-
"""HR Employee Shifts Report Wizard"""

import time

from odoo import api, fields, models


class EmployeeShiftsReport(models.TransientModel):
    """Hr Employee Shifts Report


    """
    _name = 'hr.employee.shifts.report.wizard'
    _description = 'HR Employee Shifts Report Wizard'

    date_from = fields.Date(string='From', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='To', required=True, default=lambda *a: time.strftime('%Y-%m-28'))

    @api.multi
    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        data['emp'] = self.env.context.get('active_ids', [])
        employees = self.env['hr.employee'].browse(data['emp'])
        datas = {
            'ids': data['emp'],
            'model': 'hr.employee',
            'form': data
        }
        return self.env.ref('hr_attendance_rotational_shifts.report_hr_employee_shifts_action'). \
               report_action(employees, data=datas)
