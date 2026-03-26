import uuid
from odoo import models, fields, api
from odoo.exceptions import UserError


class G2PBeneficiaryList(models.Model):
    _name = "g2p.beneficiary.list"
    _description = "G2P Beneficiary List"
    _rec_name = "mnemonic"

    beneficiary_list_id = fields.Char(string='Beneficiary List ID', readonly=True, required=True, default=lambda self: str(uuid.uuid4()))
    mnemonic = fields.Char(string="Mnemonic", required=True)
    program_id = fields.Many2one("g2p.program.definition", string="G2P Program", compute="_compute_program_id", store=True, readonly=True)
    enrollment_cycle_id = fields.Many2one("g2p.enrollment.cycle", string="Enrollment Cycle", required=False)
    disbursement_cycle_id = fields.Many2one("g2p.disbursement.cycle", string="Disbursement Cycle", required=False)

    brief = fields.Text(string="Brief")
    eligibility_process_status = fields.Selection(
        [
            ("not_applicable", "not applicable"),
            ("pending", "pending"),
            ("processing", "processing"),
            ("complete", "complete"),
            ("failed", "failed")
        ],
        string="Eligibility Process Status",
        default="pending",
    )
    eligibility_number_of_attempts = fields.Integer(string="Eligibility Number of Attempts", default=0)
    eligibility_latest_error_code = fields.Char(string="Eligibility Latest Error Code", default=None)
    eligibility_processed_date = fields.Datetime(string="Eligibility Processed Date", default=None)

    entitlement_process_status = fields.Selection(
        [
            ("not_applicable", "not applicable"),
            ("pending", "pending"),
            ("processing", "processing"),
            ("complete", "complete"),
            ("failed", "failed")
        ],
        string="Entitlement Process Status",
        default="not_applicable",
    )
    entitlement_number_of_attempts = fields.Integer(string="Entitlement Number of Attempts", default=0)
    entitlement_latest_error_code = fields.Char(string="Entitlement Latest Error Code", default=None)
    entitlement_processed_date = fields.Datetime(string="Entitlement Processed Date", default=None)

    envelope_creation_status = fields.Selection(
        [
            ("not_applicable", "not applicable"),
            ("pending", "pending"),
            ("processing", "processing"),
            ("complete", "complete"),
            ("failed", "failed")
        ],
        string="Disbursement Envelope Status",
        default="not_applicable",
    )
    envelope_creation_number_of_attempts = fields.Integer(string="Envelope Creation Number of Attempts", default=0)
    envelope_creation_latest_error_code = fields.Char(string="Envelope Creation Latest Error Code", default=None)
    envelope_creation_processed_date = fields.Datetime(string="Envelope Creation Processed Date", default=None)

    disbursement_batch_creation_status = fields.Selection(
        [
            ("not_applicable", "not applicable"),
            ("pending", "pending"),
            ("processing", "processing"),
            ("complete", "complete"),
            ("failed", "failed")
        ],
        string="Disbursement Batch Creation Status",
        default="not_applicable",
    )
    dbc_number_of_attempts = fields.Integer(string="Disbursement Batch Creation Number of Attempts", default=0)
    dbc_latest_error_code = fields.Char(string="Disbursement Batch Creation Latest Error Code", default=None)
    dbc_processed_date = fields.Datetime(string="Disbursement Batch Creation Processed Date", default=None)

    number_of_registrants = fields.Integer(string="Number of Registrants", default=0)
    number_of_entitlements_processed = fields.Integer(string="Number of Entitlements Processed", default=0)

    list_stage = fields.Selection(
        [
            ("enrollment", "ENROLLMENT"),
            ("disbursement", "DISBURSEMENT")
        ],
        string="List Stage",
    )

    # --- Approval workflow fields ---
    workflow_approval_status = fields.Selection(
        [
            ("PENDING", "Pending"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
        ],
        string="Approval Status",
        default="PENDING",
        index=True,
    )
    pending_stage_ids = fields.One2many(
        "g2p.workflow.pending.stage", "list_id", string="Pending Stage"
    )
    stage_history_ids = fields.One2many(
        "g2p.workflow.stage.history", "list_id", string="Stage History"
    )
    current_stage_name = fields.Char(
        string="Current Stage",
        compute="_compute_current_stage_name",
        store=False,
    )
    current_stage_number = fields.Integer(
        string="Stage #",
        compute="_compute_current_stage_name",
        store=False,
    )

    # --- Deprecated fields kept for backward compatibility ---
    approval_date = fields.Date(string="Approval Date", default=None, readonly=True)
    list_workflow_status = fields.Selection(
        [
            ("initiated", ""),
            ("approved_final_enrolment", "APPROVED FINAL ENROLMENT"),
            ("approved_for_disbursement", "APPROVED FOR DISBURSEMENT"),
        ],
        string="List Workflow Status",
        default="initiated",
    )
    verification_ids = fields.One2many(
        "storage.file",
        "beneficiary_list_id",
        string="Community Verification",
    )

    creation_date = fields.Datetime(string="Creation Date", default=fields.Datetime.now, readonly=True)
    processed_date = fields.Datetime(string="Processed Date", default=None, readonly=True)

    @api.depends("pending_stage_ids.current_stage_id")
    def _compute_current_stage_name(self):
        for rec in self:
            pending = rec.pending_stage_ids[:1]
            if pending and rec.workflow_approval_status == "PENDING":
                rec.current_stage_name = pending.current_stage_id.stage_name
                rec.current_stage_number = pending.current_stage_id.stage_number
            else:
                rec.current_stage_name = False
                rec.current_stage_number = 0

    @api.depends('enrollment_cycle_id.program_id', 'disbursement_cycle_id.program_id')
    def _compute_program_id(self):
        for record in self:
            if record.enrollment_cycle_id:
                record.program_id = record.enrollment_cycle_id.program_id
                record.list_stage = "enrollment"
            elif record.disbursement_cycle_id:
                record.program_id = record.disbursement_cycle_id.program_id
                record.list_stage = "disbursement"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._initialize_workflow()
        return records

    def _initialize_workflow(self):
        """Create the initial pending stage record for this list."""
        self.ensure_one()
        if not self.program_id:
            return
        cycle_type = "ENROLMENT" if self.list_stage == "enrollment" else "DISBURSEMENT"
        first_stage = self.env["g2p.workflow.stage.definition"].search(
            [
                ("program_id", "=", self.program_id.id),
                ("cycle_type", "=", cycle_type),
            ],
            order="stage_number asc",
            limit=1,
        )
        if first_stage:
            self.env["g2p.workflow.pending.stage"].create({
                "list_id": self.id,
                "current_stage_id": first_stage.id,
                "enqueued_at": fields.Datetime.now(),
                "stage_status": "PENDING",
            })
            self.workflow_approval_status = "PENDING"

    def action_approve_stage(self):
        """Approve the current pending stage; advance to next or mark APPROVED."""
        self.ensure_one()
        pending = self.pending_stage_ids[:1]
        if not pending:
            raise UserError("No pending stage found for this list.")
        if self.workflow_approval_status != "PENDING":
            raise UserError("List is not in PENDING status.")

        current_stage = pending.current_stage_id
        list_type = "ENROLMENT" if self.list_stage == "enrollment" else "DISBURSEMENT"

        self.env["g2p.workflow.stage.history"].create({
            "list_id": self.id,
            "list_type": list_type,
            "stage_id": current_stage.id,
            "enqueued_at": pending.enqueued_at,
            "acted_by": self.env.user.id,
            "acted_at": fields.Datetime.now(),
            "action_type": "APPROVED",
        })

        if current_stage.is_final_stage:
            pending.unlink()
            self.workflow_approval_status = "APPROVED"
        else:
            next_stage = self.env["g2p.workflow.stage.definition"].search(
                [
                    ("program_id", "=", self.program_id.id),
                    ("cycle_type", "=", current_stage.cycle_type),
                    ("stage_number", ">", current_stage.stage_number),
                ],
                order="stage_number asc",
                limit=1,
            )
            if next_stage:
                pending.write({
                    "current_stage_id": next_stage.id,
                    "enqueued_at": fields.Datetime.now(),
                })
            else:
                pending.unlink()
                self.workflow_approval_status = "APPROVED"

    def action_reject_stage(self):
        """Reject the current pending stage; mark list REJECTED."""
        self.ensure_one()
        pending = self.pending_stage_ids[:1]
        if not pending:
            raise UserError("No pending stage found for this list.")
        if self.workflow_approval_status != "PENDING":
            raise UserError("List is not in PENDING status.")

        current_stage = pending.current_stage_id
        list_type = "ENROLMENT" if self.list_stage == "enrollment" else "DISBURSEMENT"

        self.env["g2p.workflow.stage.history"].create({
            "list_id": self.id,
            "list_type": list_type,
            "stage_id": current_stage.id,
            "enqueued_at": pending.enqueued_at,
            "acted_by": self.env.user.id,
            "acted_at": fields.Datetime.now(),
            "action_type": "REJECTED",
        })
        pending.unlink()
        self.workflow_approval_status = "REJECTED"

    def action_open_summary_wizard(self):
        if (
            self.list_stage == 'enrollment'
            and self.list_workflow_status != 'approved_final_enrollment'
            and getattr(self.program_id, 'auto_approve_enrolment', False)
            and getattr(self.program_id, 'verifications_for_enrolment', 0) == 0
        ):
            self.list_workflow_status = 'approved_final_enrolment'
            self.approval_date = fields.Date.context_today(self)
            if self.enrollment_cycle_id:
                self.env['g2p.enrollment.cycle'].browse(self.enrollment_cycle_id.id).write({
                    'approved_for_enrollment': True,
                })

        if (
            self.list_stage == 'disbursement'
            and self.list_workflow_status != 'approved_for_disbursement'
            and getattr(self.program_id, 'auto_approve_disbursement', False)
            and getattr(self.program_id, 'verifications_for_disbursement', 0) == 0
        ):
            self.list_workflow_status = 'approved_for_disbursement'
            self.approval_date = fields.Date.context_today(self)
            if self.disbursement_cycle_id:
                self.env['g2p.disbursement.cycle'].browse(self.disbursement_cycle_id.id).write({
                    'approved_for_disbursement': True,
                })

        self.ensure_one()
        wizard_vals = {
            "target_registry": self.program_id.target_registry,
            "mnemonic": self.mnemonic,
            "brief": self.brief,
            "program_id": self.program_id.id,
            "beneficiary_list_id": self.id,
            "beneficiary_list_uuid": self.beneficiary_list_id,
            "enrollment_cycle_id": self.enrollment_cycle_id,
            "disbursement_cycle_id": self.disbursement_cycle_id,
            "list_stage": self.list_stage,
            "list_workflow_status": self.list_workflow_status,
            "enrollment_start_date": self.enrollment_cycle_id.enrollment_start_date if self.enrollment_cycle_id else None,
            "enrollment_end_date": self.enrollment_cycle_id.enrollment_end_date if self.enrollment_cycle_id else None,
            "disbursement_cycle_mnemonic": self.disbursement_cycle_id.cycle_mnemonic if self.disbursement_cycle_id else None,
            "approved_for_disbursement": self.disbursement_cycle_id.approved_for_disbursement if self.disbursement_cycle_id else None,
        }

        wizard = self.env["g2p.bgtask.summary.wizard"].create(wizard_vals)
        return {
            "name": "Eligibility Summary Details",
            "view_mode": "form",
            "res_model": "g2p.bgtask.summary.wizard",
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "target": "current",
            'context': {
                'default_target_registry': self.program_id.target_registry,
                'default_program_id': self.program_id.id,
                'default_beneficiary_list_id': self.beneficiary_list_id,
            },
        }
