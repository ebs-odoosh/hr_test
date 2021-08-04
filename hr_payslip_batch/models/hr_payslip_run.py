# -*- coding: utf-8 -*-
""" Hr Payslip Batch """

from odoo import api, fields, models, _


class HrPayslipBatch(models.Model):
    """Hr Payslip Batch Model

    Compute sheet and validate payslips of payslip batch.
    """
    _inherit = 'hr.payslip.run'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sheet_computed', 'Sheet Computed'),
        ('payslip_validated', 'Payslip Validated'),
        ('close', 'Close'), ],
        string='Status',
        index=True,
        readonly=True,
        copy=False,
        default='draft'
    )

    @api.multi
    def action_compute_sheet(self):
        """ Compute sheet of payslips of payslip batch """
        for record in self:
            for payslip in record.slip_ids:
                payslip.compute_sheet()
            record.state = 'sheet_computed'

    @api.multi
    def action_confirm_payslip(self):
        """ Confirm payslips of payslip batch """
        for record in self:
            for payslip in record.slip_ids:
                payslip.action_payslip_done()
            record.state = 'payslip_validated'
