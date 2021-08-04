# -*- coding: utf-8 -*-
""" Hr Organization Chart """

from odoo import api, models


def get_image(employee):
    """ Get employee image if there is no image, the default image
     will be returned."""
    if employee.image:
        image_path = "/web/image/hr.employee/%s/image" % (employee.id)
        return '<img src=%s />' % (image_path)

    image_path = "/hr_organization_chart/static/src/img/default_image.png"
    return '<img src=%s />' % (image_path)


def get_position(employee):
    """ Get employee job position."""
    if employee.sudo().job_id:
        return employee.sudo().job_id.name
    return ""


class HrOrganizationChart(models.Model):
    """ Hr Organization Chart Model

    Retrieve the hierarchy of the organization's departments
    and employees.
    """

    _name = 'hr.organization.chart'
    _description = 'HR Organization Chart Model'

    @api.model
    def get_organization_data(self):
        """ Retrieve the organization hierarchy of departments and
         employees
         :return {'values': data} organization's data.
         :rtype json object.
         data: is the organization hierarchy in a json object format of
         {'key': 'value'} including the children key whose value is
         a list of children, each child can be either employee
         or department differentiating between them by key type
         'department' or 'employee' this differentiation is only
         required for the template rendering."""
        data = \
            {
                'name': self.env.user.company_id.name,
                'title': '',
                'type': 'company',
                'className': 'o_hr_organization_chart_company',
                'id': '0',
                'children': [],
            }
        departments = self.env['hr.department']. \
            search([('parent_id', '=', False)])
        for department in departments:
            data['children'].append(self.get_department_children(department))
        return {'values': data}

    @api.model
    def get_department_children(self, department):
        """ Retrieve the hierarchy of each department's children
         (departments & employees).
        :param department: the parent department.
        :return department_data: the hierarchy of employees and
         departments of the passed department.
        """
        data = []
        department_data = \
            {
                'name': department.name,
                'type': 'department',
                'id': department.id,
                'className': 'o_hr_organization_chart_department',
                'manager_name': department.manager_id.name,
                'manager_title': get_position(department.manager_id),
                'manager_image': get_image(department.manager_id),
            }
        employee_children = self.get_employee_data(department)
        if employee_children:
            data += employee_children
        department_children = self.env['hr.department']. \
            search([('parent_id', '=', department.id)])
        for child in department_children:
            sub_children = self.env['hr.department']. \
                search([('parent_id', '=', child.id)])
            if not sub_children:
                employee_children = self.get_employee_data(child)
                data.append({
                    'name': child.name,
                    'type': 'department',
                    'id': child.id,
                    'className': 'o_hr_organization_chart_department',
                    'manager_name': child.manager_id.name,
                    'manager_title': get_position(child.manager_id),
                    'manager_image': get_image(child.manager_id),
                    'children': employee_children
                })
            else:
                data.append(self.get_department_children(child))
        if department_children or employee_children:
            department_data['children'] = data
        return department_data

    @api.model
    def get_employee_data(self, department):
        """ Retrieve the employees hierarchy of the passed department.
        :param department: the parent department.
        :return employee_data: the hierarchy of employees of
        the passed department.
        """
        employee_data = []
        domain = [
            ('department_id', '=', department.id),
        ]
        if department.manager_id:
            domain += [
                '|', ('parent_id', '=', False),
                ('parent_id', '=', department.manager_id.id),
                ('parent_id.department_id', '!=', department.id),
            ]
        else:
            domain += [
                '|', ('parent_id', '=', False),
                ('parent_id.department_id', '!=', department.id),
            ]
        employees = self.env['hr.employee'].search(domain)
        for employee in employees:
            children = self.get_employee_children(employee)
            employee_data.append(children)
        return employee_data

    @api.model
    def get_employee_children(self, employee):
        """ Retrieve the employees hierarchy of the passed employee.
        :param employee: the parent employee.
        :return employee_data: the hierarchy of employees of
        the passed employee.
        """
        data = []
        employee_data = \
            {
                'name': employee.name,
                'title': get_position(employee),
                'type': 'employee',
                'id': employee.id,
                'image': get_image(employee),
                'className': 'o_hr_organization_chart_employee',
            }
        children = self.env['hr.employee'].search([
            ('parent_id', '=', employee.id),
            ('department_id', '=', employee.department_id.id),
        ])
        for child in children:
            sub_children = self.env['hr.employee'].search([
                ('parent_id', '=', child.id),
                ('department_id', '=', child.department_id.id),
            ])
            if not sub_children:
                data.append({
                    'name': child.name,
                    'title': get_position(child),
                    'type': 'employee',
                    'id': child.id,
                    'className': 'o_hr_organization_chart_employee',
                    'image': get_image(child),
                })
            else:
                data.append(self.get_employee_children(child))
        if children:
            employee_data['children'] = data
        return employee_data
