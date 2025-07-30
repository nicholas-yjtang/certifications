import pandas as pd
import re
import fitz
from airium import Airium
import urllib.parse

def get_dataframe_from_checklist(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name, converters=converters)
    return df

def set_text(a, text, i):
    first_line = True
    ul_started = False
    li_stack = []
    previous_line = ''
    with a.p():
        for line in text.splitlines():
            if (line.find("Copyright © The Open Group 2022") == 0):
                continue
            if (line.find(str(i)) == 0):
                continue 
            if (line[len(line)-1] == ' '):
                previous_line += line
                continue
            if (previous_line != ''): 
                line = previous_line + line
                previous_line = ''
            print (f"Line: {line}")
            if (first_line):
                with a.h2():
                    a(line)
                first_line = False
            else:
                if (line.find('•')==0):
                    ul_started = True
                    continue
                if (ul_started):
                    li_stack.append(line)
                    ul_started = False
                    continue
                elif (len(li_stack) > 0):
                    with a.ul():
                        for li in li_stack:
                            with a.li():
                                a(li)
                    li_stack = []                
                a(line) 
    return

def set_anchor(a, text, url):
    with a.li():
        with a.a(href=url, target="_blank"):
            a(text)
    return

def get_zoom(pdf_page, block):
    if (len(block) < 2):
        return "page-width"
    return "page-width,0," + str(int(pdf_page.get_text('dict')["height"] - block[1])+1)

def get_view(pdf_page, block):
    if (len(block) < 2):
        return "FitH,0"
    return "FitH," + str(int(block[1]/pdf_page.get_text('dict')["height"]*1080)-10)

def set_pdf_anchor(a, text, url, page, pdf_page, block):
    view = get_view(pdf_page, block)
    zoom = get_zoom(pdf_page, block)
    set_anchor(a, text, f"{url}#page={page}&zoom={zoom}&view={view}")

def is_valid_klp(df, row):
    if pd.isna(df.at[row, 'KLP']):
        return False
    klp = re.split(' ', df.at[row, 'KLP'])
    if (len(klp) == 1):
        return False
    return True

def is_valid_learning_outcome(df, row):
    if pd.isna(df.at[row, 'Learning Outcome Reference']):
        return False
    return True

def is_valid_learning_outcome_title(df, row):
    if pd.isna(df.at[row, 'Learning Outcome Reference Title']):
        return False
    return True

def is_valid_reference_within_document(df, row):
    if pd.isna(df.at[row, 'Reference within document']):
        return False
    return True

def is_valid_hint(df, row):
    if pd.isna(df.at[row, 'Hint']):
        return False
    return True

def set_M_slides_anchor(a, document):
    document_name = re.split(' ', document)[0]
    if (document_name.find('MP') == 0):
        document_name = "M" + document_name[2:]
    print (f"Document: {document}")
    if (level == '1'):
        filename = 'TOGAF-EA-Foundation-' + document_name + '.pdf'
        intermediate_directory = "/Foundation/"
    elif (level == '2'):
        filename = 'TOGAF-EA-Practitioner-' + document_name + '.pdf'
        intermediate_directory = "/Practitioner/"
    else:
        print (f"Invalid level: {level}")
        return
    pdf_document = fitz.Document(source_directory + intermediate_directory + filename)
    page = re.split(' ', document)[1]
    if (page.find('-') > 0 ):
        page_range = re.split('-', page)
        start_page = int(page_range[0])
        end_page = int(page_range[1])
        for i in range(start_page, end_page+1):
            pdf_page = pdf_document.load_page(i-1)  
            text = pdf_page.get_text()
            set_pdf_anchor(a, f"{document_name} Page {i}", f"{source_directory}{intermediate_directory}{filename}", i, pdf_page, [])
    else:  
        pdf_page = pdf_document.load_page(int(page)-1)
        text = pdf_page.get_text()
        set_pdf_anchor(a, f"{document_name} Page {page}", f"{source_directory}{intermediate_directory}{filename}", page, pdf_page, [])
    return

