.. class:: text-center

HR Attendance Rotational Shifts
===============================

This module allow to assign every day, period, month or months shifts fully dynamically
to assign the required shift to the employee(s) of the chosen department(s) with the required
categories ex: (part time - full time). It creates shifts schedules lines inside the employee form
each line for a specific month allowing to exclude days as weekend days. You can also assign
previous shifts for the last 40 days.

This module depends on hr_attendance_shift module to allow to get the attendance sheet and
the payslip based on the dynamic shifts.

--------------------------------------

.. class:: text-left

Features
--------

#. Assign rotational shifts to the employees every day, period, month or months shifts
   dynamically.

#. Add configurable shifts to assign.

#. Allow to assign a shift to the employees of a department or many departments with
   a filtration of a specific category.

#. Allow to assign a shift within a specific dates range with excluding days as weekend days.

#. Allow to get the attendance sheet and the payslip based on the dynamic shifts.

#. Allow to assign previous shifts for the last 40 days.

.. class:: text-left

Usage
-----

#. Create shift from attendance/configuration/Employees Shifts.

   - Enter the name of the shift.
   - Enter the interval of the shift.

    .. class:: center-block

    .. image:: /hr_attendance_rotational_shifts/static/src/img/shift.png
        :alt: Figure 00 - shift
        :width: 400 px


#. assign the shift from attendance/configuration/Employees Shifts Assign.

    - Choose the required department.
    - Choose the required category(ies) and employee(s) if required.
    - Choose the shift , dates interval.
    - You can choose days to exclude from the assiging shift days as weekend.

    .. class:: center-block

    .. image:: /hr_attendance_rotational_shifts/static/src/img/assign_shift.png
        :alt: Figure 01 - Assign Shift
        :width: 700 px

#. A line will be created inside the employee shifts schedules for the shift assigning
    dates interval (line per month).

    .. class:: center-block

    .. image:: /hr_attendance_rotational_shifts/static/src/img/schedule.png
        :alt: Figure 02 - Shifts Schedule
        :width: 700 px

#. Create an attendance sheet for the an employee with the date range you previously
   had assigned shifts for and get the attendance sheet applying the required attendance policy.

.. class:: text-left

Credits
-------

.. |copy| unicode:: U+000A9 .. COPYRIGHT SIGN
.. |tm| unicode:: U+2122 .. TRADEMARK SIGN

- `Omnia Sameh <omnia@itss-c.com>`_ |copy|
  `ITSS <http://www.itss-c.com>`_ |tm| 2019
