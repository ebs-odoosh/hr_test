# -*- coding: utf-8 -*-
""" HR Employee Shifts """

from odoo import api, fields, models, _


class HrEmployeeShift(models.Model):
    """ Hr Employee Shift Model
    
    Configure the system with dynamic shifts to assign to employees.
    """
    _name = 'hr.employee.shift'

    name = fields.Char(
        string="Shift Name",
        required=True,
    )
    time_from = fields.Float(
        required=True,
    )
    time_to = fields.Float(
        required=True,
    )
    flexible_hours = fields.Float()
