# Python 3 and boto3 Setup on macOS (Bash)

This guide provides step-by-step instructions to:

1. Install Python 3 on macOS using Bash
2. Install the AWS SDK for Python (`boto3`) globally
3. Use a virtual environment to manage dependencies locally

---

## ✅ 1. Install Python 3 (using Homebrew)

Open Terminal and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python
```

Verify installation:

```bash
python3 --version
pip3 --version
```

---

## ✅ 2. Set Python 3 as Default (Optional)

Edit your `~/.bash_profile`:

```bash
nano ~/.bash_profile
```

Add the following lines:

```bash
alias python=/usr/local/bin/python3
alias pip=/usr/local/bin/pip3
```

Apply the changes:

```bash
source ~/.bash_profile
```

Now `python` and `pip` will point to Python 3 and pip3.

---

## ✅ 3. Install `boto3`

### 🔹 Option 1: Global Installation

```bash
pip install boto3
```

Verify:

```bash
python -c "import boto3; print(boto3.__version__)"
```

---

### 🔹 Option 2: Virtual Environment Installation

1. Create a project directory and virtual environment:

```bash
mkdir myproject
cd myproject
python3 -m venv venv
```

2. Activate the virtual environment:

```bash
source venv/bin/activate
```

3. Install `boto3`:

```bash
pip install boto3
```

4. Verify installation:

```bash
python -c "import boto3; print(boto3.__version__)"
```

5. Deactivate the virtual environment when done:

```bash
deactivate
```

---

## 🔄 Quick Commands

| Action                      | Command                     |
|----------------------------|-----------------------------|
| Activate virtual env       | `source venv/bin/activate`  |
| Deactivate virtual env     | `deactivate`                |
| Install boto3 globally     | `pip install boto3`         |
| Install boto3 in venv      | `pip install boto3`         |

---

## 📝 Optional: requirements.txt

You can export your virtual environment dependencies:

```bash
pip freeze > requirements.txt
```

Install them later with:

```bash
pip install -r requirements.txt
```
