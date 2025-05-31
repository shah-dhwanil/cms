
# List of dependencies (migration that must be applied before this one)
dependencies = []

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE users (
        id UUID,
        email_id VARCHAR(64) NOT NULL,
        password TEXT NOT NULL,
        contact_no VARCHAR(16) NOT NULL,
        profile_image VARCHAR(64),
        CONSTRAINT pk_users PRIMARY KEY (id),
        CONSTRAINT uniq_user_email UNIQUE(email_id),
        CONSTRAINT uniq_user_contact UNIQUE(contact_no)
    );
    """
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP TABLE users;
    """
]
