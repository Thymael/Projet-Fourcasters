## Comparaison avec des modèles plus simples
Avant de conserver le Random Forest, nous avons comparé ses résultats avec plusieurs modèles plus simples en utilisant exactement les mêmes données et la même séparation chronologique entre apprentissage et test.

| Modèle                |    Accuracy |  F1 macro |
| --------------------- | ----------: | --------: |
| Classe majoritaire    |     32,35 % |     0,122 |
| Régression logistique |     29,06 % |     0,253 |
| Arbre de décision     |     37,46 % |     0,275 |
| Random Forest         | **52,59 %** | **0,311** |

La régression logistique obtient une accuracy plus faible que la classe majoritaire, mais son F1 macro est meilleur. Elle répartit donc davantage ses prédictions entre les différentes classes au lieu de privilégier principalement la classe la plus fréquente.

L'arbre de décision améliore les deux indicateurs par rapport à la régression logistique, mais reste nettement en dessous du Random Forest.

Le Random Forest donne les meilleurs résultats sur les deux indicateurs. Cette comparaison nous a donc permis de vérifier que l'utilisation d'un modèle un peu plus complexe apporte un gain réel sur notre jeu de données.

Nous conservons malgré tout ces résultats comme une comparaison uniquement. La régression logistique et l'arbre de décision ne sont pas intégrés au pipeline principal.