def is_Content_Page(pdf_page):
    blocks = pdf_page.get_text("blocks")
    for block in blocks:
        block_text = block[4].strip().replace('\n', ' ').replace( '  ', ' ')
        if (block_text.find('Contents') == 0):
            print (f"Content page: {block_text}")
            return True
        if (block_text.find('Table of Contents') == 0):
            print (f"Content page: {block_text}")
            return True
        if (block_text.find("..........") >= 0):
            print (f"Content page: {block_text}")
            return True
    return False

def is_Appendix(pdf_page, appendix_text):
    text = pdf_page.get_text()
    if (text.find("Appendix") < 0):
        return False
    blocks = pdf_page.get_text("blocks")
    for block in blocks:
        block_text = block[4].strip().replace('\n', ' ').replace( '  ', ' ')
        print (f"Block: {block_text}")
        if (block_text.find(appendix_text) == 0):
            print (f"Appendix: {block_text}")
            return True    
    return False

def is_table_reference(text):
    if (text.find('Table') >= 0):
        return True
    return False

def find_keyword(pdf_page, text, keyword, page_number):

    blocklist = pdf_page.get_text("blocks")
    for block in blocklist:
        text_blocks = block[4].strip().replace('\n', ' ').replace( '  ', ' ') 
        print (f"text_blocks = {text_blocks}")
        if (text_blocks == keyword):
            print (f"Keyword: {keyword} found in block: {block}")
            return block
    return None

def find_pagenumber_from_content_page(pdf_page, text, keyword, page_number):
    if (is_Content_Page(pdf_page)):
        if (text.find(keyword) >= 0):
            blocklist = pdf_page.get_text("blocks")
            for block in blocklist:
                text_tokens = block[4].strip().replace("\n", " ").replace(" . .", "..").replace("  ", " ").replace("\xa0", "").split(' ')
                print (f"text_tokens = {text_tokens}")                
                #if (text_tokens[0] == keyword or text_tokens[0] == keyword + "." ):                    
                #    page_number_string = text_tokens[len(text_tokens)-1]      
                #    if (page_number_string.isdigit()):
                #        page_number = int(text_tokens[len(text_tokens)-1])
                #        print (f"Page number found from content page: {page_number}")
                #        return page_number
                #    else:
                #        print (f"Page number not found from content page")
                #        return 0
                #else:
                i = 0
                keyword_found = False
                page_number_found = False
                while (i < len(text_tokens)):                        
                    if (not keyword_found and (text_tokens[i] == keyword or text_tokens[i] == keyword + "." )):
                        if (i == 0):
                            keyword_found = True
                        else:
                            if (text_tokens[i-1].endswith("..")):                                    
                                keyword_found = False
                            else:
                                keyword_found = True
                        i += 1
                        continue
                    if (keyword_found and text_tokens[i].endswith("..")):
                        #next token is page number
                        page_number_found = True
                        i = i + 1
                        continue
                    if (keyword_found and page_number_found and text_tokens[i].isdigit()):
                        page_number = int(text_tokens[i])
                        print (f"Page number found from content page: {page_number}")
                        return page_number
                    i += 1
    return 0    
            
def set_Handout_Appendix_anchor(a, reference, keyword):
    if (reference.find('Handout-1 ') == 0):
        reference = reference[10:]
    if (reference.find('Handout-P1 ') == 0):
        reference = reference[11:]
    if (reference.find('Appendix') != 0):
        return
    filename = 'Handout-L' + level + '.pdf'
    pdf_document = fitz.Document(source_directory + "/" + filename)
    #search for the Appendix
    appendix_found = False
    print (f"Handling Appendix: {reference} {keyword}")
    for i in range(0, pdf_document.page_count):
        pdf_page = pdf_document.load_page(i)
        text = pdf_page.get_text()
        if (is_Content_Page(pdf_page)):
            continue
        if (not is_Appendix(pdf_page, reference) and not appendix_found):
            continue
        appendix_found = True
        page_number = i + 1
        print (f"Checking the keyword: {keyword} in page {page_number}")
        block = find_keyword(pdf_page, text, keyword, page_number)
        if (block != None):
            set_pdf_anchor(a, "Handout-" + level + f" Page {page_number}", f"{source_directory}/{filename}", page_number, pdf_page, block)
            return

    return

