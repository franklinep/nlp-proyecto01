import unicodedata

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
