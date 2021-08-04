# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.exceptions import UserError, AccessError, ValidationError,Warning

class hr_contract(models.Model):
    _inherit = 'hr.contract'
    #track_visibility="onchange"
    vacation_start = fields.Date(string='Vacation Start Date after',track_visibility="onchange")
    # contracts_count = fields.Integer(string='Contracts')

    date_start = fields.Date('Start Date', required=True, default=fields.Date.today,
        help="Start date of the contract.",track_visibility="onchange")
    date_end = fields.Date('End Date',
        help="End date of the contract (if it's a fixed-term contract).",track_visibility="onchange")

    def contract_versions(self):
        context = dict(self._context)
        view_id = self.env.ref('hr_contract.hr_contract_view_kanban').id
        context['default_employee_id']=self.employee_id.id

        context['search_default_employee_id']=[self.employee_id.id]

        action = {
            'type': 'ir.actions.act_window',
            'view_type': 'kanban',
            'view_mode': 'kanban,form',
            # 'view_id':view_id,

            'name': _('Contract Versions'),
            'res_model': 'hr.contract',
            'target': 'current',

            'context': dict(context),
        }
        print(action)
        return action


    def renew_contract(self):
            form_view_id = self.env.ref('hr_contract.hr_contract_view_form').id


            context = dict(self._context)
            if  self.employee_id:

                context['default_employee_id'] = self.employee_id.id
            if self.department_id:
                context['default_department_id'] = self.department_id.id
            if self.job_id:
                context['default_job_id'] = self.job_id.id
            if self.wage:
                context['default_wage'] = self.wage
            if self.date_end:
                last_date_end = datetime.strptime(self.date_end, "%Y-%m-%d")
                date_start = last_date_end + relativedelta(days=1)
                date_end =  last_date_end + relativedelta(years=1)
                context['default_date_start'] =  date_start
                context['default_date_end'] = date_end
                context['default_vacation_start'] =  last_date_end + relativedelta(months=11)

                context['default_name'] = self.employee_id.name +"/"+ str(date_end.year)

            print(context)
            print(dict(context))
            action = {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'name': _('Renew Contract'),
                'res_model': 'hr.contract',
                'target': 'current',
                'context': dict(context),
            }
            return action
