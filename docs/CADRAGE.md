# Cadrage — whisper-dictation

## 1. Pitch

Client de dictée vocale globale sous Windows, ultra-rapide et autonome, connecté à une instance locale partagée de Whisper (Large-v3 sur GPU NVIDIA CUDA) :
1. **Déclenchement instantané** par raccourci clavier global natif Win32 (`Ctrl + Alt + D`) depuis n'importe quelle application (VS Code, navigateur, traitement de texte).
2. **Précision maximale** avec vocabulaire technique ciblé (acronymes et anglicismes de développement).
3. **Contrôle total de la VRAM** avec arrêt/relance à la demande pour libérer 100% du GPU (16 Go) pour les jeux ou gros modèles LLM.

---

## 2. Objectifs & périmètre

**Dans le périmètre (V1)** :
- Capture audio microphone haute fidélité (16 kHz mono) en mémoire tampon (WAV pur).
- Inférence audio par API REST compatible OpenAI (`POST /v1/audio/transcriptions`).
- Support du modèle `Systran/faster-whisper-large-v3` avec prompt initial de jargon tech.
- Raccourci global natif Windows via `RegisterHotKey` (`Ctrl + Alt + D`).
- Injection automatique du texte par simulation de frappe/presse-papier au niveau du curseur.
- Contrôle du cycle de vie du conteneur via `Arreter-Service-Dictee.bat` et `Lancer-Service-Dictee.vbs`.
- Démarrage automatique silencieux sous Windows via dossier Démarrage (`shell:startup`).
- Réutilisation transparente du serveur Whisper partagé sans conflit avec d'autres projets (`watch-md`).

**Hors périmètre (V1)** :
- Interface graphique lourde (Electron ou application payante type Superwhisper).
- Envoi d'audio vers des API cloud tierces (confidentialité 100% locale garantie).
- Synthèse vocale (TTS).

---

## 3. Contraintes (fermes)

| Contrainte | Détail |
|---|---|
| Licences | Open-source (MIT pour le code, Apache-2.0 / BSD / MIT pour les dépendances) |
| Déploiement | Local uniquement (aucun flux audio ne quitte la machine hôte) |
| Matériel | GPU NVIDIA RTX 4060 Ti 16 Go (VRAM optimisée) ou repli CPU |
| Environnement | Windows 11 avec WSL 2 (Ubuntu 24.04) et gestionnaire `uv` |

---

## 4. Hypothèses

- **Serveur local partagé** : Le conteneur Docker `watch-speaches` tourne sur le port `8000` sous WSL/Windows et héberge le modèle Whisper.
- **Accès microphone** : Le périphérique audio par défaut de Windows est opérationnel et accessible via `sounddevice`.
- **Injection clavier** : L'application active au moment de la dictée accepte la commande de collage `Ctrl+V`.

---

## 5. Stack technique

| Brique | Choix | Licence |
|---|---|---|
| Gestionnaire Python | `uv` | Apache-2.0 / MIT |
| Runtime Python | Python 3.12 | PSF |
| Capture audio | `sounddevice` + `numpy` | MIT / BSD-3-Clause |
| Raccourcis clavier | Win32 `RegisterHotKey` (ctypes) | Standard Windows OS |
| Client HTTP | `httpx` | BSD-3-Clause |
| Validation config | `pydantic` + `pydantic-settings` | MIT |
| Moteur transcription | Speaches (`faster-whisper` / CTranslate2) | MIT / Apache-2.0 |

---

## 6. Décisions

**Décisions figées**
- **Client Python léger avec `uv` et Win32 natif** : Choisi **plutôt que** l'application commerciale Superwhisper, **parce que** Superwhisper impose un abonnement payant pour les modèles lourds, cloisonne ses modèles et refuse le raccordement direct au serveur Docker GPU local existant.
- **API Win32 `RegisterHotKey`** : Choisi **plutôt que** des hooks clavier de bas niveau (`pynput`), **parce que** `RegisterHotKey` est géré directement par le noyau Windows, ne manque aucun événement et fonctionne sur les claviers 60% et AZERTY.
- **Modèle `faster-whisper-large-v3`** : Choisi **plutôt que** `tiny` ou `base`, **parce que** le GPU RTX 4060 Ti offre une vitesse de transcription de 200 à 400 ms tout en restituant parfaitement les acronymes complexes et le français technique.
- **Gestionnaire ON/OFF de la VRAM (`Arreter-Service-Dictee.bat`)** : Choisi **plutôt que** de laisser Whisper charger en continu, **parce que** l'utilisateur doit pouvoir récupérer 100% de la mémoire GPU (16 Go) pour lancer des jeux vidéo ou de volumineux modèles LLM locaux.
- **Format WAV en mémoire** : Choisi **plutôt que** l'écriture de fichiers temporaires sur disque, **parce que** cela réduit la latence et préserve les disques SSD.

---

## 7. Roadmap

0. **Socle V1** : Capture audio, client HTTP, raccourci global natif, injection texte, scripts VRAM ON/OFF.
1. **V1.1** : Ajout d'une icône discrète en zone de notification Windows (systray) pour visualiser l'état ON/OFF du GPU.
2. **V1.2** : Mode de correction grammaticale locale optionnel post-transcription.

---

## 8. Stratégie de tests

- **Tests unitaires (`pytest`)** :
  - Validation du chargement de la configuration (`test_config.py`).
  - Simulation des appels HTTP de transcription et gestion des erreurs hors-ligne (`test_client.py`).
  - Validation du cycle d'enregistrement audio en mémoire (`test_audio.py`).
  - Simulation du collage presse-papier (`test_injector.py`).
- **Tests d'intégration manuels** :
  - Démarrage et arrêt du service via les scripts racine.
  - Vérification de la libération mémoire via `nvidia-smi`.
  - Test de dictée en conditions réelles dans VS Code.

---

## 9. Références

- [Speaches API documentation](https://github.com/speaches-ai/speaches)
- [Faster-Whisper (Systran)](https://github.com/SYSTRAN/faster-whisper)
- [Documentation d'architecture](ARCHITECTURE.md)
