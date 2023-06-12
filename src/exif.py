"""
Read the exif data from an image.
"""
import PIL.Image
import PIL.ExifTags
import io

def get_location_tags(image_path: str):
    """Read the exif data from an image into a dicrionary.
    Args: Image as bytes
    Returns: Exif data as dictionary
    """
    img = PIL.Image.open(image_path)
    exif_data = img._getexif()

    if exif_data == None:
        return None
    else:
        return exif_data['location']

    # exif = {
    #     PIL.ExifTags.TAGS[k]: v
    #     for k, v in img._getexif().items()
    #     if k in PIL.ExifTags.TAGS
    # }

    return exif_data 
