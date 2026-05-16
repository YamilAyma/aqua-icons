const fs = require('fs');
const path = require('path');

const ICONS_DIR = path.join(__dirname, '../icons');
const README_PATH = path.join(__dirname, '../README.md');

const ICON_TABLE_START = '<!-- ICON_TABLE_START -->';
const ICON_TABLE_END = '<!-- ICON_TABLE_END -->';

async function updateReadme() {
  try {
    const files = fs.readdirSync(ICONS_DIR)
      .filter(file => file.endsWith('.png'))
      .sort((a, b) => a.localeCompare(b));

    let tableContent = '\n| Icono | Nombre |\n| :---: | :--- |\n';
    
    // User requested a table with link to icon and name below. 
    // To make it look good in README, I'll use a standard vertical table for now, 
    // or a grid if possible. Let's do a simple 2-column table as a baseline 
    // but the user said "link para ir al icono, un nombre debajo".
    // Actually, "link para ir al icono" usually implies the image itself is a link or has a link.
    
    files.forEach(file => {
      const name = file.replace('.png', '');
      const iconPath = `./icons/${file}`;
      tableContent += `| [![${name}](${iconPath})](${iconPath}) | \`${name}\` |\n`;
    });

    const readme = fs.readFileSync(README_PATH, 'utf8');
    const startIdx = readme.indexOf(ICON_TABLE_START);
    const endIdx = readme.indexOf(ICON_TABLE_END);

    if (startIdx === -1 || endIdx === -1) {
      console.error('Placeholder flags not found in README.md');
      return;
    }

    const newReadme = 
      readme.substring(0, startIdx + ICON_TABLE_START.length) +
      '\n' + tableContent + '\n' +
      readme.substring(endIdx);

    fs.writeFileSync(README_PATH, newReadme);
    console.log(`Successfully updated README.md with ${files.length} icons.`);
  } catch (err) {
    console.error('Error updating README:', err);
  }
}

updateReadme();
