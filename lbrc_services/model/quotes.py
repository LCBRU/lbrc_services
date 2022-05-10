from lbrc_flask.database import db
from lbrc_flask.security import AuditMixin
from lbrc_flask.model import CommonMixin
from lbrc_services.model.services import Organisation, Service, User


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
    def get_task_status(cls, name):
        return QuoteStatusType.query.filter_by(name=name).one()

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    is_complete = db.Column(db.Boolean)


class Quotation(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    organisation_id = db.Column(db.Integer, db.ForeignKey(Organisation.id))
    organisation = db.relationship(Organisation, lazy="joined", backref='tasks')
    organisation_description = db.Column(db.String(255))
    requestor_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    requestor = db.relationship(User, lazy="joined", backref='tasks', foreign_keys=[requestor_id])
    current_status_type_id = db.Column(db.Integer, db.ForeignKey(QuoteStatusType.id), nullable=False)
    current_status_type = db.relationship(QuoteStatusType)
