/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

class ApprovalQueueAction extends Component {
    static template = "g2p_pbms.ApprovalQueue";
    static props = ["*"];
}

registry.category("actions").add("g2p_approval_queue", ApprovalQueueAction);
