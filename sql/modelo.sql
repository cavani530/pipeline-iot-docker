CREATE TABLE IF NOT EXISTS temperature_readings (
    reading_id text PRIMARY KEY,
    sala text NOT NULL,
    ambiente text NOT NULL CHECK (ambiente IN ('In','Out')),
    instante timestamp NOT NULL,
    temperatura double precision NOT NULL
);
CREATE OR REPLACE VIEW media_por_ponto AS
SELECT sala, ambiente, COUNT(*) AS leituras, AVG(temperatura) AS media
FROM temperature_readings GROUP BY sala, ambiente;

CREATE OR REPLACE VIEW leituras_por_hora AS
SELECT horas.hora, COUNT(r.reading_id) AS contagem
FROM generate_series(0,23) AS horas(hora)
LEFT JOIN temperature_readings r ON EXTRACT(HOUR FROM r.instante) = horas.hora
GROUP BY horas.hora;

CREATE OR REPLACE VIEW temp_max_min_por_dia AS
SELECT instante::date AS dia, MAX(temperatura) AS maxima, MIN(temperatura) AS minima
FROM temperature_readings GROUP BY instante::date;
