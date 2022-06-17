from lbrc_services.model.quotes import QuotePricingType, QuoteRequirementType, QuoteStatusType
from lbrc_services.model.services import Organisation, TaskStatusType
from lbrc_flask.database import db


def init_model(app):
    
    @app.before_first_request
    def task_status_type_setup():
        for name, details in TaskStatusType.all_details.items():
            if TaskStatusType.query.filter(TaskStatusType.name == name).count() == 0:
                db.session.add(
                    TaskStatusType(
                        name=name,
                        is_complete=details['is_complete'],
                        is_active=details['is_active'],
                    )
                )

        for name, details in QuoteStatusType.all_details.items():
            if QuoteStatusType.query.filter(QuoteStatusType.name == name).count() == 0:
                db.session.add(
                    QuoteStatusType(
                        name=name,
                        is_complete=details['is_complete'],
                    )
                )

        for name in Organisation.all_organisations:
            if Organisation.query.filter(Organisation.name == name).count() == 0:
                db.session.add(
                    Organisation(
                        name=name,
                    )
                )

        for name in QuoteRequirementType.initial_types:
            if QuoteRequirementType.query.filter(QuoteRequirementType.name == name).count() == 0:
                db.session.add(
                    QuoteRequirementType(
                        name=name,
                    )
                )

        for name, price_per_day in QuotePricingType.initial_types:
            if QuotePricingType.query.filter(QuotePricingType.name == name).count() == 0:
                db.session.add(
                    QuotePricingType(
                        name=name,
                        price_per_day=price_per_day,
                    )
                )

        db.session.commit()
