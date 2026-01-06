# YouTube Music Playlist Utilities

A command-line tool for managing your YouTube Music playlists. Perform bulk operations like liking songs, deleting duplicates, and cleaning up empty playlists.

## Features

- 🎵 **List playlists** with optional fuzzy search
- ❤️ **Like all songs** in a playlist automatically
- 🗑️ **Delete empty playlists** to clean up your library
- 🔍 **Find and delete duplicate playlists** by title
- 🧹 **Remove all songs from a playlist** without deleting the playlist itself
- ⚡ **Parallel operations** for faster processing
- 📊 **Progress bars** for long-running operations

## Prerequisites

- Python 3.10+
- A Google Cloud project with YouTube Data API v3 enabled
- Browser auth credentials setup

## Installation

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd yt-music-utilities
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   ./install
   # Or manually: pip install -r requirements.txt
   ```

4. **Set up YouTube Music authentication**

   This project uses [ytmusicapi](https://ytmusicapi.readthedocs.io/) for authentication. You'll need to create a `browser.json` file with your credentials. Follow [these instructions](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html#copy-authentication-headers) to get your credentials json.

## Usage

Run commands using the `start` script:

```bash
./start <command> [search_term]
```

### Available Commands

| Command                                   | Description                                                |
| ----------------------------------------- | ---------------------------------------------------------- |
| `list-playlists [search]`                 | List all playlists, optionally filtered by fuzzy search    |
| `delete-empty-playlists`                  | Interactively delete all empty playlists                   |
| `delete-duplicate-playlists`              | Find duplicate playlists by title and choose which to keep |
| `like-all-songs-in-playlist [search]`     | Like all songs in a selected playlist                      |
| `delete-all-playlists`                    | Delete all playlists (with confirmation)                   |
| `delete-playlist [search]`                | Delete a single playlist                                   |
| `remove-all-songs-from-playlist [search]` | Remove all songs from a playlist without deleting it       |
| `help`                                    | Show help message                                          |

### Examples

```bash
# List all playlists
./start list-playlists

# Search for playlists containing "chill"
./start list-playlists chill

# Like all songs in a playlist matching "favorites"
./start like-all-songs-in-playlist favorites

# Clean up empty playlists
./start delete-empty-playlists

# Find and remove duplicate playlists
./start delete-duplicate-playlists
```

## How It Works

- **Fuzzy Search**: Uses [thefuzz](https://github.com/seatgeek/thefuzz) for flexible playlist name matching (70% similarity threshold)
- **Rate Limiting**: When liking songs, includes random delays (1.2-2.0s) to avoid API rate limits
- **Parallel Fetching**: Uses `ThreadPoolExecutor` to fetch playlist data concurrently
- **Conflict Handling**: Automatic retry logic for 409 Conflict errors when removing tracks

## Dependencies

- [ytmusicapi](https://github.com/sigma67/ytmusicapi) - Unofficial YouTube Music API
- [thefuzz](https://github.com/seatgeek/thefuzz) - Fuzzy string matching
