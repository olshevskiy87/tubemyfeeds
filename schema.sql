CREATE OR REPLACE FUNCTION trg_fs_update_send() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
    perform id
    from channels_settings fc
    where fc.id = NEW.channel_id
        and fc.added_dt > NEW.published;

    if found then
        NEW.sent = now();
    end if;

    return NEW;
end;
$$;

CREATE TABLE IF NOT EXISTS channels_settings (
    id serial,
    ch_id text NOT NULL,
    ch_name text,
    added_dt timestamp with time zone DEFAULT now() NOT NULL,
    active boolean DEFAULT true
);

CREATE TABLE IF NOT EXISTS feeds_send (
    id serial,
    channel_id integer NOT NULL,
    entry_id text UNIQUE NOT NULL,
    published timestamp with time zone,
    title text,
    link text,
    sent timestamp with time zone
);

CREATE TRIGGER trg_fs_on_insert
BEFORE INSERT ON feeds_send
FOR EACH ROW EXECUTE PROCEDURE trg_fs_update_send();
