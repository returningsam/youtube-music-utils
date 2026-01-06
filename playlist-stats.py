import random
import sys
from ytmusicapi import YTMusic, LikeStatus
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from thefuzz import fuzz
from time import sleep


def print_progress_bar(iteration, total, prefix='', suffix='', length=40, fill='█'):
    if total == 0:
        return
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')
        sys.stdout.flush()

def print_help():
    """Print usage information."""
    print("YouTube Music Playlist Manager")
    print("=" * 40)
    print("\nUsage: ./start <command>")
    print("\nCommands:")
    print("  list-playlists [search]                 List all playlists")
    print("  delete-empty-playlists                  Delete all empty playlists in your library")
    print("  delete-duplicate-playlists              Find and delete duplicate playlists by title")
    print("  like-all-songs-in-playlist [search]     Like all songs in a selected playlist")
    print("  delete-all-playlists                    Delete all playlists (with confirmation)")
    print("  delete-playlist [search]                Delete a single playlist")
    print("  remove-all-songs-from-playlist [search] Remove all songs from a playlist without deleting it")
    print("  help                                    Show this help message")
    print("\n[search] = optional search term to filter playlists by fuzzy match")

def printPlaylistCandidate(candidate, idx):
                title = candidate.get('title')
                candidate_id = candidate.get('id')
                year = candidate.get('year')
                track_count = candidate.get('trackCount', 0)
                print(f"  [{idx+1}] Title: {title} | ID: {candidate_id} | Tracks: {track_count} | year: {year}")

def list_playlists(ytmusic: YTMusic, search_term: str | None = None):
    """List all playlists in the user's library."""

    playlists = fetch_all_playlists(ytmusic, limit=0)
    print(f"Listing {'all' if search_term is None else ''} playlists{f' with search term "{search_term}"' if search_term else ''}")
    print("=" * 40)
    
    try:
        if search_term:
            playlists = [p for p in playlists if fuzz.partial_ratio(search_term, p['title']) >= 70][:10]
        
        if playlists:
            for playlist in playlists:
                print(f"  • {playlist['title']} ({playlist['trackCount']} tracks)")
        else:
            print("No playlists found in your library.")
            
    except Exception as e:
        print(f"Error fetching playlists: {e}")
        raise

def delete_empty_playlists(ytmusic):
    """Delete all empty playlists in the user's library."""
    playlists = ytmusic.get_library_playlists(None)
    for playlist in playlists:
        data = ytmusic.get_playlist(playlist['playlistId'])
        if not data['owned']:
            print(f"Skipping playlist: {data['title']} (not owned by me)")
            continue
        if data['trackCount'] == 0:
            confirm = input(f"Delete empty playlist: \"{data['title']}\"? [y/N]: ").strip().lower()
            if confirm == "y":
                try:
                    ytmusic.delete_playlist(playlist['id'])
                    print(f"Deleted playlist: {data['title']}")
                except Exception as e:
                    print(f"Error deleting playlist '{data['title']}': {e}")
                    
                    print("Playlist data:", json.dumps(data, indent=2))
            else:
                print(f"Skipped deletion of: {data['title']}")
        else:
            print(f"Keeping playlist: {data['title']} ({data['trackCount']} tracks)")

def fetch_playlist(ytmusic: YTMusic, playlist: dict, limit: int | None = 100):
    try:
        data = ytmusic.get_playlist(playlistId=playlist['playlistId'], limit=limit)
        return data
    except Exception as e:
        print(f"Error fetching playlist {playlist['id']}: {e}")
        print(playlist)
        return None

