# Vendored from https://github.com/Mxxel/.wav_Patcher (Mxxel / Max Späth).
# Rewrites two header bytes so some Pioneer CD players will load the file
# over USB. Behavior matches that snapshot; the walk-through is in README.md.
import os
from pprint import pprint
import argparse



def patch_single_audio(file_path):
    try:
        print("New file to get checked and maybe patched: "+file_path)
        with open(file_path, 'rb') as audio_file:
            audio_bytes = bytearray(audio_file.read())

            # Step 2: Check the values of bytes 20 and 21

        # Offsets 20 and 21, not a RIFF chunk walk. When the first subchunk is
        # "fmt " (12-byte RIFF/WAVE header, then "fmt " at 12 and the chunk
        # size at 16), this pair is the little-endian format code wFormatTag:
        #   FE FF = 0xFFFE = WAVE_FORMAT_EXTENSIBLE, the files this rewrites
        #   01 00 = 0x0001 = WAVE_FORMAT_PCM, left as they are
        # Any other pair is also left as it is. Chunk size, bit depth, sample
        # rate, and every later byte are not read.
        if audio_bytes[20] == 0xFE and audio_bytes[21] == 0xFF:
            print("Start patching...")
            # Step 3: Modify the values of bytes 20 and 21
            # Relabel the format code as PCM. The extensible tail (extra size,
            # channel mask, subtype GUID) and the sample data stay put.
            audio_bytes[20] = 0x01
            audio_bytes[21] = 0x00

            # Writes the whole buffer back over the same path. No copy.
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


# Finds .wav files under _path, including subfolders. main() never calls it.
def scan_for_audiofiles_in_path(_path):
    audio_files = []
    for root, _, files in os.walk(_path):
        for file in files:
            if file.lower().endswith('.wav'):
                audio_files.append(os.path.join(root, file))
    return audio_files


# Empty. Directory patching is not implemented.
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

    # --path is parsed and then ignored. The directory walk above is unused.
    if args.file:
        if os.path.exists(args.file):
            # -f is only an existence check. The opened file is this hardcoded
            # path from the author's machine, not the path that was passed in.
            patch_single_audio("/home/user/PycharmProjects/WaveModder/exopatch.wav")
        else:
            raise FileNotFoundError("File not found")



if __name__ == "__main__":
    main()
