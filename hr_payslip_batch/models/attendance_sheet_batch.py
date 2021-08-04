# -*- coding: utf-8 -*-
""" Hr Attendance Sheet Batch Inherit """

import babel
from datetime import datetime
from odoo import api, fields, models, tools, _


class AttendanceSheetBatch(models.Model):
    """ Attendance Sheet Batch Model
    
    Generate payslip batch from attendance sheet batch.
    """
    _inherit = 'attendance.sheet.batch'

    @api.multi
    def action_create_payslip_batch(self):
        """ Generate payslip batch batching the payslips generated from
        the attendance sheet batch."""
        self.ensure_one()
        if not self.payslip_batch_id:
            hr_payslip_batch = self.env['hr.payslip.run']
            departments = self.department_ids
            date_from = fields.Date.from_string(self.date_from)
            date_to = fields.Date.from_string(self.date_to)
            date_from_time = datetime(date_from.year, date_from.month, date_from.day)
            locale = self.env.context.get('lang', 'en_US')
            payslip_batch_name = _('Payslip Batch of %s  Department(s) for %s') % \
                                 (', '.join([dep.name for dep in departments]),
                                  tools.ustr(babel.dates.format_date(
                                     date=date_from_time, format='MMMM-y', locale=locale)))
            payslip_ids = []
            for att_sheet in self.att_sheet_ids:
                    payslip_ids.append(att_sheet.payslip_id.id)
            payslip_batch = hr_payslip_batch.create({
                'name': payslip_batch_name,
                'date_start': date_from,
                'date_end': date_to,
                'slip_ids': [(6, 0, payslip_ids)],
            })
            self.payslip_batch_id = payslip_batch.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.payslip_batch_id.id,
            'views': [(False, 'form')],
            }
