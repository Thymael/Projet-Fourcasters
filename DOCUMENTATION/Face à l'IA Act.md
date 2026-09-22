# Fourcasters face à l'AI Act

Fourcasters contient un modèle de classification qui essaie de reproduire les niveaux de danger publiés par Météo-France.

Le modèle est un **prototype étudiant**. Il ne prend aucune décision automatiquement et n'est pas utilisé pour attribuer un droit, un emploi, un soin ou des moyens de secours.

Streamlit permet seulement de tester le modèle sur des observations de la période de test. Les niveaux officiels Météo-France restent la référence.

ChatGPT a également été utilisé comme outil d'aide pendant le développement et la rédaction. Il n'est pas intégré au pipeline.

## Précautions retenues

- expliquer clairement que le modèle est expérimental ;
- garder une validation humaine ;
- vérifier le code et les textes produits avec l'aide d'une IA ;
- ne jamais transmettre de clés API ou de secrets ;
- ne pas présenter une prédiction du modèle comme une décision opérationnelle.

Le risque dépend surtout de l'usage qui est fait du modèle. Dans Fourcasters, l'usage reste pédagogique et exploratoire.
