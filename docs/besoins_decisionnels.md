# Mise en place d'un système décisionnel pour la société Olist

## 1. Contexte

La société Olist, place de marché brésilienne, souhaite améliorer sa performance à l'aide d'un système décisionnel.

Le contexte détaillé et la description des neuf tables de données figurent dans le README du projet.

## 2. Questions à résoudre

Voici les questions qui ont été recensées et auxquelles devrait répondre le système mis en place.

### 2.1 Ventes et produits

- Quels sont les produits et les catégories qui se vendent le mieux ?
- Quels sont les produits en perte de vitesse (baisse du chiffre d'affaires d'un trimestre à l'autre) ?
- Quels sont les produits qui contribuent très peu au chiffre d'affaires pour un État et une année donnés ? Est-ce que ces produits peuvent être retirés du catalogue ?
- Quelle est l'évolution mensuelle du chiffre d'affaires et du nombre de commandes ? Observe-t-on une saisonnalité (Black Friday) ?
- Quels sont les États qui génèrent le plus de chiffre d'affaires ?
- Quelle est la part des frais de livraison dans le prix payé, par catégorie de produits ?
- Est-ce que les frais de livraison dépendent du poids et des dimensions du produit ?

### 2.2 Livraison et satisfaction

- Quel est le taux de livraison dans les délais, par État et par mois ?
- Quel est le retard moyen des commandes livrées en retard ?
- Est-ce que les retards de livraison font baisser la note de satisfaction ?
- Quelles sont les catégories de produits qui reçoivent les moins bonnes notes ?

### 2.3 Clients

- Quels groupes de clients sont identifiés (segmentation RFM : récence, fréquence, montant) ?
- Quels sont les clients de plus forte valeur (chiffre d'affaires cumulé) ?
- Quel est le taux de réachat, et comment évolue la fidélité par cohorte de premier achat ?
- Est-ce qu'un client satisfait (bonne note) rachète davantage ?

### 2.4 Vendeurs

- Quels sont les vendeurs qui font le plus de ventes ?
- Quels sont les vendeurs qui performent le mieux par État, par catégorie et par ancienneté d'activité ?
- Quels vendeurs proposent des produits qui génèrent le plus de chiffre d'affaires, avec les meilleures notes et le moins de retards ?

### 2.5 Paiements

- Quels sont les modes de paiement les plus utilisés ?
- Est-ce que le paiement en plusieurs échéances fait augmenter la valeur du panier ?
- Quelle est la valeur moyenne d'une commande (panier moyen) par catégorie, par État et par mode de paiement ?

### 2.6 Analyses statistiques et avancées

- Quelle est la moyenne et l'écart-type du chiffre d'affaires par commande, par vendeur et par mois ?
- Quelles sont les variables qui expliquent le mieux le montant d'une commande (catégorie, poids, État du client, nombre d'échéances, frais de livraison) ?
- Y a-t-il une différence significative entre la moyenne du chiffre d'affaires par vendeur de l'État de São Paulo et celle des vendeurs des autres États ?
- Y a-t-il une différence significative entre la note moyenne des commandes livrées à temps et celle des commandes livrées en retard ?

## 3. Adaptation des besoins aux données disponibles

Certaines questions classiques d'un système décisionnel (marge, remises, commerciaux) ne peuvent pas être posées telles quelles, car le jeu de données Olist ne contient pas les informations nécessaires. Elles ont été reformulées plutôt qu'abandonnées.

| Question classique | Équivalent retenu pour Olist | Raison |
| --- | --- | --- |
| Marge générée par un groupe de produits | Chiffre d'affaires hors frais de livraison, et part du fret | Aucune donnée de coût d'achat : on mesure le chiffre d'affaires, pas la marge |
| Les remises font-elles augmenter les ventes ou la marge ? | Le paiement en plusieurs échéances fait-il augmenter le panier ? | Aucune donnée de remise dans les tables |
| Commerciaux par pays, sexe, âge, salaire | Vendeurs par État, catégorie, ancienneté d'activité | Les vendeurs sont des entreprises indépendantes, sans attributs personnels |
| Pays | État brésilien | Toutes les commandes sont passées au Brésil |
| Clients les plus rentables | Clients de plus forte valeur | Même raison que pour la marge |
| Fournisseurs rentables | Vendeurs performants (chiffre d'affaires, notes, retards) | Olist ne distingue pas de fournisseurs |

Ces limites sont documentées pour éviter de présenter des indicateurs qui sembleraient justes mais ne reposeraient sur aucune donnée.

## 4. Besoins fonctionnels

| Besoin | Description |
| --- | --- |
| **Requêtes** | Interroger une mesure selon plusieurs axes, agréger (roll-up) et détailler (drill-down) : année, trimestre, mois, jour ; État, ville ; catégorie, produit |
| **Reporting** | Quatre tableaux de bord : vue direction (ventes), livraison et satisfaction, analyse des clients, performance des vendeurs |
| **Analyses avancées** | Segmentation RFM, analyse de cohortes, régression, tests d'hypothèse (comparaison de moyennes) |

## 5. Indicateurs clés de performance (KPI)

| KPI | Définition |
| --- | --- |
| Chiffre d'affaires | Somme des prix des articles, hors frais de livraison, pour les commandes non annulées et non indisponibles |
| Nombre de commandes | Nombre de commandes distinctes |
| Panier moyen | Chiffre d'affaires divisé par le nombre de commandes comptées dans le chiffre d'affaires |
| Taux de réachat | Clients ayant au moins deux commandes, divisés par le nombre total de clients (identifiés par `customer_unique_id`) |
| Taux de livraison dans les délais | Commandes livrées à la date estimée ou avant, divisées par les commandes livrées |
| Retard moyen | Écart en jours entre la date de livraison et la date estimée, pour les commandes en retard |
| Note moyenne | Moyenne des notes de satisfaction (1 à 5) |
| Taux d'annulation | Commandes annulées divisées par l'ensemble des commandes |

## 6. Axes d'analyse et mesures

Les questions ci-dessus ont deux niveaux de détail différents, ce qui conduit à deux tables de faits qui partagent trois dimensions conformes (date, client, statut de commande) : un modèle en constellation de faits.

| Domaine | Table de faits (grain) | Mesures | Axes d'analyse |
| --- | --- | --- | --- |
| Ventes et produits | `fact_sales` (un article d'une commande) | prix, frais de livraison | date, client, produit, vendeur, statut |
| Livraison, satisfaction, paiements | `fact_orders` (une commande) | délai et retard de livraison, livraison à temps, montant payé, nombre d'échéances, mode de paiement, note de satisfaction | date (achat, approbation, expédition, livraison, date estimée), client, statut |

Chaque question de la section 2 peut être traitée avec ces deux tables et leurs cinq dimensions (date, client, produit, vendeur, statut de commande).

## 7. Périmètre et contraintes

- **Période couverte :** septembre 2016 à octobre 2018. Les analyses de tendance portent sur janvier 2017 à août 2018 (20 mois complets), car les périodes de début et de fin contiennent très peu de commandes et novembre 2016 est absent.
- **Qualité des données :** 23 anomalies ont été identifiées et documentées, avec une règle de traitement pour chacune (doublons de géolocalisation, identifiant client généré par commande, dates de livraison manquantes, etc.).
- **Hors périmètre :** données en temps réel, coûts d'achat et marges, campagnes marketing.

## 8. Conclusion

Il faut donc construire un entrepôt de données (modèle en constellation de faits : deux tables de faits partageant des dimensions conformes (date, client, statut de commande)) capable de répondre aux besoins de requête, de reporting et d'analyses avancées exprimés ci-dessus, alimenté par un processus ETL qui applique les règles de qualité documentées.
