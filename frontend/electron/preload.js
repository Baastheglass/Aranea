const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  platform: process.platform,
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  },
  // Add any additional secure APIs you need here
  // Example:
  // sendMessage: (channel, data) => {
  //   ipcRenderer.send(channel, data);
  // },
  // onMessage: (channel, callback) => {
  //   ipcRenderer.on(channel, (event, ...args) => callback(...args));
  // }
});

// Log that preload script has been loaded
console.log('Preload script loaded successfully');
