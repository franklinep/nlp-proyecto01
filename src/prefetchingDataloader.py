import queue
import threading
import time
from math import ceil
from src.functions import (
        batch_generator,
        segment_and_process_document
    )
import multiprocessing

class PrefetchingDataLoader:
    """DataLoader con prefetching."""

    def __init__(self, documents, batch_size, buffer_size=5, num_workers=0):
        """
        Args:
            documents (list[str]): Lista de documentos crudos.
            batch_size (int): Tamaño de cada lote.
            buffer_size (int): Tamaño máximo del buffer (cola).
            num_workers (int): Número de workers para preprocesamiento paralelo
                               dentro del hilo productor (0 para secuencial).
        """
        self.documents = documents
        self.batch_size = batch_size
        self.num_docs = len(self.documents)
        self.num_batches = ceil(self.num_docs / self.batch_size)
        self.num_workers = min(num_workers, multiprocessing.cpu_count()) if num_workers > 0 else 0

        # La función que procesa un documento completo
        self.preprocess_func = segment_and_process_document

        # Componentes esenciales
        self.buffer = queue.Queue(maxsize=buffer_size)
        self._stop_event = threading.Event() # para parar el pool si es necesario
        self.producer_thread = None
        self._producer_error = None

    def _producer(self):
        """Target del hilo: Preprocesa lotes y los pone en la cola."""
        print(f"[Productor]: Iniciado (Workers={self.num_workers}).")
        processed_count = 0
        try:
            # itreramos sobres los lotes crudos
            for raw_batch in batch_generator(self.documents, self.batch_size):
                start_proc = time.time()
                processed_batch = None
                ########################################################################
                # Si hay workers, usamos multiprocessing.Pool
                if self.num_workers > 0:
                    try:
                        # Creamos un Pool de procesos para este lote
                        with multiprocessing.Pool(self.num_workers,
                                                  maxtasksperchild=100) as pool:
                            # Mapeamos la función de preprocesamiento sobre los docs del lote crudo
                            processed_batch = pool.map(self.preprocess_func, raw_batch)
                    except Exception as pool_exc:
                        print(f"\n[Productor]: ERROR en Pool.map - {pool_exc}\n")
                        raise RuntimeError("Fallo en procesamiento paralelo") from pool_exc
                else:
                    processed_batch = [self.preprocess_func(doc) for doc in raw_batch]
                ########################################################################
                proc_time = time.time() - start_proc
                print(f"[Productor]: Lote procesado ({proc_time:.2f}s).")
                processed_count += len(raw_batch)

                # Poner en cola (con chequeo de stop mientras espera)
                while not self._stop_event.is_set():
                    try:
                        self.buffer.put(processed_batch, timeout=0.1)
                        break
                    except queue.Full:
                        continue
                if self._stop_event.is_set():
                    break
            print(f"[Productor]: Finalizado. Documentos procesados: {processed_count}")

        except Exception as e:
            print(f"\n[Productor]: ERROR - {e}\n")
            self._producer_error = e
        finally:
            self.buffer.put(None) # Indicamos fin de datos

    def __iter__(self):
        """Inicia la iteración y el hilo productor."""
        self._stop_event.clear()
        self._producer_error = None
        # Limpiamos el buffer por si se usa de nuevo
        while not self.buffer.empty():
            try:
                self.buffer.get_nowait()
            except queue.Empty:
                break
        # Iniciamos el hilo productor como 'daemon' para que no bloquee la salida
        self.producer_thread = threading.Thread(target=self._producer, daemon=True)
        self.producer_thread.start()
        return self

    def __next__(self):
        """Obtiene el siguiente lote procesado de la cola."""
        # get() espera si la cola está vacía
        processed_batch = self.buffer.get()
        # Si el hilo productor ha terminado con error, lo lanzamos
        if self._producer_error:
            raise RuntimeError("Error en hilo productor") from self._producer_error
        # Si recibe None, significa fin de datos o error en productor
        if processed_batch is None:
            raise StopIteration
        return processed_batch

    def __len__(self):
        """Devuelve el número total de lotes."""
        return self.num_batches
