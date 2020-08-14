from enum import Enum
import os
import webbrowser
from time import sleep

import click
from flask import Flask, request, render_template_string
from praw import Reddit
from praw.models import Submission


CLIENT_ID = '2fINEZ0uC_0jAg'
USER_AGENT = 'https://github.com/celeo/reddit_save_transfer'
REDIRECT_URI = 'http://localhost:5000/callback'
SCOPES = ['identity', 'history', 'save']
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
SAVE_FILE_NAME = 'saved_posts.txt'


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
        count = 0
        print('Getting saved posts ...')
        with open(SAVE_FILE_NAME, 'w') as f:
            for item in reddit.user.me().saved(limit=None):
                f.write(f'{item.id}\n')
                count += 1
            print(f'Done, recorded {count} saved submissions to "{SAVE_FILE_NAME}"')
    elif action == Action.Upload:
        with open(SAVE_FILE_NAME) as f:
            submission_ids = [line.strip() for line in f.readlines()]
        for index, submission_id in enumerate(submission_ids):
            print(f'Saving submission {index + 1} of {len(submission_ids)}')
            Submission(reddit=reddit, id=submission_id).save()
            sleep(1)  # API rate limit is 60/min, this is close enough
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
