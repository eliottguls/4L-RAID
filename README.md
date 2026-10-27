# Manuel 3D · Renault 4 GTL Clan 1989

Manuel d’atelier interactif pour préparer la 4L au 4L Trophy : un modèle 3D de la voiture (carrosserie, intérieur, moteur, trains, freins, électricité) où l’on clique sur une pièce pour voir sa fiche, et où l’on cherche « comment changer… » pour lancer la procédure en vue éclatée, étape par étape.

Le contenu vient de la Revue Technique Automobile « Renault 4 GTL » (étude de base + évolutions depuis 1980).

## Ce que fait le site

- **Modèle 3D** : rotation, zoom, clic sur une pièce. Mode rayons X, vue éclatée, masquage par système, couleur de carrosserie.
- **Recherche** en langage courant : « mon moteur chauffe », « changer le delco », « embrayage patine »…
- **43 procédures** : outils, ingrédients, couples de serrage et étapes. Chaque étape déplace dans la 3D les pièces à déposer.
- **83 fiches pièces** avec les valeurs de la RTA (couples, jeux, capacités, références).
- **Vis et fixations** : environ 65 jeux de vis, écrous, bouchons et goupilles sont modélisés. À chaque étape, ceux à dévisser sortent en tournant et s’allument en bleu, avec le couple de serrage. Pour la culasse, l’ordre de serrage s’affiche en numéros. Dans une fiche pièce, la liste « Vis et fixations » permet de voir chaque jeu se dévisser.
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
- `FASTENERS` : les jeux de fixations (nom, pièce, nombre, couple, pages). `STEP_FASTENERS` relie les étapes aux fixations : `unscrew` (à dévisser), `screw` (à revisser), `sequence` (ordre de serrage numéroté).

Le modèle 3D a deux couches :

- `models/*.glb` : toute la voiture modélisée dans Blender. `caisse.glb` : carrosserie (portes, hayon, capot, vitrages, pare-chocs, calandre, phares, feux, essuie-glace) ; `chassis.glb` : plateforme, roues 145SR13 sur jantes 400B13 (marquages de flanc, valve, masses d'équilibrage), roue de secours, réservoir, échappement ; `interieur.glb` : sièges, banquette, planche de bord, volant avec commodos et barillet, levier, pédalier, frein à main, ceintures ; `equipements.glb` : radiateur, motoventilateur, batterie, alternateur et courroie, démarreur, fusibles, bobine, lave-glace, maître-cylindre, limiteur, durites. `moteur.glb` : moteur avec ses pièces internes (chemises, pistons et segments, bielles, vilebrequin et flasques de butée, arbre à cames, culbuterie, soupapes avec sièges, guides et clavettes, chambres de combustion, chaîne et tendeur, pompe à huile à pignons) ; `transmission.glb` : embrayage (disque, mécanisme, butée et fourchette, câble), carter d'embrayage, boîte-pont 354 pièce par pièce (carter et couvercles, arbre d'embrayage et arbre primaire, arbre secondaire avec pignons fous et synchros, marche arrière, fourchettes, différentiel et couple conique, avec le nombre de dents de la RTA) et transmissions (joints GI 62 et GE 76 détaillés) ; `trains.glb` : trains, direction et freins pièce par pièce (triangles et rotules, tirants de chasse, moyeux et roulements, barres de torsion et stabilisatrice, crémaillère et biellettes, étriers et plaquettes, tambours, mâchoires et cylindres de roue) ; `electricite.glb` : faisceaux avant et arrière, avertisseur, centrale clignotante, plafonnier, ampoules et chauffage. Tout est modélisé dans Blender d'après les cotes et les vues éclatées de la RTA, par les scripts de `tools/blender/` :

  ```sh
  pip install bpy          # Blender en module Python
  python3 tools/blender/moteur.py
  python3 tools/blender/transmission.py
  python3 tools/blender/trains.py
  python3 tools/blender/caisse.py
  python3 tools/blender/chassis.py
  python3 tools/blender/interieur.py
  python3 tools/blender/equipements.py
  python3 tools/blender/electricite.py
  ```

  Chaque nœud du glTF porte `extras.partId` (la pièce, clé de `PARTS`) ou `extras.fx` (une vis : jeu, sens et course de dévissage). Dans `PARTS`, `with` indique l'ensemble avec lequel une pièce part quand on le dépose (les pignons avec la boîte, les soupapes avec la culasse). `tools/view.html?f=../models/moteur.glb` affiche un modèle seul (options dans le fichier : `only`, `hide`, `explode`, `fx`, `xray`).
- `js/car.js` : une version simplifiée de la voiture construite en code, affichée tout de suite puis remplacée pièce par pièce par les `.glb` (elle reste en secours si un modèle ne se charge pas).

Dans `js/car.js`, chaque pièce est enregistrée avec `part('id', [décalage éclaté x, y, z], [maillages])`, et l’`id` doit correspondre à une entrée de `PARTS`. Les fixations sont posées avec `fasten(groupe, 'id-du-jeu', positions, options)`, et l’id doit correspondre à une entrée de `FASTENERS`.

## Limites

- Le moteur, la boîte et les trains reprennent les cotes de la RTA (alésage, course, entraxe de bielle, diamètres de soupapes, garnitures d'embrayage, nombres de dents des pignons, diamètres de disques et de tambours, voies, empattements…). Ce que la RTA ne cote pas (entraxe des cylindres, entraxe des arbres de boîte, modules de denture, formes de fonderie, bras de suspension) est estimé d'après ses vues éclatées et ses coupes : fidèle à l'œil, pas au millimètre. La carrosserie est encore procédurale et simplifiée.
- Le nombre et la position des vis sont **indicatifs**, sauf quand la RTA les donne (vis de culasse, écrous de roue, bouchons…) : la fiche indique alors la page.
- Les numéros de page renvoient au PDF scanné (1 à 93), pas à la pagination imprimée de la RTA.
- Le texte a été relu à partir d’un scan : en cas de doute sur une valeur, vérifie la page de la RTA indiquée.
- GitHub Pages ne fait que du statique : pas de serveur, donc pas de chat IA intégré ni de comptes utilisateurs.

## Licences

Three.js (MIT) et pdf.js (Apache 2.0), licences dans `vendor/`.
