from PyInstaller.utils.hooks import collect_data_files

# add datas for spacy
datas = collect_data_files('spacy', False)

hiddenimports = ['cymem', 'cymem.cymem', 'murmurhash', 'murmurhash.mrmr',
                 'spacy.strings',
                 'spacy.morphology', 'spacy.lexeme', 'spacy.tokens', 'spacy.tokens.underscore', 'spacy.parts_of_speech',
                 'spacy.tokens._retokenize',
                 'thinc.extra.search',
                 'srsly.msgpack.util', 'preshed',
                 'preshed.maps', 'thinc', 'blis',
                 'blis.py', 'spacy.vocab', 'spacy.util',
                 'spacy.lang', 'spacy.lang.lex_attrs', 'spacy.lang.norm_exceptions',
                 'spacy.pipeline._parser_internals.transition_system', 'spacy.pipeline._parser_internals.stateclass',
                 'spacy.pipeline.transition_parser', 'spacy.pipeline._parser_internals._beam_utils',
                 'spacy.pipeline._parser_internals.arc_eager', 'spacy.pipeline._parser_internals.ner', 'spacy.lang.sk']
