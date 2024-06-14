import pandas as pd
import re
import fitz
from airium import Airium

def get_dataframe_from_checklist(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name, converters=converters)
    return df

def set_anchor(a, text, url):
    with a.li():
        with a.a(href=url, target="_blank"):
            a(text)
    return

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

def is_valid_public_links(df, row):
    if pd.isna(df.at[row, 'Public Links']):
        return False
    return True

def is_table_reference(text):
    if (text.find('Table') >= 0):
        return True
    return False

def get_files (directory):
    from os import listdir
    from os.path import isfile, join
    files = [f for f in listdir(directory) if isfile(directory + "/" + f)]
    return files

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
        with a.button(klass="accordion-button collapsed", type="button", **{'data-bs-toggle':'collapse', 'data-bs-target':f"#collapse{row}", 'aria-expanded':'false', 'aria-controls':f"collapse{row}"}):
            a(text)

def process_klp(df, row):
    klp_text = df.at[row, 'KLP']
    if pd.isna(klp_text):
        return []
    klp = []
    temp_klp = re.split('\n', klp_text)
    for temp in temp_klp:
        k = re.split(',', temp)
        if len(k) > 1:
            for i in range(0, len(k)):
                if k[i].startswith(' '):
                    k[i] = k[0][0:k[0].find('§')+1] + k[i].strip()
                klp.append(k[i])
        else :
            klp.append(temp)
    return klp

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

def set_public_links(a, df, row):
    public_links_text = df.at[row, 'Public Links']
    if pd.isna(public_links_text):
        return    
    public_links = re.split('\n', public_links_text)
    klp = process_klp(df, row)
    if len(public_links) != len(klp):
        print (f"Error: Public Links and KLP are not equal in row {row}")
        print (f"Public Links: {public_links}")
        print (f"KLP: {klp}")
        return
    for i in range(0, len(public_links)):
        set_anchor(a, klp[i], public_links[i])
        continue
    return
    
try:
    source_directory = "data"
    file_path = 'conformance.xlsx'
    sheet_name = 'Level 1'
    converters = {'Learning Outcome Reference': str, 'Applicant Comment':str}
    previous_learning_outcome_title = ''
    previous_learning_outcome_reference = ''
    previous_learning_outcome_number = 1
    current_level_unit = ''

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
            a.title("Level 1 Togaf")                
            a.link(href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",rel="stylesheet",integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH",crossorigin="anonymous")
        with a.body():
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
                    bloom = df.at[row, 'Bloom’s Taxonomy']
                    if pd.isna(bloom):
                        bloom = ''                  
                    bloom_color = get_bloom_color(bloom)
                    bloom_text = get_bloom_text(bloom)
                    with a.div(klass=f"accordion-item {bloom_color}"):
                        set_accordian_header(a, row, f"{accordian_header_text} [{bloom_text}]")
                        with a.div(id=f"collapse{row}", klass="accordion-collapse collapsed collapse", **{'data-bs-parent':f"#accordion{accordion_parent}"}):
                            with a.div(klass="accordion-body"):
                                with a.ul():                                    
                                    set_public_links(a, df, row)

            close_container(a, container_open)
            a.script(src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz",crossorigin="anonymous")

except Exception as e:
    print (f"Error: {e}")

with open("level1.html", "w") as text_file:
    text_file.write(str(a))


