import cloudinary
import cloudinary.uploader

def upload_to_cloudinary(filepath, folder, public_id, resource_type="auto"):
    response = cloudinary.uploader.upload(
        filepath,
        resource_type=resource_type,
        folder=folder,
        public_id=public_id,
        use_filename=True,
        unique_filename=False,
        overwrite=True
    )
    return response['secure_url']
