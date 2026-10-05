# Gearbox

Gearbox est un plugin Claude Code d'orchestration d'ingénierie. Il transforme une idée, une spec ou une issue GitHub en boucle de développement contrôlée : clarification proportionnée, plan lean, DAG/ready frontier, routage Claude/Codex, workers isolés, batching des micro-tâches, tests crédibles, reviews croisées calibrées par le coût réel d'un échec, Ponytail, vérification, mémoire durable et PR documentée pour humains.

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
| J'ai une initiative trop grosse ou trop floue pour une seule spec | `/gearbox:wayfinder "destination"` |
| J'ai déjà une issue GitHub | `/gearbox:issue <URL-ou-numéro>` |
| J'ai déjà une spec | `/gearbox:loop <chemin-spec>` |
| J'ai un run interrompu | `/gearbox:resume <run-id-ou-issue>` |
| J'ai déjà une PR avec CI/reviews à traiter | `/gearbox:continue-pr <PR>` |
| Je veux nettoyer la mémoire technique | `/gearbox:clean-solutions` |
| Je veux améliorer les prochains runs après une session pénible | `/gearbox:retro [run-id]` |

Pour une issue classique, le mode autonome habituel est :

```text
/gearbox:issue https://github.com/acme/foo/issues/123 --auto --ship
```

Pour continuer également après l'ouverture de la PR :

```text
/gearbox:issue https://github.com/acme/foo/issues/123 --auto --ship --follow-pr
```

## Les 20 commandes

