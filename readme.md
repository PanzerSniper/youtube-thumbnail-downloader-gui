# YouTube Thumbnail Downloader

Application Python avec interface graphique pour télécharger la meilleure miniature publique disponible depuis une vidéo YouTube unique ou une playlist complète, sans télécharger les vidéos.

Version actuelle : `0.4.1`

## Aperçu

L'application permet de :

- coller une URL YouTube
- choisir un mode `Auto`, `Vidéo unique` ou `Playlist`
- sélectionner un dossier de destination
- récupérer automatiquement la meilleure miniature disponible
- suivre la progression avec une barre, un journal et des statistiques
- écraser les fichiers existants si besoin
- ouvrir le dossier de sortie à la fin

Le mode `Auto` essaie de détecter tout seul si l'URL correspond à une vidéo ou à une playlist.

## Fonctionnalités

### Sources prises en charge

- vidéo classique `youtube.com/watch?v=...`
- URL courte `youtu.be/...`
- `shorts`
- `live`
- playlist `youtube.com/playlist?...`

### Téléchargement intelligent

Pour chaque vidéo, l'application essaie ces miniatures dans cet ordre :

1. `maxresdefault`
2. `sddefault`
3. `hqdefault`
4. `mqdefault`
5. `default`

Elle priorise les formats modernes quand ils existent :

- `webp`
- `jpg`

## Organisation des fichiers

Pour une playlist, les fichiers sont rangés dans un sous-dossier dédié :

```text
NomDeLaPlaylist/
001 - Titre de la vidéo [ID_VIDEO].webp
002 - Autre titre [ID_VIDEO].jpg
```

Pour une vidéo unique, le fichier est enregistré directement dans le dossier choisi :

```text
Titre de la vidéo [ID_VIDEO].webp
```

## Pourquoi cette méthode

L'application utilise `yt-dlp` pour lire les informations de playlist en mode léger, puis télécharge les miniatures directement depuis les URLs publiques de YouTube.

Cette approche permet :

- de ne pas télécharger les vidéos
- d'être plus rapide
- de mieux gérer certains cas où l'extraction complète d'une vidéo pose problème

## Prérequis

- Python 3.11 ou plus récent recommandé
- `tkinter` disponible dans l'installation Python
- `yt-dlp`
- `requests`

## Installation

Dans le dossier du projet :

```powershell
python -m pip install -U yt-dlp requests
```

## Lancement

```powershell
python script.py
```

## Création d'un exécutable Windows

Dans le dossier du projet, installe d'abord `PyInstaller` :

```powershell
python -m pip install -U pyinstaller
```

Puis lance une première build :

```powershell
pyinstaller --onefile --windowed script.py
```

Options utilisées :

- `--onefile` crée un seul fichier `.exe`
- `--windowed` évite d'ouvrir une console noire pour une application graphique

Le résultat sera généré dans :

```text
dist\script.exe
```

## Interface

L'interface propose :

- un champ pour l'URL YouTube
- une liste déroulante pour le mode
- un sélecteur de dossier
- une option d'écrasement
- une option d'ouverture automatique du dossier final
- un bouton `Lancer`
- un bouton `Arrêter`
- un journal de traitement
- des statistiques `Total / Traitées / Téléchargées / Ignorées`

## Notes

- les vidéos uniques sont enregistrées directement dans le dossier de destination
- les playlists sont enregistrées dans un sous-dossier portant le nom de la playlist
- le détail des changements est disponible dans `CHANGELOG.txt`
