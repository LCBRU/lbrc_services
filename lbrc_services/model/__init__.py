from lbrc_services.model.quotes import QuotePricingType, QuoteRequirementType, QuoteStatusType
from lbrc_services.model.services import Organisation, TaskStatusType
from lbrc_flask.database import db
from sqlalchemy import select


def init_model(app):
    pass

def task_status_type_setup():
    for name, details in TaskStatusType.all_details.items():
        if db.session.execute(select(TaskStatusType).where(TaskStatusType.name == name)).scalar() is None:
            db.session.add(
                TaskStatusType(
                    name=name,
                    is_complete=details['is_complete'],
                    is_active=details['is_active'],
                )
            )

    for name, details in QuoteStatusType.all_details.items():
        if db.session.execute(select(QuoteStatusType).where(QuoteStatusType.name == name)).scalar() is None:
            db.session.add(
                QuoteStatusType(
                    name=name,
                    is_complete=details['is_complete'],
                )
            )

    for name in Organisation.all_organisations:
        if db.session.execute(select(Organisation).where(Organisation.name == name)).scalar() is None:
            db.session.add(
                Organisation(
                    name=name,
                )
            )

    for name in QuoteRequirementType.initial_types:
        if db.session.execute(select(QuoteRequirementType).where(QuoteRequirementType.name == name)).scalar() is None:
            db.session.add(
                QuoteRequirementType(
                    name=name,
                )
            )

    for name, price_per_day in QuotePricingType.initial_types:
        if db.session.execute(select(QuotePricingType).where(QuotePricingType.name == name)).scalar() is None:
            db.session.add(
                QuotePricingType(
                    name=name,
                    price_per_day=price_per_day,
                )
            )

    db.session.commit()