def set_Handout_anchor(a, reference, keyword):
    filename = 'Handout-L' + level + '.pdf'
    if (reference.find('Handout-1 ') == 0):
        reference = reference[10:]
    if (reference.find('Handout-P1 ') == 0):
        reference = reference[11:]
    if (reference.find('§') == 0):
        reference = reference[1:]
    print (f"Reference: {reference}, Keyword: {keyword}")
    if (reference.find('Appendix') == 0):
        set_Handout_Appendix_anchor(a, reference, keyword)
        return
    pdf_document = fitz.Document(source_directory + "/" + filename)
    #search the reference in the document
    print (f"Page count: {pdf_document.page_count}")
    for i in range(0, pdf_document.page_count):
        pdf_page = pdf_document.load_page(i)
        text = pdf_page.get_text()
        if (text.find(reference) >= 0 and text.find(keyword) >= 0 and not is_Content_Page(pdf_page) ):        
            print (f"Reference: {reference}, Keyword: {keyword} found in page {i+1}")
            blocklist = pdf_page.get_text("blocks")
            for block in blocklist:
                if (block[4].find(reference) == 0 and block[4].find(keyword) >= 0):
                    #print (f"Reference: {reference}, Keyword: {keyword} found in block: {block}")
                    set_pdf_anchor(a, "Handout-" + level + f" Page {i+1}", f"{source_directory}/{filename}", i+1, pdf_page, block)
                    return
    return

def need_document_reference(n):
    try:
        if (n.find('§') == 0):
            return True
        integer_range = re.split('-', n)
        for i in integer_range:
            int(i)
    except ValueError:
        return False
    return True    

def set_slides(a, df, row):
    if not is_valid_reference_within_document(df, row):
        return
    row_documents = re.split('\n', df.at[row, 'Reference within document'])
    document_names = df.at[row, 'Document in which evidence is found'].split('\n')
    for i in range(0, len(row_documents)):
        row_document = row_documents[i]    
        document_name = document_names[i]
        documents = row_document.split(',')
        for document in documents:
            if (need_document_reference(document)):
                document = document_name + ' ' + document
            if (document.find('M') == 0):
                set_M_slides_anchor(a, document)
            elif (document.find('Handout')==0):
                if (is_valid_learning_outcome(df, row)):
                    set_Handout_anchor(a, document, '')
                else:    
                    set_Handout_anchor(a, document, df.at[row, 'Learning Outcome Reference Title'])    
    return

def get_files (directory):
    from os import listdir
    from os.path import isfile, join
    files = [f for f in listdir(directory) if isfile(directory + "/" + f)]
    return files

def find_chapter(pdf_document, chapter):
    chapter_found = False    
    block = []
    chapter_number = -1
    i = 0
    passed_content_page = False
    while (i < pdf_document.page_count):
        pdf_page = pdf_document.load_page(i)
        text = pdf_page.get_text()
        if (is_Content_Page(pdf_page)):
            passed_content_page = True
            print (f"Content page: {i+1}")
            page_number = find_pagenumber_from_content_page(pdf_page, text, chapter, i)
            if (page_number == 0):
                page_number = find_pagenumber_from_content_page(pdf_page, text, "Chapter " + chapter, i)
                if (page_number > 0):
                    print (f"Page number found by appending Chapter to chapter number {chapter}")
                    chapter = "Chapter " + chapter
            if (page_number > 0 and page_number - 1 > i):
                i = page_number -1
            else:
                i = i + 1
            continue
        # if we have not passed the content page, we should not be looking for the chapter
        if (not passed_content_page):
            i = i + 1
            continue
        #confirm chapter does not have space        
        if (text.find(chapter) >= 0 ):            
            blocklist = pdf_page.get_text("blocks")
            for block in blocklist:
                block_text = block[4].strip().replace('\n', ' ').replace( '  ', ' ').split(' ')
                print (f"Block: {block_text}")
                if (is_chapter(block_text[0], chapter) or
                    (len(block_text) > 1 and block_text[0] == "Chapter" and is_chapter(block_text[1], chapter)) or
                    (len(block_text) > 1 and block_text[0] == "Question" and is_chapter(block_text[1], chapter))
                    ):
                    chapter_found = True
                    chapter_number = i
                    print (f"Chapter: {chapter} found in page {i+1} ")                        
                    return chapter_found, chapter_number, block
        i+= 1
    if (not chapter_found):                    
        print (f"Chapter: {chapter} not found")
    return chapter_found, chapter_number, block

