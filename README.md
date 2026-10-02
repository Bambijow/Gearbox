# Gearbox

Gearbox est un plugin Claude Code d'orchestration d'ingénierie. Il transforme une idée, une spec ou une issue GitHub en boucle de développement contrôlée : clarification du besoin, spec minimale, DAG de tâches, routage Claude/Codex par modèle et effort, TDD/SDD, workers isolés, reviews croisées, simplification Ponytail, vérifications, apprentissage durable dans `docs/solutions/`, puis PR documentée pour humains.

Le thread Claude principal agit comme **control plane** : il analyse, planifie, route, inspecte et arbitre, mais il ne modifie pas le code produit pendant un run orchestré. Les changements sont délégués à des workers et agents spécialisés, puis revus par le fournisseur opposé en mode `hybrid`.

## Installation depuis GitHub

Le repository `Bambijow/Gearbox` contient directement la source décompressée du plugin ainsi que son marketplace Claude Code.

Sur Claude Code v2.1.275 ou plus récent, le plus simple est une seule commande :

```text
/plugin install gearbox --marketplace Bambijow/Gearbox
```

Sinon, ajoute d'abord le marketplace :

```text
/plugin marketplace add Bambijow/Gearbox
```

puis installe Gearbox :

```text
/plugin install gearbox@gearbox
```

Pour récupérer une nouvelle version publiée dans ce repository, ouvre `/plugin`, sélectionne Gearbox puis **Update now**, ou lance depuis le shell :

```bash
claude plugin update gearbox@gearbox
```

Une session déjà ouverte peut ensuite appliquer la nouvelle version avec `/reload-plugins` lorsque Claude Code le demande.

Le plugin garde sa configuration projet dans `.gearbox/` et ses données temporaires de run dans `.gearbox/runs/`.

### Migration depuis l’ancien Steelthread

Tu n’as **rien à renommer à la main**. Lors du premier appel à une commande `/gearbox:*`, Gearbox détecte un ancien dossier `.steelthread/`. Si `.gearbox/` n’existe pas et qu’aucun ancien run n’est encore verrouillé, il migre automatiquement le dossier vers `.gearbox/` et adapte les références de chemins internes. Les run IDs, branches, issues, PR et preuves existantes sont conservés. Si `.steelthread/` et `.gearbox/` existent tous les deux, Gearbox bloque la migration au lieu de fusionner silencieusement deux états potentiellement divergents.

## Quel point d'entrée utiliser ?

| Situation | Commande recommandée |
| --- | --- |
| J'ai seulement une idée | `/gearbox:brainstorm "mon idée"` |
| J'ai déjà une issue GitHub | `/gearbox:issue <URL-ou-numéro>` |
| J'ai déjà une spec | `/gearbox:loop <chemin-spec>` |
| J'ai un run interrompu | `/gearbox:resume <run-id-ou-issue>` |
| J'ai déjà une PR avec CI/reviews à traiter | `/gearbox:continue-pr <PR>` |
| Je veux nettoyer la mémoire technique | `/gearbox:clean-solutions` |

Pour une issue classique, le mode autonome habituel est :

```text
/gearbox:issue https://github.com/acme/foo/issues/123 --auto --ship
```

Pour continuer également après l'ouverture de la PR :

```text
/gearbox:issue https://github.com/acme/foo/issues/123 --auto --ship --follow-pr
```

## Les 18 commandes

