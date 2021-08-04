from odoo import api, fields, models

#    create_project_Task_related_name_Addon_Line


class projectTaskAddonMenu(models.Model):
    _name = 'project.addon'
    _rec_name = 'name'

    name = fields.Char('Addon Name',required=True)



#      create_project_Task_Addon_Line

class projectTaskAddonMenuLine(models.Model):
    _name = 'project.addon.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Addon Name' ,track_visibility="alwasy")
    addon_id = fields.Many2one(comodel_name="project.task", string='Task Name' ,track_visibility="alwasy")
    project_id_line = fields.Many2one(comodel_name="project.project",related='addon_id.project_id',string='Project Name' ,track_visibility="alwasy")
    addon_tec = fields.Many2one(comodel_name="project.addon", string= 'Technical Name', required=True ,track_visibility="alwasy" )
    addon_ver = fields.Char(string="Version" ,track_visibility="alwasy")
    addon_disc = fields.Text(string="Addon Disc" ,track_visibility="alwasy")
    addon_tester = fields.Many2one(comodel_name="res.users", string="Addon Tester", required=False ,track_visibility="alwasy")
    addon_developer= fields.Many2one(comodel_name="res.users", string="Addon Developer", required=False ,track_visibility="alwasy")
    addon_link = fields.Text(string="Addon Link", required=False ,track_visibility="alwasy")