def is_chapter(block_text, chapter):
    if (block_text == chapter or block_text == chapter + "." or block_text == chapter + ":"):
        return True 
    return False

def find_hint(pdf_document, hint, chapter_found):
    hint_found = False
    block = []
    print (f"Looking for Hint: {hint} from page {chapter_found[1]}")
    for i in range(chapter_found[1], pdf_document.page_count):
        pdf_page = pdf_document.load_page(i)
        blocklist = pdf_page.get_text("blocks")
        for block in blocklist:
            blocktext = block[4].strip().replace('\n', ' ').replace( '  ', ' ')
            print (f"Block: {blocktext}")
            if (blocktext.find(hint) == 0):
                hint_found = True
                return hint_found, i, block
    print (f"Hint: {hint} not found")
    return hint_found, -1, block

def find_table(pdf_document, cell_text, chapter_found):
    table_found = False
    block = []
    for i in range(chapter_found[1], pdf_document.page_count):
        pdf_page = pdf_document.load_page(i)
        tables = pdf_page.find_tables()
        for table in tables.tables:
            block = table.bbox
            if (cell_text == ''):
                return table_found, i, block 

            cells_text = table.extract()
            for k in range(1, table.row_count):
                if (cells_text[k][0] == None):
                    continue
                current_cell_text = cells_text[k][0].strip().replace('\n', ' ')
                print (f"current_cell_text: {current_cell_text}")
                if (current_cell_text.find(cell_text) == 0):
                    table_found = True
                    print (f"Cell found: {table.rows[k].bbox}")
                    return table_found, i, table.rows[k].bbox
    return table_found, -1, block

def find_references(directory, filename, reference, chapters, hint, password):
    if (filename == ''):
        return    
    print (f"Opening {directory}/{filename}")
    pdf_document = fitz.Document(directory + "/" + filename)
    if (password != '' ):
        if (not pdf_document.authenticate(password)):
            print (f"Failed to authenticate {filename} with password {password}")
            return
        print (f"Authenticated {filename} with password {password}")
    else:
        print (f"No password for {filename}")
    hints = []
    if (hint != ''):
        hints = hint.split(',')
    print (f'hints: {hints}')

    for i in range(0, len(chapters)):
        chapter = chapters[i]
        if (len(hints) > i):
            hint = hints[i]
        table = ''
        if (is_table_reference(chapter)):
            old_chapter = chapter
            chapter = old_chapter[:old_chapter.find('Table')]
            table = old_chapter[old_chapter.find('Table'):]
            print (f"Chapter: {chapter}, Table: {table}")

        chapter_found = find_chapter(pdf_document, chapter)
        if (not chapter_found[0]):
            continue
        if (hint == '' and table == ''):
            print (f"Setting anchor for {reference} {chapter} with {chapter_found}")
            set_pdf_anchor(a, f"{reference} {chapter}", f"{directory}/{filename}", chapter_found[1]+1, pdf_document.load_page(chapter_found[1]), chapter_found[2])
            continue
        if (table != ''):
            cell_text = hint
            table_found = find_table(pdf_document, cell_text, chapter_found)
            if (not table_found[0]):
                continue
            print (f"Setting anchor for {reference} {chapter} with table {table} with hint {cell_text}")
            set_pdf_anchor(a, f"{reference} {chapter} {table} {hint}", f"{directory}/{filename}", table_found[1]+1, pdf_document.load_page(table_found[1]), table_found[2])
            continue

        hint_found = find_hint(pdf_document, hint, chapter_found)
        if (not hint_found[0]):
            continue
        print (f"Setting anchor for {reference} {chapter} with hint {hint}")
        set_pdf_anchor(a, f"{reference} {chapter} {hint}", f"{directory}/{filename}", hint_found[1]+1, pdf_document.load_page(hint_found[1]), hint_found[2])

