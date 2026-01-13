const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } = require('docx');
const fs = require('fs');

const input = fs.readFileSync(0, 'utf-8');
const data = JSON.parse(input);

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 } }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: createContent(data)
  }]
});

function formatTimestamp(seconds) {
  /**
   * Convert seconds to [MM:SS] or [HH:MM:SS] format
   */
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `[${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}]`;
  } else {
    return `[${minutes}:${secs.toString().padStart(2, '0')}]`;
  }
}

function createContent(data) {
  const content = [];
  
  content.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.CENTER,
    children: [new TextRun(data.session_name || "RPG Session Transcript")]
  }));
  
  content.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [
      new TextRun({ text: 'Session ID: ' + data.session_id + '\n', size: 20 }),
      new TextRun({ text: 'Date: ' + data.date + '\n', size: 20 }),
      new TextRun({ text: 'Duration: ' + data.duration, size: 20 })
    ]
  }));
  
  content.push(new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun("Participants")]
  }));
  
  data.participants.forEach(p => {
    content.push(new Paragraph({
      children: [new TextRun('• ' + p)]
    }));
  });
  
  content.push(new Paragraph({ spacing: { after: 240 }, children: [] }));
  
  content.push(new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun("Transcript")]
  }));
  
  data.transcript.forEach((entry, index) => {
    // Get timestamp (default to 0 if not provided)
    const timestamp = entry.timestamp || 0;
    const timeStr = formatTimestamp(timestamp);
    
    // Speaker line with timestamp
    content.push(new Paragraph({
      spacing: { before: index === 0 ? 0 : 120, after: 60 },
      children: [
        new TextRun({ text: timeStr + ' ', color: "666666", size: 22 }),
        new TextRun({ text: entry.speaker.toUpperCase(), bold: true, size: 24 })
      ]
    }));
    
    // Dialogue text
    content.push(new Paragraph({
      indent: { left: 360 },
      spacing: { after: 120 },
      children: [new TextRun({ text: entry.text, size: 24 })]
    }));
  });
  
  return content;
}

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(data.output_path, buffer);
  console.log('Transcript saved to: ' + data.output_path);
}).catch(err => {
  console.error('Error:', err);
  process.exit(1);
});