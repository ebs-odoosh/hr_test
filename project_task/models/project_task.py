from odoo import api, fields, models

#    inherit_project.task_addon_line_ids

class ProjectTask(models.Model):
    _inherit = 'project.task'

    task_module = fields.Selection(
        string="Task Module",
        required=True,
        selection=
        [
            ('accounting', 'Accounting'),
            ('crm', 'CRM'),
            ('hr', 'HR'),
            ('inventory', 'Inventory'),
            ('manufacturing', 'Manufacturing'),
            ('purchase', 'Purchasing'),
            ('quality', 'Quality'),
            ('sales', 'Sales'),
            ('study', 'Study'),
        ])

    addon_line_ids = fields.One2many("project.addon.line", 'addon_id' ,track_visibility="alwasy")




