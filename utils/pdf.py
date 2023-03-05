from pypdf import PdfWriter, PdfReader, PdfMerger

#? gets a list of rawpdf bytes and writes combined file to loc returns file path
def pdfMerge(fileList, loc):
    merger = PdfMerger()
    for byte in fileList:
        merger.append(byte)
        
    with open(loc + "/combinedPdf.pdf", 'wb') as f:
        merger.write(f)
        
    return loc + "/combinedPdf.pdf"

#? takes in a pdf, locaton, and dict of values to replace and fills it out and returns the locaiton of the filled pdf
def pdfFormFiller(pdf, loc, dict):
    reader = PdfReader(pdf)
    writer = PdfWriter()
    
    page = reader.pages[0]
    
    writer.add_page(page)
    writer.update_page_form_field_values(writer.pages[0], dict)
        
    with open(loc + "/filledOut.pdf", "wb") as f:
        writer.write(f)
    
    return loc + "/filledOut.pdf"
