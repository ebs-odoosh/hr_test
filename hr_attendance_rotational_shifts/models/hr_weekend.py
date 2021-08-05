# -*- coding: utf-8 -*-
""" Hr Weekend"""

from odoo import fields, models


class Weekend(models.Model):
    """Hr Weekend Model
    
    Configure the system with the week days to assign weekend days to
    the employee's shifts' schedule.
    """
    _name = 'hr.weekend'

    name = fields.Char(required=True)
    code = fields.Integer(required=True)
