\# Changelog



\## \[v1.1.0] - 2026-01-13



\### ✨ New Features

\- \*\*Timestamps in Transcripts\*\*: Each dialogue line now shows when it was spoken (\[MM:SS] format)

\- \*\*Fantasy Name Auto-Correction\*\*: Automatically fixes commonly misheard RPG terms

&nbsp;	- To update your own dictionary, go to bot\\transcription\_orchestrator.py and scroll down to "def \_fix\_fantasy\_names…." and add your custom text under the replacements like so:

&nbsp;	- def \_fix\_fantasy\_names(self, text):

&nbsp;  		 """Fix commonly misheard fantasy names"""

&nbsp; 		  replacements = {

&nbsp;    			'algorithm star': 'Algonstar',                           <----|

&nbsp;     	  		'algo star': 'Algonstar',	                         <----|

&nbsp;       		'next us': 'Nexus',                 		         <----|  Like so, the incorrect spelling or word on the left of the colon

&nbsp;       		'lighter college': 'Blight College',                     <----|	 and the correct spelling on the right

&nbsp;       		'man away': 'mana-waste',                                <----|

&nbsp;       		'break': 'Breok',  # The god's name                      <----|

&nbsp;       # Add more as you discover them

&nbsp;   }

&nbsp;   

&nbsp;   for wrong, right in replacements.items():

&nbsp;       text = text.replace(wrong, right)

&nbsp;       # Case-insensitive version

&nbsp;       text = text.replace(wrong.title(), right)

&nbsp;   

&nbsp;   return text





\- \*\*Enhanced AI Summaries\*\*: Summaries now scale with session length

&nbsp; - Short sessions (<100 exchanges): 300-400 words

&nbsp; - Medium sessions (100-300): 600-800 words

&nbsp; - Long sessions (300+): 1000-1500 words with detailed breakdowns

\- \*\*"Previously On..." Format\*\*: Summaries now use TV-style recap format perfect for reading aloud



\### 🐛 Bug Fixes

\- Fixed duplicate participants in transcript header

\- Fixed duplicate audio file creation bug

\- Fixed transcription method name mismatch (AttributeError)

\- Fixed database column reference (audio\_file\_id vs audio\_file\_path)

\- Fixed file path resolution for absolute vs relative paths



\### 🔧 Improvements

\- Participants now listed alphabetically (no duplicates)

\- Better chronological ordering using actual audio timestamps

\- Improved error handling and logging

\- Cleaner transcript formatting



\### 📚 Documentation

\- Added comprehensive GitHub setup guides

\- Created MIT license with explanation

\- Added distribution package documentation



\### ⚙️ Technical Changes

\- Updated transcription\_orchestrator.py with timestamp handling

\- Enhanced summary\_generator.py with dynamic token allocation

\- Fixed per\_user\_sink.py to prevent duplicate saves

\- Improved transcript\_exporter.js with timestamp display



\## \[v1.0.0] - 2026-01-12



\### Initial Release

\- Discord voice recording with per-user audio files

\- Whisper AI transcription

\- Ollama AI summaries

\- PostgreSQL database backend

\- Word document exports

