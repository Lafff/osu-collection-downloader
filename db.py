import leb128
import shutil
from datetime import datetime
from pathlib import Path


def read_existing_collections(path):
    collections = []
    with open(path/'collection.db', 'rb') as file:
        res = file.read()
        pos_uleb_collection_name_len = 9
        bytes_per_map_string = 34
        total_collection_slice = slice(4, 8)
        total_collections = int.from_bytes(res[total_collection_slice], byteorder='little')
        for counter in range(total_collections):
            uleb128 = res[pos_uleb_collection_name_len:pos_uleb_collection_name_len+1]
            coll_name_len = leb128.u.decode(uleb128)
            coll_name = res[pos_uleb_collection_name_len+1:pos_uleb_collection_name_len+1+coll_name_len]
            maps_in_coll = int.from_bytes(res[pos_uleb_collection_name_len+1+coll_name_len:pos_uleb_collection_name_len + 5 + coll_name_len], byteorder='little')
            bytes_to_skip = maps_in_coll * bytes_per_map_string
            collections.append((coll_name.decode('utf-8'), pos_uleb_collection_name_len-1))
            pos_uleb_collection_name_len = pos_uleb_collection_name_len + coll_name_len + 4 + bytes_to_skip + 2
    return res, collections


def write_collection(path, data):
    backup_path = Path(path/'laf_collections_backups')
    backup_path.mkdir(parents=True, exist_ok=True)
    shutil.copy(path/'collection.db', path/f'laf_collections_backups/collection_backup_{str(datetime.now().replace(microsecond=0)).replace(':','-')}.db')
    with open(path/'collection.db', 'wb') as file:
        file.write(data)


def prepare_data_to_write(res, collections, collection_name, beatmaps_hashes):
    collection = (collection_name, None)
    collections.append(collection)
    collections.sort(key=lambda x: (x[0].lower(), x[0].swapcase()))
    flag_collection = collections[collections.index(collection)-1]
    to_write_first_part = res[:flag_collection[1]]
    to_write_second_part = res[flag_collection[1]:]
    total_collection_slice = slice(4, 8)
    total_collections = int.from_bytes(res[total_collection_slice], byteorder='little')
    total_collections += 1
    to_write_first_part = to_write_first_part[0:4] + total_collections.to_bytes(4,byteorder='little') + to_write_first_part[8:]  # Не стал делать ограничие на размер коллекции в 4 байта. Можно потом будет дописать по необходимости
    collection_name = collection_name.encode('utf-8')
    collection_name_bytes_len = len(collection_name)
    uleb128_collection_name_len = leb128.u.encode(collection_name_bytes_len)
    uleb128_hash_len = leb128.u.encode(32)
    x0b_new_string = int(11).to_bytes()
    collection_size = len(beatmaps_hashes).to_bytes(4, byteorder='little')
    hashes_part_to_write = b''.join([x0b_new_string + uleb128_hash_len + beatmap_hash.encode('utf-8') for beatmap_hash in beatmaps_hashes])
    collection_part_to_write = x0b_new_string + uleb128_collection_name_len + collection_name + collection_size + hashes_part_to_write
    return to_write_first_part + collection_part_to_write + to_write_second_part


def update_collections(path, collection_name, beatmaps_hashes):
    res, collections = read_existing_collections(path)
    data = prepare_data_to_write(res, collections, collection_name, beatmaps_hashes)
    write_collection(path, data)
