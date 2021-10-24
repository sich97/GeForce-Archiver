import os
import shutil
from pathlib import Path
import time
import compress_video
from tqdm import tqdm
import ffmpeg


COMPRESSED_ARCHIVE_SUFFIX = "_archive"

VIDEO_FILETYPES = ["mp4"]


def main():
    source_root_folder = input("Please input the source root folder: ")
    if source_root_folder[-1] == "/":
        source_root_folder = source_root_folder[:-1]

    destination_folder = "/".join(source_root_folder.split("/")[:-1]) + "/" + source_root_folder.split("/")[-1]\
                         + COMPRESSED_ARCHIVE_SUFFIX

    correct_settings = False
    while not correct_settings:
        new_destination_folder = input("Please input the destination folder for the compressed mirror"
                                       " [leave empty to store next to the source root folder]: ")
        if new_destination_folder:
            if new_destination_folder[-1] == "/":
                new_destination_folder = new_destination_folder[:-1]

        source_size = get_folder_size(source_root_folder)
        if new_destination_folder:
            destination_free_space = shutil.disk_usage("/".join(new_destination_folder.split("/")[:-1]))[2]
        else:
            destination_free_space = shutil.disk_usage("/".join(destination_folder.split("/")[:-1]))[2]

        if source_root_folder in new_destination_folder:
            print("To prevent infinite loops, this script does not allow you to store the mirror within the source.")
            print("Please try a different destination folder for the compressed mirror.")

        elif destination_free_space <= source_size:
            print("The destination path is unfortunately too small to guarantee a flawless execution of this script!")
            print("Please try a different destination folder for the compressed mirror.")
        else:
            correct_settings = True
            if new_destination_folder:
                destination_folder = new_destination_folder

    create_compressed_mirror(source_root_folder, destination_folder)


def create_compressed_mirror(source_root_folder, destination_folder):
    """
    Creates a mirror of the source root folder in the destination folder, preserving folder structure,
    compressing video files, and includes originals of all other filetypes.
    :param source_root_folder: The folder from which the mirror will be based on.
    :type source_root_folder: str
    :param destination_folder: The folder in which the mirror will be stored in.
    :type destination_folder: str
    :return: None
    """
    Path(destination_folder).mkdir(parents=True, exist_ok=True)

    total_duration = get_total_compression_duration(source_root_folder, destination_folder)
    bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} seconds compressed [{rate_fmt}{postfix}]: ETA: {eta}"
    progress_bar = tqdm(total=round(total_duration, 2), desc="Total compression progress: ", unit=" seconds",
                        bar_format=bar_format)

    start_time = time.time()
    compress_folder(source_root_folder, destination_folder, progress_bar)
    end_time = time.time()
    elapsed_time = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
    print(f"Total time elapsed: {elapsed_time}")

    progress_bar.close()


def video_should_be_compressed(source_path, destination_path):
    if not os.path.exists(destination_path):
        return True
    else:
        if not float(ffmpeg.probe(destination_path)["format"]["duration"]) ==\
               float(ffmpeg.probe(source_path)["format"]["duration"]):
            return True

    return False


def get_total_compression_duration(source_root_folder, destination_folder):
    total_duration = 0
    try:
        for item in os.listdir(source_root_folder):
            source_path = os.path.join(source_root_folder, item)
            destination_path = os.path.join(destination_folder, item)
            if os.path.isfile(source_path):
                if source_path.split(".")[-1] in VIDEO_FILETYPES:
                    if video_should_be_compressed(source_path, destination_path):
                        total_duration += float(ffmpeg.probe(source_path)['format']['duration'])

            elif os.path.isdir(source_path):
                total_duration += get_total_compression_duration(source_path, destination_path)

    except PermissionError:
        print("Permission Error!")
        input()
    return total_duration


def compress_folder(source_folder, destination_folder, progress_bar):
    """
    Creates a new folder at the destination folder, identical to source folder and its contents,
    except that the video files are compressed.
    :param source_folder: The source folder to compress and mirror over to the destination folder.
    :type source_folder. str
    :param destination_folder: The destination folder.
    :type destination_folder: str
    :param progress_bar: A CLI progress bar to inform the user of the progress so far.
    :type progress_bar: tqdm
    :return: None
    """
    try:
        for item in os.listdir(source_folder):
            source_path = os.path.join(source_folder, item)
            destination_path = os.path.join(destination_folder, item)
            if os.path.isfile(source_path):
                if source_path.split(".")[-1] in VIDEO_FILETYPES:
                    if video_should_be_compressed(source_path, destination_path):

                        # Compress video
                        compress_video.compress_video(source_path, destination_path, progress_bar)

                else:

                    # Copy non-video file
                    if not os.path.exists(destination_path):
                        shutil.copyfile(source_path, destination_path)

            elif os.path.isdir(source_path):
                Path(destination_path).mkdir(parents=True, exist_ok=True)
                compress_folder(source_path, destination_path, progress_bar)

    except PermissionError:
        print("Permission Error!")
        input()


def get_folder_size(folder):
    """
    Returns the total size of the folder.
    :param folder: The folder to find the total size of.
    :type folder: str
    :return: total_size (int)
    """
    total_size = os.path.getsize(folder)
    try:
        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            if os.path.isfile(item_path):
                total_size += os.path.getsize(item_path)
            elif os.path.isdir(item_path):
                total_size += get_folder_size(item_path)

    except PermissionError:
        pass
    return total_size


if __name__ == "__main__":
    main()
