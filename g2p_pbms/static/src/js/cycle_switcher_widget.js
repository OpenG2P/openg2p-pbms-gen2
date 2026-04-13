/** @odoo-module **/
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CycleSwitcherWidget extends Many2OneField {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.orm = useService("orm");
    }

    async update(value) {
        if (!value || !value[0]) return;
        const cycleId = value[0];
        const wizardId = this.props.record.resId;
        if (!wizardId) return;

        const isEnrollment = this.props.name === "selected_previous_cycle_id";
        const methodName = isEnrollment
            ? "action_switch_enrollment_cycle"
            : "action_switch_disbursement_cycle";
        const contextKey = isEnrollment
            ? "selected_enrollment_cycle_id"
            : "selected_disbursement_cycle_id";

        try {
            const action = await this.orm.call(
                "g2p.bgtask.summary.wizard",
                methodName,
                [[wizardId]],
                { context: { [contextKey]: cycleId } }
            );
            if (action) {
                await this.actionService.doAction(action);
            }
        } catch (e) {
            console.error("CycleSwitcherWidget: failed to switch cycle", e);
        }
        // Do NOT call super.update() — keeps form clean (no dirty state)
    }
}

registry.category("fields").add("g2p_pbms.cycle_switcher", {
    component: CycleSwitcherWidget,
    supportedTypes: ["many2one"],
});