def set_fundamentals(a, klp, fundamental_content_files, hint):
    file_prefix = "C220-Part"
    klp = re.split(' ', klp)
    fundamental_reference = klp[0]
    fundamental_chapters = ''.join(klp[1:])
    fundamental_chapters = fundamental_chapters.replace(u'\xa0', u' ')
    if (fundamental_chapters.find('§') == 0):
        fundamental_chapters = fundamental_chapters[1:]
    fundamental_chapters = re.split(',', fundamental_chapters)
    print (f"fundamental_chapters: {fundamental_chapters}")
    print (f"fundamental_reference: {fundamental_reference}")
    filenumber = fundamental_reference[fundamental_reference.find('{S') + 2:fundamental_reference.find('}')]
    print (f"filenumber: {filenumber}")
    filename = ''
    for file in fundamental_content_files:
        if (file.find("C220-Part" + filenumber + "p") == 0):
            filename = file
            print (f"Found file: {file}")

    find_references(fundamental_content_directory, filename, fundamental_reference, fundamental_chapters, hint, '')
    return

def set_series_guides(a, klp, series_guide_files, hint):
    klp = re.split(' ', klp)
    print (f"klp: {klp}")
    series_guide_reference = klp[0]
    series_guide_chapters = ''.join(klp[1:])
    series_guide_chapters = series_guide_chapters.replace(u'\xa0', u' ')
    if (series_guide_chapters.find('§') == 0):
        series_guide_chapters = series_guide_chapters[1:]
    series_guide_chapters = re.split(',', series_guide_chapters)

    print (f"series_guide_reference: {series_guide_reference}")
    print (f"series_guide_chapters: {series_guide_chapters}")

    filename = ''
    for file in series_guide_files:
        if (file.find(series_guide_reference) == 0): 
            filename = file
            print (f"Found file: {file}")
    find_references(series_guide_directory, filename, series_guide_reference, series_guide_chapters, hint, '')
    return

def set_klp(a, df, row, fundamental_content_files, series_guide_files):
    klps = re.split('\n',  df.at[row, 'KLP'])
    if is_valid_hint(df, row):
        hints = re.split('\n',  df.at[row, 'Hint'])
    else:
        hints = []
    hint = ''
    print (f"hints: {hints}")
    for i in range(0, len(klps)):
        if (i < len(hints)):
            hint = hints[i]
        else:
            hint = ''           
        if (klps[i].find("G")==0):             
            set_series_guides(a, klps[i], series_guide_files, hint)
        elif (klps[i].find("{S")==0):
            set_fundamentals(a, klps[i], fundamental_content_files, hint)
    return

def close_container(a, container_open):
    if container_open:
        a('</div>')
        container_open = False
    return container_open

def open_container(a, container_open, row):
    if not container_open:
        a(f'<div class="accordion accordion-flush" id="accordion{row}">')
        container_open = True
    return container_open

def set_accordian_header(a, row, text):
    with a.h2(klass="accordion-header", id=f"heading{row}"):
        with a.button(klass="accordion-button collapsed",  type="button", **{'data-bs-toggle':'collapse', 'data-bs-target':f"#collapse{row}", 'aria-expanded':'false', 'aria-controls':f"collapse{row}"}):
            a(text)

def get_bloom_color(bloom):
    bloom = bloom.strip()
    if bloom =='1_Remembering':
        return  ""
    if bloom == '2_Understanding':
        return 'bg-info-subtle'
    if bloom == '3_Applying':
        return 'bg-success-subtle'
    if bloom == '4_Analyzing':
        return 'bg-warning-subtle'
    if bloom == '5_Evaluating':
        return 'bg-warning-subtle'
    if bloom == '6_Creating':
        return 'bg-danger-subtle'
    return 'bg-light-subtle'

