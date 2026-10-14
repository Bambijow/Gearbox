# Reverse engineering avec Gearbox et REA

Retrouver un comportement dans ce qui reste d'un ancien projet, puis préparer son adaptation à un nouveau projet, même sans le code source.

**Documentation vérifiée le 14 octobre 2026.** Les sources REA consultées sont épinglées en fin de page. Elles décrivent le code upstream, pas nécessairement la dernière publication npm. L'aide de la version installée et les schémas du serveur effectivement connecté restent prioritaires.

## Sommaire

- [Ce qui est installé, et ce qui ne l'est pas](#installation-et-integration)
- [Comment Gearbox détecte REA](#detection)
- [Installation pour Claude Code et Codex](#installation)
- [Installation limitée à un projet ou un profil](#portee)
- [Vérifier que tout fonctionne](#verification)
- [Moteurs et prérequis selon la cible](#moteurs)
- [Reprendre un comportement et le transférer](#utilisation)
- [Preuves, délégation et sécurité](#preuves)
- [Mises à jour, désinstallation et dépannage](#maintenance)
- [Limites de validation et sources](#sources)

<a id="installation-et-integration"></a>
## 1. Ce que Gearbox installe réellement

Il y a quatre couches distinctes :

| Couche | Rôle | Sa présence prouve quoi ? |
| --- | --- | --- |
| Plugin Gearbox | `/gearbox:reverse`, protocole, artefacts, validations et passage vers le développement | Le parcours est disponible dans le plugin chargé. |
| Paquet `rea-agents` | CLI `rea` et serveur MCP REA | Le logiciel peut être lancé dans cet environnement, sous réserve de ses prérequis. |
| Enregistrement MCP dans le client | Rend le serveur accessible à Claude Code, Codex ou un autre client | La connexion est configurée, pas nécessairement établie. |
| Fournisseur d'analyse | Par exemple Ghidra, Hopper, IDA ou un navigateur accessible | Certaines opérations peuvent être utilisables sur certaines cibles. |

Gearbox **n'embarque pas REA**, ne lance pas `npm install` au chargement et n'ajoute pas de serveur MCP automatiquement. Son skill de reverse est utilisable avec d'autres outils adaptés. Il ne garantit pas qu'un binaire arbitraire puisse être décompilé.

Dans cette intégration, la découverte de REA est un **protocole exécuté par l'agent**, pas un service Python de détection automatique. `scripts/capabilities.py` sait inventorier la configuration MCP de Codex ; il ne réalise pas le handshake REA. `scripts/reconstruction.py` valide un dossier de reconstruction ; il ne détecte, n'installe et ne lance aucun serveur.

Installer le skill upstream avec `npx skills add morluto/rea --skill reverse-engineer-anything` installe des instructions, **pas le MCP ni les moteurs**. Avec Gearbox, ce skill supplémentaire n'est pas nécessaire. Le setup REA peut l'omettre avec `--skill=false`. Cette option ne supprime pas une copie déjà installée. [S1]

<a id="detection"></a>
## 2. Comment Gearbox sait que REA est utilisable

La vérification distingue **configuration**, **connexion**, **opération disponible** et **prise en charge de la cible**. Ce ne sont pas quatre synonymes d'« installé ».

### Étape A : identifier la session qui fera le travail

Identifier le client, le profil, l'hôte et le répertoire de travail : Claude Code, worker Codex, WSL, conteneur ou machine distante. Une installation sur Windows ne devient pas automatiquement une installation dans WSL. Un serveur configuré pour Claude n'est pas automatiquement transmis à Codex.

### Étape B : découvrir les vrais outils

Utiliser le mécanisme de découverte d'outils du client. Si les outils sont différés, les rechercher avant de conclure à leur absence. Le nom d'enregistrement courant est `rea`, mais il peut avoir été changé. Ne pas imposer un préfixe complet tel que `mcp__rea__...`.

`tools/list` désigne une méthode du protocole MCP, **pas une commande à taper dans le terminal**, et pas forcément un outil exposé directement à l'agent. Le client fournit les noms et les schémas. La liste REA peut contenir des opérations momentanément indisponibles. La seule présence d'un nom ne suffit donc pas. [S2, S6]

### Étape C : vérifier la session REA

Après avoir découvert son schéma réel, appeler l'outil REA **`binary_session` avec `{}`**. Ce n'est pas une slash command. Malgré son nom, cet appel fonctionne avant l'ouverture d'un binaire.

Selon le contrat courant, sa réponse permet de consulter l'identité du serveur et du paquet, ainsi que `result.tool_availability`. Les versions récentes regroupent les opérations dans `groups` : conserver les noms, disponibilités, raisons, remédiations, modes et exigences du client de chaque groupe. Ne pas supposer une ancienne liste plate. Si la version connectée expose une autre forme, suivre son schéma et conserver les inconnues.

Pour l'analyse native, distinguer `analysis_provider_candidates` (fournisseurs possibles) de `analysis_provider_binding` (fournisseur réellement sélectionné). Sans cible, son support peut encore être `unknown`. La réussite de la découverte n'autorise aucune exécution de l'ancien programme. [S2]

### Étape D : vérifier l'opération nécessaire, puis la cible

Une analyse statique JavaScript n'a pas besoin du même moteur qu'une décompilation native. Un serveur connecté peut être utile pour la première et inutilisable pour la seconde. Choisir l'opération la moins coûteuse qui répond à la question et traiter ses erreurs réelles. Ne pas ouvrir un exécutable simplement pour tester la connexion.

Le compte rendu de preflight doit indiquer, sans secrets : client/hôte, serveur effectivement découvert, identité/version réellement observée ou inconnue, opérations nécessaires, capacités manquantes et prochaine action. C'est un relevé du run, **pas un nouveau flag `rea_installed: true` dans la configuration**.

### Ce que les contrôles ne prouvent pas

| Contrôle | Ce qu'il établit | Ce qu'il n'établit pas |
| --- | --- | --- |
| CLI présente sur `PATH` | Un lanceur est accessible au shell. | Le client MCP l'utilise ou utilise la même version. |
| `claude mcp list` / `get` | Configuration et diagnostic du client dans ce contexte. | Les capacités exactes d'une session déjà ouverte. |
| `rea doctor --client claude_code --json` | État de l'enregistrement pris en charge et prérequis inspectés. | Une connexion live ; les enregistrements Claude en scope local ne sont pas couverts. |
| Découverte MCP | Noms et schémas reçus par le client. | Toutes les opérations sont actuellement disponibles. |
| `binary_session {}` | Identité et disponibilités de cette connexion. | Toute cible est supportée, ou son comportement est déjà connu. |
| Analyse réussie | Les observations contenues dans le résultat. | Une équivalence complète avec une nouvelle implémentation. |

`doctor` peut rapporter un état global non sain à cause d'un moteur optionnel inutile à ta tâche. Diagnostiquer le client ou le fournisseur concerné plutôt que tout réinstaller. [S1, S2]

<a id="installation"></a>
## 3. Installer REA pour Claude Code

### Prérequis

Exécuter ces commandes dans **le même environnement qui lance le client** :

```bash
node --version
npm --version
claude --version
```

Le manifeste upstream consulté accepte Node **22.x à partir de 22.19.0**, **24.x à partir de 24.11.0**, ou **26 et plus**. Cela ne veut pas dire « toutes les versions supérieures à 22.19 », notamment pour la branche 25. Vérifier les contraintes de la publication retenue. REA ne remplace pas l'installation et la connexion de Claude Code. [S3]

### Parcours simple, limité au client choisi

Dans un terminal utilisateur, hors d'un run Gearbox gardé :

```bash
npx rea-agents@latest setup --client claude_code --skill=false --dry-run
```

Cette commande prépare le plan sans modifier la configuration des clients. `npx` peut néanmoins télécharger le paquet et remplir son cache : le dry-run REA ne rend pas le téléchargement npm inexistant.

Lire le plan, les chemins, la portée et les éventuelles propositions de moteur. Puis lancer :

```bash
npx rea-agents@latest setup --client claude_code --skill=false
```

Approuver uniquement les changements voulus. Ne pas ajouter `--yes`, `--all-detected` ou `--install-hopper` pour éliminer une question. L'autorisation de télécharger le paquet npm et l'approbation du plan REA sont distinctes. Ne pas accepter Hopper lorsqu'aucune analyse native ne le nécessite.

Le setup configure normalement REA au niveau utilisateur de Claude Code, sous `~/.claude.json`, donc pour ses différents projets. Il épingle l'enregistrement package-runner sur la version exécutée. Avec `--skill=false`, Gearbox reste l'entrée de workflow ; les outils REA sont disponibles sans une seconde procédure de développement. **Quitter puis relancer Claude Code** après modification. [S1]

Deux appels à `@latest` peuvent résoudre deux publications différentes. Pour appliquer exactement la version examinée, utiliser le parcours ci-dessous.

### Parcours reproductible : même version pour le plan et l'application

Sur Linux/macOS avec un shell POSIX :

```bash
REA_VERSION="$(npm view rea-agents dist-tags.latest)" &&
test -n "$REA_VERSION" &&
printf 'Version retenue : %s\n' "$REA_VERSION" &&
npm view "rea-agents@$REA_VERSION" engines --json &&
npx "rea-agents@$REA_VERSION" setup --client claude_code --skill=false --dry-run
```

Si la résolution npm échoue ou renvoie une version vide, s'arrêter. Après lecture et approbation du plan, dans le même terminal :

```bash
npx "rea-agents@$REA_VERSION" setup --client claude_code --skill=false
```

Sur Windows PowerShell :

```powershell
$ReaVersion = (npm view rea-agents dist-tags.latest)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($ReaVersion)) {
  throw "Impossible de résoudre la version REA"
}
$ReaVersion = $ReaVersion.Trim()
npm view "rea-agents@$ReaVersion" engines --json
npx "rea-agents@$ReaVersion" setup --client claude_code --skill=false --dry-run
# Après lecture du plan :
npx "rea-agents@$ReaVersion" setup --client claude_code --skill=false
```

La version du dépôt `main` n'est pas une preuve de publication npm. Ce guide ne fige pas un numéro présenté comme éternellement « latest ». Les variables ci-dessus ne survivent pas à la fermeture du terminal : conserver la version retenue pour les vérifications et mises à jour. [S1]

### Utilisation avec les workers Codex

Configurer explicitement les deux clients lorsqu'ils doivent tous deux inspecter la référence :

```bash
npx "rea-agents@$REA_VERSION" setup --client claude_code --client codex --skill=false --dry-run
# Après approbation du plan :
npx "rea-agents@$REA_VERSION" setup --client claude_code --client codex --skill=false
```

En PowerShell, remplacer `$REA_VERSION` par `$ReaVersion`. Le client ID Claude Code est **`claude_code`**, pas `claude` ni `claude-code`. Une installation uniquement dans Claude Desktop ne configure pas Claude Code. Le setup connaît les chemins propres aux clients et les éventuels profils ; vérifier ceux qu'il annonce. [S1]

Les tâches réellement dépendantes de REA doivent déclarer son **nom MCP effectivement découvert**, par exemple :

```yaml
required_capabilities: [rea]
```

Il s'agit du contrat de tâche Gearbox, pas d'une configuration serveur suffisante à elle seule. Le pruning Codex `required-only` peut désactiver REA pour une tâche qui ne le déclare pas. À l'inverse, une tâche d'implémentation recevant un contrat exporté n'a pas forcément besoin de REA. Voir [le routage des capacités](../references/capability-routing.md).

### CLI globale, facultative

Pour disposer d'une commande `rea` dans le shell, au lieu de toujours employer `npx` :

```bash
npm install --global "rea-agents@$REA_VERSION"
rea --help
```

Cette installation globale **ne suffit pas à enregistrer le MCP**. Exécuter aussi le setup choisi. Un MCP précédemment épinglé peut continuer à utiliser une autre version que la CLI globale. Ne pas résoudre une erreur de permissions npm en ajoutant automatiquement `sudo` ; corriger l'installation Node ou son préfixe utilisateur.

Les exemples `rea ...` plus bas supposent cette CLI globale. Sans elle, remplacer `rea` par `npx "rea-agents@$REA_VERSION"` dans le terminal où la version a été définie. Ce lancement peut télécharger le paquet et doit rester volontaire. [S1, S4]

<a id="portee"></a>
## 4. Limiter l'installation à un projet ou un profil

Choisir **une** stratégie pour Claude Code ; ne pas cumuler des enregistrements concurrents sans nécessité.

### Un projet seulement

Depuis le répertoire du projet, après choix de `REA_VERSION`, pour Linux/macOS :

```bash
claude mcp add --transport stdio --scope local rea -- npx -y "rea-agents@$REA_VERSION" mcp
```

Sous PowerShell natif, après choix de `$ReaVersion` :

```powershell
claude mcp add --transport stdio --scope local rea -- cmd.exe /d /c npx -y "rea-agents@$ReaVersion" mcp
```

`-y` autorise npm à télécharger le paquet pour le lanceur non interactif ; ce n'est pas une permission d'exécuter les cibles inspectées. Cette route installe le MCP à la demande, mais pas le skill upstream.

Le scope `local` stocke l'enregistrement dans la configuration personnelle, rattaché à ce répertoire. Le scope `project` écrirait un `.mcp.json` partageable dans le dépôt. Utiliser ce dernier uniquement pour une configuration d'équipe intentionnelle, sans secrets et avec l'approbation de chaque poste. [S1, S6]

**Particularité REA :** `doctor --client claude_code`, `rea update` et `rea uninstall` ne gèrent pas cet enregistrement local comme l'entrée utilisateur. Vérifier depuis le même répertoire avec `claude mcp list`, `claude mcp get rea`, puis le test live ci-dessous. Un diagnostic `missing` dans doctor n'annule pas une connexion locale réellement fonctionnelle. [S1]

Une ancienne entrée `user` reste active dans les autres projets. Après sauvegarde, la supprimer explicitement avec `claude mcp remove --scope user rea` lorsqu'on souhaite cette migration. Ne pas effacer les autres MCP ni restaurer tout le fichier de configuration aveuglément. Un ancien skill REA reste également indépendant.

### Profil Claude Code séparé

Alternative POSIX, avec une version déjà choisie :

```bash
CLAUDE_CONFIG_DIR="$HOME/.claude-rea" npx "rea-agents@$REA_VERSION" setup --client claude_code --skill=false --dry-run
# Après lecture du plan :
CLAUDE_CONFIG_DIR="$HOME/.claude-rea" npx "rea-agents@$REA_VERSION" setup --client claude_code --skill=false
CLAUDE_CONFIG_DIR="$HOME/.claude-rea" claude
```

Garder le même préfixe pour les diagnostics, mises à jour et suppressions de ce profil. Il peut nécessiter de reconnecter le client et de charger Gearbox. Sous PowerShell, définir temporairement `$env:CLAUDE_CONFIG_DIR`, puis restaurer sa valeur précédente après la session ; ne pas coller la syntaxe POSIX. Le guide upstream fournit le bloc `try/finally` complet. [S1]

Un profil séparé **n'est pas un sandbox**. Il limite les outils découverts dans le client, pas les accès fichiers/réseau d'un processus du même compte.

<a id="verification"></a>
## 5. Vérifier l'installation sans analyser un ancien programme

Depuis le répertoire et le profil qui seront réellement utilisés :

```bash
claude mcp list
claude mcp get rea
```

Après redémarrage, dans Claude Code :

```text
/mcp
```

Vérifier que le bon serveur est connecté, et non désactivé, en échec ou en attente d'approbation. Utiliser son vrai nom lorsqu'il n'est pas `rea`. Puis demander à l'agent :

```text
Vérifie REA pour cette session sans ouvrir ni exécuter de cible.
Découvre son outil binary_session, lis le schéma puis appelle-le avec {}.
Rapporte l'identité et la version réellement reçues, les opérations utiles
pour une analyse JavaScript statique et pour une analyse native,
ainsi que les capacités manquantes. N'installe et ne configure rien.
```

Ce test est réussi lorsqu’**un vrai appel revient** avec une identité cohérente et un diagnostic de disponibilité compréhensible. Copier un résultat d'exemple, reconnaître le nom REA ou lire une configuration ne constitue pas ce test. Une capacité native absente peut être un résultat normal.

Pour diagnostiquer un enregistrement utilisateur, avec la **version épinglée dans cet enregistrement** :

```bash
npx "rea-agents@$REA_VERSION" doctor --client claude_code --json
npx "rea-agents@$REA_VERSION" doctor --client codex --json
```

La seconde commande n'est utile que si Codex a été configuré. `--skill` teste le skill REA, pas le MCP ; ne pas l'exiger après une installation volontaire avec `--skill=false`. Les rapports peuvent contenir des chemins et des métadonnées privées : ne pas les publier bruts. [S1, S2]

Le guard Gearbox peut refuser `npx`, `rea`, `claude mcp ...` ou un helper shell pendant un run orchestré. Il ne faut pas le contourner pour installer ou diagnostiquer. Faire ces opérations dans le terminal utilisateur, puis rouvrir le client. La découverte MCP utilise les outils du client, pas une exception générale à la protection du shell.

<a id="moteurs"></a>
## 6. Quels moteurs faut-il installer ?

Installer seulement ce que nécessite la cible. Le tableau décrit l'orientation du protocole, pas une promesse universelle de support. Vérifier la disponibilité de l'opération dans la session. [S1, S4, S5]

| Ce qui reste de l'ancien projet | Départ raisonnable | Prérequis supplémentaires possibles |
| --- | --- | --- |
| Sources | Lecture, tests existants et historique | Aucun REA obligatoire. |
| Dossier JavaScript/Electron ou ASAR | Analyse statique REA | Node/npm ; `ps` compatible procps sous Linux. |
| Assembly .NET avec métadonnées PE/CLI | Inspection statique du managed | Pas de moteur natif requis pour les métadonnées/CIL pris en charge ; NativeAOT et IL2CPP sont d'autres cas. |
| Binaire natif | Inventaire, puis décompilation si nécessaire | Ghidra, Hopper ou IDA compatibles avec l'hôte et la cible. |
| Site web encore accessible | Observations et captures | Navigateur Chromium avec endpoint CDP local, ou autre outil navigateur adapté. |
| CLI encore exécutable | Caractérisation bornée | Environnement isolé ; la capture de processus REA courante demande Linux/macOS et un PTY fonctionnel. |
| HAR, traces ou vidéos seulement | Analyse des éléments effectivement conservés | Pas de conclusion sur les branches jamais observées. |

### Ghidra

Installer Ghidra et un JDK complet depuis leurs distributions officielles, **en dehors de REA**. La documentation upstream consultée cible Ghidra 12.1.x et décrit une vérification avec 12.1.4/JDK 21. Revalider la compatibilité avec la version REA choisie plutôt que supposer que toute version future est acceptée. Le JDK et le décompilateur natif doivent correspondre à l'architecture de l'hôte. [S1]

Exemple POSIX, avec des chemins à remplacer par les installations réelles :

```bash
export GHIDRA_INSTALL_DIR="/chemin/absolu/ghidra_12.1.4_PUBLIC"
export JAVA_HOME="/chemin/absolu/jdk-21"
rea doctor --provider ghidra --json
rea setup --client claude_code --skill=false --dry-run
```

Après validation du diagnostic et du plan, répéter le setup sans `--dry-run`, approuver et redémarrer. Le setup peut enregistrer les chemins détectés pour que le serveur ne dépende pas d'un `PATH` différent dans l'éditeur. Il n'installe pas Ghidra ni Java.

Sous PowerShell, employer `$env:GHIDRA_INSTALL_DIR = "C:\tools\ghidra_12.1.4_PUBLIC"` et `$env:JAVA_HOME = "C:\chemin\jdk-21"`. Le support Windows Ghidra décrit par REA est expérimental et borné ; ne pas assimiler un `.exe` quelconque à une cible compatible. [S7]

### Hopper et IDA

REA peut proposer une installation Hopper sur les hôtes pris en charge, avec une approbation séparée. Hopper conserve ses propres conditions de licence et limitations. Pour une installation existante : `rea doctor --provider hopper --json`. IDA suit son adaptateur et ses prérequis upstream : `rea doctor --provider ida --json`. Ne pas installer les trois moteurs pour obtenir artificiellement un doctor entièrement vert. [S1, S4]

### Particularités Linux, macOS et Windows

Sur Linux, le superviseur REA exige un `ps` compatible procps pour plusieurs outils, y compris l'analyse statique JavaScript qui lance un worker d'analyse. Le paquet de distribution est généralement `procps` ou `procps-ng` ; utiliser le gestionnaire adapté à la machine. Une analyse statique peut lancer un **outil d'analyse** sans exécuter le **programme étudié**. [S1]

Pour la capture de processus sous macOS, REA demande notamment le compilateur Swift accessible via `xcrun` pour vérifier la propriété des processus. Les permissions d'automatisation ou de capture d'écran concernent les opérations qui en ont besoin. Suivre leur diagnostic, pas une demande de permissions globales. La capture de processus native Windows n'est pas établie par le support de Ghidra Windows. WSL capture des processus Linux ; cela ne démontre pas la capture d'une arborescence Windows native. [S5, S7]

### Site web : navigateur séparé

Pour une application de test, démarrer soi-même un navigateur avec un profil dédié. Exemple Linux, remplacer le lanceur si nécessaire :

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/rea-browser-profile http://127.0.0.1:3000
```

Ne pas réutiliser le profil contenant les sessions personnelles ni exposer le port de débogage hors loopback. Vérifier son adresse d'écoute et les accès de l'environnement. Le profil doit être dédié à cette investigation. L'ouverture de la page exécute son JavaScript et peut provoquer des requêtes : elle nécessite le périmètre d'exécution autorisé.

REA peut ensuite découvrir les pages, par exemple via `rea list-browser-targets http://127.0.0.1:9222`. Son observation CDP passive ne devient pas automatiquement de l'automatisation Playwright. Fermer soi-même ce navigateur à la fin : REA ne possède pas le processus lancé par cette commande. [S8]

<a id="utilisation"></a>
## 7. Retrouver puis adapter un comportement

La version de Gearbox chargée doit contenir `skills/reverse/SKILL.md`. Tant que la branche de fonctionnalité n'est pas fusionnée/publiée, une mise à jour ordinaire du marketplace ne garantit pas sa présence. Pour tester un checkout connu, Claude Code permet `claude --plugin-dir /chemin/absolu/Gearbox` depuis le projet cible. Vérifier dans `/plugin` la copie chargée et éviter deux copies Gearbox concurrentes. [S9]

### Investigation sans exécution de la cible

```text
/gearbox:reverse /archives/ancienne-app --mode auto --target /projets/nouvelle-app
```

Ajouter une question précise, par exemple : « Retrouve le comportement de recherche et les règles de classement. Je veux l'adapter à mon nouveau projet, pas copier toute l'application. »

Les modes `source`, `behavior`, `interface` et `binary` choisissent une stratégie. Ils n'installent aucun outil et ne remplacent pas une autorisation. Avec uniquement des traces, `behavior` peut les examiner sans lancer le programme. Un site vivant à ouvrir ou une application à piloter demande un périmètre runtime ; sans cela, rester sur les fichiers et captures fournis.

### Capture autorisée

```text
/gearbox:reverse /archives/ancienne-cli --mode behavior --target /projets/nouvelle-cli --execute
```

Avant toute capture, préciser la commande, les entrées, la durée maximale, les chemins lisibles/modifiables, les éventuels accès réseau, les données initiales et le nettoyage. `--execute` appartient à **Gearbox**, pas à une commande REA générique. Il n'autorise ni installation, ni accès production, ni modification du nouveau projet.

### Résultat et passage au développement

Le dossier contient les observations, déductions, inconnues et scénarios ; chaque décision de transfert est `preserve`, `adapt`, `discard` ou `defer`. Exemple : conserver le classement des résultats, adapter les noms de champs, écarter un bug d'affichage, différer une règle jamais observée.

Le skill s'arrête avant l'implémentation. Après acceptation des décisions, demander la préparation de la spec cible et poursuivre par le parcours normal spec/plan/approbation/build. Un dossier `READY_FOR_SHAPING` n'est pas une approbation humaine et ne prouve pas l'équivalence runtime.

<a id="preuves"></a>
## 8. Preuves, portabilité et limites de sécurité

Les dossiers de reconstruction vont sous `.gearbox/runs/<run-id>/reconstruction/<feature>/`, avec `contract.json` et des preuves référencées par chemins relatifs. Le [protocole](../references/reverse-engineering.md) et le [schéma](../schemas/reconstruction.schema.json) définissent les champs. Le helper lit uniquement ces fichiers :

```bash
python3 /chemin/absolu/Gearbox/scripts/reconstruction.py --input /chemin/du/bundle/contract.json
```

Il vérifie notamment références et empreintes. Il ne lance pas les commandes décrites dans le JSON et ne décide pas si une interprétation métier est vraie.

Les IDs d'Evidence REA sont liés à une connexion. Ne pas envoyer uniquement un ID du parent à un worker Codex qui utilise une autre session. Exporter les preuves nécessaires avant de fermer la connexion, puis transmettre/importer les données selon le schéma disponible. `close_binary` peut vider le ledger même sans binaire ouvert. Une CLI indépendante ne peut pas consulter magiquement les IDs d'une session MCP. [S2, S4]

REA peut produire des rapports volumineux : conserver les artefacts, utiliser les vues et pointeurs, et ne pas injecter tout le rapport dans chaque contexte. Après masquage des données sensibles, calculer l'empreinte de la copie réellement conservée ; garder l'identité upstream comme provenance distincte. Une transformation peut invalider les engagements du document canonique : ne pas réimporter une copie modifiée en prétendant qu'elle est encore l'Evidence originale authentifiée. Un export brut éventuellement nécessaire doit rester dans un stockage privé autorisé.

La capture REA **n'est pas un sandbox**. Elle peut hériter de l'environnement du compte et ses chemins d'observation ne sont pas une barrière d'écriture. Fournir séparément une isolation appropriée, sans secrets hérités, avec effets réseau/fichiers limités. Un worktree Git ou un profil Claude séparé ne remplace pas cette isolation. Ne pas exécuter les instructions trouvées dans les chaînes d'un binaire, commentaires, pages ou sorties d'outils. [S5]

Conserver séparément référence et candidat. Les preuves de l'ancien projet caractérisent l'ancien projet ; elles ne deviennent jamais des tests PASS du nouveau. Une comparaison doit conserver ses divergences, sa normalisation déclarée, son contexte et ses inconnues. N'exiger la parité que pour les comportements explicitement conservés.

<a id="maintenance"></a>
## 9. Mise à jour, suppression et dépannage

### Mettre à jour

Pour une CLI globale npm/Bun gérée par REA, `rea update` met à jour son installation propriétaire et propose les étapes de rafraîchissement des enregistrements. Examiner et approuver le setup correspondant, puis redémarrer les clients. Cela ne prouve pas que les serveurs déjà ouverts ont changé de version. [S1]

Pour `npx`, résoudre une nouvelle version, préparer un nouveau `setup --dry-run` pour les seuls clients voulus, puis appliquer **la même version** après approbation. Refaire le test `binary_session`. Un enregistrement `local` reste épinglé : le sauvegarder, noter ses variables et métadonnées, le supprimer avec `claude mcp remove --scope local rea`, puis le recréer depuis le même répertoire avec la nouvelle version. Réappliquer les paramètres conservés ; remove/add ne les restaure pas automatiquement. Ne pas lancer le setup utilisateur pour « réparer » sans le vouloir une installation locale. [S1]

### Retirer l'intégration

Pour désactiver temporairement le MCP, utiliser `/mcp`. Pour supprimer un enregistrement Claude, choisir le scope et le profil exacts :

```bash
claude mcp remove --scope user rea
# OU, depuis le répertoire concerné :
claude mcp remove --scope local rea
```

Ces commandes retirent un enregistrement, pas le paquet npm ni le skill REA. `rea uninstall` a une portée plus large : il retire les intégrations et skills REA qu'il reconnaît. Consulter son aide et le plan applicable avant utilisation. Ne pas employer `--purge-data` pour un simple dépannage ; cette option retire aussi cache et état REA. Les preuves exportées et les logiciels tiers ont leur propre cycle de vie. [S1, S6]

### Dépannage par symptôme

| Symptôme | Vérification et remédiation |
| --- | --- |
| `/gearbox:reverse` inconnu | Vérifier la branche/version du plugin réellement chargée, pas seulement son numéro de manifeste ; ne pas réinstaller REA pour ce problème. |
| `rea` introuvable | La CLI globale est facultative. Vérifier le lanceur du MCP ; un setup `npx` peut fonctionner sans commande globale `rea`. |
| REA installé, absent dans Claude | Vérifier profil, scope et environnement, puis `claude mcp list` depuis le bon projet. Redémarrer après setup. |
| `doctor` dit `missing`, mais `/mcp` fonctionne | Vérifier un enregistrement `local`, non audité par le doctor Claude utilisateur. Le test live est décisif. |
| `doctor` est vert, mais aucun outil live | Doctor vérifie configuration/prérequis. Reconnecter, vérifier les permissions du client et découvrir réellement les outils. |
| Les outils ne sont pas dans le contexte initial | Utiliser la recherche d'outils différés ; ne pas conclure immédiatement à une installation absente. |
| `binary_session` absent du catalogue reçu | Vérifier version et schémas du vrai serveur ; signaler une découverte incompatible/partielle, ne pas inventer un résultat. |
| `healthy: false` à cause d'un autre moteur | Employer `doctor --client ...` ou `doctor --provider ...` pour la tâche ; ne pas installer tout le catalogue. |
| Opération listée mais indisponible | Lire `tool_availability`, ses raisons et les prérequis ; un nom de tool n'est pas une capacité opérationnelle. |
| Fonctionne dans Claude, pas dans Codex | Vérifier le setup Codex, son environnement et le `required_capabilities` de la tâche ; contrôler le pruning. |
| Échec sous Linux malgré Node présent | Vérifier le `ps` compatible procps dans le `PATH` du serveur et les prérequis du fournisseur. |
| Échec Windows au lancement du MCP | Privilégier le setup officiel ; en enregistrement manuel `npx`, employer le wrapper `cmd.exe /d /c` documenté. |
| Ghidra indisponible | Vérifier dossier, JDK complet, version et architecture ; diagnostiquer le fournisseur, pas seulement le paquet REA. |
| Navigateur inaccessible | Vérifier profil dédié, endpoint loopback et port ; un navigateur lancé avec un pipe privé n'expose pas nécessairement un endpoint CDP HTTP. |
| Timeout ou `cleanup_incomplete` | Lire l'état réel et les ressources retenues avant de relancer. Un client qui cesse d'attendre ne prouve pas que le fournisseur est arrêté. |
| Evidence introuvable dans un worker | Ne pas réutiliser un ID d'une autre connexion ; exporter/importer des preuves portables compatibles. |
| Commande refusée par le guard Gearbox | Ne pas contourner le guard. Installer/diagnostiquer depuis le terminal utilisateur, puis rouvrir le client. |
| REA indisponible | Employer un outil déjà accessible qui produit une preuve adéquate, ou rendre un résultat partiel avec la capacité manquante ; jamais un faux PASS. |

<a id="sources"></a>
## 10. Vérification de cette documentation et sources

Cette page documente le contrat et les commandes upstream. Sa rédaction ne constitue pas une installation sur ton poste ni un test end-to-end Claude Code/Codex + REA. Les tests déterministes de Gearbox vérifient le plugin, pas la disponibilité de tes moteurs. Le contrôle opérationnel reste la procédure de la section 5, puis une investigation bornée sur une cible autorisée.

Sources REA consultées au commit `1438422dfedf1de29368b595e09a04f1fc10750d`. Le code du paquet et une publication npm peuvent différer ; comparer avec la version effectivement lancée.

- [S1 : REA, installation, scopes, doctor et maintenance](https://github.com/morluto/rea/blob/1438422dfedf1de29368b595e09a04f1fc10750d/docs/installation.md)
- [S2 : REA, identité et découverte MCP](https://github.com/morluto/rea/blob/1438422dfedf1de29368b595e09a04f1fc10750d/docs/mcp-contracts.md)
- [S3 : REA, paquet et versions Node](https://github.com/morluto/rea/blob/1438422dfedf1de29368b595e09a04f1fc10750d/package.json)
- [S4 : REA, CLI et preuves](https://github.com/morluto/rea/blob/1438422dfedf1de29368b595e09a04f1fc10750d/docs/cli.md)
- [S5 : REA, capture de processus](https://github.com/morluto/rea/blob/1438422dfedf1de29368b595e09a04f1fc10750d/docs/process-capture.md)
- [S6 : Claude Code, configuration MCP](https://code.claude.com/docs/en/mcp)
- [S7 : REA, périmètre Ghidra Windows](https://github.com/morluto/rea/blob/1438422dfedf1de29368b595e09a04f1fc10750d/docs/windows-ghidra-p0.md)
- [S8 : REA, observation navigateur](https://github.com/morluto/rea/blob/1438422dfedf1de29368b595e09a04f1fc10750d/docs/browser-observation.md)
- [S9 : Claude Code, développement local de plugins](https://code.claude.com/docs/en/plugins-reference)

Les fichiers agent-facing [rea-integration.md](../references/rea-integration.md) et [reverse-engineering.md](../references/reverse-engineering.md) portent les instructions opérationnelles ; ce guide explique l'installation et l'exploitation humaine.

<a id="api-backend"></a>
## Reverse engineering de backend/API à partir des captures

Le mode `api` complète `behavior` pour les projets dont le code serveur est perdu. Ce mode **ne décompile pas un serveur à travers HTTP** : il reconstruit une ébauche des comportements observables et des scénarios candidats à partir des traces conservées. Voir [le protocole API](../references/reverse-api.md) et [les contrats de raisonnement](../references/reasoning-quality.md).

Avec un fichier HAR 1.2 disponible localement, et sans démarrer l'ancien serveur :

```bash
python3 scripts/api_reconstruct.py --har /chemin/vers/ancien-backend.har
```

Le helper fonctionne hors ligne et renvoie un inventaire de méthodes/routes (certains segments dynamiques sont regroupés), statuts HTTP, formes JSON observées, ordinals des enregistrements, scénarios de probes proposés et `openapi_candidate`. **Aucun champ requis, politique de permissions, formule métier, idempotence ou comportement caché n'est affirmé sans preuve.** Il n'émet pas d'exemples de payload, valeurs des headers, noms d'hôtes ni valeurs de query. Ce JSON n'est pas une spec OpenAPI prête à publier. Le fichier HAR brut reste sensible, notamment avec cookies/jetons : l'inspecter et le protéger avant tout partage.

REA, si disponible, sait aussi analyser les captures HAR et certains autres formats avec `inspect_web_network_capture`, dont SAZ ; `inspect_analysis_view` peut projeter les routes observées pour des HAR compatibles. Vérifier la disponibilité réelle dans `binary_session`. Voir [l'analyse de captures REA](https://github.com/morluto/rea/blob/main/docs/web-network-captures.md). L'analyse passive n'a pas besoin d'un moteur Ghidra/Hopper.

Avec Gearbox, après chargement de la branche contenant le nouveau skill :

```text
/gearbox:reverse /chemin/ancien-backend.har --mode api --target /chemin/nouveau-projet
```

L'agent produit d'abord un contrat comportemental, distingue observation/hypothèse/inconnue et demande des décisions explicites d'adaptation. Une requête GET 200 ne permet pas d'inférer automatiquement les erreurs, contraintes, permissions ou effets de bord absents de la capture. Toute **requête active** sur une API exige une autorisation distincte, un environnement de test contrôlé et des budgets/reset explicites ; aucune exploration automatisée de la production par défaut.

Le contrat matérialisé peut être suivi avec `scripts/decision_trace.py` (preuves/invalidations), `scripts/investigation_plan.py` (prochaine expérience discriminante, risque séparé de l'incertitude) et `scripts/contract_challenge.py` (contre-exemple sur la nouvelle implémentation). Les preuves cible doivent être fraîches, et une revue terminée ne vaut jamais démonstration d'équivalence universelle. Les tests déterministes couvrent ces garde-fous, mais aucun benchmark de qualité agentique réelle n'est inclus dans la CI.
