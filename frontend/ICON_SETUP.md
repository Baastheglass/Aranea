# Electron App Icon Setup

## Required Icon Files

For a professional Electron app, you need to provide icon files for each platform:

### macOS (.icns)
Location: `frontend/public/icon.icns`
- Format: ICNS (Apple Icon Image)
- Recommended size: 1024x1024px base image
- Tools: Use `iconutil` (macOS) or online converters

### Windows (.ico)
Location: `frontend/public/icon.ico`
- Format: ICO (Windows Icon)
- Recommended sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
- Tools: Use GIMP, Paint.NET, or online converters

### Linux (.png)
Location: `frontend/public/icon.png`
- Format: PNG
- Recommended size: 512x512px or 1024x1024px
- Transparent background recommended

## Current Status

⚠️ **Icon files are not yet created!**

You're currently using placeholder icons. Before distributing your app, you should:

1. Design a proper app icon (1024x1024px recommended)
2. Convert it to the required formats
3. Place the files in the locations listed above

## Quick Icon Generation Guide

### Using a Single PNG (1024x1024px)

1. **For macOS (.icns):**
   ```bash
   # Create iconset folder
   mkdir icon.iconset
   
   # Generate all required sizes
   sips -z 16 16     icon1024.png --out icon.iconset/icon_16x16.png
   sips -z 32 32     icon1024.png --out icon.iconset/icon_16x16@2x.png
   sips -z 32 32     icon1024.png --out icon.iconset/icon_32x32.png
   sips -z 64 64     icon1024.png --out icon.iconset/icon_32x32@2x.png
   sips -z 128 128   icon1024.png --out icon.iconset/icon_128x128.png
   sips -z 256 256   icon1024.png --out icon.iconset/icon_128x128@2x.png
   sips -z 256 256   icon1024.png --out icon.iconset/icon_256x256.png
   sips -z 512 512   icon1024.png --out icon.iconset/icon_256x256@2x.png
   sips -z 512 512   icon1024.png --out icon.iconset/icon_512x512.png
   sips -z 1024 1024 icon1024.png --out icon.iconset/icon_512x512@2x.png
   
   # Convert to .icns
   iconutil -c icns icon.iconset -o frontend/public/icon.icns
   ```

2. **For Windows (.ico):**
   - Use an online converter like: https://convertio.co/png-ico/
   - Or use ImageMagick:
   ```bash
   convert icon1024.png -define icon:auto-resize=256,128,64,48,32,16 frontend/public/icon.ico
   ```

3. **For Linux (.png):**
   ```bash
   cp icon1024.png frontend/public/icon.png
   ```

## Using the Spider Logo

Since your app is called "Sentinel" and uses spider imagery:

1. Use one of the provided spider ASCII art as inspiration
2. Create a modern, professional spider icon
3. Consider using purple/blue colors to match the theme
4. Keep it simple and recognizable at small sizes

## Online Icon Generators

If you don't want to manually create icons:
- https://www.electron.build/icons
- https://icon.kitchen/
- https://appicon.co/

## Design Tips

- **Simplicity**: Icons should be recognizable at 16x16px
- **Contrast**: Use high contrast colors
- **No Text**: Avoid text in icons (especially small text)
- **Centered**: Main element should be centered
- **Padding**: Leave 10-15% padding around edges

## Testing Your Icons

After adding icon files:
```bash
# Build the app to see the icons
npm run pack

# Check the built app in frontend/dist/
```

---

**Note**: The app will still build and run without custom icons, but will use default Electron icons instead.
