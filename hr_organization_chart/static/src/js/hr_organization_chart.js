var employee_data = [];

var nodeTemplate = function(data) {
    if (data.type == 'employee'){
        return `
            <div class="title">${data.title}</div>
            <div class="content">
                 <span class="o_hr_organization_chart_image">${data.image}</span><br/>
                 <span> ${data.name}</span>
            </div>`;
    }else if(data.type == 'department'){
        var department_template = `
            <div class="title">${data.name}</div>`;
        if (data.manager_name){
            department_template += `
            <div class="content" style="height:75px;">
            <div>
                <span class="o_hr_organization_chart_image">${data.manager_image}</span><br/>
                <span> ${data.manager_name}</span>
            </div>
            <br/>
            <div class="title" style="width:100%; border-radius: 0px;">${data.manager_name}
            </div></div></div>`;
            }else{
                department_template +=`<div class="content" style="height:75px;"></div>`;
            }
        return department_template;
    }else if (data.type == 'company'){
        return `<div class="title">${data.name}</div>`;
    }
 };

odoo.define("hr_organization_chart.org_chart", function (require) {
    "use strict";

    var core = require('web.core');
    var QWeb = core.qweb;
    var ajax = require('web.ajax');
    var Widget = require('web.Widget');
    var AbstractAction = require('web.AbstractAction');

    var ControlPanelMixin = require('web.ControlPanelMixin');
    var OrgChartHierarchy = AbstractAction.extend(ControlPanelMixin, {
    init: function(parent, context) {
        this._super(parent, context);
        var self = this;
        console.log(self);
        if (context.tag == 'hr_organization_chart.org_chart_department') {
            self._rpc({
                model:  'hr.organization.chart',
                method: 'get_organization_data',
            }, []).then(function(result){
                employee_data = result;
            }).done(function(){
                self.render();
                self.href = window.location.href;
            });
        }
    },
    willStart: function() {
      return $.when(ajax.loadLibs(this), this._super());
    },
    start: function() {
      var self = this;
      return this._super();
    },
    render: function() {
        var super_render = this._super;
        var self = this;
        var org_chart = QWeb.render('hr_organization_chart.hr_organization_chart_template', {
            widget: self,
        });
        $( ".o_control_panel" ).addClass( "o_hidden" );
        $(org_chart).prependTo(self.$el);
        return org_chart;
    },
    reload: function () {
      window.location.href = this.href;
    },
    });

    core.action_registry.add('hr_organization_chart.org_chart_department', OrgChartHierarchy);

    return OrgChartHierarchy;

});
