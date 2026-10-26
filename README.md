# Manuel 3D · Renault 4 GTL Clan 1989

Manuel d’atelier interactif pour préparer la 4L au 4L Trophy : un modèle 3D de la voiture (carrosserie, intérieur, moteur, trains, freins, électricité) où l’on clique sur une pièce pour voir sa fiche, et où l’on cherche « comment changer… » pour lancer la procédure en vue éclatée, étape par étape.

Le contenu vient de la Revue Technique Automobile « Renault 4 GTL » (étude de base + évolutions depuis 1980).

## Ce que fait le site

- **Modèle 3D** : rotation, zoom, clic sur une pièce. Mode rayons X, vue éclatée, masquage par système, couleur de carrosserie.
- **Recherche** en langage courant : « mon moteur chauffe », « changer le delco », « embrayage patine »…
- **33 procédures** : outils, ingrédients, couples de serrage et étapes. Chaque étape déplace dans la 3D les pièces à déposer.
- **55 fiches pièces** avec les valeurs de la RTA (couples, jeux, capacités, références).
- **Entretien** : intervalles et capacités.
- **Ma RTA** : charge ton PDF de la revue technique pour ouvrir la bonne page (avec les schémas) depuis chaque fiche. Le PDF reste dans ton navigateur et n’est jamais publié.
- **Hors-ligne** : après une première visite avec du réseau, le site marche sans connexion (utile dans le désert).
- Liens partageables : `#/proc/plaquettes/3` ouvre l’étape 3 du changement de plaquettes.

## Publier avec GitHub Pages

1. Dans le dépôt : **Settings → Pages**.
2. *Build and deployment* → Source : **Deploy from a branch**.
3. Branch : **main**, dossier **/ (root)**, puis **Save**.
4. Après une minute environ, le site est sur `https://eliottguls.github.io/4L-RAID/`.

Aucun build n’est nécessaire : ce sont des fichiers statiques (HTML, CSS, JavaScript), et Three.js et pdf.js sont inclus dans `vendor/`.

## Tester en local

```sh
python3 -m http.server 8000
# puis ouvrir http://localhost:8000
```

(Ouvrir `index.html` directement en double-cliquant ne marche pas : les modules JavaScript ont besoin d’un petit serveur.)

## Ajouter ou corriger une procédure

Tout le contenu est dans `js/data.js` :

- `PARTS` : les fiches pièces (nom, système, description, caractéristiques, pages du PDF).
- `PROCEDURES` : les interventions. Chaque étape peut avoir `remove` (pièces qui s’écartent dans la 3D) et `focus` (pièces mises en évidence).

Le modèle 3D est dans `js/car.js`. Chaque pièce est enregistrée avec `part('id', [décalage éclaté x, y, z], [maillages])`, et l’`id` doit correspondre à une entrée de `PARTS`.

## Limites

- Le modèle 3D est **procédural et simplifié** (formes géométriques placées aux cotes de la RTA : empattement, voies, porte-à-faux…). Il sert à situer les pièces, pas à les représenter fidèlement. On peut le remplacer plus tard par un vrai modèle `.glb`.
- Les numéros de page renvoient au PDF scanné (1 à 93), pas à la pagination imprimée de la RTA.
- Le texte a été relu à partir d’un scan : en cas de doute sur une valeur, vérifie la page de la RTA indiquée.
- GitHub Pages ne fait que du statique : pas de serveur, donc pas de chat IA intégré ni de comptes utilisateurs.

## Licences

Three.js (MIT) et pdf.js (Apache 2.0), licences dans `vendor/`.
