# -*- coding: utf-8 -*-
""" Hr Employee Shifts Schedule """

from odoo import fields, models


class Employee(models.Model):
    """ Hr Employee Model Inherit
    inherit to add shifts' schedules lines.
    """
    _inherit = 'hr.employee'

    employee_shift_schedule_ids = fields.One2many(
        comodel_name="hr.employee.shift.schedule",
        inverse_name="employee_id",
        ondelete='cascade',
    )
