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

    console.log(`Starting Python backend from: ${scriptPath}`);

    // Spawn Python process
    // Ensure 'python' is in PATH or use a bundled python
    pythonProcess = spawn('python', [scriptPath], {
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
