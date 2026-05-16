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

    const COLUMNS = 4;
    let tableContent = '\n| | | | |\n| :---: | :---: | :---: | :---: |\n';
    
    for (let i = 0; i < files.length; i += COLUMNS) {
      let rowIcons = '|';
      let rowNames = '|';
      
      for (let j = 0; j < COLUMNS; j++) {
        const file = files[i + j];
        if (file) {
          const name = file.replace('.png', '');
          const iconPath = `./icons/${file}`;
          rowIcons += ` <a href="${iconPath}"><img src="${iconPath}" width="48" alt="${name}"></a> |`;
          rowNames += ` \`${name}\` |`;
        } else {
          rowIcons += ' |';
          rowNames += ' |';
        }
      }
      tableContent += rowIcons + '\n' + rowNames + '\n';
    }

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
    console.log(`Successfully updated README.md with a grid of ${files.length} icons.`);
  } catch (err) {
    console.error('Error updating README:', err);
  }
}

updateReadme();
