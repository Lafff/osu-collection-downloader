from httpx import AsyncClient
import asyncio


async def download_beatmap(beatmapset_id, semaphore, osu_songs_path, progress_dict):
    async with semaphore:
        filename_path = osu_songs_path / (str(beatmapset_id) + '.osz')
        filename_error_path = osu_songs_path / (str(beatmapset_id) + '_error.txt')
        download_url = f'https://bm1.gatari.pw/d/{beatmapset_id}'
        count = 0
        while count < 5:
            try:
                response = await session.get(url = download_url, timeout=15)
                with open(filename_path, 'wb') as file:
                    file.write(response.content)
                progress_dict['downloaded'] +=1
                break
            except Exception as e:
                with open(filename_error_path, 'a') as file_error:
                    file_error.write(f'download url is {download_url}, TIMEOUT EXCEEDED. Count = {count}. Count limit < 5. Error: {str(e)}\n')
                    continue
            finally:
                count+=1
        

session = AsyncClient(follow_redirects=True)
downloaded_maps_count = 0

async def refresh_window(progress_dict, window):
    while True:
        window['progress_bar'].update(progress_dict['downloaded'])
        window.refresh()
        if progress_dict['total'] == progress_dict['downloaded']:
            break
        await asyncio.sleep(0.1)


async def download_beatmapsets(beatmaps_set_ids, osu_songs_path, progress_dict, window):
    semaphore = asyncio.Semaphore(5)
    tasks = [asyncio.create_task(download_beatmap(beatmapset_id, semaphore, osu_songs_path, progress_dict)) for beatmapset_id in beatmaps_set_ids]
    tasks += [asyncio.create_task(refresh_window(progress_dict, window))]
    await asyncio.gather(*tasks)
