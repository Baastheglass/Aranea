const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess;
let isQuitting = false;
let cleanupTimeout = null;

// Graceful shutdown function
function cleanupProcesses() {
  if (isQuitting) {
    return Promise.resolve();
  }
  
  isQuitting = true;
  console.log('🛑 Initiating graceful shutdown...');
  
  return new Promise((resolve) => {
    let cleaned = false;
    
    // Set a maximum timeout for cleanup
    cleanupTimeout = setTimeout(() => {
      if (!cleaned) {
        console.log('⚠ Cleanup timeout reached, forcing shutdown');
        forceCleanup();
        cleaned = true;
        resolve();
      }
    }, 10000); // 10 second timeout
    
    // Kill Python process gracefully
    if (pythonProcess && !pythonProcess.killed) {
      console.log('Stopping Python backend...');
      
      // Try graceful shutdown first
      pythonProcess.kill('SIGTERM');
      
      // Wait for process to exit
      const checkInterval = setInterval(() => {
        if (pythonProcess.killed || !pythonProcess.pid) {
          clearInterval(checkInterval);
          console.log('✓ Python backend stopped');
          
          // Also kill any remaining processes on ports
          killPortProcesses(() => {
            cleaned = true;
            if (cleanupTimeout) {
              clearTimeout(cleanupTimeout);
            }
            resolve();
          });
        }
      }, 500);
      
      // Force kill after 5 seconds
      setTimeout(() => {
        if (pythonProcess && !pythonProcess.killed) {
          console.log('⚠ Force killing Python backend');
          try {
            pythonProcess.kill('SIGKILL');
          } catch (e) {
            console.error('Error force killing:', e);
          }
        }
      }, 5000);
    } else {
      // No python process to clean
      killPortProcesses(() => {
        cleaned = true;
        if (cleanupTimeout) {
          clearTimeout(cleanupTimeout);
        }
        resolve();
      });
    }
  });
}

// Force cleanup all related processes
function forceCleanup() {
  console.log('⚠ Performing force cleanup');
  
  if (pythonProcess) {
    try {
      pythonProcess.kill('SIGKILL');
    } catch (e) {
      console.error('Error in force cleanup:', e);
    }
  }
  
  // Kill processes on specific ports (synchronous)
  try {
    exec('lsof -ti:8000 | xargs kill -9 2>/dev/null', () => {});
    exec('lsof -ti:55552 | xargs kill -9 2>/dev/null', () => {});
    exec('pkill -9 -f msfrpcd 2>/dev/null', () => {});
  } catch (e) {
    // Ignore errors in force cleanup
  }
}

// Kill processes on ports used by the app
function killPortProcesses(callback) {
  console.log('Freeing ports 8000 and 55552...');
  
  // Kill process on port 8000 (FastAPI)
  exec('lsof -ti:8000 | xargs kill -TERM 2>/dev/null', (error1) => {
    // Kill process on port 55552 (msfrpcd)
    exec('lsof -ti:55552 | xargs kill -TERM 2>/dev/null', (error2) => {
      // Kill any msfrpcd processes
      exec('pkill -TERM -f msfrpcd 2>/dev/null', (error3) => {
        console.log('✓ Port cleanup complete');
        setTimeout(callback, 1000); // Wait a bit for processes to terminate
      });
    });
  });
}

// Check if Python backend is available
function checkPythonBackend() {
  const pythonPath = !app.isPackaged 
    ? path.join(__dirname, '../../backend/env/bin/python')
    : path.join(process.resourcesPath, 'backend', 'env', 'bin', 'python');
  
  return fs.existsSync(pythonPath);
}

