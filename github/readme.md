# GitHub SSH Key Setup Script

This script helps you generate a new SSH key, configure your local environment, and connect securely to GitHub using SSH.

---

## 🚀 Quick Start

### 1. Clone this repo or download the script

Save the script to your local machine, for example:

```bash
curl -O https://yourdomain.com/setup_github_ssh.sh
chmod +x setup_github_ssh.sh
```

### 2. Edit the script

Open the script and replace this line:

```bash
GITHUB_EMAIL="your_email@example.com"
```

with your actual GitHub email address.

### 3. Run the script

```bash
./setup_github_ssh.sh
```

---

## 🔐 What the script does

1. Generates a new SSH key using your GitHub email.
2. Starts the SSH agent and adds your private key.
3. Prints your public key so you can paste it into GitHub.
4. Tests the SSH connection to GitHub.

---

## 🔗 Add the SSH key to GitHub

After running the script:

1. Copy the public key displayed in the terminal.
2. Go to [https://github.com/settings/keys](https://github.com/settings/keys).
3. Click **New SSH key**, give it a name (e.g., "MacBook Pro"), paste the key, and save.

---

## ✅ Verify

To confirm that SSH is working, you can run:

```bash
ssh -T git@github.com
```

You should see:

```
Hi your-username! You've successfully authenticated...
```

---

## 👥 Using Multiple GitHub Accounts

If you have more than one GitHub account (e.g., personal and work), you can configure multiple SSH keys like this:

### 1. Generate multiple keys

```bash
ssh-keygen -t ed25519 -C "personal@example.com" -f ~/.ssh/id_ed25519_personal
ssh-keygen -t ed25519 -C "work@example.com" -f ~/.ssh/id_ed25519_work
```

### 2. Add keys to the SSH agent

```bash
ssh-add ~/.ssh/id_ed25519_personal
ssh-add ~/.ssh/id_ed25519_work
```

### 3. Edit `~/.ssh/config`

```bash
nano ~/.ssh/config
```

Add the following:

```ssh
# Personal GitHub
Host github-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_personal
  IdentitiesOnly yes

# Work GitHub
Host github-work
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_work
  IdentitiesOnly yes
```

### 4. Clone using the custom host

```bash
git clone git@github-personal:username/repo.git
git clone git@github-work:yourorg/repo.git
```

---

## 🛠 Troubleshooting

- If you see permission denied errors, ensure your SSH agent is running and the key is added.
- You can list all your SSH keys with `ssh-add -l`.

---

## 📘 Resources

- [GitHub: Connecting to GitHub with SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
