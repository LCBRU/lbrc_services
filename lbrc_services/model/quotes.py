from lbrc_flask.database import db
from lbrc_flask.security import AuditMixin
from lbrc_flask.model import CommonMixin
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

    number_of_sites = db.Column(db.Integer)
    length_of_study_months = db.Column(db.Integer)
    number_of_participants = db.Column(db.Integer)
    number_of_crfs = db.Column(db.Integer)
    number_of_visits = db.Column(db.Integer)

    other_requirements = db.Column(db.String())
    out_of_scope = db.Column(db.String())


class QuoteStatus(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey(Quote.id), nullable=False)
    quote = db.relationship(Quote, backref="status_history")
    notes = db.Column(db.String(255))
    quote_status_type_id = db.Column(db.Integer, db.ForeignKey(QuoteStatusType.id), nullable=False)
    quote_status_type = db.relationship(QuoteStatusType, backref="quotes")
