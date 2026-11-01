-- Full database schema for the college backend (PostgreSQL 16), generated from the Alembic migrations.
-- Normally you do NOT run this file: 'alembic upgrade head' creates the same tables and keeps
-- track of versions. Use this file to review the schema, or to create a database by hand with:
--   psql "$DATABASE_URL" -f db/schema.sql
-- Regenerate after adding a migration: alembic upgrade head --sql > db/schema.sql

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade -> 0001

CREATE TABLE admin_users (
    email VARCHAR(320) NOT NULL,
    full_name VARCHAR(120),
    is_active BOOLEAN DEFAULT true NOT NULL,
    last_login_at TIMESTAMP WITH TIME ZONE,
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_admin_users PRIMARY KEY (id),
    CONSTRAINT uq_admin_users_email UNIQUE (email)
);

CREATE TABLE announcements (
    message VARCHAR(500) NOT NULL,
    link_url VARCHAR(500),
    starts_at TIMESTAMP WITH TIME ZONE,
    ends_at TIMESTAMP WITH TIME ZONE,
    display_order INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_announcements PRIMARY KEY (id)
);

CREATE TABLE courses (
    code VARCHAR(20) NOT NULL,
    name VARCHAR(120) NOT NULL,
    duration_text VARCHAR(68) NOT NULL,
    summary TEXT,
    eligibility TEXT,
    total_fee_inr INTEGER NOT NULL,
    fee_note VARCHAR(300),
    fee_breakup JSON NOT NULL,
    display_order INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_courses PRIMARY KEY (id),
    CONSTRAINT uq_courses_code UNIQUE (code)
);

CREATE TABLE exam_sets (
    slot INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    source_filename VARCHAR(255) NOT NULL,
    question_count INTEGER NOT NULL,
    uploaded_by VARCHAR(320) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    id UUID NOT NULL,
    CONSTRAINT pk_exam_sets PRIMARY KEY (id),
    CONSTRAINT ck_exam_sets_valid_slot CHECK (slot BETWEEN 1 AND 3),
    CONSTRAINT uq_exam_sets_slot UNIQUE (slot)
);

CREATE TABLE gallery_images (
    caption VARCHAR(200),
    image_path VARCHAR(300) NOT NULL,
    image_url VARCHAR(1000) NOT NULL,
    thumb_path VARCHAR(300) NOT NULL,
    thumb_url VARCHAR(1000) NOT NULL,
    image_width INTEGER NOT NULL,
    image_height INTEGER NOT NULL,
    display_order INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_gallery_images PRIMARY KEY (id)
);

CREATE TABLE pending_sheet_rows (
    tab VARCHAR(100) NOT NULL,
    headers JSON NOT NULL,
    row JSON NOT NULL,
    attempts INTEGER NOT NULL,
    last_error TEXT,
    next_attempt_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    id UUID NOT NULL,
    CONSTRAINT pk_pending_sheet_rows PRIMARY KEY (id)
);

CREATE INDEX ix_pending_sheet_rows_next_attempt_at ON pending_sheet_rows (next_attempt_at);

CREATE TABLE site_settings (
    id SERIAL NOT NULL,
    phone VARCHAR(30),
    whatsapp VARCHAR(30),
    email VARCHAR(320),
    address TEXT,
    google_form_url VARCHAR(500),
    social_links JSON NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_site_settings PRIMARY KEY (id),
    CONSTRAINT ck_site_settings_single_row CHECK (id = 1)
);

CREATE TABLE videos (
    title VARCHAR(150) NOT NULL,
    url VARCHAR(500) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    video_id VARCHAR(60) NOT NULL,
    embed_url VARCHAR(500) NOT NULL,
    display_order INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_videos PRIMARY KEY (id)
);

CREATE TABLE banners (
    title VARCHAR(150) NOT NULL,
    course_id UUID,
    image_path VARCHAR(300) NOT NULL,
    image_url VARCHAR(1000) NOT NULL,
    thumb_path VARCHAR(300) NOT NULL,
    thumb_url VARCHAR(1000) NOT NULL,
    image_width INTEGER NOT NULL,
    image_height INTEGER NOT NULL,
    display_order INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_banners PRIMARY KEY (id),
    CONSTRAINT fk_banners_course_id_courses FOREIGN KEY(course_id) REFERENCES courses (id) ON DELETE SET NULL
);