| Commande | Quand l'utiliser | Ce qu'elle fait exactement |
| --- | --- | --- |
| `/gearbox:setup` | Première utilisation sur un repository, ou migration de configuration | Analyse les conventions du repo, détecte tests/lint/typecheck/build/e2e, GitHub, Codex et Ponytail, initialise `.gearbox/config.md`, la politique de risque, les budgets, les modèles Claude/Codex et l'index `docs/solutions/`. Le setup ne modifie pas le produit. |
| `/gearbox:wayfinder <idée-ou-map>` | Pour une initiative trop grande ou trop incertaine pour converger honnêtement en une seule spec | Cartographie la destination et les **decision tickets** sans implémenter. Sépare recherche, prototype, décision humaine et prérequis ; garde le brouillard non encore spécifiable dans la map ; exécute les recherches indépendantes via `researcher` ; maintient une ready frontier de décisions ; puis handoff vers shaping/plan/loop quand il ne reste plus de décision matérielle à inventer. `--create` matérialise la map/issues GitHub et `--auto-research` peut lancer les recherches indépendantes. |
| `/gearbox:brainstorm "<idée>"` | Quand le besoin est encore flou | Classe d’abord le travail en **spike**, **bounded**, **architectural** ou **wayfinder**. Un spike produit une réponse/probe sans spec ni code produit ; un bounded reste léger ; l’architectural suit le flux spec complet ; un gros brouillard est redirigé vers Wayfinder. Avec `--issue`/`--ship`, Gearbox matérialise le contrat durable nécessaire avant implémentation. |
| `/gearbox:shape <demande>` | Quand la demande est connue mais pas encore assez précise pour coder | Transforme une feature, une issue ou une demande en spec décisionnellement complète. Distingue ce qui peut être déduit du repo, ce qui peut être assumé de façon réversible, et ce qui exige une question utilisateur. Ne lance aucun worker tant que la spec est `SPEC_BLOCKED`. |
| `/gearbox:spec-to-issue <spec>` | Quand une spec doit devenir une issue GitHub | Distille la spec en issue concise : objectif, scope, non-scope, critères d'acceptation, contraintes et vérification. Par défaut produit un draft ; `--create` crée réellement l'issue. La spec reste la source de vérité, l'issue sert de tracker. |
| `/gearbox:spec-to-issues <spec>` | Quand une spec est trop grosse pour une seule issue | Découpe une grande spec en epic + plusieurs issues dépendantes et verticales. Garde la spec comme source de vérité et évite de figer trop tôt le DAG d'implémentation. `--create` crée les issues. |
| `/gearbox:issue <URL-ou-numéro>` | Point d'entrée principal pour une issue GitHub | Charge l'issue, construit la spec puis le DAG/routing. **Sans `--auto`, il s'arrête ici et attend ton approbation du plan exact avant tout worker.** Après approbation : TDD/SDD, cross-reviews, intégration, Ponytail, vérification, repairs, learning éventuel et PR si `--ship`. |
| `/gearbox:loop <issue-ou-spec-ou-demande>` | Quand tu veux utiliser directement le moteur générique | Lance la boucle convergente depuis une issue, une spec ou une demande locale. Réutilise les artefacts connus et itère seulement sur les gates qui échouent jusqu'à `PASS`, `BLOCKED` ou `MAX_CYCLES`. Peut shipper et suivre la PR. |
| `/gearbox:flow <demande>` | Compatibilité avec l'ancien point d'entrée générique | Alias de compatibilité vers la logique de boucle pour du travail substantiel hors issue. Pour un nouveau workflow, préfère `/gearbox:loop`. |
| `/gearbox:plan <spec-ou-issue>` | Quand tu veux seulement produire/inspecter le plan | Produit un **plan lean** : décisions, interfaces/signatures, valeurs imposées, tests/assertions et vérification, sans transcrire les corps de code. Ajoute `Review Focus` (0-5 failure modes), la ready frontier, ownership, routing et éventuels micro-batches. `plan_guard.py` contrôle la proportion du plan. |
| `/gearbox:build <plan-ou-tâche>` | Pour implémenter manuellement un plan déjà approuvé | Exécute via workers délégués, RED → GREEN → REFACTOR et **Test Credibility Gate**. Les petites tâches indépendantes de même forme peuvent être batchées en un worker + une cross-review, tout en gardant la traçabilité de chaque membre. Dans un run orchestré, le parent n’a toujours aucune exception « petit edit ». |
| `/gearbox:debug <symptôme>` | Bug, test rouge, incident ou comportement mystérieux | Construit une boucle red-capable, minimise, falsifie les hypothèses et protège par un test crédible. Après root cause, un scan ciblé cherche la même classe de bug : à **3+ occurrences** (ou risque catastrophique), Gearbox traite le motif systémique/défense plutôt que de jouer au whack-a-bug. |
| `/gearbox:simplify [diff]` | Après intégration, pour réduire le code | Lance un agent frais de simplification. Utilise Ponytail s'il est installé ; sinon applique la discipline interne Gearbox : supprimer duplication, wrappers et abstractions inutiles, préférer stdlib/framework/existant, conserver validation, sécurité et accessibilité. Rejoue ensuite les checks nécessaires. |
| `/gearbox:review [diff-ou-PR]` | Pour une review indépendante | Vérifie spec/correctness/sécurité/tests/opérations et calibre les findings par failure path + failure cost. Dans la boucle orchestrée, la review finale est routée `lite / focused / full` selon la conséquence : pas de nouveau reviewer si les task reviews suffisent, un adversarial reviewer pour le risque silencieux, spine complète uniquement sur les frontières à fort impact. |
| `/gearbox:learn <leçon>` | Après une découverte non évidente qui mérite d'être conservée | Écrit/réconcilie `docs/solutions/` et peut ajouter `retire_when` quand la guidance dépend d’un bug/version/service externe. Régénère l’index puis passe l’audit déterministe de frontmatter/index. |
| `/gearbox:clean-solutions [scope]` | Maintenance périodique de `docs/solutions/` | Audite métadonnées/index, vérifie en priorité les `retire_when` satisfaits, puis confronte la mémoire au code/tests/specs/ADRs. Classe en `KEEP`, `REFRESH`, `MERGE`, `DELETE` ou `BLOCKED`. `--dry-run` reste disponible. |
| `/gearbox:retro [run-id / issue/ PR / session] [--bundle]` | Après un run coûteux, confus ou riche en corrections | Produit une rétro **forensic** avec preuves `path:line`/artifact fields : plan adherence, repeated work, stumbles, request conflicts, dispatch/escalation/repair cost proxies et quality escapes. `--bundle` génère en plus un dossier redacted sous `.gearbox/diagnostics/` pour partager/analyser la session. |
| `/gearbox:ship` | Quand le code est prêt à être publié | Vérifie les gates, délègue commit/push, crée ou met à jour la PR et son commentaire technique. La description de PR est compréhensible par un non-tech ; le commentaire technique contient les checks, reviews, changements Ponytail, screenshots UI/UX et 1 à 5 vrais extraits de code critique avec fichier:lignes, justification et focus de review. |
| `/gearbox:resume <run-id/issue/PR>` | Après fermeture/crash/interruption ou pour approuver un plan en attente | Recharge l'état sans rejouer le travail. `--approve-plan` approuve uniquement le plan actuellement hashé ; s'il a changé depuis sa présentation, Gearbox refuse et redemande une approbation. |
| `/gearbox:continue-pr <PR>` | Après création de la PR, quand CI ou un reviewer humain a parlé | Charge uniquement les nouveaux checks/commentaires, valide les findings au lieu de les accepter aveuglément, construit un repair DAG borné, corrige via workers, repousse sur la même branche et met à jour le même commentaire technique sans rejouer toute l'issue. |

