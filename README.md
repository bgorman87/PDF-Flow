# Report Sorter
This program has multi-threaded functionality to:
- Analyze PDF document contents
  - Uses Poppler to transform PDF to Image
  - Image is then pre-processed using OpenCv
  - Processed image is then fed into the Tesseract OCR Engine
  - Returned text is processed. Main info its looking for is project number
  - Project Number is used to determine what file is named, where its saved, and who ti gets emailed to
  - Use other OCR results to format other report specific data into filename
- Save document onto server location dependant upon OCR project info results
- View analyzed files in the output tab
  - Allows editing the filename while viewing file contents
    - Manual review is advised due to OCR un-reliability at times
- If project data not read due to bad OCR results, manual entry can be done which will also return project data
- Email reports to project client list
  - Draft email will be created with To and CC list autofilled with project specific email lists, as well as subject, body, and signature already in place, with the newly analyzed document already attached
