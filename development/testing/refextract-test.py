from refextract import extract_references_from_url
references = extract_references_from_url('https://arxiv.org/pdf/1503.07589.pdf')
print(references[0])