## Flags les plus utiles

| Flag | Effet |
| --- | --- |
| `--auto` | Automatise les décisions d'ingénierie raisonnables, **saute le checkpoint humain d'approbation du plan** et autorise les repair cycles bornés. N'autorise jamais Gearbox à inventer une décision produit/métier ou à franchir les gates destructifs. |
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

## Approbation du plan

Par défaut, un run substantiel sépare **planifier** et **autoriser l'implémentation**.

```text
/gearbox:issue #123
→ spec / clarification
→ reconnaissance
→ plan lean + DAG
→ routing Claude/Codex + reviewers
→ hash du plan
→ PLAN_APPROVAL_REQUIRED
→ STOP
```

Gearbox te montre alors un résumé compact : tâches, ready frontier, modèles/efforts, Review Focus, risques et topologie de review. Aucun worker/reviewer ne peut consommer de budget tant que ce plan n'est pas approuvé.

Tu peux approuver le plan exact dans la conversation par un « go » non ambigu, ou de façon explicite/reprenable :

```text
/gearbox:resume issue-123 --approve-plan
```

L'approbation est liée au SHA-256 du `dag.yaml`. Si le plan change, l'approbation précédente est invalidée et Gearbox doit te présenter la nouvelle version.

Avec :

```text
/gearbox:issue #123 --auto
```

le digest est toujours enregistré, mais le checkpoint humain est marqué auto-approved et le run continue. `--ship` ne remplace jamais `--auto` : `--ship` sans `--auto` s'arrête toujours au plan.

## Économie d'exécution et plans lean

Gearbox 1.3 applique un **delegation gate** aux subagents auxiliaires. Un agent d'analyse/recherche supplémentaire doit justifier au moins une chose : protéger le contexte parent d'une grosse lecture, fournir un jugement réellement indépendant, exécuter une unité substantielle en parallèle, ou utiliser un modèle différent réellement sélectionnable. Les workers d'implémentation et rôles obligatoires du control plane restent délégués sans exception.

Les plans enregistrent les décisions que l'implémenteur ne peut pas choisir seul. Ils privilégient signatures, interfaces, valeurs exactes, noms/assertions de tests et commandes de vérification. Un `Review Focus` limité à cinq failure modes ferme les angles morts probables sans transformer le plan en copie du futur code.

Les petites tâches **same-shape** low-risk peuvent être fusionnées en un micro-batch : un worker et une cross-review, avec chaque membre explicitement vérifié. Les changements sécurité/auth, migrations/destruction, contrats publics distincts et tâches demandant des jugements différents ne sont jamais batchés.

## Tests crédibles et réparations bornées

Un test vert ne compte comme preuve que s'il exerce un vrai seam, possède une attente indépendante du code testé et a une mutation réaliste qui le ferait échouer. Les tests de présence de texte, change detectors décoratifs, mocks contournant le vrai failure path et seams production créés uniquement pour tester ne satisfont pas ce gate.

Chaque finding réparable reçoit un id stable. Deux tentatives avec la même stratégie sont permises ; une troisième identique est bloquée et force re-diagnostic/split/changement de stratégie. Cinq tentatives totales forcent une adjudication du contrôleur si le budget global n'a pas arrêté la boucle avant.

## Review finale proportionnée

Gearbox 1.5 sépare les **task reviews** obligatoires de la profondeur de review du diff intégré final.

`scripts/final_review_router.py` choisit mécaniquement :

