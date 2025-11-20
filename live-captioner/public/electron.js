const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 300,
        minWidth: 620,
        minHeight: 300,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false, // For easier IPC in MVP
            enableRemoteModule: true,
        },
        frame: false, // Frameless for custom UI
        transparent: true, // Enable transparency
        alwaysOnTop: false, // Toggleable later
        resizable: true,
    });

    mainWindow.loadURL(
        isDev
            ? 'http://localhost:3000'
            : `file://${path.join(__dirname, '../build/index.html')}`
    );

    if (isDev) {
        // mainWindow.webContents.openDevTools({ mode: 'detach' });
    }

    mainWindow.on('closed', () => (mainWindow = null));
}

function startPythonBackend() {
    const scriptPath = isDev
        ? path.join(__dirname, '../../src/electron_bridge.py')
        : path.join(process.resourcesPath, 'src/electron_bridge.py'); // Adjust for prod

    const cwd = isDev
        ? path.join(__dirname, '../../src')
        : path.join(process.resourcesPath, 'src');

    // Try to use venv Python first, fall back to system Python
    const projectRoot = isDev
        ? path.join(__dirname, '../..')
        : process.resourcesPath;

    const venvPythonPath = path.join(projectRoot, 'venv', 'Scripts', 'python.exe');
    const fs = require('fs');

    let pythonCommand = 'python'; // Default to system Python

    if (fs.existsSync(venvPythonPath)) {
        pythonCommand = venvPythonPath;
        console.log(`✓ Using venv Python: ${venvPythonPath}`);
    } else {
        console.warn('⚠ Virtual environment not found. Using system Python.');
        console.warn('  Run scripts/setup_venv.ps1 to create the venv.');
    }

    console.log(`Starting Python backend from: ${scriptPath}`);

    // Spawn Python process
    pythonProcess = spawn(pythonCommand, [scriptPath], {
        cwd: cwd,
        stdio: ['pipe', 'pipe', 'pipe'], // Pipe stdio to communicate
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python stdout: ${data}`);
        // Send data to renderer
        if (mainWindow) {
            mainWindow.webContents.send('python-data', data.toString());
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
    });
}

// IPC for resizing
ipcMain.on('resize-window', (event, { width, height, x, y }) => {
    if (mainWindow) {
        mainWindow.setBounds({ x, y, width, height });
    }
});

// IPC for Settings
ipcMain.on('set-always-on-top', (event, isAlwaysOnTop) => {
    if (mainWindow) {
        mainWindow.setAlwaysOnTop(isAlwaysOnTop);
    }
});

ipcMain.on('set-opacity', (event, opacity) => {
    if (mainWindow) {
        mainWindow.setOpacity(opacity);
    }
});

ipcMain.on('set-ignore-mouse-events', (event, ignore, options) => {
    if (mainWindow) {
        mainWindow.setIgnoreMouseEvents(ignore, options);
    }
});

ipcMain.on('minimize-window', () => {
    if (mainWindow) {
        mainWindow.minimize();
    }
});

ipcMain.on('close-window', () => {
    if (mainWindow) {
        mainWindow.close();
    }
});

ipcMain.on('set-languages', (event, languages) => {
    if (pythonProcess && pythonProcess.stdin) {
        const command = JSON.stringify({ command: 'set_languages', languages }) + '\n';
        pythonProcess.stdin.write(command);
        console.log(`Sent language selection to Python: ${languages}`);
    }
});

app.on('ready', () => {
    createWindow();
    startPythonBackend();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

app.on('will-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});
