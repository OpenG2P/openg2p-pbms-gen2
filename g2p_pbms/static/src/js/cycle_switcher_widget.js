/** @odoo-module **/
import { Many2OneField, many2OneField } from "@web/views/fields/many2one/many2one_field";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CycleSwitcherWidget extends Many2OneField {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.ormService = useService("orm");
    }

    /**
     * Defined as a class field (arrow function) to guarantee this overrides the
     * parent even if Many2OneField.update is also a class field.
     *
     * value format varies by Odoo version:
     *   - Odoo 16/17: { id, display_name }  (object)
     *   - Some builds:  [id, displayName]    (array)
     */
    update = async (value) => {
        if (!value) return;

        const cycleId = Array.isArray(value)
            ? value[0]
            : (value && typeof value === "object" ? value.id : null);

        if (!cycleId) return;

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
            const action = await this.ormService.call(
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
        // Never call super.update() — form stays clean, no dirty state
    };
}

// Spread parent registry entry so extractProps, placeholder, supportedTypes, etc. all carry over
registry.category("fields").add("g2p_pbms.cycle_switcher", {
    ...many2OneField,
    component: CycleSwitcherWidget,
});