```text
lite
→ task review gates déjà satisfaits
→ failure loud + local
→ risque low/medium
→ 0 nouveau reviewer modèle
→ diff inspection + verifier

focused
→ failure silencieux/mixte
   ou risque high mais borné
   ou shared seam
→ 1 fresh adversarial integration reviewer

full
→ auth / permissions / money / secrets
→ destructive migration / persistence / public contract
→ production config / concurrency
→ architecture structurante / critical risk
→ comprehensive reviewer
→ + cross-provider peer en hybrid
```

Le nombre de lignes ne peut **jamais** faire gagner `lite`. Un gros volume de code exécutable peut seulement forcer `full` comme filet de sécurité.

Le mode choisi est persisté dans `state.final_review` et apparaît dans le rapport technique de PR. `verifier` reste obligatoire quel que soit le mode : une review n'est pas une preuve exécutable.

## Benchmarks agentiques

`benchmarks/agentic/` permet de comparer une baseline et une candidate Gearbox dans de vraies sessions d'agent, chacune dans un clone et un contexte frais.

Le protocole mesure d'abord :

- correctness ;
- safety.

Seulement si **tous les runs comparés** passent ces gates, Gearbox autorise la comparaison économique :

- lignes source ajoutées ;
- input/output/cached tokens quand le runner les rapporte ;
- coût provider réellement rapporté ;
- durée et turns ;
- workers/reviews/escalades/repair cycles depuis `.gearbox/runs/*/state.json` ;
- mode de final review choisi.

Les workspaces sont conservés et peuvent être rescored offline, donc changer un scorer ne repaie pas les modèles.

Le runner Claude de référence exclut les plugins globaux, charge explicitement le plugin de chaque arm, neutralise mémoire/CLAUDE.md externes et lance un processus frais par cellule afin d'éviter une baseline contaminée.

Le CI normal ne lance **aucune session modèle**. Il exécute uniquement :

```bash
python3 scripts/agentic_bench.py self-test
python3 scripts/agentic_bench.py validate benchmarks/agentic/manifest.example.json
```

Les campagnes live sont explicites et leurs résultats appartiennent uniquement au repo/commit/tasks/models/harness mesurés. Gearbox ne transforme jamais un benchmark en promesse universelle de « X% moins cher ».

## Plomberie intelligente

Gearbox 1.4 ajoute une couche de contrôle qui cherche surtout à éviter les dépenses silencieuses et les régressions de prompts.

### Prompt budgets

Chaque `skills/*/SKILL.md` a un plafond de bytes dans `prompt-budgets.json`. `scripts/prompt_budget.py` fait échouer le CI si un skill regrossit au-delà de son ratchet. Le détail conditionnel doit aller dans `references/`, et la mécanique déterministe dans `scripts/`.

### Behavioral evals

`evals/behavior/` couvre les comportements que les validateurs de fichiers ne peuvent pas voir : plan qui recommence à transcrire du code, brainstorm qui transforme un spike en spec, délégation auxiliaire inutile, review trop défensive, etc.

Le CI normal valide les scénarios et le harness seulement. Il **ne lance jamais Claude/Codex et ne dépense aucun token modèle**. Les campagnes comportementales se lancent explicitement/localement avec `scripts/behavior_eval.py`.

### Findings canoniques

CI, reviewer humain et review modèle peuvent signaler le même défaut. Gearbox normalise d'abord le failure path puis `finding_registry.py` regroupe les sources sous un seul finding stable. Une root cause = une repair history, pas trois workers parallèles sur le même problème.

### Evidence reuse

`evidence.py reuse` permet de réutiliser une preuve valide au **même SHA exact**, même commande/scope, tant qu'elle n'est ni invalidée, volatile ni expirée. Un reviewer frais n'a donc plus le droit de relancer une suite lourde uniquement pour se rassurer.

### Child reconciliation

Les enfants/background workers peuvent être enregistrés dans `children.json`. Gearbox privilégie les retours event-driven, travaille pendant l'attente, puis fait une reconciliation bornée plutôt que du polling serré. Un artifact présent peut récupérer un worker dont le message de retour s'est perdu.

### Usage accounting

Quand le host/provider expose réellement tokens ou coût, `usage_ledger.py` les enregistre dans `usage.json`. Gearbox ne contient aucune grille tarifaire figée et n'invente jamais un coût absent. Des plafonds optionnels `max_total_tokens` et `max_reported_cost_usd` peuvent être configurés.

