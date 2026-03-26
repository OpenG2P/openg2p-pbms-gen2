from odoo import models, fields


class G2PWorkflowStageHistory(models.Model):
    _name = "g2p.workflow.stage.history"
    _description = "G2P Workflow Stage History"
    _order = "acted_at desc"

    list_id = fields.Many2one(
        "g2p.beneficiary.list",
        required=True,
        index=True,
        ondelete="cascade",
        string="Beneficiary List",
    )
    list_type = fields.Selection(
        [("ENROLMENT", "Enrolment"), ("DISBURSEMENT", "Disbursement")],
        required=True,
        string="List Type",
    )
    stage_id = fields.Many2one(
        "g2p.workflow.stage.definition", required=True, string="Stage"
    )
    stage_name = fields.Char(related="stage_id.stage_name", string="Stage Name", store=True)
    stage_number = fields.Integer(related="stage_id.stage_number", string="Stage Number", store=True)
    enqueued_at = fields.Datetime(string="Enqueued At")
    acted_by = fields.Many2one("res.users", string="Acted By")
    acted_at = fields.Datetime(string="Acted At")
    action_type = fields.Selection(
        [("APPROVED", "Approved"), ("REJECTED", "Rejected")],
        required=True,
        string="Action",
    )

    _sql_constraints = [
        (
            "unique_list_stage",
            "UNIQUE(list_id, stage_id)",
            "Each stage can only appear once per list.",
        )
    ]
