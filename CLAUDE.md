# Projet : site de révision Physique 2mm (Technion 114075)

Site statique de révision pour l'examen de Physique 2mm (électromagnétisme), session d'été.
Examen : vendredi 30/10/2026, QCM de 12 questions, 3 heures.
L'auteur (Meyer) travaille en français et étudie en hébreu. Le site sera partagé avec d'autres étudiants via un lien.

## Langues (règles strictes)
- **Interface** (menus, boutons, titres de navigation, messages, compteur) : 100 % **anglais**.
- **Énoncés des questions** : **hébreu uniquement**, tels quels, exactement comme dans le PDF. Utiliser une image recadrée du PDF. Si l'énoncé a un schéma, il est inclus dans l'image (jamais redessiné). S'il n'y a pas de schéma, ne pas en ajouter.
- **Leçons et corrections** : **français ET hébreu**, avec une bascule FR / HE. Pas d'anglais dans le contenu pédagogique.
- Texte hébreu en `dir="rtl"`, formules toujours en LTR.

## Programme
- Il n'y a pas de planning de révision. Les **chapitres suivent le syllabus** `syllabus/syllabus_physique2mm_ete2026.txt` (11 chapitres, de l'électrostatique à l'interférence). Ce fichier **fait foi** pour ce qui est au programme, ce qui est hors programme et les règles de frontière. Le lire en premier. Proposer le découpage final (on peut fusionner ou scinder des chapitres) dans le plan avant de construire.
- **Examens** : dossier `exam/`. Convention de noms : `114075-<année><sp|wn><A|B|C>` ; `sp` = printemps (אביב), `wn` = hiver (חורף) ; `+sol` = énoncé et solution dans le même PDF ; `sol` seul = PDF de solution séparé de l'énoncé. Les 3 fichiers à nom hébreu sont les solutions du printemps 2026 (מועד א, מועד ב, מועד מילואים).
- **Questions hors programme déjà triées** : `syllabus/questions_hors_programme_anciens_examens.md` liste 15 questions à **ne jamais utiliser** (ni en question, ni en exemple), ainsi que des cas « frontière » jugés OK. Elle porte sur 23 examens (2021 printemps → 2026 hiver). Lire ce fichier avant d'extraire quoi que ce soit.
- **Les 3 examens du printemps 2026 (noms hébreux) ne sont PAS triés** dans ce fichier : appliquer toi-même le syllabus à leurs questions, et lister dans le plan chaque question que tu écartes, avec la raison.
- Un exercice dont seule une partie touche un sujet hors programme : sauter cette partie ou ne pas l'inclure, et le signaler dans le plan. Dans le doute (numérotation ou nom d'examen ambigus), demander plutôt que deviner.
- Les sujets hors programme (rappel) : diélectriques dans un condensateur, circuits RLC (et LC pur, par prudence), inductance mutuelle, modèle de Drude, interférence à N fentes, diffraction par une fente simple, potentiel vecteur, rayonnement d'une charge accélérée (champ/puissance rayonnés), dipôle magnétique. En cas de conflit, le syllabus l'emporte.
- **Au programme** : notamment l'expérience de Young (2 fentes), le vecteur de Poynting, la sphère d'information d'une charge accélérée (où est l'information, pas le champ rayonné), les circuits RC et RL.
- Le nombre total de questions N est celui des questions du programme restantes, une fois les questions hors programme retirées. Toujours l'annoncer dans le plan.

## Leçon (avant chaque série d'exercices)
- Intuition physique ET mathématique détaillée : le « pourquoi » derrière le chapitre, cadrage visuel / géométrique, analogies (ex. circuit hydraulique pour RC/RL).
- Quand utiliser quelle loi, et pourquoi.
- Toutes les formules utiles du chapitre, bien mises en forme (KaTeX), jamais en Unicode illisible.
- Pièges connus à inclure quand ils sont pertinents :
  - RL : l'énergie décroît en e^(−2t/τ), pas e^(−t/τ).
  - Méthode des images avec potentiel imposé sur une sphère conductrice : ajouter une charge q₀ = φ₀R/k au centre (absent du formulaire officiel).
  - Biot-Savart : les formes en sinus et cosinus sont identiques par angles complémentaires ; si le pied de la perpendiculaire est dans le segment, les contributions des deux angles s'additionnent.
  - Rapport universel f_B/f_E = β².
  - Invariants de Lorentz (E² − c²B²) : disent si E ou B peut être annulé dans un référentiel inertiel.
- Points faibles à renforcer : transformation relativiste des champs, f.é.m. de mouvement (motional EMF), circuits RL, méthode des images, référentiel tournant dans un solénoïde, potentiel de trois coquilles concentriques.

## Questions et correction
- Sous l'énoncé : boutons א ב ג ד (autant que dans la question).
- Au clic : « Correct » ou « Wrong » immédiatement, puis, en dessous, **deux blocs dans cet ordre** :
  1. **Official solution** : la correction officielle, reprise telle quelle depuis le PDF de l'examen (ou le fichier de solutions correspondant), en image recadrée, sans réécriture.
  2. **Detailed correction** : la correction détaillée de Claude, en français ET en hébreu (bascule FR / HE), qui explique le raisonnement pas à pas et le « pourquoi ».
- Si aucune solution officielle n'existe pour une question, afficher seulement le bloc 2.
- Si la correction de Claude diverge de l'officielle, ne pas la corriger en silence : le signaler explicitement dans le bloc 2 (« Note: differs from official solution ») et le dire à l'auteur à la fin du chapitre.
- Une question terminée = une question répondue.

## Compteur de progression
- Barre de pourcentage globale : avec N questions au total, chaque question terminée ajoute 100/N %.
- Progression par chapitre, plus un petit score de réussite.
- Sauvegarde dans `localStorage` (pas de compte, pas de serveur). Chaque visiteur a sa propre progression. Bouton « Reset progress ».

## Qualité (important : d'autres étudiants vont s'en servir)
- La bonne réponse (א ב ג ד) vient de la solution officielle quand elle existe. Sinon, résoudre soi-même, vérifier numériquement et symboliquement (Python / sympy), et afficher un badge « To verify » en cas de doute.
- La correction détaillée de Claude doit être vérifiée de façon indépendante, qu'il y ait une solution officielle ou non.
- Ne jamais inventer ni modifier un énoncé.
- Vérifier chaque lien, image et formule dans un navigateur avant de terminer un chapitre.

## Technique
- Site 100 % statique : HTML / CSS / JS simples, **aucune étape de build**, chemins relatifs uniquement, prêt pour GitHub Pages.
- Données des questions en JSON, images dans un dossier dédié.
- Design propre, fluide, motivant, adapté au téléphone. Pas de sur-ingénierie.
- Un commit par chapitre.
