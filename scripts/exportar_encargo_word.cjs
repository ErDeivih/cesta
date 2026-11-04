// Exporta el Markdown vigente sin mantener otra especificacion divergente.
// NODE_PATH puede apuntar a las dependencias documentales del entorno.
const fs = require('node:fs');
const path = require('node:path');
const {
  AlignmentType, Document, ExternalHyperlink, Footer, Header, HeadingLevel,
  LevelFormat, Packer, PageNumber, Paragraph, ShadingType,
  Table, TableCell, TableRow, TextRun, WidthType,
} = require('docx');

const [input, output] = process.argv.slice(2);
if (!input || !output) throw new Error('Uso: node exportar_encargo_word.cjs entrada.md salida.docx');
const width = 10006;

function runs(text, options = {}) {
  const result = [];
  const pattern = /\[([^\]]+)\]\(([^)]+)\)|`([^`]+)`|\*\*([^*]+)\*\*/g;
  let start = 0;
  for (const match of text.matchAll(pattern)) {
    if (match.index > start) result.push(new TextRun({ text: text.slice(start, match.index), ...options }));
    if (match[1] && /^https:\/\//.test(match[2])) {
      result.push(new ExternalHyperlink({ link: match[2], children: [
        new TextRun({ text: match[1], style: 'Hyperlink', ...options }),
      ] }));
    } else if (match[1]) {
      result.push(new TextRun({ text: match[1], ...options }));
    } else if (match[3]) {
      result.push(new TextRun({ text: match[3], font: 'Consolas', size: 19, ...options }));
    } else {
      result.push(new TextRun({ text: match[4], bold: true, ...options }));
    }
    start = match.index + match[0].length;
  }
  if (start < text.length) result.push(new TextRun({ text: text.slice(start), ...options }));
  return result;
}

function table(lines) {
  const cells = lines.map(line => line.trim().slice(1, -1).split('|').map(x => x.trim()))
    .filter(row => !row.every(x => /^:?-+:?$/.test(x)));
  const n = cells[0].length;
  const widths = Array(n).fill(Math.floor(width / n));
  widths[n - 1] += width - widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: width, type: WidthType.DXA }, columnWidths: widths,
    rows: cells.map((row, index) => new TableRow({
      tableHeader: index === 0, cantSplit: true,
      children: row.map((text, col) => new TableCell({
        width: { size: widths[col], type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: index === 0 ? '183A32' : (index % 2 ? 'F4F0E8' : 'FFFFFF') },
        margins: { top: 90, bottom: 90, left: 100, right: 100 },
        children: [new Paragraph({ spacing: { after: 30 }, children: runs(text, {
          size: 19, color: index === 0 ? 'FFFFFF' : '202724', bold: index === 0,
        }) })],
      })),
    })),
  });
}

const children = [];
const lines = fs.readFileSync(input, 'utf8').split(/\r?\n/);
let pending = [];
const flush = () => {
  if (pending.length) children.push(new Paragraph({ children: runs(pending.join(' ')) }));
  pending = [];
};
for (let i = 0; i < lines.length; i++) {
  const line = lines[i].trim();
  if (!line) { flush(); continue; }
  const heading = /^(#{1,3}) (.+)$/.exec(line);
  if (heading) {
    flush();
    children.push(new Paragraph({ children: runs(heading[2]),
      heading: [HeadingLevel.TITLE, HeadingLevel.HEADING_1, HeadingLevel.HEADING_2][heading[1].length - 1],
      keepNext: true,
    }));
  } else if (line.startsWith('|')) {
    flush();
    const rows = [line];
    while (i + 1 < lines.length && lines[i + 1].trim().startsWith('|')) rows.push(lines[++i]);
    children.push(table(rows));
    children.push(new Paragraph({ spacing: { after: 50 } }));
  } else if (/^- /.test(line)) {
    flush();
    let text = line.slice(2);
    while (i + 1 < lines.length && /^  \S/.test(lines[i + 1])) text += ' ' + lines[++i].trim();
    children.push(new Paragraph({ children: runs(text), numbering: { reference: 'bullets', level: 0 } }));
  } else {
    pending.push(line);
  }
}
flush();
const doc = new Document({
  creator: 'Cesta · revisión y planificación', title: 'Encargo vigente para DeepSeek · 13/10/2026',
  description: 'Compra, recetas y calorias: plan operativo B00-B16 y aceptacion de cinco recetas.',
  styles: {
    default: { document: { run: { font: 'Calibri', size: 21, color: '202724' },
      paragraph: { spacing: { after: 100, line: 260 } } } },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal',
        run: { font: 'Cambria', size: 40, bold: true, color: '183A32' },
        paragraph: { spacing: { after: 250 } } },
      { id: 'Heading1', name: 'heading 1', basedOn: 'Normal', next: 'Normal',
        run: { font: 'Cambria', size: 30, bold: true, color: '183A32' },
        paragraph: { keepNext: true, spacing: { before: 230, after: 120 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'heading 2', basedOn: 'Normal', next: 'Normal',
        run: { size: 24, bold: true, color: 'A94D36' },
        paragraph: { keepNext: true, spacing: { before: 190, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET,
    text: '\u2022', alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 280, hanging: 180 } } },
  }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 },
      margin: { top: 950, bottom: 950, left: 950, right: 950, header: 400, footer: 400 } } },
    headers: { default: new Header({ children: [new Paragraph({
      children: [new TextRun({ text: 'CESTA  /  ENCARGO VIGENTE  /  13 OCT 2026', color: '536158', size: 16 })],
    })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: 'Plan B00–B16  ·  ', size: 16, color: '536158' }),
        new TextRun({ children: [PageNumber.CURRENT], size: 16 }), new TextRun({ text: ' / ', size: 16 }),
        new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16 })],
    })] }) },
    children,
  }],
});
fs.mkdirSync(path.dirname(output), { recursive: true });
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(output, buffer);
  console.log(JSON.stringify({ output, bytes: buffer.length, blocks: children.length }));
}).catch(error => { console.error(error); process.exitCode = 1; });
