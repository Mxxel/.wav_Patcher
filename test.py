import os
from pprint import pprint
import argparse



def patch_single_audio(file_path):
    try:
        print("New file to get checked and maybe patched: "+file_path)
        with open(file_path, 'rb') as audio_file:
            audio_bytes = bytearray(audio_file.read())

            # Step 2: Check the values of bytes 20 and 21

        if audio_bytes[20] == 0xFE and audio_bytes[21] == 0xFF:
            print("Start patching...")
            # Step 3: Modify the values of bytes 20 and 21
            audio_bytes[20] = 0x01
            audio_bytes[21] = 0x00

            with open(file_path, 'wb') as modified_audio_file:
                modified_audio_file.write(audio_bytes)
            print("Patching done... so maybe just give it a try ;D")
            return True
        else:
            print(file_path + "must not be patched")
            return True
    except Exception as e:
        print("An error occurred during modification:", str(e))
        return None


def scan_for_audiofiles_in_path(_path):
    audio_files = []
    for root, _, files in os.walk(_path):
        for file in files:
            if file.lower().endswith('.wav'):
                audio_files.append(os.path.join(root, file))
    return audio_files


def patch_mutiple_files(pathlist):
    return


def main():
    parser = argparse.ArgumentParser(
        description="A sample script to patch and make our .wav files playable because many cd-players (especially pioneer) won't read them otherwise via USB",
        epilog="Thank you for using this script!",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    input_output_group = parser.add_mutually_exclusive_group(required=True)
    input_output_group.add_argument('-f', '--file', help='Path to the .wav to patch.')
    input_output_group.add_argument('-p', '--path', help='Path to directory that should get, including all subdirectories, recursively scanned and all found .wav files are patched.')
    args = parser.parse_args()

    if args.file:
        if os.path.exists(args.file):
            patch_single_audio("/home/user/PycharmProjects/WaveModder/exopatch.wav")
        else:
            raise FileNotFoundError("File not found")



if __name__ == "__main__":
    main()
