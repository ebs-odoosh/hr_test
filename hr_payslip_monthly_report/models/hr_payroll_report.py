# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, tools, api


class PayrollReportView(models.Model):
    _name = 'hr.payroll.report.view'
    _auto = False

    name = fields.Many2one('hr.employee', string='Employee')
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    state = fields.Selection([('draft', 'Draft'), ('verify', 'Waiting'), ('done', 'Done'), ('cancel', 'Rejected')],
                             string='Status')
    category_ids = fields.Many2many(
        related='name.category_ids',
    )
    job_id = fields.Many2one('hr.job', string='Job Title')
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr.department', string='Department')
    amount = fields.Float(string='Amount')
    rule_name = fields.Many2one(comodel_name="hr.salary.rule",string="Salary Rule")

    def _select(self):
        select_str = """min(ps.id) as id ,s_rule.id as rule_name, emp.id as name,jb.id as job_id,dp.id as department_id,
        cmp.id as company_id,ps.date_from, ps.date_to, sum(psl.total) as amount, ps.state as state
        """
        return select_str

    def _from(self):
        from_str = """
           hr_payslip_line psl  
           join hr_payslip ps on (ps.employee_id=psl.employee_id and ps.id=psl.slip_id) 
           join hr_employee emp on (ps.employee_id=emp.id) 
           left join hr_department dp on (emp.department_id=dp.id)
           left join hr_job jb on (emp.job_id=jb.id) 
           left join res_company cmp on (cmp.id=ps.company_id)
           join hr_salary_rule s_rule on s_rule.id = psl.salary_rule_id
           where ps.state = 'done'
         """
        return from_str

    def _group_by(self):
        group_by_str = """
            group by emp.id,psl.total,ps.date_from, ps.date_to, ps.state,jb.id,dp.id,cmp.id,rule_name,psl.id,s_rule.sequence
            order by id ,s_rule.sequence
        """
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as ( SELECT
               %s
               FROM %s
               %s
               )""" % (self._table, self._select(), self._from(), self._group_by()))
