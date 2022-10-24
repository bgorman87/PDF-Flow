# Report Sorter
This program has funtionality to:
- Analyze PDF document contents
  - Use OCR results to retrieve project data
  - Use project data to format filename
  - Use other OCR results to format other report specific data into filename
- Save document onto server location dependant upon OCR project info results
- Allow editing filename which will rename file with open preview
- If project data not read due to bad OCR results, manual entry can be done which will also return project data
- Email reports to project client list
  - Draft email will be created with To and CC list autofilled with project specific email lists, as well as subject, body, and signature already in place, with the newly analyzed document already attached
