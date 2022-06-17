from lbrc_flask.database import db
from lbrc_flask.security import AuditMixin
from lbrc_flask.model import CommonMixin
from sqlalchemy.sql import func
from lbrc_services.model.services import Organisation, User


class QuoteStatusType(db.Model, CommonMixin):

    DRAFT = 'Draft'
    AWAITING_APPROVAL = 'Awaiting Approval'
    ISSUED = 'Issued'
    DUE = 'Due'
    CHARGED = 'Charged'
    PAID = 'Paid'
    DELETED = 'Deleted'
    DUPLICATE = 'Duplicate'

    all_details = {
        DRAFT: {
            'is_complete': False,
        },
        AWAITING_APPROVAL: {
            'is_complete': False,
        },
        ISSUED: {
            'is_complete': False,
        },
        DUE: {
            'is_complete': False,
        },
        CHARGED: {
            'is_complete': False,
        },
        PAID: {
            'is_complete': True,
        },
        DELETED: {
            'is_complete': True,
        },
        DUPLICATE: {
            'is_complete': True,
        },
    }

    @classmethod
    def get_quote_status(cls, name):
        return QuoteStatusType.query.filter_by(name=name).one()

    @classmethod
    def get_draft(cls):
        return QuoteStatusType.get_quote_status(QuoteStatusType.DRAFT)

    @classmethod
    def get_awaiting_approval(cls):
        return QuoteStatusType.get_quote_status(QuoteStatusType.AWAITING_APPROVAL)

    @classmethod
    def get_issued(cls):
        return QuoteStatusType.get_quote_status(QuoteStatusType.ISSUED)

    @classmethod
    def get_due(cls):
        return QuoteStatusType.get_quote_status(QuoteStatusType.DUE)

    @classmethod
    def get_charged(cls):
        return QuoteStatusType.get_quote_status(QuoteStatusType.CHARGED)

    @classmethod
    def get_paid(cls):
        return QuoteStatusType.get_quote_status(QuoteStatusType.PAID)

    @classmethod
    def get_deleted(cls):
        return QuoteStatusType.get_quote_status(QuoteStatusType.DELETED)

    @classmethod
    def get_duplicate(cls):
        return QuoteStatusType.get_quote_status(QuoteStatusType.DUPLICATE)

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    is_complete = db.Column(db.Boolean)


class QuoteRequirementType(db.Model, CommonMixin):
    initial_types = [
        'Number of Sites',
        'Length of Study',
        'Number of participants',
        'Number of CRFs',
        'Number of Visits',
        'OpenSpecimen Protocols',
        'Label Packs',
        'Blinding IDs',
        'Bespoke Applications',
        'Email Notifications',
        'Integrations with UHL Systems',
        'Data Warehousing',
        'Data Quality Reporting',
        'Specific Exclusion from Scope',
        'Other requirements',
    ]

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))


class QuotePricingType(db.Model, CommonMixin):
    initial_types = [
        {
            'name': 'BRC',
            'price_per_day': 300,
        },
        {
            'name': 'External',
            'price_per_day': 500,
        },
        {
            'name': 'PhD',
            'price_per_day': 0,
        },
        {
            'name': 'LDC',
            'price_per_day': 0,
        },
        {
            'name': 'For Information Only',
            'price_per_day': 0,
        },
    ]

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    price_per_day = db.Column(db.DECIMAL())
    disabled = db.Column(db.Boolean())


class Quote(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    organisation_id = db.Column(db.Integer, db.ForeignKey(Organisation.id))
    organisation = db.relationship(Organisation, lazy="joined", backref='quotes')
    organisation_description = db.Column(db.String(255))
    requestor_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    requestor = db.relationship(User, lazy="joined", backref='quotes', foreign_keys=[requestor_id])
    current_status_type_id = db.Column(db.Integer, db.ForeignKey(QuoteStatusType.id), nullable=False)
    current_status_type = db.relationship(QuoteStatusType)
    introduction = db.Column(db.String())
    conslusion = db.Column(db.String())

    @property
    def total_days(self):
        return sum([s.total_days for s in self.work_sections])

    @property
    def requirements_types(self):
        return set([r.quote_requirement_type for r in self.requirements])


class QuoteStatus(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey(Quote.id), nullable=False)
    quote = db.relationship(Quote, backref="status_history")
    notes = db.Column(db.String(255))
    quote_status_type_id = db.Column(db.Integer, db.ForeignKey(QuoteStatusType.id), nullable=False)
    quote_status_type = db.relationship(QuoteStatusType, backref="quotes")


class QuoteRequirement(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey(Quote.id), nullable=False)
    quote = db.relationship(Quote, backref="requirements")
    quote_requirement_type_id = db.Column(db.Integer, db.ForeignKey(QuoteRequirementType.id), nullable=False)
    quote_requirement_type = db.relationship(QuoteRequirementType)
    notes = db.Column(db.String())


class QuoteWorkSection(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey(Quote.id), nullable=False)
    quote = db.relationship(Quote, backref="work_sections")
    name = db.Column(db.String(255))

    @property
    def total_days(self):
        return QuoteWorkLine.query.with_entities(func.sum(QuoteWorkLine.days)).filter(QuoteWorkLine.quote_work_section_id == self.id).scalar() or 0


class QuoteWorkLine(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    quote_work_section_id = db.Column(db.Integer, db.ForeignKey(QuoteWorkSection.id), nullable=False)
    quote_work_section = db.relationship(QuoteWorkSection, backref="lines")
    name = db.Column(db.String(255))
    days = db.Column(db.DECIMAL())
