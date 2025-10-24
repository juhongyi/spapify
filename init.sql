CREATE TABLE artists (
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(255)    NOT NULL,
    lastfm_url  VARCHAR(255)    NOT NULL UNIQUE
);
CREATE TABLE tracks (
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(255)    NOT NULL,
    artist_id   INTEGER         NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    lastfm_url  VARCHAR(255)    NOT NULL UNIQUE
);
CREATE TABLE chart_histories (
    id          SERIAL          PRIMARY KEY,
    track_id    INTEGER         NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    playcount   INTEGER         NOT NULL,
    listener    INTEGER         NOT NULL,
    chart_date  TIMESTAMP       NOT NULL,
    rank        SMALLINT        NOT NULL,
    UNIQUE(track_id, chart_date)
);
