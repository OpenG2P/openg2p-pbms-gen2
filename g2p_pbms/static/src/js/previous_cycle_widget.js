/** @odoo-module **/
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class PreviousCycleField extends Many2OneField {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.orm = useService("orm");
    }

    async update(value) {
        if (value && value[0]) {
            const cycleId = value[0];
            const methodName =
                this.props.name === "selected_previous_cycle_id"
                    ? "action_open_enrollment_cycle_by_id"
                    : "action_open_disbursement_cycle_by_id";
            try {
                const action = await this.orm.call(
                    "g2p.bgtask.summary.wizard",
                    methodName,
                    [[], cycleId]
                );
                if (action) {
                    await this.actionService.doAction(action);
                    return;
                }
            } catch (e) {
                console.error("PreviousCycleField: failed to navigate to cycle:", e);
            }
        }
        return super.update(value);
    }
}

PreviousCycleField.template = Many2OneField.template;

const existingMany2One = registry.category("fields").get("many2one");
registry.category("fields").add("previous_cycle_many2one", {
    ...existingMany2One,
    component: PreviousCycleField,
});
