CREATE TABLE IF NOT EXISTS ingestion_receipts (
    ingestion_source TEXT NOT NULL,
    delivery_id TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ingestion_source, delivery_id)
);

CREATE TABLE IF NOT EXISTS product_cursors (
    source_system TEXT NOT NULL,
    partner_sku TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version > 0),
    content_hash TEXT NOT NULL,
    snapshot JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_system, partner_sku)
);

CREATE TABLE IF NOT EXISTS product_changes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_system TEXT NOT NULL,
    partner_sku TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version > 0),
    change_type TEXT NOT NULL CHECK (change_type IN ('created', 'updated')),
    changed_fields TEXT[] NOT NULL,
    content_hash TEXT NOT NULL,
    snapshot JSONB NOT NULL,
    ingestion_source TEXT NOT NULL,
    delivery_id TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_system, partner_sku, version),
    FOREIGN KEY (ingestion_source, delivery_id)
        REFERENCES ingestion_receipts (ingestion_source, delivery_id)
);

CREATE INDEX IF NOT EXISTS product_changes_lookup
    ON product_changes (source_system, partner_sku, version);
