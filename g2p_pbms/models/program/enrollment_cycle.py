from odoo import models, fields, api
from odoo.exceptions import UserError


class G2PEnrollmentCycle(models.Model):
    _name = "g2p.enrollment.cycle"
    _description = "G2P Enrollment Cycle"
    _rec_name = "cycle_mnemonic"

    enrollment_cycle_id = fields.Char(string='Enrollment Cycle ID')
    cycle_number = fields.Integer(string="Cycle Number", required=True, default=lambda self: self._get_default_cycle_number())
    cycle_mnemonic = fields.Char(string="Enrollment Cycle Mnemonic", compute='_compute_cycle_mnemonic')
    program_id = fields.Many2one("g2p.program.definition", string="G2P Program", readonly=True)
    beneficiary_list_ids = fields.One2many(
        "g2p.beneficiary.list", "enrollment_cycle_id", string="Beneficiary Lists"
    )

    # Date fields made optional (no longer required)
    enrollment_start_date = fields.Date(string="Enrollment Start Date")
    enrollment_end_date = fields.Date(string="Enrollment End Date")
    disbursement_start_date = fields.Date(string="Disbursement Start Date")
    disbursement_end_date = fields.Date(string="Disbursement End Date")

    # Deprecated: kept for backward compatibility
    approved_for_enrollment = fields.Boolean(string="Approved for Enrollment", default=False)

    is_readonly = fields.Boolean(compute='_compute_is_readonly', store=False)

    # WIP and count computed fields
    wip_list_id = fields.Many2one(
        "g2p.beneficiary.list",
        string="WIP List",
        compute="_compute_wip_and_counts",
        store=False,
    )
    wip_stage_name = fields.Char(
        string="Current Stage",
        compute="_compute_wip_and_counts",
        store=False,
    )
    list_count = fields.Integer(
        string="# Lists",
        compute="_compute_wip_and_counts",
        store=False,
    )
    approved_count = fields.Integer(
        string="# Approved",
        compute="_compute_wip_and_counts",
        store=False,
    )
    pending_count = fields.Integer(
        string="# Pending",
        compute="_compute_wip_and_counts",
        store=False,
    )
    has_wip_list = fields.Boolean(
        string="Has WIP List",
        compute="_compute_wip_and_counts",
        store=False,
    )

    _sql_constraints = [
        (
            'cycle_number_program_id_unique',
            'unique(cycle_number, program_id)',
            'Cycle Number must be unique per Program.'
        ),
    ]

    @api.depends_context('enrollment_cycle_form_view')
    def _compute_is_readonly(self):
        for rec in self:
            rec.is_readonly = self.env.context.get('enrollment_cycle_form_view', True)

    @api.depends("beneficiary_list_ids.workflow_approval_status", "beneficiary_list_ids.current_stage_name")
    def _compute_wip_and_counts(self):
        for rec in self:
            lists = rec.beneficiary_list_ids
            rec.list_count = len(lists)
            rec.approved_count = len(lists.filtered(lambda l: l.workflow_approval_status == "APPROVED"))
            pending_lists = lists.filtered(lambda l: l.workflow_approval_status == "PENDING")
            rec.pending_count = len(pending_lists)
            wip = pending_lists[:1]
            rec.wip_list_id = wip or False
            rec.wip_stage_name = wip.current_stage_name if wip else False
            rec.has_wip_list = bool(wip)

    @api.onchange('cycle_number')
    def _compute_cycle_mnemonic(self):
        for rec in self:
            rec.cycle_mnemonic = "Enrollment Cycle %s" % rec.cycle_number

    @api.model
    def _get_default_cycle_number(self):
        program_id = self.env.context.get('default_program_id')
        last = self.search([('program_id', '=', program_id)], order='cycle_number desc', limit=1)
        return last.cycle_number + 1 if last else 1

    def _check_wip_list(self):
        """Raise if a WIP list already exists for this cycle."""
        self.ensure_one()
        wip = self.beneficiary_list_ids.filtered(
            lambda l: l.workflow_approval_status == "PENDING"
        )
        if wip:
            raise UserError(
                "A list is already in progress (%s). Complete or reject it before creating a new one." % wip[0].mnemonic
            )

    def action_refresh_data(self):
        self.ensure_one()
        self._invalidate_cache()
        self.invalidate_recordset()
        return True

    def action_open_view(self):
        return {
            "type": "ir.actions.act_window",
            "name": "View Enrollment Cycle",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
            'context': {'create': False, 'enrollment_cycle_form_view': True},
        }
