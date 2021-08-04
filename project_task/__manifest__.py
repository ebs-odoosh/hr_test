
# -*- coding: utf-8 -*-
{
    'name': "project_task",
    'summary': """ project_task. """,
    'author': "khalil al shareef, ITSS <https://www.itss-c.com>",
    'category': 'project_task',
    'version': '1.0.0',
    'depends': ['base','project'],
    'data': [

        'security/ir.model.access.csv',
        'views/project_task_addon_line.xml',
        'views/base_addon_menu.xml',
        'views/project_task_kanban.xml',

    ]
}