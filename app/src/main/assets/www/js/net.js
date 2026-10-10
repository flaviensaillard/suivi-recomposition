/*
 * Transport volontairement inactif.
 *
 * L'ancien code envoyait une clé stockée dans localStorage et ne faisait qu'une
 * lecture unidirectionnelle. Tant qu'il n'existe pas d'authentification par
 * personne, de file d'attente et de gestion des conflits, aucune requête réseau
 * ne doit partir de la coque mobile.
 */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};

    function synchroniserSupabase(cb) {
        var resultat = {
            synchronise: false,
            etat: 'desactivee',
            message: 'Synchronisation indisponible : les données restent sur cet appareil. Aucune donnée n’a été envoyée.'
        };
        if (typeof cb === 'function') cb(resultat);
        return resultat;
    }

    EQ.net = {
        synchroniserSupabase: synchroniserSupabase
    };
})(typeof window !== 'undefined' ? window : this);
