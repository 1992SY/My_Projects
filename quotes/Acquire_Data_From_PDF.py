import urllib.request
from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

# load a sample PDF report
url= "https://unesdoc.unesco.org/in/rest/"
url += "annotationSVC/DownloadWatermarkedAttachment/"
url += "attach_import_db06f7c4-b33f"
url += "-4833-be56-bbf54afdee3f?"
url += "_=375724eng.pdf"
urllib.request.urlretrieve(url, "UN_water_report.pdf")

# read the PDF
file_path = "UN_water_report.pdf"
output_string= StringIO()
with open(file_path,'rb') as in_file:
    parser = PDFParser(in_file)
    doc= PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.create_pages(doc):
        interpreter.process_page(page)

# print the output string
print(output_string.getvalue())

# extract certain pages from the PDF file
pages = [7,8]

file_path = "UN_water_report.pdf"
output_string_2= StringIO()
with open(file_path,'rb') as in_file:
    parser = PDFParser(in_file)
    doc= PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, output_string_2, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    page_enum = enumerate(PDFPage.create_pages(doc))
    for pagenumber, page in page_enum:
        if pagenumber in pages:
            interpreter.process_page(page)
        else:
            continue
# print the output string
print(output_string_2.getvalue())

import tabula

tab = tabula.read_pdf('UN_water_report.pdf', pages = '77')

print(tab[0])

    


