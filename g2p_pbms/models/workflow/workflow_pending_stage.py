from odoo import models, fields


class G2PWorkflowPendingStage(models.Model):
    _name = "g2p.workflow.pending.stage"
    _description = "G2P Workflow Pending Stage"

    list_id = fields.Many2one(
        "g2p.beneficiary.list",
        required=True,
        index=True,
        ondelete="cascade",
        string="Beneficiary List",
    )
    current_stage_id = fields.Many2one(
        "g2p.workflow.stage.definition", required=True, string="Current Stage"
    )
    enqueued_at = fields.Datetime(
        default=fields.Datetime.now, string="Enqueued At"
    )
    stage_status = fields.Selection(
        [("PENDING", "Pending")], default="PENDING", string="Status"
    )

    _sql_constraints = [
        (
            "unique_list",
            "UNIQUE(list_id)",
            "Only one pending stage allowed per list.",
        )
    ]
