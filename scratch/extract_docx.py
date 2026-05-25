import os
import zipfile
import xml.etree.ElementTree as ET

def extract_docx_text(docx_path):
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text_content = []
    
    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read('word/document.xml')
        root = ET.fromstring(xml_content)
        
        # Iterate over all elements
        for elem in root.iter():
            if elem.tag.endswith('}p'):
                p_text = []
                for child in elem.iter():
                    if child.tag.endswith('}t'):
                        if child.text:
                            p_text.append(child.text)
                # Combine text in paragraph
                paragraph_str = "".join(p_text)
                text_content.append(paragraph_str)
                
    return "\n".join(text_content)

if __name__ == '__main__':
    docx_file = "Manuale Gestionale Laboratorio.docx"
    output_file = "scratch/manuale_text.txt"
    
    if os.path.exists(docx_file):
        print(f"Extracting text from {docx_file}...")
        extracted_text = extract_docx_text(docx_file)
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        print(f"Extracted text saved to {output_file}")
    else:
        print(f"Error: {docx_file} not found.")
