import shutil
import multiprocessing
from os import path, listdir, makedirs
from index.index import index_a_table


def index_all(db_path, index_path, path_file):
    tables = listdir(db_path)
    params = []
    for table in tables:
        params.append((db_path, table, index_path, None, path_file))
    if path.exists(index_path):
        shutil.rmtree(index_path)
    makedirs(index_path)
    pool = multiprocessing.Pool()
    pool.map(index_a_table, params)
