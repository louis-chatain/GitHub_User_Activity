import sys
import json
import urllib.request
import urllib.error

# Set a basic user agent, as some public APIs might require it or treat non-browser requests suspiciously.
USER_AGENT = "GitHubActivityCLI/1.0 (Python CLI)"


def check_argv() -> str | None:
    if len(sys.argv) == 2:
        username = sys.argv[1]
        return username
    else:
        print("Usage: python github_activity.py <github username>")
        print("Example: python github_activity.py louis-chatain")


def get_events(username: str) -> list | None:
    api_url = f"https://api.github.com/users/{username}/events"
    request = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})

    print(f"looking the activity of {username}...")
    try:
        with urllib.request.urlopen(request) as reponse:
            data = reponse.read()
            event = json.loads(data)
            return event
        
    except urllib.error.HTTPError as e:
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


def formated_json_data(raw_json_data: list, number_max_of_events: int) -> list:
    formated_string = []

    for dict_json_data in raw_json_data:
        if len(formated_string) >= number_max_of_events:
            break
        else:
            event_type = dict_json_data.get("type", "no type of event found...")
            actor_name = dict_json_data.get("actor", "no actor").get(
                "display_login", "no display login"
            )
            commit_count = dict_json_data.get("payload", {}).get(
                "size", "unknown numbers of commits"
            )
            branch = dict_json_data.get("repo", {}).get("name", "branch not found")
            date = dict_json_data.get("created_at", "unknown date")
            payload = dict_json_data.get("payload", {})

            # --- PUSH EVENT ---
            if event_type == "PushEvent":
                formated_string.append(
                    f"Pushed {commit_count} commit{'s' if commit_count > 1 else ''} to branch '{branch}' the {date}."
                )

            # --- WATCH EVENT (Star) ---
            elif event_type == "WatchEvent":
                formated_string.append(f"Starred {actor_name}.")

            # --- ISSUE EVENT ---
            elif event_type == "IssuesEvent":
                action = payload.get("action")
                issue_title = payload.get("issue", {}).get("title", "an issue")
                issue_number = payload.get("issue", {}).get("number", "N/A")
                formated_string.append(
                    f'{action.capitalize()} issue #{issue_number}: "{issue_title}" in {actor_name} the {date}.'
                )

            # --- PULL REQUEST EVENT ---
            elif event_type == "PullRequestEvent":
                action = payload.get("action")
                pr_title = payload.get("pull_request", {}).get(
                    "title", "a pull request"
                )
                pr_number = payload.get("pull_request", {}).get("number", "N/A")
                formated_string.append(
                    f'{action.capitalize()} pull request #{pr_number}: "{pr_title}" in {actor_name} the {date}.'
                )

            # --- CREATE EVENT (Repo, Branch, Tag) ---
            elif event_type == "CreateEvent":
                ref_type = payload.get("ref_type")
                ref = payload.get("ref")
                if ref_type == "repository":
                    formated_string.append(
                        f"Created a new repository {actor_name} the {date}."
                    )
                elif ref_type == "branch":
                    formated_string.append(
                        f"Created branch '{ref}' in {actor_name} the {date}."
                    )
                elif ref_type == "tag":
                    formated_string.append(
                        f"Created tag '{ref}' in {actor_name} the {date}."
                    )

            # --- FORK EVENT ---
            elif event_type == "ForkEvent":
                formated_string.append(
                    f"Forked {actor_name} to {payload.get('forkee', {}).get('full_name', 'a new repository')}"
                )

            # --- OTHER UNHANDLED EVENT TYPES (e.g., DeleteEvent, MemberEvent) ---
            else:
                # Returning None will skip this event in the main loop
                formated_string.append(None)
    return formated_string


def main():
    username = check_argv()
    raw_json_data = get_events(username)
    if raw_json_data is None:
        sys.exit(1)
    format_json_data = formated_json_data(raw_json_data, 5)
    for i in format_json_data:
        print(f"- {i}")
    return format_json_data


if __name__ == "__main__":
    main()
    