# Virtual Environment Setup Guide

This project uses a Python virtual environment to isolate dependencies and ensure consistent behavior across different systems.

## Quick Start

### 1. Create the Virtual Environment

Run the setup script from the project root:

```powershell
.\scripts\setup_venv.ps1
```

This will:
- Create a `venv` folder in the project root
- Install all dependencies from `requirements.txt`
- Configure the environment for the project

### 2. The Electron App Will Auto-Use the venv

When you run the Electron app, it will automatically detect and use the Python interpreter from the venv if available.

No manual activation needed for normal app usage!

## Manual Activation (Optional)

If you need to run Python commands manually (e.g., testing, debugging), activate the venv:

```powershell
# Option 1: Direct activation
.\venv\Scripts\Activate.ps1

# Option 2: Helper script
.\scripts\activate_venv.ps1
```

You'll see `(venv)` in your terminal prompt when activated.

To deactivate:
```powershell
deactivate
```

## Adding New Dependencies

1. Activate the venv (if not already active)
2. Install the package:
   ```powershell
   pip install package-name
   ```
3. Update requirements.txt:
   ```powershell
   pip freeze > requirements.txt
   ```

## Troubleshooting

### "Cannot run scripts" error on Windows

If you get an execution policy error, run PowerShell as Administrator and execute:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Venv not found

Make sure you've run the setup script:
```powershell
.\scripts\setup_venv.ps1
```

### Dependencies not installing

1. Make sure you have Python 3.8+ installed
2. Try upgrading pip:
   ```powershell
   python -m pip install --upgrade pip
   ```
3. Run setup again

## Current Dependencies

- **vosk** - Speech recognition models
- **pyaudio** - Audio input/output
- **numpy** - Numerical operations for audio processing

## Notes

- The `venv` folder is gitignored and won't be committed
- Each developer needs to create their own venv
- The Electron app automatically detects the venv Python path
- If venv is not found, it falls back to system Python (with a warning)
