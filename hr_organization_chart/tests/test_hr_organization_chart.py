# -*- coding: utf-8 -*-
"""Integrated Tests For HR Organization Chart"""

from odoo.tests.common import TransactionCase


class TestOrganizationChart(TransactionCase):
    """Integrated Tests For HR Organization Chart"""

    def setUp(self):
        """Setup the testing environment."""
        super(TestOrganizationChart, self).setUp()

        self.departments = \
            self.env.ref('hr_organization_chart.hr_department_management') | \
            self.env.ref('hr_organization_chart.hr_department_research')
        self.employees = \
            self.env.ref('hr_organization_chart.hr_employee_manager') | \
            self.env.ref('hr_organization_chart.hr_employee_sample_employee')

        self.organization_chart = self.env['hr.organization.chart']

    def test_00_get_employee_children(self):
        """Test Scenario: Test Retrieving The Employees Hierarchy"""
        employee_data = self.organization_chart.\
            get_employee_children(self.employees[0])
        child_employee = employee_data['children'][0]
        self.assertEqual(child_employee['id'], self.employees[1].id,
                         "Employee Hierarchy isn't Retrieved Successfully.")

    def test_01_get_employee_data(self):
        """Test Scenario: Test Retrieving The Employee Hierarchy Of
          A Department."""
        employee_data = self.organization_chart. \
            get_employee_data(self.departments[1])
        if employee_data:
            employee_data = employee_data[0]
        self.assertEqual(employee_data['id'], self.employees[0].id,
                         "Parent Data isn't Retrieved Successfully")
        employee_children = employee_data['children'][0]
        self.assertEqual(employee_children['id'],
                         self.employees[1].id,
                         "Children Data isn't Retrieved Successfully")

    def test_02_get_department_children(self):
        """ Test Scenario: Test Retrieving The hierarchy Of Each
        Department's Children (Departments & Employees)"""
        department_data = \
            self.organization_chart. \
            get_department_children(self.departments[0])
        self.assertEqual(department_data['id'], self.departments[0].id,
                         "Department Data isn't "
                         "Retrieved Successfully")
        children_departments = department_data['children'][0]
        self.assertEqual(children_departments['id'],
                         self.departments[1].id,
                         "Departments Children Data isn't "
                         "Retrieved Successfully")
        employee_children = department_data['children'][0]['children'][0]
        self.assertEqual(employee_children['id'], self.employees[0].id,
                         "Employees Children Data isn't "
                         "Retrieved Successfully")
        self.assertEqual(employee_children['children'][0]['id'],
                         self.employees[1].id,
                         "Employees Children Data isn't "
                         "Retrieved Successfully")
