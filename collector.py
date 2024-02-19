from httpx import Client
import json

def parse_collection_id(collection_url):
    collection_id = collection_url.split('/')[4]
    return collection_id

def parse_collection_name(collection_url):
    new_collection_name = '_'.join(collection_url.split('/')[-2:])
    return new_collection_name

def get_maps_by_collection_id(collection_id):
    beatmapset_ids = set()
    beatmaps_hashes = set()
    collection_api_url = f'https://osucollector.com/api/collections/{collection_id}/beatmapsv2?perPage=100'
    with Client() as session:
        while True:
            response = session.get(url=collection_api_url)
            if response.status_code == 200:
                response = json.loads(response.text)
                for beatmap in response['beatmaps']:
                    beatmapset_ids.add(beatmap['beatmapset_id'])
                    beatmaps_hashes.add(beatmap['checksum'])
                if not response['hasMore']:
                    break
                collection_api_url = f'https://osucollector.com/api/collections/{collection_id}/beatmapsv2?perPage=100&cursor={response['nextPageCursor']}'
            else:
                break
    return beatmapset_ids, beatmaps_hashes


def get_beatmaps_from_collection(collection_url):
    collection_id = parse_collection_id(collection_url)
    collection_name = parse_collection_name(collection_url)
    beatmapset_ids, beatmaps_hashes = get_maps_by_collection_id(collection_id)
    return collection_name, beatmapset_ids, beatmaps_hashes
