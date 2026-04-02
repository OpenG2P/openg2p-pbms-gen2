/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { View } from "@web/views/view";

class ApprovalsAction extends Component {
    static template = "g2p_pbms.ApprovalsAction";
    static components = { View };
    static props = ["*"];

    setup() {
        this.rpc = useService("rpc");
        this.user = useService("user");
        this.state = useState({ activeTab: "queue" });
        this.queueDomain = [];

        onWillStart(async () => {
            this.queueDomain = await this.rpc(
                "/web/dataset/call_kw/g2p.workflow.pending.stage/get_approval_queue_domain",
                {
                    model: "g2p.workflow.pending.stage",
                    method: "get_approval_queue_domain",
                    args: [],
                    kwargs: {},
                }
            );
        });
    }

    onTabClick(tab) {
        this.state.activeTab = tab;
    }

    get queueViewProps() {
        return {
            type: "list",
            resModel: "g2p.workflow.pending.stage",
            domain: this.queueDomain,
            context: { approval_queue: true },
        };
    }

    get historyViewProps() {
        return {
            type: "list",
            resModel: "g2p.workflow.stage.history",
            domain: [
                ["acted_by", "=", this.user.userId],
                ["status", "in", ["APPROVED", "REJECTED"]],
            ],
        };
    }
}

registry.category("actions").add("g2p_approvals_tabbed", ApprovalsAction);
