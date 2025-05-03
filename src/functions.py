import unicodedata
import nltk
from nltk.corpus import wordnet

def batch_generator(data_list, batch_size):
    """
    Generador que divide una lista de datos en lotes (batches).

    Args:
        data_list (list): La lista completa de datos a dividir.
        batch_size (int): El tamaño deseado para cada lote.

    Yields:
        list: Un lote  de datos. El último lote puede ser más pequeño.
            No produce nada si la lista de entrada está vacía o batch_size <= 0.
    """
    if not data_list or batch_size <= 0:
        print("Advertencia: La lista de datos está vacía o el tamaño de lote es inválido. No se generarán lotes.")
        return

    num_total_items = len(data_list)
    # Iteramos sobre la lista en pasos de tamaño batch_size
    for start_index in range(0, num_total_items, batch_size):
        end_index = start_index + batch_size
        batch = data_list[start_index:end_index]
        yield batch

def preprocess_text_step1(text):
    if not isinstance(text, str):
        return ""

    try:
        normalized_text = unicodedata.normalize('NFKC', text) # normalizamos el texto
        lower_text = normalized_text.lower() # convertimos a minusculas

        return lower_text

    except Exception as e:
        print(f"Error: {e}")
        return ""

# Mapeo de etiquetas POS
def get_wordnet_pos(treebank_tag):
    """Convierte etiquetas POS de Penn Treebank a formato WordNet."""
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN

############### --- Lematización --- ###############
global lemmatizer
lemmatizer = nltk.WordNetLemmatizer()
def lemmatize_sentence_nltk(sentence_text):
    """Tokeniza, etiqueta POS y lematiza una única oración (string)."""
    tokens = nltk.word_tokenize(sentence_text, language='english')
    pos_tags = nltk.pos_tag(tokens)
    lemmas = []
    for word, tag in pos_tags:
        if word.isalnum():
            wordnet_tag = get_wordnet_pos(tag)
            lemma = lemmatizer.lemmatize(word, pos=wordnet_tag)
            lemmas.append(lemma)
    return lemmas

# función principal que orquesta el pipeline para 1 documento
def segment_and_process_document(doc_text):
    """
    Normaliza, segmenta en oraciones y lematiza cada oración de un documento.

    Args:
        doc_text (str): Texto crudo del documento.

    Returns:
        list[list[str]]: Lista de oraciones, donde cada oración es una lista de lemas.
    """
    # normalizamos los documentos previamente a la segmentación
    normalized_doc = preprocess_text_step1(doc_text)

    # usamos el segmentor de oraciones de nltk para dividir el texto en oraciones
    sentences = nltk.sent_tokenize(normalized_doc, language='english')

    # lematizamos cada oración y la agregamos a una lista
    processed_doc = []
    for sentence in sentences:
        lemmatized_sentence = lemmatize_sentence_nltk(sentence)
        # nos aseguramos de no agregar  listas vacías si una oración solo contenía puntuación
        if lemmatized_sentence:
            processed_doc.append(lemmatized_sentence)

    return processed_doc
