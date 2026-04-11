# Portfolio for Joshua Cundiff

This repository will include the projects of mine to show off on a portfolio.

## Setup After Cloning / Pulling

### FlakkOps

```bash
cd FlakkOps
python seed.py
```

### Histacruise

The `instance/` directory is gitignored and must be created manually before seeding:

```bash
mkdir -p Histacruise/instance
cd Histacruise
pip install -r requirements.txt
python seed.py
```

Demo login: `demo@histacruise.com` / `Demo1234!`