| Commande | Quand l'utiliser | Ce qu'elle fait exactement |
| --- | --- | --- |
| `/gearbox:setup` | Première utilisation sur un repository, ou migration de configuration | Analyse les conventions du repo, détecte tests/lint/typecheck/build/e2e, GitHub, Codex et Ponytail, initialise `.gearbox/config.md`, la politique de risque, les budgets, les modèles Claude/Codex et l'index `docs/solutions/`. Le setup ne modifie pas le produit. |
| `/gearbox:brainstorm "<idée>"` | Quand le besoin est encore flou | Ouvre une conversation de shaping produit/technique. Gearbox inspecte d'abord le repo pour éviter les questions inutiles, maintient un ledger compact de décisions, bloque sur les vraies décisions produit manquantes, puis écrit une spec acceptée. Avec `--issue`, crée ensuite l'issue GitHub ; avec `--auto --ship`, poursuit jusqu'à la PR. |
| `/gearbox:shape <demande>` | Quand la demande est connue mais pas encore assez précise pour coder | Transforme une feature, une issue ou une demande en spec décisionnellement complète. Distingue ce qui peut être déduit du repo, ce qui peut être assumé de façon réversible, et ce qui exige une question utilisateur. Ne lance aucun worker tant que la spec est `SPEC_BLOCKED`. |
| `/gearbox:spec-to-issue <spec>` | Quand une spec doit devenir une issue GitHub | Distille la spec en issue concise : objectif, scope, non-scope, critères d'acceptation, contraintes et vérification. Par défaut produit un draft ; `--create` crée réellement l'issue. La spec reste la source de vérité, l'issue sert de tracker. |
| `/gearbox:spec-to-issues <spec>` | Quand une spec est trop grosse pour une seule issue | Découpe une grande spec en epic + plusieurs issues dépendantes et verticales. Garde la spec comme source de vérité et évite de figer trop tôt le DAG d'implémentation. `--create` crée les issues. |
| `/gearbox:issue <URL-ou-numéro>` | Point d'entrée principal pour une issue GitHub | Charge l'issue, retrouve ou crée la spec, passe le clarification gate, consulte les solutions pertinentes, fait la reconnaissance du repo, construit et pré-valide le DAG, route chaque tâche vers Claude ou Codex avec modèle/effort, lance TDD/SDD, reviews croisées, intégration, Ponytail, vérification, repair loops, `/learn` conditionnel puis éventuellement la PR. |
| `/gearbox:loop <issue-ou-spec-ou-demande>` | Quand tu veux utiliser directement le moteur générique | Lance la boucle convergente depuis une issue, une spec ou une demande locale. Réutilise les artefacts connus et itère seulement sur les gates qui échouent jusqu'à `PASS`, `BLOCKED` ou `MAX_CYCLES`. Peut shipper et suivre la PR. |
| `/gearbox:flow <demande>` | Compatibilité avec l'ancien point d'entrée générique | Alias de compatibilité vers la logique de boucle pour du travail substantiel hors issue. Pour un nouveau workflow, préfère `/gearbox:loop`. |
| `/gearbox:plan <spec-ou-issue>` | Quand tu veux seulement produire/inspecter le plan | Transforme la spec en DAG de petites tranches verticales. Définit dépendances, ownership, critères de vérification, risque, moteur, modèle et effort. Le preflight détecte les tâches concurrentes incompatibles avant de payer des workers. |
| `/gearbox:build <plan-ou-tâche>` | Pour implémenter manuellement un plan déjà approuvé | Exécute le travail via workers délégués. Utilise RED → GREEN → REFACTOR quand le comportement est testable, produit des preuves ciblées et respecte les chemins/contrats de la tâche. Dans un run orchestré, le parent n'a pas d'échappatoire « petit edit ». |
| `/gearbox:debug <symptôme>` | Bug, test rouge, incident ou comportement mystérieux | Reproduit le problème, réduit la surface, construit des hypothèses falsifiables, identifie la root cause, délègue la correction, ajoute une protection de régression et crée un candidat `/learn` si la découverte est réutilisable. |
| `/gearbox:simplify [diff]` | Après intégration, pour réduire le code | Lance un agent frais de simplification. Utilise Ponytail s'il est installé ; sinon applique la discipline interne Gearbox : supprimer duplication, wrappers et abstractions inutiles, préférer stdlib/framework/existant, conserver validation, sécurité et accessibilité. Rejoue ensuite les checks nécessaires. |
| `/gearbox:review [diff|PR]` | Pour une review indépendante | Vérifie conformité à la spec, correctness, sécurité, régressions, tests, risque opérationnel et architecture post-simplification. En mode `hybrid`, les tâches sont déjà revues par le fournisseur opposé ; cette commande sert aussi de review globale. |
| `/gearbox:learn <leçon>` | Après une découverte non évidente qui mérite d'être conservée | Écrit ou réconcilie la connaissance canonique dans `docs/solutions/`. Cherche d'abord les doublons et contradictions, puis choisit création, refresh, merge ou suppression de l'ancienne vérité. Les solutions durables restent courtes et pointent vers les preuves/code pertinents. |
| `/gearbox:clean-solutions [scope]` | Maintenance périodique de `docs/solutions/` | Confronte la mémoire technique au code, tests, specs et solutions plus récentes. Classe chaque note en `KEEP`, `REFRESH`, `MERGE`, `DELETE` ou `BLOCKED`. `--dry-run` montre le plan sans modifier les fichiers. |
| `/gearbox:ship` | Quand le code est prêt à être publié | Vérifie les gates, délègue commit/push, crée ou met à jour la PR et son commentaire technique. La description de PR est compréhensible par un non-tech ; le commentaire technique contient les checks, reviews, changements Ponytail, screenshots UI/UX et 1 à 5 vrais extraits de code critique avec fichier:lignes, justification et focus de review. |
| `/gearbox:resume <run-id|issue|PR>` | Après fermeture/crash/interruption | Recharge `state.json`, réconcilie git, locks, worktrees, budgets et preuves, puis reprend exactement au bon endroit sans relancer les workers déjà terminés et encore valides. Si le run était `SPEC_BLOCKED`, ressort les questions en attente. |
| `/gearbox:continue-pr <PR>` | Après création de la PR, quand CI ou un reviewer humain a parlé | Charge uniquement les nouveaux checks/commentaires, valide les findings au lieu de les accepter aveuglément, construit un repair DAG borné, corrige via workers, repousse sur la même branche et met à jour le même commentaire technique sans rejouer toute l'issue. |

