# -*- coding: utf-8 -*-
"""HR Attendance Report"""

import time
from datetime import datetime
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import UserError, AccessError, ValidationError
import babel


class AttendanceSheet(models.Model):
    _inherit = 'attendance.sheet'

    @api.multi
    def onchange_employee_id(self, date_from, date_to, employee_id=False):
        # defaults
        res = {
            'value': {
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        # ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        employee = self.env['hr.employee'].browse(employee_id)

        locale = self.env.context.get('lang', 'en_US')
        if locale == "ar_SY":
            locale = "ar"
        res['value'].update({
            'name': _('Attendance Sheet of %s for %s') % (employee.name,
                                                          tools.ustr(
                                                              babel.dates.format_date(date=date_from, format='MMMM-y',
                                                                                      locale=locale)))
        })

        contract_ids = self.env['hr.payslip'].get_contract(employee, date_from, date_to)

        if not contract_ids:
            raise ValidationError(_("Employee %s doesn`t have a valid Contract" % employee.name))

        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })

        if not contract.att_policy_id:
            raise ValidationError(_('Please add attendance policy for %s contract  ') % employee.name)
        att_policy_id = contract.att_policy_id

        res['value'].update({
            'att_policy_id': att_policy_id.id,
        })
        return res
