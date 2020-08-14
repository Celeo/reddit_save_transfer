from enum import Enum
import json
import os
import webbrowser
from time import sleep

import click
from flask import Flask, request, render_template_string
from praw import Reddit
from praw.models import Comment, Submission


CLIENT_ID = '2fINEZ0uC_0jAg'
USER_AGENT = 'https://github.com/celeo/reddit_save_transfer'
REDIRECT_URI = 'http://localhost:5000/callback'
SCOPES = ['identity', 'history', 'save', 'read']
TEMPLATE_STRING = """
<html>
    <body>
        <h2>Finishing login, you can close this tab in a few seconds</h2>
        <script type="text/javascript">
            const access_token = new URL(window.location.href.replace('#', '?')).searchParams.get('access_token');
            console.log(access_token);
            window.fetch('http://localhost:5000/callback/actual?access_token=' + access_token);
        </script>
    </body>
</html>
"""
SAVE_FILE_NAME = 'saved_posts.json'


class Action(Enum):
    Download = 1
    Upload = 2


def get_reddit() -> Reddit:
    return Reddit(
        client_id=CLIENT_ID,
        client_secret=None,  # installed app
        user_agent=USER_AGENT,
        redirect_uri=REDIRECT_URI,
    )


def start_auth_flow(action: Action) -> None:
    reddit = get_reddit()
    url = reddit.auth.url(SCOPES, '...', implicit=True)
    print('Opening your browser ...')
    webbrowser.open(url)
    run_server(action)


def run_server(action: Action) -> None:
    app = Flask(__name__)

    def initial_callback() -> str:
        return render_template_string(TEMPLATE_STRING)

    def callback() -> str:
        access_token = request.args.get('access_token')
        request.environ.get('werkzeug.server.shutdown')()
        if not access_token:
            raise ValueError('"access_token" arg is None')
        finish_processing(action, access_token)
        return 'Return to application'

    app.add_url_rule('/callback', None, initial_callback)
    app.add_url_rule('/callback/actual', None, callback)
    app.run(host='0.0.0.0', port=5000, debug=False)


def finish_processing(action: Action, access_token: str) -> None:
    reddit = get_reddit()
    reddit.auth.implicit(access_token, 3600, ' '.join(SCOPES))
    if action == Action.Download:
        print('Getting saved submissions ...')
        submissions = []
        for item in reddit.user.me().saved(limit=None):
            if isinstance(item, (Comment, )):
                submissions.append({
                    "type": "comment",
                    "id": item.id,
                    "link_id": item.link_id,
                    "submission_id": item.submission.id,
                    "subreddit": item.subreddit.display_name,
                })
            else:
                submissions.append({
                    "type": "post",
                    "id": item.id,
                    "subreddit": item.subreddit.display_name,
                    "title": item.title,
                    "is_self": item.is_self,
                    "url": item.url,
                })
        with open(SAVE_FILE_NAME, 'w') as f:
            json.dump(submissions, f, indent=2)
    elif action == Action.Upload:
        with open(SAVE_FILE_NAME) as f:
            data = json.load(f)
        for index, item in enumerate(data[::-1]):
            print(f'Saving submission {index + 1} of {len(data)}')
            Submission(reddit=reddit, id=item['id']).save()
            sleep(1)  # API rate limit is 60/min; this is close enough
    else:
        raise ValueError(f'Unknown action {action}')


@click.group()
def cli() -> None:
    pass


@cli.command()
def download() -> None:
    """Download your saved posts to a file"""
    if os.path.exists(SAVE_FILE_NAME):
        print(f'"{SAVE_FILE_NAME}" already exists, delete or rename before starting this process')
        return
    start_auth_flow(Action.Download)


@cli.command()
def upload() -> None:
    """Upload saved posts from a file to your account"""
    if not os.path.exists(SAVE_FILE_NAME):
        print(f'Cannot open "{SAVE_FILE_NAME}"')
        return
    start_auth_flow(Action.Upload)


if __name__ == '__main__':
    cli()
