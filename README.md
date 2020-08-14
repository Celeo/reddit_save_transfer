# reddit_save_transfer

CLI program to transfer all of your [reddit](https://old.reddit.com) saves from one account to another.

You must own both accounts.

## Using

Note: this program is not tailored for non-technical users. Some technical knowledge is required.

```sh
git clone https://github.com/Celeo/reddit_save_transfer
cd reddit_save_transfer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then you can do `python main.py download` to download your saved submission to a text file, and `python main.py upload` to upload those to another account.

Authentication is done through Reddit's OAuth; you will not be entering your password into this application. While it's certainly short enough for you to audit the code to make sure that nothing weird is being done with your credentials, utilizing this authorization flow avoids all of that.

## Developing

### Building

### Requirements

* Git
* Python 3

### Steps

Pretty much the same as running it.

## Contributing

Please feel free to contribute. Please open an issue first (or comment on an existing one) so that I know that you want to add/change something.

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in the work by you, as defined in the Apache-2.0 license,
shall be dual licensed as above, without any additional terms or conditions.
