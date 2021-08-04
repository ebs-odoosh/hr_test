# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2018-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################



import itertools
from lxml import etree
import time
import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import SUPERUSER_ID
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import UserError, AccessError, ValidationError
import babel
from operator import itemgetter
import logging


class attendance_sheet(models.Model):
    _inherit = 'attendance.sheet'

    batch_id = fields.Many2one(comodel_name='attendance.sheet.batch',string='Attendance Sheet '
                                                                           'Batch',domain="[('state', '!=', 'done')]")

    @api.multi
    def create_payslip_id(self):
        payslips = self.env['hr.payslip']
        for att_sheet in self:
            if att_sheet.payslip_id:
                new_payslip = att_sheet.payslip_id
                continue

            from_date = att_sheet.date_from
            to_date = att_sheet.date_to
            employee = att_sheet.employee_id
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            contract_id = slip_data['value'].get('contract_id')
            if not contract_id:
                raise exceptions.Warning(
                    'There is No Contracts for %s That covers the period of the Attendance sheet' % employee.name)
            worked_days_line_ids = slip_data['value'].get('worked_days_line_ids')
            worktime = [{
                'name': "Worked Hours",
                'code': 'WH',
                'contract_id': contract_id,
                'sequence': 20,
                'number_of_days': att_sheet.no_wd,
                'number_of_hours': att_sheet.tot_wh,
            }]
            overtime = [{
                'name': "Overtime",
                'code': 'OVT',
                'contract_id': contract_id,
                'sequence': 30,
                'number_of_days': att_sheet.no_overtime,
                'number_of_hours': att_sheet.tot_overtime,
            }]
            absence = [{
                'name': "Absence",
                'code': 'ABS',
                'contract_id': contract_id,
                'sequence': 35,
                'number_of_days': att_sheet.no_absence,
                'number_of_hours': att_sheet.tot_absence,
            }]
            late = [{
                'name': "Late In",
                'code': 'LATE',
                'contract_id': contract_id,
                'sequence': 40,
                'number_of_days': att_sheet.no_late,
                'number_of_hours': att_sheet.tot_late,
            }]
            difftime = [{
                'name': "Difference time",
                'code': 'DIFFT',
                'contract_id': contract_id,
                'sequence': 45,
                'number_of_days': att_sheet.no_difftime,
                'number_of_hours': att_sheet.tot_difftime,
            }]
            worked_days_line_ids += overtime + late + absence + difftime + worktime
            # worked_days_line_ids += overtime + late + absence

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': contract_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in worked_days_line_ids],
                'date_from': from_date,
                'date_to': to_date,
            }
            new_payslip = self.env['hr.payslip'].create(res)
            att_sheet.payslip_id = new_payslip
            payslips += new_payslip
        return True

    @api.multi
    def create_payslip_id(self):
        payslips = self.env['hr.payslip']
        for att_sheet in self:
            if att_sheet.payslip_id:
                new_payslip = att_sheet.payslip_id
                continue

            from_date = att_sheet.date_from
            to_date = att_sheet.date_to
            employee = att_sheet.employee_id
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            contract_id = slip_data['value'].get('contract_id')
            if not contract_id:
                raise exceptions.Warning(
                    'There is No Contracts for %s That covers the period of the Attendance sheet' % employee.name)
            worked_days_line_ids = slip_data['value'].get('worked_days_line_ids')
            worktime = [{
                'name': "Worked Hours",
                'code': 'WH',
                'contract_id': contract_id,
                'sequence': 20,
                'number_of_days': att_sheet.no_wd,
                'number_of_hours': att_sheet.tot_wh,
            }]
            overtime = [{
                'name': "Overtime",
                'code': 'OVT',
                'contract_id': contract_id,
                'sequence': 30,
                'number_of_days': att_sheet.no_overtime,
                'number_of_hours': att_sheet.tot_overtime,
            }]
            absence = [{
                'name': "Absence",
                'code': 'ABS',
                'contract_id': contract_id,
                'sequence': 35,
                'number_of_days': att_sheet.no_absence,
                'number_of_hours': att_sheet.tot_absence,
            }]
            late = [{
                'name': "Late In",
                'code': 'LATE',
                'contract_id': contract_id,
                'sequence': 40,
                'number_of_days': att_sheet.no_late,
                'number_of_hours': att_sheet.tot_late,
            }]
            difftime = [{
                'name': "Difference time",
                'code': 'DIFFT',
                'contract_id': contract_id,
                'sequence': 45,
                'number_of_days': att_sheet.no_difftime,
                'number_of_hours': att_sheet.tot_difftime,
            }]
            worked_days_line_ids += overtime + late + absence + difftime + worktime
            # worked_days_line_ids += overtime + late + absence

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': contract_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in worked_days_line_ids],
                'date_from': from_date,
                'date_to': to_date,
            }
            new_payslip = self.env['hr.payslip'].create(res)
            att_sheet.payslip_id = new_payslip
            payslips += new_payslip
        return True


    @api.multi
    def onchange_employee_id(self, date_from, date_to, employee_id=False):
        # defaults
        res = {
            'value': {
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        employee = self.env['hr.employee'].browse(employee_id)

        locale = self.env.context.get('lang', 'en_US')
        if locale == "ar_SY":
            locale = "ar"
        res['value'].update({
            'name': _('Attendance Sheet of %s for %s') % (employee.name,
                                                          tools.ustr(
                                                              babel.dates.format_date(date=ttyme, format='MMMM-y',
                                                                                      locale=locale)))
        })

        contract_ids = self.env['hr.payslip'].get_contract(employee, date_from, date_to)
        res['value'].update({
            'month': tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM', locale=locale)),
            'year': tools.ustr(babel.dates.format_date(date=ttyme, format='y', locale=locale)),
            # 'resource_calendar_id': employee.resource_calendar_id,

        })

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
