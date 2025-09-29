import sys
import json
import urllib.request
import urllib.error

# Set a basic user agent, as some public APIs might require it or treat non-browser requests suspiciously.
USER_AGENT = "GitHubActivityCLI/1.0 (Python CLI)"

def fetch_activity(username: str) -> list | None:
    # Fetches the recent public events for a given GitHub username.

    # Args:
    #     username: The GitHub username to fetch activity for.

    # Returns:
    #     A list of event dictionaries, or None if fetching failed.

    api_url = f"https://api.github.com/users/{username}/events"
    
    # Create a request object with a User-Agent header
    request = urllib.request.Request(api_url, headers={'User-Agent': USER_AGENT})

    print(f"-> Fetching activity for user: {username}...")

    try:
        with urllib.request.urlopen(request) as response:
            data = response.read()
            # Decode the data and parse the JSON response
            events = json.loads(data)
            return events

    except urllib.error.HTTPError as e:
        # Handle HTTP errors (e.g., 404 for non-existent user, 403 for rate limit)
        if e.code == 404:
            print(f"\nError: GitHub user '{username}' not found. Please check the spelling.")
        elif e.code == 403:
            print("\nError: GitHub API rate limit exceeded (403 Forbidden). Try again later.")
        else:
            print(f"\nError fetching data: HTTP status code {e.code} - {e.reason}")
        return None
    
    except urllib.error.URLError as e:
        # Handle network-related errors (e.g., DNS failure, connection refused)
        print(f"\nError connecting to GitHub API: {e.reason}")
        return None
    
    except json.JSONDecodeError:
        # Handle cases where the response is not valid JSON
        print("\nError: Failed to parse API response as JSON.")
        return None

def format_event(event: dict) -> str | None:
    # Formats a single GitHub event into a human-readable string.

    # Args:
    #     event: A dictionary representing a single GitHub event.

    # Returns:
    #     A formatted string describing the activity, or None if the event type 
    #     is not handled.

    event_type = event.get('type')
    repo_name = event.get('repo', {}).get('name', 'Unknown Repository')
    payload = event.get('payload', {})
    commit_count = event.get('payload', {}).get('size', "x")
    date = event.get('created_at')
    
    # --- PUSH EVENT ---
    if event_type == 'PushEvent':
        branch = payload.get('ref', '').split('/')[-1]
        return f"Pushed {commit_count} commit{'s' if commit_count != 1 else ''} to branch '{branch}' in {repo_name} the {date}"

    # --- WATCH EVENT (Star) ---
    elif event_type == 'WatchEvent':
        return f"Starred {repo_name}"

    # --- ISSUE EVENT ---
    elif event_type == 'IssuesEvent':
        action = payload.get('action')
        issue_title = payload.get('issue', {}).get('title', 'an issue')
        issue_number = payload.get('issue', {}).get('number', 'N/A')
        return f"{action.capitalize()} issue #{issue_number}: \"{issue_title}\" in {repo_name}"

    # --- PULL REQUEST EVENT ---
    elif event_type == 'PullRequestEvent':
        action = payload.get('action')
        pr_title = payload.get('pull_request', {}).get('title', 'a pull request')
        pr_number = payload.get('pull_request', {}).get('number', 'N/A')
        return f"{action.capitalize()} pull request #{pr_number}: \"{pr_title}\" in {repo_name}"

    # --- CREATE EVENT (Repo, Branch, Tag) ---
    elif event_type == 'CreateEvent':
        ref_type = payload.get('ref_type')
        ref = payload.get('ref')
        if ref_type == 'repository':
            return f"Created a new repository {repo_name}"
        elif ref_type == 'branch':
            return f"Created branch '{ref}' in {repo_name}"
        elif ref_type == 'tag':
            return f"Created tag '{ref}' in {repo_name}"

    # --- FORK EVENT ---
    elif event_type == 'ForkEvent':
        return f"Forked {repo_name} to {payload.get('forkee', {}).get('full_name', 'a new repository')}"

    # --- OTHER UNHANDLED EVENT TYPES (e.g., DeleteEvent, MemberEvent) ---
    else:
        # Returning None will skip this event in the main loop
        return None

def main():
    
    # Main entry point for the CLI application.
    
    # 1. Check for the required command-line argument
    if len(sys.argv) < 2:
        print("Usage: python github_activity.py <username>")
        print("Example: python github_activity.py louis-chatain")
        sys.exit(1)

    username = sys.argv[1]

    # 2. Fetch the activity
    events = fetch_activity(username)

    if events is None:
        # Error already printed in fetch_activity
        sys.exit(1)

    # 3. Display the formatted activity
    print("\n--- Recent GitHub Activity ---")

    if not events:
        print(f"No recent public activity found for user: {username}.")
        sys.exit(0)

    # Filter out events we can't format and display a limited number
    displayed_count = 0
    MAX_EVENTS_TO_SHOW = 10
    
    for event in events:
        if displayed_count >= MAX_EVENTS_TO_SHOW:
            break
            
        formatted_line = format_event(event)
        # formatted_line = event
        
        if formatted_line:
            # Add a bullet point and print the formatted line
            print(f"- {formatted_line}")
            displayed_count += 1
            
    if displayed_count == 0:
        print(f"Found events, but none of the recent public activities for {username} could be displayed.")


if __name__ == "__main__":
    main()
