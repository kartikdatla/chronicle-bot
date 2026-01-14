/**
 * Chronicle Bot Transcript Exporter
 * Exports transcript data to formatted Word documents
 */

const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } = require('docx');

async function createTranscript(data) {
    try {
        console.log('📖 Processing transcript data...');
        console.log(`✅ Session: ${data.session_name || data.session_id}`);
        console.log(`✅ Participants: ${data.participants.length}`);
        console.log(`📝 Transcript entries: ${data.transcript.length}`);
        
        const doc = new Document({
            sections: [{
                properties: {},
                children: [
                    // Title
                    new Paragraph({
                        text: `Session Transcript`,
                        heading: HeadingLevel.HEADING_1,
                        alignment: AlignmentType.CENTER,
                        spacing: { after: 400 }
                    }),
                    
                    // Session Name
                    new Paragraph({
                        children: [
                            new TextRun({
                                text: `Session: ${data.session_name || 'Unnamed Session'}`,
                                bold: true,
                                size: 24
                            })
                        ],
                        spacing: { after: 200 }
                    }),
                    
                    // Session ID
                    new Paragraph({
                        children: [
                            new TextRun({
                                text: `Session ID: ${data.session_id}`,
                                size: 20
                            })
                        ],
                        spacing: { after: 200 }
                    }),
                    
                    // Date/Duration
                    new Paragraph({
                        children: [
                            new TextRun({
                                text: `Date: ${data.date || new Date().toISOString().split('T')[0]}`,
                                size: 20
                            })
                        ],
                        spacing: { after: 200 }
                    }),
                    
                    // Participants
                    new Paragraph({
                        children: [
                            new TextRun({
                                text: 'Participants: ',
                                bold: true,
                                size: 20
                            }),
                            new TextRun({
                                text: data.participants.join(', '),
                                size: 20
                            })
                        ],
                        spacing: { after: 400 }
                    }),
                    
                    // Summary section (if present)
                    ...(data.summary ? [
                        new Paragraph({
                            text: 'Summary',
                            heading: HeadingLevel.HEADING_2,
                            spacing: { before: 400, after: 200 }
                        }),
                        new Paragraph({
                            text: data.summary,
                            spacing: { after: 400 }
                        })
                    ] : []),
                    
                    // Transcript section
                    new Paragraph({
                        text: 'Transcript',
                        heading: HeadingLevel.HEADING_2,
                        spacing: { before: 400, after: 200 }
                    }),
                    
                    // Transcript entries
                    ...data.transcript.map(entry => {
                        const timestamp = entry.timestamp ? 
                            `[${Math.floor(entry.timestamp / 60)}:${String(Math.floor(entry.timestamp % 60)).padStart(2, '0')}] ` : 
                            '';
                        
                        return new Paragraph({
                            children: [
                                new TextRun({
                                    text: `${timestamp}${entry.speaker.toUpperCase()}: `,
                                    bold: true
                                }),
                                new TextRun({
                                    text: entry.text
                                })
                            ],
                            spacing: { after: 100 }
                        });
                    })
                ]
            }]
        });
        
        console.log('📄 Generating Word document...');
        const buffer = await Packer.toBuffer(doc);
        
        const outputPath = data.output_path;
        console.log(`💾 Writing to: ${outputPath}`);
        fs.writeFileSync(outputPath, buffer);
        
        console.log(`✅ Success! Created: ${outputPath}`);
        console.log(`📊 File size: ${(buffer.length / 1024).toFixed(1)} KB`);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        console.error(error.stack);
        process.exit(1);
    }
}

// Read from stdin
let inputData = '';

process.stdin.on('data', chunk => {
    inputData += chunk;
});

process.stdin.on('end', async () => {
    try {
        const data = JSON.parse(inputData);
        await createTranscript(data);
        process.exit(0);
    } catch (error) {
        console.error('Failed to parse input:', error);
        process.exit(1);
    }
});

module.exports = { createTranscript };