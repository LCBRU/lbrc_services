from lbrc_flask.forms.migrations import create_dynamic_form_tables, drop_security_tables


def upgrade(migrate_engine):
    create_dynamic_form_tables(migrate_engine)

def downgrade(migrate_engine):
    drop_security_tables(migrate_engine)