## Flags les plus utiles

| Flag | Effet |
| --- | --- |
| `--auto` | Automatise les décisions d'ingénierie raisonnables et les cycles de réparation. N'autorise pas Gearbox à inventer une décision produit/métier. |
| `--ship` | Continue jusqu'au commit, push et création/mise à jour de la PR. |
| `--follow-pr` | Après le ship, continue sur les échecs CI et retours de review dans les budgets définis. |
| `--models hybrid` | Autorise Gearbox à choisir Claude ou Codex tâche par tâche. En hybrid, l'implémentation est revue par le fournisseur opposé. |
| `--models claude-heavy` | Favorise Claude pour l'implémentation, tout en pouvant garder Codex comme reviewer/outillage si disponible. |
| `--models codex-heavy` | Favorise Codex pour l'implémentation. |
| `--models ask` | Force un nouveau choix interactif de politique modèles pour le run courant. |
| `--no-codex` | Désactive Codex pour ce run. |
| `--workers N` | Limite le nombre de workers parallèles. |
| `--max-cycles N` | Limite le nombre de repair cycles. |
| `--token-profile efficient` | Profil par défaut : contexte borné, handoffs par fichiers, reviews proportionnées au risque. |
| `--token-profile strict` | Vérification/review plus lourde pour les changements sensibles. |

## Routing des modèles

Gearbox route séparément le **fournisseur**, le **modèle** et l'**effort** pour chaque tâche.

### Codex

Le registre par défaut reste volontairement petit :

| Niveau | Modèle | Usage typique |
| --- | --- | --- |
| `bounded` | GPT-6 Luna | docs, changelog, mapping, fixtures, renommages, wiring simple |
| `normal` | GPT-6.1 Sol | feature/bug normal, implémentation bornée multi-fichiers |
| `deep` | GPT-6.1 Sol avec effort plus élevé | migrations, auth, concurrence, invariants de persistance, debug difficile |
| `exceptional` | GPT-6 Astra | uniquement après vraie escalade ou cas exceptionnellement critique/ambigu |

