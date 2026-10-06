/* Contrôleur principal de l'application Équilibre.
   Navigation, routage entre les cinq écrans et gestion des événements interactifs. */
(function (root) {
    'use strict';
    var EQ = root.EQ;
    var U = EQ.util, UI = EQ.ui, Store = EQ.store, Views = EQ.views, Net = EQ.net;

    var ONGLETS = {
        bord: { titre: 'Tableau de bord', sous: 'recomposition corporelle' },
        pesee: { titre: 'Pesée & Tendance', sous: 'mesures & graphiques' },
        seances: { titre: 'Mes séances', sous: 'programme 30 min & séries' },
        menus: { titre: 'Menus & Courses', sous: 'planning, recettes & foyer' },
        apps: { titre: 'Applications Web', sous: 'coque Suivi ⇄ Menus' }
    };

    var etat = {
        onglet: 'bord',
        chargement: false,
        contexte: null
    };

    function obtenirContexte() {
        return {
            reglages: Store.getReglages(),
            logs: Store.getLogs(),
            mensurations: Store.getMensurations(),
            seances: Store.getSeances()
        };
    }

    function rafraichirVue() {
        etat.contexte = obtenirContexte();
        var main = UI.$('#view');
        if (!main) return;

        var html = '';
        switch (etat.onglet) {
            case 'bord':
                html = Views.vueBord(etat.contexte);
                break;
            case 'pesee':
                html = Views.vuePesee(etat.contexte);
                break;
            case 'seances':
                html = Views.vueSeances(etat.contexte);
                break;
            case 'menus':
                html = Views.vueMenus(etat.contexte);
                break;
            case 'apps':
                html = Views.vueApps(etat.contexte);
                break;
            default:
                html = Views.vueBord(etat.contexte);
        }

        main.innerHTML = html;
        main.classList.remove('enter');
        void main.offsetWidth; // Reflow pour redéclencher l'animation
        main.classList.add('enter');

        attacherEvenementsVue();
    }

    function naviguer(onglet) {
        if (!ONGLETS[onglet]) onglet = 'bord';
        etat.onglet = onglet;
        Store.setOnglet(onglet);

        // Mise à jour de la barre supérieure
        var tInfo = ONGLETS[onglet];
        var titreEl = UI.$('#titreOnglet');
        if (titreEl) {
            titreEl.innerHTML = U.echapper(tInfo.titre) +
                '<span class="sub" id="sousTitre">' + U.echapper(tInfo.sous) + '</span>';
        }

        // Mise à jour de la barre inférieure
        var boutons = UI.$$('#nav button[data-onglet]');
        boutons.forEach(function (b) {
            if (b.getAttribute('data-onglet') === onglet) {
                b.classList.add('actif');
            } else {
                b.classList.remove('actif');
            }
        });

        UI.haptic(8);
        window.scrollTo(0, 0);
        rafraichirVue();
    }

    function attacherEvenementsVue() {
        var main = UI.$('#view');
        if (!main) return;

        // ----------------------------------------------------------- Écran Bord
        var btnAjoutPesee = UI.$('#btnAjoutPeseeRapide', main);
        if (btnAjoutPesee) {
            btnAjoutPesee.onclick = function () {
                Views.feuillePesee(etat.contexte, rafraichirVue);
            };
        }

        var tuileProt = UI.$('#tuileProt', main);
        if (tuileProt) {
            tuileProt.onclick = function () {
                Views.feuillePesee(etat.contexte, rafraichirVue);
            };
        }

        var tuileKcal = UI.$('#tuileKcal', main);
        if (tuileKcal) {
            tuileKcal.onclick = function () {
                Views.feuillePesee(etat.contexte, rafraichirVue);
            };
        }

        var tuileSeance = UI.$('#tuileSeance', main);
        if (tuileSeance) {
            tuileSeance.onclick = function () {
                naviguer('seances');
            };
        }

        var tuileMidi = UI.$('#tuileMidi', main);
        if (tuileMidi) {
            tuileMidi.onclick = function () {
                Views.setSousOngletMenus('planning');
                naviguer('menus');
            };
        }

        var tuileCoursesBord = UI.$('#tuileCoursesBord', main);
        if (tuileCoursesBord) {
            tuileCoursesBord.onclick = function () {
                Views.setSousOngletMenus('courses');
                naviguer('menus');
            };
        }

        // Boutons 1-clic repas types
        var btnsRepas = UI.$$('.btn-noter-repas', main);
        btnsRepas.forEach(function (btn) {
            btn.onclick = function (e) {
                e.stopPropagation();
                var cle = btn.getAttribute('data-repas');
                var r = M.REPAS_TYPES.find(function (x) { return x.cle === cle; });
                if (r) {
                    var logs = Store.getLogs();
                    var auj = logs[logs.length - 1];
                    if (auj) {
                        auj.proteinesG = (auj.proteinesG || 0) + Math.round(r.prot);
                        auj.caloriesKcal = (auj.caloriesKcal || 0) + Math.round(r.kcal);
                        Store.saveLog(auj);
                        UI.toast('✅ ' + r.nom + ' ajouté (+ ' + r.prot + ' g prot)');
                        rafraichirVue();
                    }
                }
            };
        });

        // ---------------------------------------------------------- Écran Pesée
        var btnNouvP = UI.$('#btnNouvPesee', main);
        if (btnNouvP) {
            btnNouvP.onclick = function () {
                Views.feuillePesee(etat.contexte, rafraichirVue);
            };
        }

        var btnNouvM = UI.$('#btnNouvMensurations', main);
        if (btnNouvM) {
            btnNouvM.onclick = function () {
                Views.feuilleMensurations(etat.contexte, rafraichirVue);
            };
        }

        // Points interactifs du graphique
        var cercles = UI.$$('.point-poids', main);
        cercles.forEach(function (c) {
            c.onclick = function () {
                var d = c.getAttribute('data-date');
                var p = c.getAttribute('data-poids');
                var info = UI.$('#graphiqueInfo');
                if (info) {
                    info.innerHTML = '<b>' + U.dateFr(d, { jour: true, court: true }) + '</b> : <span class="up" style="font-weight:700;">' + U.formatKg(p, 1) + '</span>';
                }
                UI.haptic(10);
            };
        });

        // -------------------------------------------------------- Écran Séances
        var chipsSeance = UI.$$('.chips button[data-seance]', main);
        chipsSeance.forEach(function (b) {
            b.onclick = function () {
                Views.setSousOngletSeances(b.getAttribute('data-seance'));
                rafraichirVue();
            };
        });

        // Minuteur de repos
        var btnsTimer = UI.$$('.btn-timer', main);
        btnsTimer.forEach(function (b) {
            b.onclick = function () {
                var sec = parseInt(b.getAttribute('data-sec'), 10);
                Views.demarrerMinuteur(sec);
            };
        });

        // Accordéons
        var accordeons = UI.$$('.accordeon', main);
        accordeons.forEach(function (acc) {
            var tete = UI.$('.tete', acc);
            if (tete) {
                tete.onclick = function () {
                    acc.classList.toggle('ouvert');
                    UI.haptic(6);
                };
            }
        });

        // Validation de la séance
        var btnValider = UI.$('#btnValiderSeance', main);
        if (btnValider) {
            btnValider.onclick = function () {
                Store.saveSeance({
                    date: U.dateIso(new Date()),
                    type: 'A',
                    nom: 'Séance d’entraînement validée',
                    dureeMin: 30,
                    rpe: 8
                });
                UI.toast('🎉 Félicitations ! Séance enregistrée.');
                Views.setSousOngletSeances('historique');
                rafraichirVue();
            };
        }

        // ---------------------------------------------------------- Écran Menus
        var chipsMenu = UI.$$('.chips button[data-menu-tab]', main);
        chipsMenu.forEach(function (b) {
            b.onclick = function () {
                Views.setSousOngletMenus(b.getAttribute('data-menu-tab'));
                rafraichirVue();
            };
        });

        // Liste de courses interactive
        var lignesCourses = UI.$$('.ligne-course', main);
        lignesCourses.forEach(function (l) {
            l.onclick = function () {
                var id = l.getAttribute('data-id');
                Store.toggleCourse(id);
                UI.haptic(10);
                rafraichirVue();
            };
        });

        var btnResetCourses = UI.$('#btnResetCourses', main);
        if (btnResetCourses) {
            btnResetCourses.onclick = function () {
                var liste = Store.getCourses();
                liste.forEach(function (x) { x.pris = false; });
                Store.saveReglages(Store.getReglages());
                UI.toast('Liste réinitialisée pour la nouvelle semaine');
                rafraichirVue();
            };
        }

        // Voir recette
        var btnsVoirRecette = UI.$$('.btn-voir-recette', main);
        btnsVoirRecette.forEach(function (b) {
            b.onclick = function () {
                var id = b.getAttribute('data-id');
                Views.feuilleRecette(id);
            };
        });

        // Recherche instantanée de recettes
        var inRecherche = UI.$('#rechercheRecette', main);
        if (inRecherche) {
            inRecherche.oninput = function () {
                var q = inRecherche.value.toLowerCase().trim();
                var cartes = UI.$$('.card-recette', main);
                cartes.forEach(function (card) {
                    var texte = card.textContent.toLowerCase();
                    card.style.display = texte.indexOf(q) >= 0 ? '' : 'none';
                });
            };
        }

        // ----------------------------------------------------------- Écran Apps
        var btnBascule = UI.$('#btnBasculeApp', main);
        if (btnBascule) {
            btnBascule.onclick = function () {
                var r = Store.getReglages();
                r.appCouranteWeb = r.appCouranteWeb === 'menus' ? 'suivi' : 'menus';
                Store.saveReglages(r);
                UI.haptic(10);
                rafraichirVue();
            };
        }

        var btnReload = UI.$('#btnReloadWeb', main);
        if (btnReload) {
            btnReload.onclick = function () {
                var frame = UI.$('#frameStreamlit', main);
                var chargement = UI.$('#chargementFrame', main);
                if (frame) {
                    if (chargement) chargement.style.display = 'flex';
                    frame.src = frame.src;
                }
            };
        }

        var btnOuvrirNav = UI.$('#btnOuvrirNav', main);
        if (btnOuvrirNav) {
            btnOuvrirNav.onclick = function () {
                var r = Store.getReglages();
                var url = r.appCouranteWeb === 'menus' ? r.urlMenus : r.urlSuivi;
                if (typeof root.Native !== 'undefined' && root.Native.openExternal) {
                    root.Native.openExternal(url);
                } else {
                    window.open(url, '_blank');
                }
            };
        }

        var frame = UI.$('#frameStreamlit', main);
        if (frame) {
            frame.onload = function () {
                var chargement = UI.$('#chargementFrame', main);
                if (chargement) chargement.style.display = 'none';
            };
        }
    }

    // ------------------------------------------------------------- Démarrage
    function demarrer() {
        // Barre de navigation inférieure
        var nav = UI.$('#nav');
        if (nav) {
            nav.addEventListener('click', function (e) {
                var b = e.target.closest ? e.target.closest('button[data-onglet]') : null;
                if (!b) return;
                naviguer(b.getAttribute('data-onglet'));
            });
        }

        // Bouton Rafraîchir
        var btnRefresh = UI.$('#btnRefresh');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', function () {
                btnRefresh.classList.add('spin');
                UI.toast('Actualisation…');
                Net.synchroniserSupabase(function () {
                    btnRefresh.classList.remove('spin');
                    rafraichirVue();
                });
            });
        }

        // Bouton Réglages
        var btnReglages = UI.$('#btnReglages');
        if (btnReglages) {
            btnReglages.addEventListener('click', function () {
                Views.feuilleReglages(obtenirContexte(), function () {
                    rafraichirVue();
                });
            });
        }

        var ongletInitial = Store.getOnglet() || 'bord';
        naviguer(ongletInitial);
    }

    // Gestion du bouton retour Android
    function onBack() {
        var voile = UI.$('#voile');
        if (voile && voile.classList.contains('ouvert')) {
            UI.fermerFeuille();
            return true;
        }
        if (etat.onglet !== 'bord') {
            naviguer('bord');
            return true;
        }
        return false;
    }

    root.App = {
        demarrer: demarrer,
        naviguer: naviguer,
        rafraichir: rafraichirVue,
        onBack: onBack
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', demarrer);
    } else {
        demarrer();
    }
})(typeof window !== 'undefined' ? window : this);
