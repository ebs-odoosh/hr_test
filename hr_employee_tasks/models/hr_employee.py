# -*- coding: utf-8 -*-
""" Hr Employee Tasks"""

from odoo import fields, models, api, _ ,tools, SUPERUSER_ID
import logging

LOGGER = logging.getLogger(__name__)


class Employee(models.Model):
    """Hr Employee Model

    Add the employee's opened tasks to the employee's form.
    """
    _inherit = 'hr.employee'

    task_ids = fields.One2many(
        comodel_name="hr.employee.task",
        inverse_name="employee_id",
        string="Tasks",
        domain=[('state', '=', 'open')]
    )