def get_bloom_text(bloom):
    bloom = bloom.strip()
    if bloom == '1_Remembering':
        return  "Remembering"
    if bloom == '2_Understanding':
        return 'Understanding'
    if bloom == '3_Applying':
        return 'Applying'
    if bloom == '4_Analyzing':
        return 'Analyzing'
    if bloom == '5_Evaluating':
        return 'Evaluating'
    if bloom == '6_Creating':
        return 'Creating'
    return 'Unknown'

def get_unit_question(unit_question):
    unit_question = unit_question.strip()
    chapter = ''
    if unit_question.find("U")>=0:
        unit = int(unit_question[unit_question.find("U")+1:unit_question.find("Q")]) + 2
        if unit > 5:
            chapter = str (unit + 1)
        else:
            chapter = str (unit)
    if unit_question.find("Q")>=0:
        chapter += "." + unit_question[unit_question.find("Q")+1:]
    print (f"Unit Question: {unit_question} Chapter: {chapter}")
    return chapter

def get_unit_answer(unit_answer, learning_studies_directory, answer_file, answer_password):
    unit_answer = unit_answer.strip()
    unit_answer = unit_answer.replace("Coverd by LS ", "")
    unit_answer = unit_answer.replace("U", "Unit ")
    unit_answer = unit_answer.replace("Q", " Question ")
    print (f"Unit Answer: {unit_answer}")
    pdf_document = fitz.Document(learning_studies_directory + "/" + answer_file)
    if (answer_password != '' ):
        if (not pdf_document.authenticate(answer_password)):
            print (f"Failed to authenticate {answer_file} with password {answer_password}")
            return
        print (f"Authenticated {answer_file} with password {answer_password}")
    else:
        print (f"No password for {answer_file}")
    
    chapter_found = ""
    for i in range(0, pdf_document.page_count):
        pdf_page = pdf_document.load_page(i)
        text = pdf_page.get_text()
        if (is_Content_Page(pdf_page)):
            continue
        if (text.find(unit_answer) >= 0 ):            
            blocklist = pdf_page.get_text("blocks")
            for block in blocklist:
                if (block[4].find(unit_answer) >= 0):
                    print (f"Block[4]: {block[4]}")
                    chapter_found = block[4][0:block[4].find(unit_answer)].strip()
    return chapter_found


def is_valid_learning_studies(df, row):
    if 'Applicant Comment' not in df.columns:
        return False
    if pd.isna(df.at[row, 'Applicant Comment']):
        return False
    return True

def get_learning_studies_question_answer_files(directory):
    if (unlock):
        question_file = "12. LearningStudies-2023-QB.pdf"
        answer_file = "13. LearningStudies-2023-AB.pdf"
        password_file = "14. Passwords for Learning Studies.txt"
        question_password = ''
        answer_password = ''
        #open the password file
        with open(directory + "/" + password_file, "r") as text_file:
            for line in text_file:
                if (line.find("LS-2023-QB.pdf") == 0):
                    question_password = line.split('  ')[1].strip()
                elif (line.find("LS-2023-AB.pdf") == 0):
                    answer_password = line.split('  ')[1].strip()
    else:
        question_file = "learning studies question book.pdf"
        answer_file = "learning studies answer book.pdf"
        question_password = ''
        answer_password = ''
    return question_file, question_password, answer_file, answer_password


def set_learning_studies(directory, df, row):
    if (not is_valid_learning_studies(df, row)):
        return
    document = df.at[row, 'Applicant Comment'].strip()
    print (f"Document: {document}")
    if (document.find('Covered by LS ') == 0):
        document = document[14:]
    if (document.find("Covered by ") == 0):
        document = document[11:]
    if (document.find ("Coverd also by LS ") == 0):
        document = document[18:]

    ls = document.split(',')
    question_chapters = []
    answer_chapters = []
    question_file, question_password, answer_file, answer_password = get_learning_studies_question_answer_files(directory)    
    for i in range(0, len(ls)):
        ls[i] = ls[i].strip()
        chapter = get_unit_question(ls[i])
        question_chapters.append(chapter)
        print (f"Question Chapter: {chapter}")
        chapter = get_unit_answer(ls[i], directory, answer_file, answer_password)
        answer_chapters.append(chapter)
        print (f"Answer Chapter: {chapter}")
    find_references(directory, question_file, 'Learning Studies Question Book', question_chapters, '', question_password)
    find_references(directory, answer_file, 'Learning Studies Answer Book', answer_chapters, '', answer_password)

