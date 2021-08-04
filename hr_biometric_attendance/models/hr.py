# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Employee(models.Model):
    _name = "hr.employee"
    _inherit = "hr.employee"

    att_user_id = fields.Char("Attendance User ID")