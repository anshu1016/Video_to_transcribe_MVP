# from pyairtable import Api
# import os

# api_key = os.getenv("AIRTABLE_API_KEY")
# base_id = os.getenv("AIRTABLE_BASE_ID")
# table_name = os.getenv("AIRTABLE_TABLE_NAME")

# api = Api(api_key)
# table = api.base(base_id).table(table_name)

# def sync_to_airtable(video_url, audio_url, transcript_url, transcript_text):
#     return table.create({
#         "video_url": video_url,
#         "audio_url": audio_url,
#         "transcribe_url": transcript_url,
#         "transcript_text": transcript_text,
#         "status": "completed"
#     })

from pyairtable import Api
import os

api_key = os.getenv("AIRTABLE_API_KEY")
base_id = os.getenv("AIRTABLE_BASE_ID")
table_name = os.getenv("AIRTABLE_TABLE_NAME")

api = Api(api_key)
table = api.base(base_id).table(table_name)

# Final correct field mapping
def sync_to_airtable(video_url, audio_url, transcript_url, transcript_text):
    return table.create({
        "Video URL": video_url,
        "Audio URL": audio_url,
        "Transcript URL": transcript_url,
        "Transcript JSON": transcript_text,
        "Status": "completed"
    })