def fetch_all_playlists(ytmusic: YTMusic, limit: int | None = 100, search_term: str | None = None):
    print("Fetching library playlists...")
    playlists = ytmusic.get_library_playlists(limit=None)
    if search_term:
        playlists = [p for p in playlists if fuzz.partial_ratio(search_term, p['title']) >= 70]
    all_results = []
    print(f"Found {len(playlists)} playlists")
    print_progress_bar(0, len(playlists), prefix='Fetching playlists:', suffix='Complete')
    with ThreadPoolExecutor() as executor:
        future_to_playlist = {executor.submit(fetch_playlist, ytmusic, playlist, limit): playlist for playlist in playlists}
        for idx, future in enumerate(as_completed(future_to_playlist), 1):
            print_progress_bar(idx, len(playlists), prefix='Fetching playlists:', suffix='Complete')
            data = future.result()
            if data:
                all_results.append(data)
    return all_results

def delete_duplicate_playlists(ytmusic): 
    playlists = fetch_all_playlists(ytmusic)
    registry = {}

    # Process playlists into a registry of duplicate playlists (by title)
    for data in playlists:
      if registry.get(data['title']):
        registry.get(data['title']).get('candidates').append(data)
      else:
        registry[data['title']] = {
          'title': data['title'],
          'candidates': [data]
        }

    unique_playlist_names = list(registry.keys())

    for playlist_name in unique_playlist_names:
        data = registry[playlist_name]
        if len(data['candidates']) > 1:
            print(f"Duplicate playlists found for: {data['title']}")
            print("Candidates:")
            candidates = data.get('candidates')


            for idx, candidate in enumerate(candidates):
                printPlaylistCandidate(candidate, idx)
            to_delete = input(
                "Select the number of the playlist to keep\n"
                "Leave blank to skip this group: "
            ).strip()
            if not to_delete:
                continue
            try:
                pid = candidates[int(to_delete)-1]['id']
                title = candidates[int(to_delete)-1]['title']
                ytmusic.delete_playlist(pid)
                print(f"Deleted playlist: {title}")
            except Exception as e:
                print(f"Error deleting playlist '{title}': {e}")
        else:
            print(f"Keeping playlist: {data['title']}")

def like_all_songs_in_playlist(ytmusic: YTMusic, search_term: str | None = None):
  # list all playlists and ask for the user to choose one
  # limit to none because we want all songs from each playlist
  playlists = fetch_all_playlists(ytmusic, limit=None, search_term=search_term)
  
  for idx, playlist in enumerate(playlists):
      printPlaylistCandidate(playlist, idx)
  choice = input("Select the number of the playlist to like all songs in: ")
  if not choice:
      return
  try:
    playlist = playlists[int(choice)-1]
    print(f"This playlist has {len(playlist['tracks'])} songs! Would you like to like all of them? [y/N]")
    print(f"tracks length: {len(playlist['tracks'])}")
    print(f"trackcount: {playlist['trackCount']}")
    choice = input()
    if choice != "y":
        return
    skipped_count = 0
    liked_count = 0
    for song in playlist['tracks']:
        if song['likeStatus'] == LikeStatus.LIKE:
            print(f"Skipping song: {song['title']} - already liked")
            skipped_count += 1
            continue
        else:
            ytmusic.rate_song(song['videoId'], LikeStatus.LIKE)
            sleep(1.2 + random.random() * 0.8)
            print(f"Liked song: {song['title']}")
            liked_count += 1
    print("\n--- Stats ---")
    print(f"Skipped (already liked): {skipped_count}")
    print(f"Newly liked: {liked_count}")
    print(f"Total: {skipped_count + liked_count}")

  except Exception as e:
      raise e

def delete_all_playlists(ytmusic: YTMusic):
  playlists = fetch_all_playlists(ytmusic, limit=None)
  print(f"This will delete {len(playlists)} playlists! Would you like to continue? [y/N]")
  choice = input()
  if choice != "y":
    return
  for playlist in playlists:
    if playlist['owned']:
      ytmusic.delete_playlist(playlist['id'])
      print(f"Deleted playlist: {playlist['title']}")
    else:
      print(f"Skipping playlist: {playlist['title']} (not owned by me)")