// Start Python backend
function startPythonBackend() {
  return new Promise((resolve, reject) => {
    const pythonPath = !app.isPackaged 
      ? path.join(__dirname, '../../backend/env/bin/python')
      : path.join(process.resourcesPath, 'backend', 'env', 'bin', 'python');
    
    const scriptPath = !app.isPackaged
      ? path.join(__dirname, '../../backend/app.py')
      : path.join(process.resourcesPath, 'backend', 'app.py');

    console.log('Starting Python backend...');
    console.log('Python path:', pythonPath);
    console.log('Script path:', scriptPath);

    // Set environment variables for Python process
    const env = Object.assign({}, process.env);
    
    // Add Python path to environment
    if (!app.isPackaged) {
      const backendDir = path.join(__dirname, '../../backend');
      env.PYTHONPATH = backendDir;
    }

    pythonProcess = spawn(pythonPath, [
      '-u',  // Unbuffered output
      scriptPath
    ], { 
      env: env,
      cwd: !app.isPackaged ? path.join(__dirname, '../../backend') : path.join(process.resourcesPath, 'backend'),
      detached: false // Keep as child process for proper cleanup
    });
    
    // Track the process for cleanup
    if (pythonProcess.pid) {
      console.log(`Python backend started with PID: ${pythonProcess.pid}`);
    }
    
    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log(`[Python Backend] ${output}`);
      
      // Resolve when server starts
      if (output.includes('Uvicorn running') || output.includes('Application startup complete')) {
        console.log('✓ Python backend started successfully');
        resolve();
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`[Python Error] ${data}`);
    });

    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python backend:', error);
      reject(error);
    });

    pythonProcess.on('close', (code) => {
      console.log(`Python backend exited with code ${code}`);
      if (code !== 0 && code !== null) {
        reject(new Error(`Python backend exited with code ${code}`));
      }
    });

    // Timeout after 30 seconds
    setTimeout(() => {
      console.log('Backend startup timeout - assuming success');
      resolve();
    }, 30000);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../public/favicon.ico'),
    title: 'Sentinel - AI Penetration Testing Assistant',
    backgroundColor: '#000000'
  });

  // Load the app
  const startURL = !app.isPackaged
    ? 'http://localhost:3000'
    : `file://${path.join(__dirname, '../out/index.html')}`;

  console.log('Loading URL:', startURL);
  mainWindow.loadURL(startURL);

  // Open DevTools in development
  if (!app.isPackaged) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
    // Trigger cleanup when main window is closed
    if (!isQuitting) {
      cleanupProcesses().then(() => {
        if (process.platform !== 'darwin') {
          app.quit();
        }
      });
    }
  });

  // Handle navigation
  mainWindow.webContents.on('will-navigate', (event, url) => {
    // Allow navigation within the app
    if (!url.startsWith('http://localhost') && !url.startsWith('file://')) {
      event.preventDefault();
    }
  });
}

async function initializeApp() {
  try {
    // Check if Python backend is available
    if (!checkPythonBackend()) {
      await dialog.showMessageBox({
        type: 'error',
        title: 'Backend Not Found',
        message: 'Python backend not found. Please ensure the backend is properly installed.',
        buttons: ['OK']
      });
      app.quit();
      return;
    }

    // Start Python backend
    console.log('Initializing Python backend...');
    await startPythonBackend();
    
    // Wait a bit more for the server to be fully ready
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Create Electron window
    createWindow();
  } catch (error) {
    console.error('Failed to initialize app:', error);
    await dialog.showMessageBox({
      type: 'error',
      title: 'Startup Error',
      message: `Failed to start the application: ${error.message}`,
      buttons: ['OK']
    });
    app.quit();
  }
}

// App lifecycle events
app.whenReady().then(initializeApp);

app.on('window-all-closed', async () => {
  // Perform cleanup
  await cleanupProcesses();
  
  // Quit app
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null && BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Handle app quit - ensure cleanup happens
app.on('before-quit', async (event) => {
  if (!isQuitting) {
    event.preventDefault();
    await cleanupProcesses();
    app.quit();
  }
});

// Handle process exit signals
process.on('SIGTERM', async () => {
  console.log('Received SIGTERM');
  await cleanupProcesses();
  app.quit();
});

process.on('SIGINT', async () => {
  console.log('Received SIGINT');
  await cleanupProcesses();
  app.quit();
});

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}
