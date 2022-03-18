# SlackExporter
This script backups Slack channels(public and private), dms, users, and channels.


## Authentication with Slack
1. Visit [https://api.slack.com/apps/](https://api.slack.com/apps/) and sign in to your workspace.
2. Click `Create New App`, enter a name (e.g., `Slack Exporter`), and select your workspace.
3. In prior versions of the Slack API, OAuth permissions had to be specified manually. Now, when prompted for an App Manifest, just paste in the contents of the `slack.yaml` file in the root of this repo.
4. Select `Install to Workspace` at the top of that page (or `Reinstall to Workspace` if you have done this previously) and accept at the prompt.
5. Copy the `OAuth Access Token` (which will generally start with `xoxp` for user-level permissions)

## Usage
1. Clone or download this project.
2. Go to project folder, and install requirements by pip: `pip install -r requirements.txt`
3. Execute script `python main.py -t <oauth token>`
