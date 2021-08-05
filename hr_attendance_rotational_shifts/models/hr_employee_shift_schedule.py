# -*- coding: utf-8 -*-
""" Hr Employee Shifts Schedule """

from odoo import fields, models


class HrEmployeeShiftSchedule(models.Model):
    """Hr Employee Shift Schedule
    
    Create every month shifts Schedule for each employee.
    """
    _name = 'hr.employee.shift.schedule'

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        required=True,
        ondelete='cascade',
    )
    resource_calendar_id = fields.Many2one(
        comodel_name="resource.calendar",
        required=True,
        ondelete='cascade',
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
