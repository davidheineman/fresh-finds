Pulls arXiv papers every morning for [these researchers](https://raw.githubusercontent.com/davidheineman/conference-papers/main/constants.py).

### setup

```sh
pip install requests arxiv

python fetch.py
```

### install the chrome extension

```sh
# go to chrome://extensions/
# turn on Developer mode (top-right corner)
# click “Load unpacked”.
# select chrome/
```

### push to trmnl

```sh
# set env vars for your trmnl
export TRMNL_API_KEY="..."
export TRMNL_USER_API_KEY="..."
export TRMNL_PLUGIN_UUID="..."
export TRMNL_MAC_ADDRESS="..."

# pull sdk
pip install git+https://github.com/davidheineman/trmnl.git

python terminal.py
```