Astra n'est pas choisi simplement parce qu'une tâche est « importante ». Gearbox augmente d'abord l'effort de Sol. Les tâches triviales ont un plafond dur qui les empêche d'atteindre Astra.

### Review croisée en mode hybrid

En `hybrid`, chaque tâche est revue par **l'autre fournisseur** avant intégration :

```text
Claude implémente → Codex review
Codex implémente  → Claude review
```

Le reviewer reçoit seulement le packet de tâche, le diff et les preuves ciblées. Il n'hérite pas du raisonnement conversationnel de l'implémenteur.

## Control plane : le parent ne code pas

Pour `/issue`, `/loop`, `/flow`, `/brainstorm` lorsqu'il continue vers l'implémentation, `/resume` et `/continue-pr`, un hook `PreToolUse` active une frontière stricte :

- le thread principal peut lire, planifier, dispatcher, comparer des diffs et arbitrer ;
- il peut écrire les specs/plans et les artefacts transients sous `.gearbox/runs/` ;
- il ne peut pas modifier le code produit, les tests produit, les migrations ou faire un `git add` pour « aider » ;
- même un changement d'une ligne est envoyé à un worker peu coûteux ;
- l'intégration, la simplification, la vérification, le learning et le shipping utilisent des agents dédiés.

## Mémoire durable

Gearbox stocke les apprentissages utiles dans :

```text
docs/solutions/
```

`docs/solutions/index.md` sert d'index léger pour éviter de relire tout le corpus à chaque issue. `/learn` écrit seulement quand la découverte est suffisamment non évidente et réutilisable ; `/clean-solutions` supprime ou réconcilie ce qui n'est plus vrai.

La philosophie est simple : **Git conserve l'histoire ; `docs/solutions/` représente la vérité technique active que le prochain agent doit croire.**

## État, reprise et preuves

Un run substantiel garde son état temporaire ici :

```text
.gearbox/runs/<run-id>/
├── state.json
├── evidence.json
├── spec.md
├── repo-facts.md
├── dag.yaml
├── learning-candidates.md
└── tasks/
```

`state.json` rend le run reprenable et borné par budgets. `evidence.json` est la source des affirmations de vérification : tests, lint, typecheck, build, reviews et screenshots ne sont pas annoncés comme réussis s'ils n'ont pas été enregistrés sur le bon état du code.

## PR générées par Gearbox

Une PR Gearbox a deux niveaux :

1. **Description principale** : problème, résultat, impact et limites, écrits pour quelqu'un qui n'a pas besoin de lire le code.
2. **Commentaire technique** : carte des changements, vérifications, findings, simplifications, preuves UI/UX et vrais extraits de logique critique.

Pour chaque extrait critique, le commentaire indique :

- `fichier:lignes` ;
- le code final exact ;
- pourquoi ce bloc mérite l'attention ;
- ce qu'un reviewer doit vérifier.

Un gate valide ce rapport avant publication. Une simple liste de fichiers ne satisfait pas le contrat.

## Structure du repository

```text
.claude-plugin/     manifest plugin + marketplace
skills/             commandes `/gearbox:*`
agents/             workers, reviewers, integrator, verifier, shipper, etc.
hooks/              garde-fou control-plane
scripts/            runtime Python : state, routing, Codex, evidence, worktrees, validations
references/         protocoles partagés par les skills
schemas/            contrats JSON si présents
evals/              scénarios de régression du plugin
README.md            documentation utilisateur
NOTICE.md            inspirations et attributions
LICENSE              licence MIT
```

Les scripts Python font partie du plugin et sont volontairement versionnés. Seuls les artefacts générés (`__pycache__`, `.pyc`, runs temporaires, etc.) sont exclus.

## Licence et inspirations

Gearbox est publié sous licence MIT. Le design s'inspire de plusieurs projets publics d'ingénierie agentique, notamment les skills de Matt Pocock, Compound Engineering, Superpowers et Ponytail. Voir `NOTICE.md` pour les attributions et la manière dont ces idées sont réinterprétées dans Gearbox.