def is_valid_examp_prep(df, row):
    if 'Exam Prep' not in df.columns:
        return False
    if pd.isna(df.at[row, 'Exam Prep']):
        return False
    if (df.at[row, 'Exam Prep'] == ''):
        return False
    return True

def get_exam_prep_question_answer_files(directory):
    if (unlock):
        if (level == '1'):
            exam_root_name = "B220a-b1-atc"
            answer_root_name = "B220b-v1-atc"
            question_file = "6. " + exam_root_name + "_Level 1 Practice Test Nov 2023.pdf"
            answer_file = "7. " + answer_root_name + "_Level 1 Practice Test Answer Nov 2023.pdf"
        elif (level == '2'):
            exam_root_name = "B221a-v1-atc"
            answer_root_name = "B221b-v1-atc"
            question_file = "8. " + exam_root_name + " - Level 2 Practice Test Sep 2022.pdf"
            answer_file = "9. " + answer_root_name + " - Level 2 Practice Test Answer Jan 2023.pdf"
        else:
            print (f"Invalid level: {level}")
            return 
        password_file = "10. Passwords for Practice Tests.txt"
        with open(directory + "/" + password_file, "r") as text_file:
            for line in text_file:
                if (line.find(exam_root_name) == 0):
                    question_password = line.split(' ')[1].strip()
                elif (line.find(answer_root_name) == 0):
                    answer_password = line.split(' ')[1].strip()        
    else:
        if (level == '1'):
            question_file = "level 1 practice test.pdf"
            answer_file = "level 1 practice test answer.pdf"
            question_password = ''
            answer_password = ''
        elif (level == '2'):
            question_file = "level 2 practice test.pdf"
            answer_file = "level 2 practice test answer.pdf"
            question_password = ''
            answer_password = ''
        else:
            print (f"Invalid level: {level}")
            return
    return question_file, question_password, answer_file, answer_password 
           
def set_exam_prep(directory, df, row):
    if (not is_valid_examp_prep(df, row)):
        return
    question_chapters = []
    answer_chapters = []
    answer_hints = ""
    question_file, question_password, answer_file, answer_password = get_exam_prep_question_answer_files(directory)
    for exam_prep in df.at[row, 'Exam Prep'].split(','):
        exam_prep = exam_prep.strip()
        if (exam_prep != ''):
            if (level == '1'):
                question_chapters.append(exam_prep)
                answer_chapters.append(exam_prep)
            elif (level == '2'):
                if (exam_prep.find('Q') == 0):
                    exam_prep = exam_prep.replace('Q', '')
                    print (f"New Exam Prep: {exam_prep}")
                question_chapters.append("2" +"." + exam_prep)
                answer_chapters.append(exam_prep)
                answer_hints = "Question " + exam_prep + ","
            print (f"Exam Prep: {exam_prep}")
    find_references(directory, question_file, 'Practice Test', question_chapters, '', question_password)
    find_references(directory, answer_file, 'Practice Test Answer', answer_chapters,answer_hints,answer_password)
    return

def is_valid_public_links(df, row):
    if 'Public Links' not in df.columns:
        return False
    if pd.isna(df.at[row, 'Public Links']):
        return False
    return True

def set_public_links(a, df, row):
    if (not is_valid_public_links(df, row)):
        return
    public_links_text = df.at[row, 'Public Links']
    if pd.isna(public_links_text):
        return    
    public_links = re.split('\n', public_links_text)
    for i in range(0, len(public_links)):
        public_links_url = public_links[i].strip()
        public_links_text = public_links_url.split('#')[1]
        set_anchor(a, public_links_text, public_links[i])
        continue
    return


#get arguments
import sys
if len(sys.argv) < 2:
    print (f"Usage: {sys.argv[0]} <level>")
level = sys.argv[1]
if (level != '1' and level != '2'):
    print (f"Invalid level: {level}")
    sys.exit(1)

