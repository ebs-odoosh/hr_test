# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.exceptions import UserError, AccessError, ValidationError,Warning
class contract_salary_line(models.Model):
    _name = 'hr.contract.salary.line'

    rule_id = fields.Many2one('hr.salary.rule','Salary Rule')
    line_amount = fields.Monetary('Line Amount', digits=(16, 2), required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id,invisible=1 )
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True,invisible=1 )
    contract_id = fields.Many2one("hr.contract", string="Contract",invisible=1 )

class hr_contract(models.Model):
    _inherit = 'hr.contract'
    salary_line_ids = fields.One2many("hr.contract.salary.line", 'contract_id',string="salary Rules")
    # , default=lambda self: self._get_default_lines()
    wage = fields.Monetary('Wage', digits=(16, 2), compute='_compute_salary_wage',required=True,default=0, track_visibility="onchange", help="Employee's monthly gross wage.",store=True)

    @api.depends('salary_line_ids') #,'salary_line_ids.line_amount'
    def _compute_salary_wage(self):
        print("_compute_salary_wage")
        for record in self:
            record.wage = sum(line.line_amount for line in record.salary_line_ids)
            print(record.wage)
            if not record.salary_line_ids:
                record.wage = 0


    def get_by_code(self,code):
        for line in self.salary_line_ids:
            print(line.rule_id.code)
            if line.rule_id.code == code:
                return line.line_amount
        return 0