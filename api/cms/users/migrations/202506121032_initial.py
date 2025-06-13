# List of dependencies (migration that must be applied before this one)
dependencies = []

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS users (
        id UUID,
        email_id VARCHAR(64) NOT NULL,
        password VARCHAR(512) NOT NULL,
        contact_no VARCHAR(20) NOT NULL,
        profile_image_id UUID,
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP(0) WITH TIME ZONE DEFAULT now(),
        CONSTRAINT pk_users PRIMARY KEY(id),
        CONSTRAINT uniq_users_email_id UNIQUE(email_id),
        CONSTRAINT uniq_users_contact_no UNIQUE(contact_no)
    );
    """
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP TABLE IF EXISTS users;
    """
]