## Wayfinding, recherche et modèle de domaine

Gearbox sépare maintenant trois problèmes qui se mélangeaient facilement :

- **Wayfinder** découvre la route d'une grosse initiative en résolvant des décisions, pas en pré-découpant tout le développement ;
- **researcher** isole la lecture de documentation/source primaire dans un contexte séparé et renvoie un pointeur vers une note compacte sous `.gearbox/runs/<run>/research/` ;
- **GLOSSARY / ADR** portent respectivement le vocabulaire canonique et les décisions structurantes difficiles à renverser.

Une décision n'obtient un ADR que si elle est difficile à renverser, surprenante sans contexte et issue d'un vrai trade-off. Les incidents/pièges techniques continuent d'aller dans `docs/solutions/`.

Pour les changements d'interface/seam réellement structurants, Gearbox peut appliquer un **design-it-twice** borné : 2 propositions indépendantes en risque deep, jusqu'à 3 seulement pour un cas exceptionnel, puis comparaison par profondeur de module, localité, placement du seam, migration et testabilité.

## Ready frontier

Le DAG n'est plus exécuté comme une série de vagues rigides. Gearbox maintient une **ready frontier** : dès que les dépendances d'une tâche sont intégrées et que son ownership ne conflict pas avec un worker actif, elle peut démarrer. Avant handoff, le worker resynchronise le tip d'intégration et rerun ses checks ciblés.

Cette discipline augmente le parallélisme sans cacher les conflits à l'intégrateur.

## Écriture pour agents

Les règles destinées aux agents suivent une hiérarchie de contexte : instructions indispensables inline, référence conditionnelle derrière un pointeur, mécanique vérifiable dans lint/test/CI/hooks. `CLAUDE.md` et `AGENTS.md` doivent rester des cartes, pas des encyclopédies.

Gearbox ne suppose pas qu'écrire « utilise /gearbox:foo » dans un autre skill charge magiquement ce skill : le comportement partagé vit dans `references/`, les actions déléguées dans `agents/`, et les mécanismes déterministes dans `scripts/`.

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

## Retrospective d'environnement

`/gearbox:retro` ferme une boucle différente de `/learn`. `/learn` conserve une vérité technique sur le système ; `/retro` cherche pourquoi **l'agent** a perdu du temps, du contexte ou de la fiabilité pendant un run et propose une amélioration durable de son environnement.

La rétro s'appuie d'abord sur les artefacts Gearbox (`state.json`, DAG, evidence, résultats workers/reviews et repair cycles) plutôt que de relire aveuglément toute la conversation. Elle privilégie les garde-fous déterministes pour les erreurs mécaniques, garde les standards de jugement côté review, et évite de gonfler `CLAUDE.md` / `AGENTS.md` avec des détails qui devraient vivre ailleurs.

Gearbox ne lance pas une rétro automatiquement sur chaque ticket. Il peut la recommander lorsqu'un run présente des signaux coûteux : repair cycles répétés, escalade de modèle, mauvais routage, packet insuffisant, règle découverte trop tard par la review ou check manquant.

## État, reprise et preuves

Un run substantiel garde son état temporaire ici :

```text
.gearbox/runs/<run-id>/
├── state.json
├── evidence.json
├── children.json
├── usage.json          # seulement si télémétrie disponible
├── spec.md
├── repo-facts.md
├── dag.yaml
├── learning-candidates.md
└── tasks/
```

`state.json` rend le run reprenable et borné par budgets. `evidence.json` est la source des affirmations de vérification et peut réutiliser une preuve au SHA exact sans rerun inutile. `children.json` sert à réconcilier les travaux délégués et `usage.json` ne contient que la télémétrie réellement rapportée par les providers/hosts.

## PR générées par Gearbox

Une PR Gearbox expose aussi le risque de merge avec **Before/After Evidence**, **Door** (one-way/two-way) et **Blast Radius**.

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

Gearbox est publié sous licence MIT.


Les bundles forensic optionnels de `/gearbox:retro --bundle` vivent sous `.gearbox/diagnostics/` et sont ignorés par git. La redaction est defense-in-depth : relis le bundle avant de le partager hors du périmètre du projet.