def remove_track_from_playlist(ytmusic: YTMusic, playlist_id: str, track: dict):
    """Remove a single track from a playlist with retry logic for 409 conflicts."""
    import time
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            ytmusic.remove_playlist_items(playlistId=playlist_id, videos=[track])
            return {'success': True, 'track': track}
        except Exception as e:
            # Check if it's a 409 Conflict error, else re-raise immediately
            if hasattr(e, 'args') and any("HTTP 409: Conflict" in str(arg) for arg in e.args):
                if attempt == max_retries:
                    return {'success': False, 'track': track, 'error': str(e)}
                time.sleep(0.6)  # small delay before retrying
                continue
            else:
                return {'success': False, 'track': track, 'error': str(e)}
    return {'success': False, 'track': track, 'error': 'Max retries exceeded'}

def remove_all_songs_from_playlist(ytmusic: YTMusic, search_term: str | None = None):
    playlists = fetch_all_playlists(ytmusic, limit=None, search_term=search_term)
    for idx, playlist in enumerate(playlists):
        printPlaylistCandidate(playlist, idx)
    choice = input("Select the number of the playlist to remove all songs from: ")
    if not choice:
        return
    try:
        playlist = playlists[int(choice)-1]
        total_tracks = len(playlist['tracks'])
        failed_removals = []

        with ThreadPoolExecutor() as executor:
            future_to_track = {
                executor.submit(remove_track_from_playlist, ytmusic, playlist['id'], track): track 
                for track in playlist['tracks']
            }
            for idx, future in enumerate(as_completed(future_to_track), 1):
                print_progress_bar(idx, total_tracks, prefix='Removing songs:', suffix='Complete')
                result = future.result()
                if not result['success']:
                    print(f"Failed to remove song: {result['track'].get('title', '[unknown]')}: {result['error']}")

        if failed_removals:
            print(f"\nFailed to remove {len(failed_removals)} songs:")
            for failure in failed_removals:
                print(f"  • {failure['track'].get('title', '[unknown]')}: {failure['error']}")

        newPlaylistData = ytmusic.get_playlist(playlist['id'])
        if newPlaylistData['trackCount'] == 0:
            print(f"Removed all songs from playlist: {playlist['title']}")
        else:
            print(f"Failed to remove all songs from playlist: {playlist['title']} ({newPlaylistData['trackCount']} remaining)")
    except Exception as e:
        print('failed')
        raise e

def delete_playlist(ytmusic: YTMusic, search_term: str | None = None):
  playlists = fetch_all_playlists(ytmusic, limit=None, search_term=search_term)
  for idx, playlist in enumerate(playlists):
      printPlaylistCandidate(playlist, idx)
  choice = input("Select the number of the playlist to delete: ")
  if not choice:
    return

  try:
    playlist = playlists[int(choice)-1]
    ytmusic.delete_playlist(playlist['id'])
    print(f"Deleted playlist: {playlist['title']}")
  except Exception as e:
    print(f"Error deleting playlist '{playlist['title']}': {e}")





def main():
    """Main entry point for the playlist stats script."""
    command = sys.argv[1] if len(sys.argv) > 1 else None
    search_term = sys.argv[2] if len(sys.argv) > 2 else None
    

    if not command:
        print_help()
        return


    ytmusic = YTMusic('browser.json')
    match command:
        case "list-playlists":
            list_playlists(ytmusic, search_term)
        case "delete-empty-playlists":
            delete_empty_playlists(ytmusic)
        case "delete-duplicate-playlists":
            delete_duplicate_playlists(ytmusic)
        case "like-all-songs-in-playlist":
            like_all_songs_in_playlist(ytmusic, search_term)
        case "delete-all-playlists":
            delete_all_playlists(ytmusic)
        case "delete-playlist":
            delete_playlist(ytmusic, search_term)
        case "remove-all-songs-from-playlist":
            remove_all_songs_from_playlist(ytmusic, search_term)
        case _:
            print_help()


if __name__ == "__main__":
    main()
