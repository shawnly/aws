
bash --version
1. Install bash 4.0

brew install bash

# Add the new Bash to the list of allowed shells
echo /usr/local/bin/bash | sudo tee -a /etc/shells
which bash
echo /opt/homebrew/bin/bash | sudo tee -a /etc/shells
# Change your default shell
chsh -s /usr/local/bin/bash
Replace /usr/local/bin/bash with the actual path where Homebrew installed Bash, if different.

Check the available shells by running:
cat /etc/shells

Change your default shell to Bash by executing:
chsh -s /bin/bash