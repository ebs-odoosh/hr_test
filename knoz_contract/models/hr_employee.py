# -*- coding: utf-8 -*-

from odoo import models, fields, api
class hr_employee(models.Model):
    _inherit = 'hr.employee'

    joining_date = fields.Date(string='Joining Date')
    is_citizen = fields.Boolean('Is Citizen ',default=False)