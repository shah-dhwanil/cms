# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202506121032_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS parents (
        id UUID,
        fathers_name VARCHAR(64) NOT NULL,
        mothers_name VARCHAR(64) NOT NULL,
        fathers_email_id VARCHAR(64) NOT NULL,
        mothers_email_id VARCHAR(64) NOT NULL,
        fathers_contact_no VARCHAR(15) NOT NULL,
        mothers_contact_no VARCHAR(15) NOT NULL,
        address TEXT NOT NULL,
        extra_info JSON,
        is_active BOOLEAN DEFAULT TRUE,
        CONSTRAINT pk_parents PRIMARY KEY (id,is_active),
        CONSTRAINT uniq_fathers_email_id UNIQUE (fathers_email_id,is_active),
        CONSTRAINT uniq_mothers_email_id UNIQUE (mothers_email_id,is_active),
        CONSTRAINT uniq_fathers_contact_no UNIQUE (fathers_contact_no,is_active),
        CONSTRAINT uniq_mothers_contact_no UNIQUE (mothers_contact_no,is_active),
        CONSTRAINT fk_parents_users FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
    );
    """
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP TABLE IF EXISTS parents;
    """
]
