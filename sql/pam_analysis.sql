-- PAM portfolio SQL queries
-- These queries target pam_mobilite.db after `make pam-pipeline`.

-- 1. Row counts by operational domain.
SELECT * FROM vw_pam_quality_summary;

-- 2. Reservations by transport date and status.
SELECT
    date_transport,
    statut_reservation,
    COUNT(*) AS nb_reservations
FROM vw_reservations_operationales
GROUP BY date_transport, statut_reservation
ORDER BY date_transport, statut_reservation;

-- 3. Reservations without planned trips.
SELECT
    reservation_id,
    usager_id,
    ville,
    date_transport,
    heure_souhaitee,
    statut_reservation
FROM vw_reservations_operationales
WHERE trajet_id IS NULL
ORDER BY date_transport, heure_souhaitee;

-- 4. Regulation events and delay minutes by trip.
SELECT
    trajet_id,
    reservation_id,
    vehicule_id,
    nb_evenements,
    minutes_retard
FROM vw_trajets_regulation
ORDER BY minutes_retard DESC, nb_evenements DESC;

-- 5. Vehicle utilization.
SELECT
    v.vehicule_id,
    v.statut,
    COUNT(t.trajet_id) AS nb_trajets
FROM vehicules v
LEFT JOIN trajets t ON t.vehicule_id = v.vehicule_id
GROUP BY v.vehicule_id, v.statut
ORDER BY nb_trajets DESC;

-- 6. Wheelchair bookings by city.
SELECT
    u.ville,
    COUNT(*) AS nb_reservations_fauteuil
FROM reservations r
JOIN usagers u ON u.usager_id = r.usager_id
WHERE r.besoin_fauteuil = 'Oui'
GROUP BY u.ville
ORDER BY nb_reservations_fauteuil DESC;

-- 7. Event type distribution.
SELECT
    event_type,
    COUNT(*) AS nb_evenements
FROM regulation_events
GROUP BY event_type
ORDER BY nb_evenements DESC;