unlock = False
if len(sys.argv) == 3:
    if (sys.argv[2] == 'unlock'):
        unlock = True

try:
    source_directory = "TOGAF Licensed Slides"
    file_path = 'TOGAF-EA_Training_Course_Materials__Checklist_v1.0-Foundation_Practitioner.xlsx'
    sheet_name = 'Level ' + level + ' checklist'
    converters = {'Learning Outcome Reference': str, 'Hint':str}
    previous_learning_outcome_title = ''
    previous_learning_outcome_reference = ''
    previous_learning_outcome_number = 1
    current_level_unit = ''
    fundamental_content_directory = "TOGAF 10 Standard/Fundamental Content"
    fundamental_content_files = get_files(fundamental_content_directory)    
    series_guide_directory = "TOGAF 10 Standard/Series Guide"
    series_guide_files = get_files(series_guide_directory)
    exam_prep_directory = "TOGAF 10 Exam Prep"

    df = get_dataframe_from_checklist(source_directory + "/" + file_path, sheet_name)
    df.rename (columns = {'Unnamed: 2': 'Learning Outcome Reference Title'}, inplace = True)

    a = Airium()
    a('<!DOCTYPE html>')
    container_open = False
    accordion_parent = ''
    with a.html(lang="en", **{'data-bs-theme':'dark'}):
        with a.head():
            a.meta(charset="UTF-8")
            a.meta(name="viewport",content="width=device-width, initial-scale=1")
            a.title("Level " + level + " Togaf")                
            a.link(href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",rel="stylesheet",integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH",crossorigin="anonymous")

        with a.body():
            with a.div(klass="container"):
                for row in range(0, len(df)):
                    accordian_header_text = ''
                    if is_valid_learning_outcome_title(df, row):
                        level_unit = df.at[row, 'Level/Unit']
                        if not pd.isna(level_unit):
                            container_open = close_container(a, container_open)
                            container_open = open_container(a, container_open, row)
                            if (container_open):
                                accordion_parent = row
                            with a.h1():
                                a(level_unit)
                        if is_valid_learning_outcome (df, row):
                            if not is_valid_klp(df, row):
                                previous_learning_outcome_reference = df.at[row, 'Learning Outcome Reference']
                                previous_learning_outcome_title = df.at[row, 'Learning Outcome Reference Title']
                                previous_learning_outcome_number = 1
                                continue
                            else:
                                if not is_valid_klp(df, row):
                                    continue
                                accordian_header_text = f"{df.at[row, 'Learning Outcome Reference']} {df.at[row, 'Learning Outcome Reference Title']}"
                        else:
                            if not is_valid_klp(df, row):
                                continue
                            accordian_header_text = f"{previous_learning_outcome_reference}.{previous_learning_outcome_number} {previous_learning_outcome_title} {df.at[row, 'Learning Outcome Reference Title']}"
                            previous_learning_outcome_number += 1                                        
                    if is_valid_klp(df, row):
                        bloom = df.at[row, "Bloom’s Taxonomy"]
                        if pd.isna(bloom):
                            bloom = ''                  
                        bloom_color = get_bloom_color(bloom)
                        bloom_text = get_bloom_text(bloom)                        
                        with a.div(klass=f"accordion-item {bloom_color}"):
                            set_accordian_header(a, row, f"{accordian_header_text} [{bloom_text}]")
                            with a.div(id=f"collapse{row}", klass="accordion-collapse collapsed collapse", **{'data-bs-parent':f"#accordion{accordion_parent}"}):
                                with a.div(klass="accordion-body"):
                                    with a.ul():                                    
                                        set_klp(a, df, row, fundamental_content_files, series_guide_files)                        
                                        set_slides(a, df, row)
                                        set_public_links(a, df, row)
                                        set_learning_studies(exam_prep_directory, df, row)
                                        set_exam_prep(exam_prep_directory, df, row)
                                        print ("done with row: ", row)
                close_container(a, container_open)
            a.script(src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz",crossorigin="anonymous")

except Exception as e:
    print (f"Error: {e}")

with open("level" + level + ".html", "w") as text_file:
    text_file.write(str(a))


