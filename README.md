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

  <p align="center">
<img width="600" alt="chrome-demo" src="https://github.com/user-attachments/assets/97c717a4-c3aa-4980-b4d2-4a3c057d1bba" />
  </p>

### push to trmnl

this pushes to a [physical device](https://trmnl.com).

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

<p align="center">
<img width="600" alt="trmnl-demo" src="https://github.com/user-attachments/assets/b6bc818f-da9d-43f1-808a-f4d15cc27858" />
</p>