CREATE TABLE batches (
    course_id UUID NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    timings VARCHAR(100) NOT NULL,
    mode VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_batches PRIMARY KEY (id),
    CONSTRAINT ck_batches_valid_mode CHECK (mode IN ('online', 'offline')),
    CONSTRAINT ck_batches_dates_in_order CHECK (end_date >= start_date),
    CONSTRAINT fk_batches_course_id_courses FOREIGN KEY(course_id) REFERENCES courses (id) ON DELETE CASCADE
);

CREATE INDEX ix_batches_course_id ON batches (course_id);

CREATE TABLE brochures (
    course_id UUID NOT NULL,
    file_path VARCHAR(300) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    size_bytes INTEGER NOT NULL,
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_brochures PRIMARY KEY (id),
    CONSTRAINT fk_brochures_course_id_courses FOREIGN KEY(course_id) REFERENCES courses (id) ON DELETE CASCADE,
    CONSTRAINT uq_brochures_course_id UNIQUE (course_id)
);

CREATE TABLE exam_passages (
    exam_set_id UUID NOT NULL,
    passage_key VARCHAR(50) NOT NULL,
    section VARCHAR(1) NOT NULL,
    content JSON NOT NULL,
    id UUID NOT NULL,
    CONSTRAINT pk_exam_passages PRIMARY KEY (id),
    CONSTRAINT fk_exam_passages_exam_set_id_exam_sets FOREIGN KEY(exam_set_id) REFERENCES exam_sets (id) ON DELETE CASCADE
);

CREATE INDEX ix_exam_passages_exam_set_id ON exam_passages (exam_set_id);

CREATE TABLE exam_questions (
    exam_set_id UUID NOT NULL,
    passage_id UUID,
    position INTEGER NOT NULL,
    section VARCHAR(1) NOT NULL,
    subsection VARCHAR(100) NOT NULL,
    content JSON NOT NULL,
    id UUID NOT NULL,
    CONSTRAINT pk_exam_questions PRIMARY KEY (id),
    CONSTRAINT fk_exam_questions_exam_set_id_exam_sets FOREIGN KEY(exam_set_id) REFERENCES exam_sets (id) ON DELETE CASCADE,
    CONSTRAINT fk_exam_questions_passage_id_exam_passages FOREIGN KEY(passage_id) REFERENCES exam_passages (id) ON DELETE CASCADE
);

CREATE INDEX ix_exam_questions_exam_set_id ON exam_questions (exam_set_id);

CREATE INDEX ix_exam_questions_passage_id ON exam_questions (passage_id);

CREATE TABLE exam_options (
    question_id UUID NOT NULL,
    label VARCHAR(1) NOT NULL,
    content TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    id UUID NOT NULL,
    CONSTRAINT pk_exam_options PRIMARY KEY (id),
    CONSTRAINT fk_exam_options_question_id_exam_questions FOREIGN KEY(question_id) REFERENCES exam_questions (id) ON DELETE CASCADE
);

CREATE INDEX ix_exam_options_question_id ON exam_options (question_id);

INSERT INTO courses (id, code, name, duration_text, total_fee_inr, fee_breakup, display_order) VALUES
(CAST('a3dbc20a-074a-5403-89f9-3fdefbbe76c4' AS UUID), 'IBFAP', 'IBFAP', '45 days', 55000, CAST('{}' AS JSON), 1);

INSERT INTO courses (id, code, name, duration_text, total_fee_inr, fee_breakup, display_order) VALUES
(CAST('29881920-2048-566e-a511-f76f114e697d' AS UUID), 'ADV_BCOM', 'Advance B.Com', '3 years', 300000,
 CAST('[{"label": "Year 1", "amount_inr": 100000}, {"label": "Year 2", "amount_inr": 100000}, {"label": "Year 3", "amount_inr": 100000}]' AS JSON), 2);

INSERT INTO courses (id, code, name, duration_text, total_fee_inr, fee_breakup, display_order)
VALUES (CAST('27eeb92a-9758-538c-8a65-296b571d9bcf' AS UUID), 'PGDM', 'PGDM', '2 years', 550000, CAST('{}' AS JSON), 3);

INSERT INTO site_settings (id, social_links) VALUES (1, CAST('{}' AS JSON));

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;
