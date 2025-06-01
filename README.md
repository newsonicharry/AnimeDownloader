A command-line tool to collect anime series data and download episodes in bulk based on popularity or specific series identifiers with myanimelist integration.

To start the scraping process use this:
python main.py <video_path> <json_path> <temp_path> --start
The <video_path> <json_path> <temp_path> are all required to start, and any arguments attached to it will actually run things

ex: python main.py C:/ C:/ C:/ --start
The video and temp folders will be created automatically at those locations and a json.data will be created/found in that directory 
recommeded to use the already attached data.json as I already scraped most of it. You will simply need to run a --start to build the directory and update the data given
Otherwise, the scrapeing process takes around 6 hours.

Use --update_all to update series that are currently airing

When downloading use 
--download_top_popularity <series_num> --episode_limit <max_episodes_per_series> --sequential_download_limit <num_concurrent_downloads> 
Where --download_top_popularitydownloads series based on their popularity from most popular to the specified number
Where --episode_limit is the max amount of episodes that will be downloaded from a series (the default is 40)
Where --sequential_download_limit is max concurrent episodes that will be downloaded at once (the default is 25)

