# -*- coding: utf-8 -*-
""" Hr Employee Tasks"""

from odoo import api, fields, models,  _
from odoo.exceptions import ValidationError

import logging

LOGGER = logging.getLogger(__name__)


class EmployeeTask(models.Model):
    """Hr Employee Task

    Create tasks for employee with weight.
    """
    _name = 'hr.employee.task'
    _description = 'Employee Task'
    _inherit = ['mail.thread']

    name = fields.Char(required=True)
    achieved_weight = fields.Integer(
        compute='_compute_task_weights',
        store=True
    )
    total_weight = fields.Integer(
        compute='_compute_task_weights',
        store=True
    )
    expiration_date = fields.Datetime(
        required=True,
    )
    description = fields.Text()
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        required=True,
    )
    sub_tasks_ids = fields.One2many(
        comodel_name="hr.employee.sub.task",
        inverse_name="task_id",
        required=True,
        track_visibility='always',)

    state = fields.Selection(
        string="Status",
        default="draft",
        selection=[('draft', 'Draft'),
                   ('open', 'Opened'),
                   ('closed', 'Closed'),
                   ('cancel', 'Cancelled')],
        track_visibility='always',
    )
    user_id = fields.Many2one(comodel_name="res.users",
                              default=lambda record: record.env.user.id, )

    @api.constrains('expiration_date')
    def _check_task_expiration_date(self):
        for record in self:
            if record.expiration_date < fields.Datetime.now():
                raise ValidationError(_("Expiration date and time must be greater than the current "
                                        "date and time"))

    @api.constrains('sub_tasks_ids', 'state')
    def _check_employee_sub_tasks(self):
        for record in self:
            if record.state == 'open' and not self.sub_tasks_ids:
                raise ValidationError(_("Missing Sub Tasks, Please enter at least one."))

    @api.multi
    @api.depends('sub_tasks_ids')
    def _compute_task_weights(self):
        for record in self:
            sub_tasks_ids = record.sub_tasks_ids
            record.total_weight = sum(sub_tasks_ids.mapped('weight'))
            record.achieved_weight = sum(sub_tasks_ids.filtered(lambda record: record.state == 'closed').
                                         mapped('achieved_weight'))

    @api.multi
    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        if employee.user_id:
            self.message_subscribe(partner_ids=employee.user_id.partner_id.ids)

    @api.model
    def create(self, values):
        """ Override to avoid automatic logging of creation """
        task = super(EmployeeTask, self).\
            create(values)
        self.message_subscribe(partner_ids=task.user_id.partner_id.ids)
        return task

    @api.multi
    def write(self, values):
        result = super(EmployeeTask, self).write(values)
        if 'state' in values and values.get('state') == 'open':
            self.add_follower(self.employee_id.id)
        return result

    @api.multi
    def _track_subtype(self, init_values):
        if 'state' in init_values and self.state == 'draft':
            return 'hr_employee_tasks.mt_task_created'
        elif 'state' in init_values and self.state == 'open':
            return 'hr_employee_tasks.mt_task_confirmed'
        elif 'state' in init_values and self.state == 'closed':
            return 'hr_employee_tasks.mt_task_closed'
        elif 'state' in init_values and self.state == 'cancel':
            return 'hr_employee_tasks.mt_task_cancelled'
        return super(EmployeeTask, self)._track_subtype(init_values)

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        self.state = 'open'

    @api.multi
    def action_close(self):
        self.ensure_one()
        for sub in self.sub_tasks_ids.filtered(lambda record: record.state != 'closed'):
            sub.state = 'closed'
        self.state = 'close'

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        for sub in self.sub_tasks_ids.filtered(lambda record: record.state != 'closed'):
            sub.state = 'closed'
        self.state = 'cancel'


class EmployeeSubTask(models.Model):
    """Hr Employee Sub Task

    Create task details with weight and achieved weight.
    """
    _name = 'hr.employee.sub.task'
    _description = 'Employee Sub Task'

    name = fields.Char(required=True, )
    state = fields.Selection(
        string="Status",
        default="open",
        selection=[('open', 'Open'),
                   ('submit', 'Waiting Approval'),
                   ('closed', 'Closed'), ],
    )
    description = fields.Text()
    employee_comments = fields.Text()
    weight = fields.Integer(required=True, )
    achieved_weight = fields.Integer(required=True, )
    task_id = fields.Many2one(
        comodel_name="hr.employee.task",
    )
    task_state = fields.Selection(
        related='task_id.state',
    )

    @api.multi
    def action_reopen(self):
        self.ensure_one()
        self.state = 'open'

    @api.multi
    def action_submit(self):
        self.ensure_one()
        self.state = 'submit'

    @api.multi
    def action_close(self):
        self.ensure_one()
        self.state = 'closed'
